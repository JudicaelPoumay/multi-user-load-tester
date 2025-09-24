"""Factory class for generating custom locust test configurations"""

import json
from typing import Dict, Any

class LocustFileFactory:
    """Factory class for generating custom locust test configurations"""
    
    @staticmethod
    def create_test_config(
        http_method: str, 
        route: str, 
        wait_time: float, 
        json_payload: Dict[Any, Any] = None, 
        log_file_path: str = None
    ) -> str:
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
        log_code = ""
        if log_file_path:
            log_code = f'''
            # Log to temporary file
            import datetime
            with open(r"{log_file_path}", "a", encoding="utf-8") as log_file:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                log_file.write(f"{{timestamp}} - {{response.status_code}} - {{response.url}} - {{response.elapsed.total_seconds():.3f}}s\\n")
                log_file.flush()'''
        
        locustfile_content = f'''from locust import HttpUser, task, between
import json
import datetime

class CustomUser(HttpUser):
    wait_time = between({wait_time}, {wait_time + 1})
    
    @task
    def custom_task(self):
        """Custom task generated from user input"""
        try:
            {request_code}
            {log_code}
            
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
