"""
Locust Runner Class Module

This module provides the LocustRunner class for managing isolated Locust subprocess
instances. Each runner handles a single user session with its own Locust process,
ensuring complete isolation between concurrent users.

Key Features:
- Subprocess management with proper cleanup
- Real-time statistics polling via HTTP API
- Custom test file generation and execution
- Automatic resource management and error handling
- Session-specific logging and monitoring

Author: JudicaelPoumay
"""

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
    """
    Manages a Locust subprocess instance for isolated load testing.
    
    This class handles the complete lifecycle of a Locust process, from creation
    to cleanup, providing real-time statistics and custom test configuration
    capabilities. Each instance is isolated to a specific user session.
    
    Attributes:
        _process: The asyncio subprocess running Locust
        _stats_queue: Queue for streaming statistics to clients
        _polling_task: Background task for polling Locust stats
        _stderr_task: Background task for consuming stderr output
        _locust_port: Unique port assigned to this Locust instance
        _temp_locustfile: Path to temporary test file (if created)
        _factory: Factory instance for generating custom test configurations
    """
    
    def __init__(self, port: int = 8089) -> None:
        """
        Initialize a new LocustRunner instance.
        
        Args:
            port (int): Unique port number for this Locust web interface.
                       Each runner must have a different port for isolation.
        """
        # Subprocess and task management
        self._process: Optional[Process] = None
        self._stats_queue: Optional[asyncio.Queue] = None
        self._polling_task: Optional[asyncio.Task] = None
        self._stderr_task: Optional[asyncio.Task] = None
        
        # Configuration
        self._locust_port = port
        self._temp_locustfile: Optional[str] = None
        
        # Factory for generating custom test configurations
        self._factory = LocustFileFactory()

    def create_custom_test(self, http_method: str, route: str, wait_time: float, 
                          json_payload: Dict[Any, Any] = None, log_file_path: str = None) -> str:
        """
        Create a custom test configuration using the factory pattern.
        
        This method delegates to the LocustFileFactory to generate a complete
        Locust test file based on user-specified parameters.
        
        Args:
            http_method (str): HTTP method (GET, POST, PUT, DELETE, PATCH)
            route (str): Target endpoint route/path
            wait_time (float): Wait time between requests in seconds
            json_payload (Dict[Any, Any], optional): JSON payload for POST/PUT requests
            log_file_path (str, optional): Path to session-specific log file
            
        Returns:
            str: Complete Locust test file content as a string
        """
        return self._factory.create_test_config(http_method, route, wait_time, json_payload, log_file_path)

    async def start(self, host: str, num_users: int, spawn_rate: int, custom_locustfile: str = None) -> None:
        """
        Start the Locust subprocess with specified parameters.
        
        This method creates and launches a new Locust process with the given
        configuration. It handles both custom test files and default configurations.
        
        Args:
            host (str): Target host URL for load testing
            num_users (int): Maximum number of concurrent users
            spawn_rate (int): Rate at which users are spawned (users/second)
            custom_locustfile (str, optional): Custom Locust test file content.
                                             If None, uses the default locustfile.py
                                             
        Raises:
            Exception: If the Locust process cannot be started or temporary files fail
        """
        # Ensure any existing process is stopped first
        await self.stop()
        
        # Determine which locustfile to use
        locustfile_path = "locustfile.py"  # Default fallback
        
        if custom_locustfile:
            # Create a temporary file for the custom test configuration
            fd, self._temp_locustfile = tempfile.mkstemp(suffix='.py', prefix='locust_')
            try:
                # Write the custom test content to the temporary file
                with os.fdopen(fd, 'w') as temp_file:
                    temp_file.write(custom_locustfile)
                locustfile_path = self._temp_locustfile
                logger.info(f"Created temporary locustfile: {locustfile_path}")
            except Exception as e:
                logger.error(f"Failed to create temporary locustfile: {e}")
                # Clean up on failure
                if self._temp_locustfile:
                    try:
                        os.unlink(self._temp_locustfile)
                    except:
                        pass
                    self._temp_locustfile = None
                raise
        
        # Build the Locust command with all necessary parameters
        command = [
            sys.executable,
            "-u",                           # Unbuffered stdout/stderr
            "-m",                           # Run module
            "locust",
            "-f",                           # Locustfile path
            locustfile_path,
            "--host",                       # Target host
            host,
            "--users",                      # Maximum concurrent users
            str(num_users),
            "--spawn-rate",                 # Users spawned per second
            str(spawn_rate),
            "--web-host",                   # Web interface bind address
            "127.0.0.1",                   # Bind only to localhost for security
            "--web-port",                   # Web interface port
            str(self._locust_port),
            "--autostart"                   # Start test automatically
        ]
        
        logger.info("Launching locust with web interface: %s", " ".join(command))
        
        # Initialize the statistics queue for real-time data streaming
        self._stats_queue = asyncio.Queue()
        
        # Create and start the Locust subprocess
        self._process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        # Wait a moment for Locust web server to initialize
        await asyncio.sleep(2)
        
        # Start background tasks for monitoring the subprocess
        self._stderr_task = asyncio.create_task(self._consume_stderr())
        self._polling_task = asyncio.create_task(self._poll_stats())

    async def stop(self) -> None:
        """
        Gracefully stop the Locust subprocess and clean up all resources.
        
        This method handles the complete shutdown process including:
        - Cancelling background tasks
        - Terminating the Locust process
        - Cleaning up temporary files
        - Resetting internal state
        
        The method is idempotent and safe to call multiple times.
        """
        # Cancel background monitoring tasks
        if self._polling_task:
            self._polling_task.cancel()
        if self._stderr_task:
            self._stderr_task.cancel()
            
        # Collect tasks for cleanup
        tasks = [t for t in (self._polling_task, self._stderr_task) if t]
        
        # Terminate the Locust subprocess if running
        if self._process and self._process.returncode is None:
            logger.info("Terminating locust subprocess (pid=%s)", self._process.pid)
            self._process.terminate()
            try:
                # Wait for graceful shutdown with timeout
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                # Force kill if graceful shutdown fails
                logger.warning("Locust subprocess did not exit in time; killing")
                self._process.kill()
                await self._process.wait()
                
        # Wait for background tasks to complete/cancel
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass  # Expected when tasks are cancelled
                
        # Reset internal state
        self._process = None
        if self._stats_queue:
            await self._stats_queue.put(None)  # Signal end of stats stream
        self._stats_queue = None
        self._polling_task = None
        self._stderr_task = None
        
        # Clean up temporary locustfile if created
        if self._temp_locustfile:
            try:
                os.unlink(self._temp_locustfile)
                logger.info(f"Cleaned up temporary locustfile: {self._temp_locustfile}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary locustfile: {e}")
            finally:
                self._temp_locustfile = None

    async def stats(self):
        """
        Async generator that yields real-time statistics from the Locust instance.
        
        This method provides a stream of statistics data that can be consumed
        by clients for real-time monitoring. The generator continues until the
        Locust instance is stopped or an error occurs.
        
        Yields:
            dict: Statistics payload containing:
                - user_count (int): Current number of active users
                - total_rps (float): Requests per second
                - fail_ratio (float): Failure percentage (0-100)
                - total_avg_response_time (float): Average response time in ms
                
        Returns:
            None: If no stats queue is available (process not started)
        """
        if not self._stats_queue:
            return
        while True:
            payload = await self._stats_queue.get()
            if payload is None:  # Sentinel value indicating end of stream
                break
            yield payload

    async def _poll_stats(self) -> None:
        """
        Background task that continuously polls Locust's web API for statistics.
        
        This method runs as a background task and fetches statistics from the
        Locust web interface every second. The data is processed and queued
        for consumption by the stats() generator method.
        
        The polling continues until the task is cancelled or the process stops.
        Errors are logged but don't stop the polling to maintain resilience.
        """
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    # Query Locust's built-in statistics API endpoint
                    async with session.get(f"http://localhost:{self._locust_port}/stats/requests") as response:
                        if response.status == 200:
                            data = await response.json()
                            stats = data.get("stats", [])
                            
                            # Find the aggregated statistics entry
                            total_stats = next((s for s in stats if s.get("name") == "Aggregated"), None)
                            
                            if total_stats and self._stats_queue:
                                # Calculate failure ratio as percentage
                                num_failures = total_stats.get("num_failures", 0)
                                num_requests = total_stats.get("num_requests", 0)
                                fail_ratio = (num_failures / num_requests * 100) if num_requests > 0 else 0

                                # Create standardized payload for client consumption
                                payload = {
                                    "user_count": data.get("user_count", 0),
                                    "total_rps": total_stats.get("current_rps", 0),
                                    "fail_ratio": fail_ratio,
                                    "total_avg_response_time": total_stats.get("avg_response_time", 0),
                                }
                                
                                # Queue the statistics for streaming to clients
                                await self._stats_queue.put(payload)
                            
                except Exception as e:
                    # Log errors but continue polling for resilience
                    logger.debug("Error polling Locust stats: %s", e)
                
                # Poll every second for responsive real-time updates
                await asyncio.sleep(1)

    async def _consume_stderr(self) -> None:
        """
        Background task that consumes stderr output from the Locust subprocess.
        
        This method runs as a background task to continuously read and log
        stderr output from the Locust process. This prevents the subprocess
        from blocking on stderr buffer fills and provides debugging information.
        
        All stderr output is logged at debug level for troubleshooting.
        The task gracefully handles process termination and exceptions.
        """
        assert self._process and self._process.stderr
        try:
            while True:
                # Read stderr line by line
                line = await self._process.stderr.readline()
                if not line:  # EOF indicates process termination
                    break
                # Log stderr output for debugging purposes
                logger.debug("Locust stderr: %s", line.decode().rstrip())
        except Exception:
            # Silently handle exceptions (process may have terminated)
            pass
