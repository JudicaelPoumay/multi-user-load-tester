"""
Multi-User Load Testing Application

A Flask-based web application that provides isolated load testing capabilities
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

from flask import Flask, request, jsonify, render_template, session, has_request_context,redirect, url_for
from flask_socketio import SocketIO
import jwt
import asyncio
import json
import os
from locust_runner import LocustRunner
from port_manager import PortManager
import logging
from msal import ConfidentialClientApplication, TokenCache
from werkzeug.middleware.proxy_fix import ProxyFix
from security.belfius_security import get_user_groups_memberships, get_userinfo
from flask_dance.consumer import oauth_authorized
from security.belfius_sso_azure import azure, make_azure_blueprint
from asgiref.wsgi import WsgiToAsgi

# Initialize Flask application
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


# Configure logging for the application
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Socket.IO server setup for real-time communication
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Global session management
# Dictionary to hold active locust runner instances for each user session
runners = {}
timeout_tasks = {}

# Port manager instance to allocate unique ports for each Locust instance
port_manager = PortManager()

REDIRECT_PATH = "/getAToken"  # Used for forming an absolute URL to your redirect URI

app.config.update(SECRET_KEY=os.environ.get("APPLICATION_SIGNATURE_KEY"))

blueprint = make_azure_blueprint(
    client_id=os.environ.get("APPLICATION_ID"),
    client_secret=os.environ.get("APPLICATION_SECRET"),
    tenant="83ba98e9-2851-416c-9d81-c0bee20bb7f3",
    domain_hint="belfius.be",
    scope=[os.environ.get("BACKEND_APPLICATION_SCOPE")],
)

client = ConfidentialClientApplication(
    client_id=os.environ.get("APPLICATION_ID"),
    authority="https://login.microsoftonline.com/83ba98e9-2851-416c-9d81-c0bee20bb7f3",
    client_credential=os.environ.get("APPLICATION_SECRET")
)


sso_prefix = "/login"
app.register_blueprint(blueprint, url_prefix=sso_prefix)

@oauth_authorized.connect
def redirect_to_next_url(blueprint, token):
    """
    Make sure we redirect to the original url when SSO is completed
    """

    print("redirect_to_next_url :", str(token), flush=True)
    blueprint.token = token
    session["access_token"] = token.get("access_token")
    id_claims = jwt.decode(token.get("id_token"), options={"verify_signature": False})
    session["user_id"] = id_claims.get("mailnickname")
    next_url = session["next_url"]
    return redirect(next_url)

def check_user_groups():
    if has_request_context():
        user_info = get_userinfo()
        ALLOWED_USERS = ["baerta", "poumaj", "poullj"]

        if ALLOWED_USERS and user_info:
            print(ALLOWED_USERS)
            print(user_info.get("userid").lower())
            if user_info and user_info.get("userid").lower() in ALLOWED_USERS:
                return True

        required_groups = ['LoadTesterUser']
        groups = get_user_groups_memberships()
        if(groups):
            return any([role in groups for role in required_groups])
        return False
    return False

def login_required(func):
    def check_authorization(*args, **kwargs):
        if not azure.authorized or azure.token.get("expires_in") < 0:
            # Save original URL to redirect after SSO
            session["next_url"] = request.path
            if len(request.args) > 0:
                session["next_url"] = (
                    session["next_url"] + "?" + urlparse.urlencode(request.args)
                )

            # redirect to azure login page
            return redirect(url_for("azure.login"))
        else:
            return func(*args, **kwargs)

    return check_authorization

@app.route("/")
@login_required
def index():
    if not check_user_groups():
        return render_template("403.html"), 403
    return render_template("index.html")

@app.route("/logs/<session_id>")
def get_logs(session_id):
    """
    Retrieve the last 100 log entries for a specific user session.
    """
    runner = runners.get(session_id)
    if not runner:
        return jsonify({"error": "Session not found"}), 404

    # Get the log file path associated with this session
    log_file_path = getattr(runner, '_session_log_file', None)
    if not log_file_path or not os.path.exists(log_file_path):
        return jsonify({"logs": []})

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Return last 100 lines for efficient display
            return jsonify({"logs": [line.strip() for line in lines[-100:]]})
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return jsonify({"logs": [], "error": str(e)}), 500

@app.route("/generate_aad_token", methods=["POST"])
def generate_aad_token():
    """
    Generate an Azure Active Directory (AAD) token.
    """
    try:
        data = request.get_json()
        application_id = data.get("application_id")
        application_secret = data.get("application_secret")
        api_scope = data.get("api_scope")

        authority = "https://login.microsoftonline.com/83ba98e9-2851-416c-9d81-c0bee20bb7f3"

        msal_client = ConfidentialClientApplication(
            client_id=application_id,
            authority=authority,
            client_credential=application_secret
        )

        token_response = msal_client.acquire_token_for_client(scopes=[api_scope])

        if "access_token" in token_response:
            return jsonify({"access_token": token_response["access_token"]})
        else:
            error_description = token_response.get("error_description", "Unknown error")
            return jsonify({"error": "Failed to acquire token", "details": error_description}), 400

    except Exception as e:
        logger.error(f"Error generating AAD token: {e}")
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

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
            socketio.emit('stats', stats, to=sid)
    except Exception as e:
        logger.error(f"Error streaming stats for {sid}: {e}")

@socketio.on('connect')
def handle_connect(sid):
    """
    Handle new client connections.
    """
    logger.info(f"Client connected: {sid}")

    # Allocate a unique port for this user's Locust instance
    port = port_manager.allocate_port(sid)
    logger.info(f"Allocated port {port} for session {sid}")

    # Create a new isolated LocustRunner for this session
    runners[sid] = LocustRunner(port=port)

    def timeout_task():
        socketio.sleep(600)
        logger.info(f"Timeout for session {sid}. Disconnecting client.")
        socketio.emit('test_stopped', {'message': 'Timeout: Stopping load testing for safety reasons (max 10 minutes). Please contact the administrator if you want to increase the timeout.'}, to=sid)
        stop_load_test(sid)
        socketio.disconnect(sid)

    task = socketio.start_background_task(timeout_task)
    timeout_tasks[sid] = task

@socketio.on('disconnect')
def handle_disconnect(sid):
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
        asyncio.run(runner.stop())

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

@socketio.on('start_load_test')
def handle_start_load_test(sid, data):
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
                socketio.emit('error', {'message': 'Missing required parameters.'}, to=sid)
                return

            # Validate and parse JSON payload if provided
            parsed_json = None
            if json_payload:
                try:
                    parsed_json = json.loads(json_payload)
                except json.JSONDecodeError:
                    socketio.emit('error', {'message': 'Invalid JSON payload.'}, to=sid)
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
            asyncio.run(runner.start(host, num_users, spawn_rate, locustfile_content))

            # Store log file reference for later access via REST API
            runner._session_log_file = log_file_path

            # Start background task to stream real-time statistics
            socketio.start_background_task(stream_locust_stats, sid)

        except Exception as e:
            logger.error(f"Error starting load test for {sid}: {e}")
            socketio.emit('error', {'message': str(e)}, to=sid)

@socketio.on('stop_load_test')
def handle_stop_load_test(sid):
    """
    Stop the load test for a specific user session.
    """
    
    logger.info(f"Stopping load test for {sid}")

    runner = runners.get(sid)
    if runner:
        try:
            asyncio.run(runner.stop())
        except Exception as e:
            logger.error(f"Error stopping load test for {sid}: {e}")
            socketio.emit('error', {'message': str(e)}, to=sid)


asgi = WsgiToAsgi(app)

if __name__ == '__main__':
    """
    Application entry point.
    """
    socketio.run(app, host='0.0.0.0', port=8080)
