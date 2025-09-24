from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import socketio
import asyncio
import json
from locust_runner import LocustRunner
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Socket.IO setup
sio = socketio.AsyncServer(async_mode='asgi')
socket_app = socketio.ASGIApp(sio, app)

# Dictionary to hold locust runners for each session
runners = {}

# Port management for unique Locust instances
class PortManager:
    def __init__(self, start_port: int = 8090):
        self._start_port = start_port
        self._used_ports = set()
        self._session_ports = {}
    
    def allocate_port(self, session_id: str) -> int:
        if session_id in self._session_ports:
            return self._session_ports[session_id]
        
        port = self._start_port
        while port in self._used_ports:
            port += 1
        
        self._used_ports.add(port)
        self._session_ports[session_id] = port
        return port
    
    def release_port(self, session_id: str) -> None:
        if session_id in self._session_ports:
            port = self._session_ports[session_id]
            self._used_ports.discard(port)
            del self._session_ports[session_id]

port_manager = PortManager()

def generate_custom_locustfile(http_method: str, route: str, wait_time: float, json_payload: dict = None) -> str:
    """Generate a custom locustfile based on user parameters"""
    
    # Build the request code based on HTTP method
    if http_method == 'GET':
        request_code = f'response = self.client.get("{route}")'
    elif http_method in ['POST', 'PUT', 'PATCH']:
        if json_payload:
            json_str = json.dumps(json_payload, indent=12)  # Extra indent for proper alignment
            request_code = f'''json_data = {json_str}
            response = self.client.{http_method.lower()}("{route}", json=json_data)'''
        else:
            request_code = f'response = self.client.{http_method.lower()}("{route}")'
    elif http_method == 'DELETE':
        request_code = f'response = self.client.delete("{route}")'
    else:
        request_code = f'response = self.client.get("{route}")  # Fallback to GET'

    # Generate the complete locustfile
    locustfile_content = f'''from locust import HttpUser, task, between
import json

class CustomUser(HttpUser):
    wait_time = between({wait_time}, {wait_time + 1})
    
    @task
    def custom_task(self):
        """Custom task generated from user input"""
        try:
            {request_code}
            
            # Log response details
            print(f"{{self.__class__.__name__}} - {{response.status_code}} - {{response.url}}")
            
            # Explicitly mark failures for Locust statistics
            if response.status_code >= 400:
                response.failure(f"HTTP {{response.status_code}}: {{response.text[:100]}}")
                print(f"FAILURE - {{response.status_code}}: {{response.text[:200]}}")
            else:
                print(f"SUCCESS - {{response.status_code}}")
                
        except Exception as e:
            print(f"Request failed: {{str(e)}}")
            # This will automatically be marked as a failure by Locust
'''
    
    return locustfile_content

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

async def stream_locust_stats(sid):
    runner = runners.get(sid)
    if not runner:
        return
    
    try:
        async for stats in runner.stats():
            logger.info(f"Emitting stats for {sid}: {stats}")
            await sio.emit('stats', stats, to=sid)
    except Exception as e:
        logger.error(f"Error streaming stats for {sid}: {e}")

@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")
    port = port_manager.allocate_port(sid)
    logger.info(f"Allocated port {port} for session {sid}")
    runners[sid] = LocustRunner(port=port)

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")
    if sid in runners:
        runner = runners[sid]
        await runner.stop()
        del runners[sid]
        port_manager.release_port(sid)
        logger.info(f"Released port for session {sid}")

@sio.event
async def start_load_test(sid, data):
    logger.info(f"Starting load test for {sid} with data: {data}")
    runner = runners.get(sid)
    if runner:
        try:
            host = data.get('host')
            num_users = int(data.get('num_users'))
            spawn_rate = int(data.get('spawn_rate'))
            
            # Extract custom test parameters
            http_method = data.get('http_method', 'GET').upper()
            route = data.get('route', '/')
            wait_time = float(data.get('wait_time', 1.0))
            json_payload = data.get('json_payload', '').strip()

            if not all([host, num_users, spawn_rate]):
                await sio.emit('error', {'message': 'Missing required parameters.'}, to=sid)
                return

            # Validate JSON payload if provided
            parsed_json = None
            if json_payload:
                try:
                    parsed_json = json.loads(json_payload)
                except json.JSONDecodeError:
                    await sio.emit('error', {'message': 'Invalid JSON payload.'}, to=sid)
                    return

            # Generate custom locustfile for this session
            locustfile_content = generate_custom_locustfile(
                http_method, route, wait_time, parsed_json
            )
            
            await runner.start(host, num_users, spawn_rate, locustfile_content)
            sio.start_background_task(stream_locust_stats, sid)

        except Exception as e:
            logger.error(f"Error starting load test for {sid}: {e}")
            await sio.emit('error', {'message': str(e)}, to=sid)

@sio.event
async def stop_load_test(sid):
    logger.info(f"Stopping load test for {sid}")
    runner = runners.get(sid)
    if runner:
        await runner.stop()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(socket_app, host='0.0.0.0', port=8000)
