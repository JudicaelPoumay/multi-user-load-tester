from locust import HttpUser, task, between

class DefaultUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def index_page(self):
        response = self.client.get("/")
        
        # Explicitly mark failures for Locust statistics
        if response.status_code >= 400:
            response.failure(f"HTTP {response.status_code}: {response.text[:100]}")
        
        print(f"DefaultUser - {response.status_code} - {response.url}")
