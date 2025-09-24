from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import socketio
import asyncio
import json
import os
from locust_runner_class import LocustRunner
from port_manager import PortManager
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

port_manager = PortManager()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logs/{session_id}")
async def get_logs(session_id: str):
    """Get the trailing log for a specific session"""
    runner = runners.get(session_id)
    if not runner:
        return {"error": "Session not found"}
    
    log_file_path = getattr(runner, '_session_log_file', None)
    if not log_file_path or not os.path.exists(log_file_path):
        return {"logs": []}
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Return last 100 lines
            return {"logs": [line.strip() for line in lines[-100:]]}
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return {"logs": [], "error": str(e)}

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
        
        # Clean up session log file
        session_log_file = getattr(runner, '_session_log_file', None)
        if session_log_file:
            try:
                os.unlink(session_log_file)
                logger.info(f"Cleaned up session log file: {session_log_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up session log file: {e}")
        
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

            # Create a temporary log file for this session
            import tempfile
            fd_log, log_file_path = tempfile.mkstemp(suffix='.log', prefix=f'port_{runners[sid]._locust_port}_')
            os.close(fd_log)
            
            # Generate custom locustfile with logging using the factory
            locustfile_content = runner.create_custom_test(
                http_method, route, wait_time, parsed_json, log_file_path
            )
            
            # Start the runner with the custom locustfile
            await runner.start(host, num_users, spawn_rate, locustfile_content)
            
            # Store the log file path in the runner so we can access it later
            runner._session_log_file = log_file_path
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
