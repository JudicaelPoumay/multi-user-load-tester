"""
Default Locust Test Configuration

This file provides a simple, default Locust test configuration for basic load testing.
It serves as a fallback when no custom test configuration is specified by the user.

The default test performs basic HTTP GET requests to the root endpoint with configurable
wait times and proper error handling. This file can be used independently with Locust
or as a reference for creating custom test configurations.

Key Features:
- Simple GET request to root endpoint
- Configurable wait times between requests
- Proper error handling and status reporting
- Console logging for real-time monitoring

Usage:
    # Run with Locust directly:
    locust -f locustfile.py --host https://example.com
    
    # Or use as fallback in the web application when no custom config is provided

Author: JudicaelPoumay
"""

from locust import HttpUser, task, between

class DefaultUser(HttpUser):
    """
    Default HTTP user class for basic load testing scenarios.
    
    This user performs simple GET requests to the root endpoint of the target
    application. It includes proper error handling, status reporting, and
    configurable wait times between requests.
    
    The class serves as a simple baseline test that can be used when users
    don't specify custom test parameters, ensuring that basic load testing
    functionality is always available.
    
    Attributes:
        wait_time: Random wait time between requests (1-5 seconds)
    """
    
    # Configure wait time between requests (adds variance for realistic testing)
    wait_time = between(1, 5)

    @task
    def index_page(self):
        """
        Test the index/root page of the target application.
        
        This task performs a simple HTTP GET request to the root endpoint ("/")
        and handles the response appropriately. Success and failure cases are
        explicitly tracked and logged for monitoring purposes.
        
        The task includes:
        - HTTP GET request to root endpoint
        - Response status code validation
        - Explicit failure marking for Locust statistics
        - Console logging for real-time monitoring
        """
        # Perform HTTP GET request to the root endpoint
        response = self.client.get("/")
        
        # Handle response based on status code
        if response.status_code >= 400:
            # Mark HTTP 4xx/5xx responses as failures for Locust statistics
            response.failure(f"HTTP {response.status_code}: {response.text[:100]}")
            print(f"FAILURE - DefaultUser - {response.status_code} - {response.url}")
        else:
            # Log successful responses (2xx/3xx status codes)
            print(f"SUCCESS - DefaultUser - {response.status_code} - {response.url}")