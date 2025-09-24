"""Simple default locustfile for basic load testing"""

from locust import HttpUser, task, between

class DefaultUser(HttpUser):
    """Default HTTP user for basic load testing"""
    wait_time = between(1, 5)

    @task
    def index_page(self):
        """Test the index page"""
        response = self.client.get("/")
        
        # Explicitly mark failures for Locust statistics
        if response.status_code >= 400:
            response.failure(f"HTTP {response.status_code}: {response.text[:100]}")
            print(f"FAILURE - DefaultUser - {response.status_code} - {response.url}")
        else:
            print(f"SUCCESS - DefaultUser - {response.status_code} - {response.url}")