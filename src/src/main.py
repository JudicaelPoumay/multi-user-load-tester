"""
Multi-User Load Testing Application

A FastAPI-based web application that provides isolated load testing capabilities
for multiple concurrent users. Each user session gets its own Locust instance
with custom test configurations.

Key Features:
- Multi-user isolation with separate Locust instances
- Real-time statistics via WebSocket
- Custom test configuration (HTTP methods, routes, JSON payloads)
- Session-based logging and monitoring
- Automatic resource cleanup

Author: JudicaelPoumay
"""
import asyncio
import json
import logging
import os
import tempfile
from typing import Optional, Dict, Any

import jwt
import socketio
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from itsdangerous import URLSafeSerializer
from msal import ConfidentialClientApplication
from pydantic import BaseModel

from locust_runner import LocustRunner
from port_manager import PortManager

# from security.belfius_security import get_user_groups_memberships, get_userinfo
# from security.belfius_sso_azure import azure, make_azure_blueprint


# Initialize FastAPI application
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Configure logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Socket.IO server setup for real-time communication
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins="*")
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)


# Global session management
# Dictionary to hold active locust runner instances for each user session
runners: Dict[str, LocustRunner] = {}
timeout_tasks: Dict[str, asyncio.Task] = {}

# Port manager instance to allocate unique ports for each Locust instance
port_manager = PortManager()


# --- Authentication Configuration ---
CLIENT_ID = os.environ.get("APPLICATION_ID")
CLIENT_SECRET = os.environ.get("APPLICATION_SECRET")
TENANT_ID = "83ba98e9-2851-416c-9d81-c0bee20bb7f3"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = [os.environ.get("BACKEND_APPLICATION_SCOPE", "api://your-app-id/.default")]
REDIRECT_PATH = "/auth/callback"

# Session management
SECRET_KEY = os.environ.get("APPLICATION_SIGNATURE_KEY", "a_very_secret_key")
serializer = URLSafeSerializer(SECRET_KEY)


msal_client = ConfidentialClientApplication(
    client_id=CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET
)


# --- Authentication Middleware and Dependencies ---
async def get_session(request: Request):
    session_cookie = request.cookies.get("session")
    if session_cookie:
        try:
            return serializer.loads(session_cookie)
        except Exception:
            return {}
    return {}


async def get_current_user(session: dict = Depends(get_session)):
    if "user" not in session:
        return None
    # TODO: Check for token expiry
    return session["user"]


async def require_auth(request: Request, user: dict = Depends(get_current_user)):
    if not user:
        # Store original URL to redirect after SSO
        session = await get_session(request)
        session["next_url"] = str(request.url)
        response = RedirectResponse(url="/login")
        response.set_cookie(key="session", value=serializer.dumps(session))
        return response
    return user


@app.get("/login")
async def login(request: Request):
    session = await get_session(request)
    auth_url_params = {
        "scope": SCOPE,
        "response_type": "code",
        "redirect_uri": str(request.url_for('auth_callback')),
    }
    auth_url = msal_client.get_authorization_request_url(**auth_url_params)
    session["state"] = auth_url_params.get("state") # MSAL generates a state
    response = RedirectResponse(url=auth_url)
    response.set_cookie(key="session", value=serializer.dumps(session))
    return response

@app.get("/auth/callback", name="auth_callback")
async def auth_callback(request: Request, code: str, state: str):
    session = await get_session(request)
    if state != session.get("state"):
        raise HTTPException(status_code=400, detail="State mismatch")

    try:
        token_response = msal_client.acquire_token_by_authorization_code(
            code,
            scopes=SCOPE,
            redirect_uri=str(request.url_for('auth_callback'))
        )

        if "access_token" in token_response:
            id_token_claims = jwt.decode(token_response['id_token'], options={"verify_signature": False})
            session["user"] = {
                "name": id_token_claims.get("name"),
                "email": id_token_claims.get("preferred_username"),
                "oid": id_token_claims.get("oid"),
                "roles": id_token_claims.get("roles", []),
            }
            session["access_token"] = token_response["access_token"]

            next_url = session.get("next_url", "/")
            response = RedirectResponse(url=next_url)
            response.set_cookie(key="session", value=serializer.dumps(session))
            return response
        else:
            logger.error(f"Error acquiring token: {token_response.get('error_description')}")
            raise HTTPException(status_code=400, detail="Failed to acquire token.")

    except Exception as e:
        logger.error(f"Error during token acquisition: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def check_user_groups_fastapi(user: dict) -> bool:
    if not user:
        return False

    email_nickname = user.get("email", "").split("@")[0].lower()
    ALLOWED_USERS = ["baerta", "poumaj", "poullj"]

    if email_nickname in ALLOWED_USERS:
        return True

    required_groups = ['LoadTesterUser']
    user_roles = user.get("roles", [])
    if any(role in user_roles for role in required_groups):
        return True

    return False

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: dict = Depends(require_auth)):
    if isinstance(user, RedirectResponse):
        return user
    
    if not check_user_groups_fastapi(user):
        return templates.TemplateResponse("403.html", {"request": request}, status_code=403)

    return templates.TemplateResponse("index.html", {"request": request, "user": user})


@app.get("/logs/{session_id}")
async def get_logs(session_id: str, user: dict = Depends(require_auth)):
    """
    Retrieve the last 100 log entries for a specific user session.
    """
    runner = runners.get(session_id)
    if not runner:
        raise HTTPException(status_code=404, detail="Session not found")

    log_file_path = getattr(runner, '_session_log_file', None)
    if not log_file_path or not os.path.exists(log_file_path):
        return JSONResponse(content={"logs": []})

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return JSONResponse(content={"logs": [line.strip() for line in lines[-100:]]})
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading log file: {e}")


