"""Locust runner class for managing Locust subprocess instances"""

import asyncio
import logging
import sys
import tempfile
import os
import aiohttp
from asyncio.subprocess import Process
from typing import Optional, Dict, Any
from locust_file_factory import LocustFileFactory

logger = logging.getLogger(__name__)

class LocustRunner:
    """Manages a Locust subprocess instance for load testing"""
    
    def __init__(self, port: int = 8089) -> None:
        self._process: Optional[Process] = None
        self._stats_queue: Optional[asyncio.Queue] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        self._locust_port = port
        self._temp_locustfile: Optional[str] = None
        self._factory = LocustFileFactory()

    def create_custom_test(self, http_method: str, route: str, wait_time: float, 
                          json_payload: Dict[Any, Any] = None, log_file_path: str = None) -> str:
        """Create a custom test configuration using the factory"""
        return self._factory.create_test_config(http_method, route, wait_time, json_payload, log_file_path)

    async def start(self, host: str, num_users: int, spawn_rate: int, custom_locustfile: str = None) -> None:
        """Start the Locust subprocess with the given parameters"""
        await self.stop()
        
        # Use custom locustfile if provided, otherwise use default
        locustfile_path = "locustfile.py"
        if custom_locustfile:
            # Create temporary locustfile
            fd, self._temp_locustfile = tempfile.mkstemp(suffix='.py', prefix='locust_')
            try:
                with os.fdopen(fd, 'w') as temp_file:
                    temp_file.write(custom_locustfile)
                locustfile_path = self._temp_locustfile
                logger.info(f"Created temporary locustfile: {locustfile_path}")
            except Exception as e:
                logger.error(f"Failed to create temporary locustfile: {e}")
                if self._temp_locustfile:
                    try:
                        os.unlink(self._temp_locustfile)
                    except:
                        pass
                    self._temp_locustfile = None
                raise
        
        command = [
            sys.executable,
            "-u",
            "-m",
            "locust",
            "-f",
            locustfile_path,
            "--host",
            host,
            "--users",
            str(num_users),
            "--spawn-rate",
            str(spawn_rate),
            "--web-host",
            "127.0.0.1",  # Bind only to localhost - not exposed outside container!
            "--web-port",
            str(self._locust_port),
            "--autostart"
        ]
        
        logger.info("Launching locust with web interface: %s", " ".join(command))
        self._stats_queue = asyncio.Queue()
        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Wait a moment for Locust web server to start
        await asyncio.sleep(2)
        
        self._stderr_task = asyncio.create_task(self._consume_stderr())
        self._polling_task = asyncio.create_task(self._poll_stats())

    async def stop(self) -> None:
        """Stop the Locust subprocess and clean up resources"""
        if self._polling_task:
            self._polling_task.cancel()
        if self._stderr_task:
            self._stderr_task.cancel()
            
        tasks = [t for t in (self._polling_task, self._stderr_task) if t]
        
        if self._process and self._process.returncode is None:
            logger.info("Terminating locust subprocess (pid=%s)", self._process.pid)
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("Locust subprocess did not exit in time; killing")
                self._process.kill()
                await self._process.wait()
                
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
                
        self._process = None
        if self._stats_queue:
            await self._stats_queue.put(None)
        self._stats_queue = None
        self._polling_task = None
        self._stderr_task = None
        
        # Clean up temporary locustfile
        if self._temp_locustfile:
            try:
                os.unlink(self._temp_locustfile)
                logger.info(f"Cleaned up temporary locustfile: {self._temp_locustfile}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary locustfile: {e}")
            finally:
                self._temp_locustfile = None

    async def stats(self):
        """Generator that yields statistics from the Locust instance"""
        if not self._stats_queue:
            return
        while True:
            payload = await self._stats_queue.get()
            if payload is None:
                break
            yield payload

    async def _poll_stats(self) -> None:
        """Poll Locust's web API for statistics"""
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Get the main stats data
                    async with session.get(f"http://localhost:{self._locust_port}/stats/requests") as response:
                        if response.status == 200:
                            data = await response.json()
                            stats = data.get("stats", [])
                            total_stats = next((s for s in stats if s.get("name") == "Aggregated"), None)
                            
                            if total_stats and self._stats_queue:
                                # Calculate failure ratio
                                num_failures = total_stats.get("num_failures", 0)
                                num_requests = total_stats.get("num_requests", 0)
                                fail_ratio = (num_failures / num_requests * 100) if num_requests > 0 else 0

                                payload = {
                                    "user_count": data.get("user_count", 0),
                                    "total_rps": total_stats.get("current_rps", 0),
                                    "fail_ratio": fail_ratio,
                                    "total_avg_response_time": total_stats.get("avg_response_time", 0),
                                }
                                
                                await self._stats_queue.put(payload)
                            
                except Exception as e:
                    logger.debug("Error polling Locust stats: %s", e)
                
                await asyncio.sleep(1)

    async def _consume_stderr(self) -> None:
        """Consume stderr from the Locust subprocess"""
        assert self._process and self._process.stderr
        try:
            while True:
                line = await self._process.stderr.readline()
                if not line:
                    break
                logger.debug("Locust stderr: %s", line.decode().rstrip())
        except Exception:
            pass
