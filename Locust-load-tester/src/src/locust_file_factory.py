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
        
        # Step 1: Read the template file
        with open("app/locustfile_sample.py", "r", encoding="utf-8") as f:
            template = f.read()

        # Step 2: Prepare variable replacements
        replacements = {
            "{HTTP_METHOD}": http_method,
            "{ROUTE}": route,
            "{JSON_PAYLOAD}": json.dumps(json_payload) if json_payload else "None",
            "{BEARER_TOKEN}": f'"{bearer_token}"' if bearer_token else "None",
            "{LOG_FILE_PATH}": f'r"{log_file_path}"' if log_file_path else "None",
            "{WAIT_TIME_MIN}": str(wait_time),
            "{WAIT_TIME_MAX}": str(wait_time + 1),
        }

        # Step 3: Replace placeholders in the template
        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)
        
        return template