class AADTokenRequest(BaseModel):
    application_id: str
    application_secret: str
    api_scope: str


@app.post("/generate_aad_token")
async def generate_aad_token(token_request: AADTokenRequest, user: dict = Depends(require_auth)):
    """
    Generate an Azure Active Directory (AAD) token.
    """
    try:
        authority = "https://login.microsoftonline.com/83ba98e9-2851-416c-9d81-c0bee20bb7f3"

        msal_client = ConfidentialClientApplication(
            client_id=token_request.application_id,
            authority=authority,
            client_credential=token_request.application_secret
        )

        token_response = msal_client.acquire_token_for_client(scopes=[token_request.api_scope])

        if "access_token" in token_response:
            return JSONResponse(content={"access_token": token_response["access_token"]})
        else:
            error_description = token_response.get("error_description", "Unknown error")
            raise HTTPException(status_code=400, detail=f"Failed to acquire token: {error_description}")

    except Exception as e:
        logger.error(f"Error generating AAD token: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")


async def stream_locust_stats(sid):
    """
    Stream real-time statistics from a Locust instance to the client.
    """
    runner = runners.get(sid)
    if not runner:
        return

    try:
        # Continuously stream statistics until the session ends
        async for stats in runner.stats():
            logger.info(f"Emitting stats for {sid}: {stats}")
            await sio.emit('stats', stats, to=sid)
    except Exception as e:
        logger.error(f"Error streaming stats for {sid}: {e}")


@sio.event
async def connect(sid, environ):
    """
    Handle new client connections.
    """
    logger.info(f"Client connected: {sid}")

    # Allocate a unique port for this user's Locust instance
    port = port_manager.allocate_port(sid)
    logger.info(f"Allocated port {port} for session {sid}")

    # Create a new isolated LocustRunner for this session
    runners[sid] = LocustRunner(port=port)

    async def timeout_task():
        await asyncio.sleep(600)
        logger.info(f"Timeout for session {sid}. Disconnecting client.")
        await sio.emit('test_stopped', {'message': 'Timeout: Stopping load testing for safety reasons (max 10 minutes). Please contact the administrator if you want to increase the timeout.'}, to=sid)
        await handle_stop_load_test(sid, None)
        await sio.disconnect(sid)

    task = asyncio.create_task(timeout_task())
    timeout_tasks[sid] = task


@sio.event
async def disconnect(sid):
    """
    Handle client disconnections and clean up resources.
    """
    logger.info(f"Client disconnected: {sid}")

    if sid in timeout_tasks:
        timeout_tasks[sid].cancel()
        del timeout_tasks[sid]

    if sid in runners:
        runner = runners[sid]

        # Stop the Locust subprocess
        await runner.stop()

        # Clean up session-specific log file
        session_log_file = getattr(runner, '_session_log_file', None)
        if session_log_file:
            try:
                os.unlink(session_log_file)
                logger.info(f"Cleaned up session log file: {session_log_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up session log file: {e}")

        # Remove runner from active sessions and release port
        del runners[sid]
        port_manager.release_port(sid)
        logger.info(f"Released port for session {sid}")


@sio.event
async def start_load_test(sid, data):
    """
    Start a custom load test for a specific user session.
    """
    logger.info(f"Starting load test for {sid} with data: {data}")
    runner = runners.get(sid)
    if runner:
        try:
            # Extract and validate required parameters
            host = data.get('host')
            num_users = int(data.get('num_users'))
            spawn_rate = int(data.get('spawn_rate'))

            # Extract custom test parameters with defaults
            http_method = data.get('http_method', 'GET').upper()
            route = data.get('route', '/')
            wait_time = float(data.get('wait_time', 1.0))
            json_payload = data.get('json_payload', '').strip()

            # Validate required parameters
            if not all([host, num_users, spawn_rate]):
                await sio.emit('error', {'message': 'Missing required parameters.'}, to=sid)
                return

            # Validate and parse JSON payload if provided
            parsed_json = None
            if json_payload:
                try:
                    parsed_json = json.loads(json_payload)
                except json.JSONDecodeError:
                    await sio.emit('error', {'message': 'Invalid JSON payload.'}, to=sid)
                    return

            # Get bearer token if provided
            bearer_token = data.get('bearer_token', '').strip()

            # Create a temporary log file for session-specific request logging
            fd_log, log_file_path = tempfile.mkstemp(
                suffix='.log',
                prefix=f'port_{runners[sid]._locust_port}_'
            )
            os.close(fd_log)

            # Generate custom locustfile using the factory pattern
            locustfile_content = runner.create_custom_test(
                http_method, route, wait_time, parsed_json, log_file_path, bearer_token
            )

            # Start the Locust subprocess with the custom configuration
            await runner.start(host, num_users, spawn_rate, locustfile_content)

            # Store log file reference for later access via REST API
            runner._session_log_file = log_file_path

            # Start background task to stream real-time statistics
            asyncio.create_task(stream_locust_stats(sid))

        except Exception as e:
            logger.error(f"Error starting load test for {sid}: {e}")
            await sio.emit('error', {'message': str(e)}, to=sid)


@sio.event
async def stop_load_test(sid, data):
    """
    Stop the load test for a specific user session.
    """
    logger.info(f"Stopping load test for {sid}")
    runner = runners.get(sid)
    if runner:
        try:
            await runner.stop()
        except Exception as e:
            logger.error(f"Error stopping load test for {sid}: {e}")
            await sio.emit('error', {'message': str(e)}, to=sid)


if __name__ == '__main__':
    """
    Application entry point.
    """
    uvicorn.run(socket_app, host='0.0.0.0', port=8080)
