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

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import socketio
import asyncio
import json
import os
from locust_runner import LocustRunner
from port_manager import PortManager
import logging
from msal import ConfidentialClientApplication
from fastapi import Body

# Initialize FastAPI application
app = FastAPI(
    title="Multi-User Load Tester",
    description="A web-based load testing platform with multi-user isolation",
    version="1.0.0"
)

# Configure logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mount static files (CSS, JavaScript, images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configure Jinja2 templates for HTML rendering
templates = Jinja2Templates(directory="app/templates")

# Socket.IO server setup for real-time communication
sio = socketio.AsyncServer(async_mode='asgi')
socket_app = socketio.ASGIApp(sio, app)

# Global session management
# Dictionary to hold active locust runner instances for each user session
runners = {}
timeout_tasks = {}

# Port manager instance to allocate unique ports for each Locust instance
port_manager = PortManager()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Serve the main dashboard page.
    
    Returns the HTML template for the load testing dashboard interface
    where users can configure and monitor their load tests.
    
    Args:
        request (Request): FastAPI request object
        
    Returns:
        HTMLResponse: Rendered HTML template
    """
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logs/{session_id}")
async def get_logs(session_id: str):
    """
    Retrieve the last 100 log entries for a specific user session.
    
    This endpoint provides access to the request logs generated during
    load testing for real-time monitoring and debugging purposes.
    
    Args:
        session_id (str): Unique session identifier (Socket.IO session ID)
        
    Returns:
        dict: JSON response containing:
            - logs (list): List of log line strings (last 100 entries)
            - error (str, optional): Error message if logs cannot be retrieved
    """
    runner = runners.get(session_id)
    if not runner:
        return {"error": "Session not found"}
    
    # Get the log file path associated with this session
    log_file_path = getattr(runner, '_session_log_file', None)
    if not log_file_path or not os.path.exists(log_file_path):
        return {"logs": []}
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Return last 100 lines for efficient display
            return {"logs": [line.strip() for line in lines[-100:]]}
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return {"logs": [], "error": str(e)}

@app.post("/generate_aad_token")
async def generate_aad_token(
    application_id: str = Body(...),
    application_secret: str = Body(...),
    api_scope: str = Body(...)
):
    """
    Generate an Azure Active Directory (AAD) token.
    """
    try:
        authority = "https://login.microsoftonline.com/83ba98e9-2851-416c-9d81-c0bee20bb7f3"
        
        msal_client = ConfidentialClientApplication(
            client_id=application_id,
            authority=authority,
            client_credential=application_secret
        )

        token_response = msal_client.acquire_token_for_client(scopes=[api_scope])
        
        if "access_token" in token_response:
            return {"access_token": token_response["access_token"]}
        else:
            error_description = token_response.get("error_description", "Unknown error")
            return {"error": "Failed to acquire token", "details": error_description}
            
    except Exception as e:
        logger.error(f"Error generating AAD token: {e}")
        return {"error": "An unexpected error occurred", "details": str(e)}

async def stream_locust_stats(sid):
    """
    Stream real-time statistics from a Locust instance to the client.
    
    This function runs as a background task and continuously polls the Locust
    instance for statistics, then emits them to the client via WebSocket.
    
    Args:
        sid (str): Socket.IO session identifier
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
    
    When a client connects, allocate a unique port and create a new
    LocustRunner instance for session isolation.
    
    Args:
        sid (str): Socket.IO session identifier
        environ (dict): WSGI environ dictionary
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
        await sio.emit('test_stopped', {'message': 'Timeout: Stopping load testing for safety reasons (max 10 minutes).  Please contact the administrator if you want to increase the timeout.'}, to=sid)
        await stop_load_test(sid)
        await sio.disconnect(sid)

    task = sio.start_background_task(timeout_task)
    timeout_tasks[sid] = task

@sio.event
async def disconnect(sid):
    """
    Handle client disconnections and clean up resources.
    
    When a client disconnects, stop the associated Locust instance,
    clean up temporary files, and release allocated resources.
    
    Args:
        sid (str): Socket.IO session identifier
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
    
    This function processes user-provided test configuration, validates
    parameters, creates a custom Locust test file, and starts the load test.
    
    Args:
        sid (str): Socket.IO session identifier
        data (dict): Test configuration containing:
            - host (str): Target host URL
            - num_users (int): Number of concurrent users
            - spawn_rate (int): Users spawned per second
            - http_method (str): HTTP method (GET, POST, etc.)
            - route (str): Target endpoint route
            - wait_time (float): Wait time between requests
            - json_payload (str): Optional JSON payload for requests
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
            import tempfile
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
            sio.start_background_task(stream_locust_stats, sid)

        except Exception as e:
            logger.error(f"Error starting load test for {sid}: {e}")
            await sio.emit('error', {'message': str(e)}, to=sid)

@sio.event
async def stop_load_test(sid):
    """
    Stop the load test for a specific user session.
    
    This function gracefully stops the Locust subprocess associated
    with the given session, allowing users to halt their tests.
    
    Args:
        sid (str): Socket.IO session identifier
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
    
    Start the FastAPI application with Uvicorn server when run directly.
    The application binds to all interfaces (0.0.0.0) on port 8000 for
    Docker compatibility and external access.
    """
    import uvicorn
    uvicorn.run(socket_app, host='0.0.0.0', port=8000)
