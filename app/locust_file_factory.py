"""
Locust File Factory Module

This module provides the LocustFileFactory class for dynamically generating
custom Locust test files based on user-specified parameters. The factory
creates complete, executable Locust test scripts with custom HTTP methods,
routes, payloads, and logging capabilities.

Key Features:
- Support for all HTTP methods (GET, POST, PUT, DELETE, PATCH)
- Dynamic JSON payload handling
- Session-specific logging integration
- Proper error handling and status reporting
- Configurable wait times between requests

Author: JudicaelPoumay
"""

import json
from typing import Dict, Any

class LocustFileFactory:
    """
    Factory class for generating custom Locust test configurations.
    
    This class implements the Factory pattern to create customized Locust
    test files based on user input. Each generated test file is a complete,
    self-contained Python script that can be executed by Locust.
    
    The factory supports various HTTP methods, custom routes, JSON payloads,
    and session-specific logging to provide flexible load testing capabilities.
    """
    
    @staticmethod
    def create_test_config(
        http_method: str, 
        route: str, 
        wait_time: float, 
        json_payload: Dict[Any, Any] = None, 
        log_file_path: str = None,
        bearer_token: str = None
    ) -> str:
        """
        Generate a complete Locust test file based on user parameters.
        
        This method creates a fully functional Locust test script with:
        - Custom HTTP method and route configuration
        - Optional JSON payload handling
        - Session-specific request logging
        - Proper error handling and status reporting
        - Configurable wait times between requests
        
        Args:
            http_method (str): HTTP method to use (GET, POST, PUT, DELETE, PATCH)
            route (str): Target route/endpoint to test
            wait_time (float): Base wait time between requests in seconds
            json_payload (Dict[Any, Any], optional): JSON data for POST/PUT requests
            log_file_path (str, optional): Path for session-specific request logging
            bearer_token (str, optional): Bearer token for authorization headers
            
        Returns:
            str: Complete Locust test file content as executable Python code
            
        Example:
            >>> factory = LocustFileFactory()
            >>> config = factory.create_test_config(
            ...     http_method='POST',
            ...     route='/api/users',
            ...     wait_time=2.0,
            ...     json_payload={'name': 'test', 'email': 'test@example.com'}
            ... )
            >>> print(config)  # Outputs complete Locust test file
        """
        
        # Step 0: Handle Authorization Header
        auth_header_code = ""
        if bearer_token:
            auth_header_code = f'self.client.headers["Authorization"] = f"Bearer {bearer_token}"'

        # Step 1: Generate HTTP request code based on the specified method
        if http_method == 'GET':
            # Simple GET request without payload
            request_code = f'response = self.client.get("{route}")'
        elif http_method in ['POST', 'PUT', 'PATCH']:
            # Methods that typically include request bodies
            if json_payload:
                # Format JSON with proper indentation for readable generated code
                json_str = json.dumps(json_payload, indent=12)  # 12 spaces for alignment
                request_code = f'''json_data = {json_str}
            response = self.client.{http_method.lower()}("{route}", json=json_data)'''
            else:
                # No payload provided for POST/PUT/PATCH request
                request_code = f'response = self.client.{http_method.lower()}("{route}")'
        elif http_method == 'DELETE':
            # DELETE requests typically don't have payloads
            request_code = f'response = self.client.delete("{route}")'
        else:
            # Fallback for unsupported methods - default to GET
            request_code = f'response = self.client.get("{route}")  # Fallback to GET'

        # Step 2: Generate optional logging code for session-specific request tracking
        log_code = ""
        if log_file_path:
            log_code = f'''
            # Log request details to session-specific file
            import datetime
            with open(r"{log_file_path}", "a", encoding="utf-8") as log_file:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_file.write(f"{{timestamp}} - {{response.status_code}} - {{response.url}} - {{response.elapsed.total_seconds():.3f}}s\\n")
                log_file.flush()'''
        
        # Step 3: Generate the complete Locust test file template
        locustfile_content = f'''from locust import HttpUser, task, between
import json
import datetime

class CustomUser(HttpUser):
    # Configure wait time between requests (adds +1 second variance)
    wait_time = between({wait_time}, {wait_time + 1})
    
    def on_start(self):
        """Called when a user starts a test"""
        {auth_header_code}

    @task
    def custom_task(self):
        """Custom task generated from user input"""
        try:
            # Execute the generated HTTP request
            {request_code}
            {log_code}
            
            # Log response details to console for real-time monitoring
            print(f"{{self.__class__.__name__}} - {{response.status_code}} - {{response.url}}")
            
            # Explicitly mark failures for Locust statistics tracking
            if response.status_code >= 400:
                # Mark as failure and log detailed error information
                response.failure(f"HTTP {{response.status_code}}: {{response.text[:100]}}")
                print(f"FAILURE - {{response.status_code}}: {{response.text[:200]}}")
            else:
                # Log successful requests
                print(f"SUCCESS - {{response.status_code}}")
                
        except Exception as e:
            # Handle request exceptions (network errors, timeouts, etc.)
            print(f"Request failed: {{str(e)}}")
            # This will automatically be marked as a failure by Locust
'''
        
        return locustfile_content
