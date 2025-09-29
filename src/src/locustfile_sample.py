from locust import HttpUser, task, between
import json
import datetime

class CustomUser(HttpUser):
    # --- User-defined variables ---
    HTTP_METHOD = "{HTTP_METHOD}"
    ROUTE = "{ROUTE}"
    JSON_PAYLOAD = {JSON_PAYLOAD}
    BEARER_TOKEN = {BEARER_TOKEN}
    LOG_FILE_PATH = {LOG_FILE_PATH}
    # ------------------------------
    
    wait_time = between({WAIT_TIME_MIN}, {WAIT_TIME_MAX})

    def on_start(self):
        """Called when a user starts a test"""
        if self.BEARER_TOKEN:
            self.client.headers["Authorization"] = f"Bearer {self.BEARER_TOKEN}"
            self.client.headers["X-Access-Token"] = self.BEARER_TOKEN

    @task
    def custom_task(self):
        """Custom task generated from user input"""
        try:
            kwargs = {}
            if self.HTTP_METHOD in ['POST', 'PUT', 'PATCH'] and self.JSON_PAYLOAD:
                kwargs['json'] = self.JSON_PAYLOAD

            response = self.client.request(method=self.HTTP_METHOD, url=self.ROUTE, **kwargs)

            if self.LOG_FILE_PATH:
                # Log request details to session-specific file
                import datetime
                with open(self.LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    log_file.write(f"{timestamp} - {response.status_code} - {response.url} - {response.elapsed.total_seconds():.3f}s\n")
                    log_file.flush()
            
            # Log response details to console for real-time monitoring
            print(f"{self.__class__.__name__} - {response.status_code} - {response.url}")
            
            # Explicitly mark failures for Locust statistics tracking
            if response.status_code >= 400:
                # Mark as failure and log detailed error information
                response.failure(f"HTTP {response.status_code}: {response.text[:100]}")
                print(f"FAILURE - {response.status_code}: {response.text[:200]}")
            else:
                # Log successful requests
                print(f"SUCCESS - {response.status_code}")
                
        except Exception as e:
            # Handle request exceptions (network errors, timeouts, etc.)
            print(f"Request failed: {str(e)}")
            # This will automatically be marked as a failure by Locust
