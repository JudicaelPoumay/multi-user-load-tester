"""
Test Server for Multi-User Load Tester
=====================================

This server provides various endpoints to test different scenarios:
- Success responses
- Failure responses  
- JSON payload handling
- Different response times
- Various HTTP methods

Run with: uvicorn test_server.main:app --host 0.0.0.0 --port 8080
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import time
import random
import asyncio
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Load Test Server",
    description="A test server for demonstrating load testing capabilities",
    version="1.0.0"
)

# Request/Response models
class JsonPayload(BaseModel):
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None

class UserData(BaseModel):
    username: str
    email: str
    age: Optional[int] = None
    preferences: Optional[Dict[str, Any]] = None

# Global stats for demonstration
request_count = 0
failure_count = 0

@app.get("/", response_class=HTMLResponse)
async def root():
    """Welcome page with API documentation"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Load Test Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .endpoint { background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold; }
            .get { background-color: #28a745; }
            .post { background-color: #007bff; }
            .put { background-color: #ffc107; color: black; }
            .delete { background-color: #dc3545; }
            code { background: #e9ecef; padding: 2px 4px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>🚀 Load Test Server</h1>
        <p>This server provides various endpoints for testing your load testing platform.</p>
        
        <h2>📊 Available Endpoints:</h2>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span> /success</h3>
            <p>Always returns HTTP 200 with success message. Use this to test successful requests.</p>
            <code>curl http://localhost:8080/success</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span> /fail</h3>
            <p>Always returns HTTP 500 with error message. Use this to test failure handling.</p>
            <code>curl http://localhost:8080/fail</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method post">POST</span> /json</h3>
            <p>Requires JSON payload. Returns processed data or validation errors.</p>
            <code>curl -X POST http://localhost:8080/json -H "Content-Type: application/json" -d '{"message": "test"}'</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span> /slow</h3>
            <p>Simulates slow responses (1-3 seconds delay). Test response time monitoring.</p>
            <code>curl http://localhost:8080/slow</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span> /random</h3>
            <p>Random success/failure responses. 70% success rate for realistic testing.</p>
            <code>curl http://localhost:8080/random</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method post">POST</span> /users</h3>
            <p>User creation endpoint. Requires username and email in JSON.</p>
            <code>curl -X POST http://localhost:8080/users -H "Content-Type: application/json" -d '{"username": "test", "email": "test@example.com"}'</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span> /users/{user_id}</h3>
            <p>Get user by ID. Try different IDs to test parameterized routes.</p>
            <code>curl http://localhost:8080/users/123</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method delete">DELETE</span> /users/{user_id}</h3>
            <p>Delete user by ID. Test DELETE method handling.</p>
            <code>curl -X DELETE http://localhost:8080/users/123</code>
        </div>
        
        <div class="endpoint">
            <h3><span class="method get">GET</span> /stats</h3>
            <p>View server statistics and request counts.</p>
            <code>curl http://localhost:8080/stats</code>
        </div>
        
        <h2>🔧 Usage Examples for Load Tester:</h2>
        <ol>
            <li><strong>Basic Success Test:</strong> Use GET /success with 10 users</li>
            <li><strong>Failure Rate Test:</strong> Use GET /fail to test error monitoring</li>
            <li><strong>JSON POST Test:</strong> Use POST /json with payload: <code>{"message": "load test", "data": {"key": "value"}}</code></li>
            <li><strong>Performance Test:</strong> Use GET /slow to test response time monitoring</li>
            <li><strong>Mixed Load Test:</strong> Use GET /random for realistic success/failure ratios</li>
        </ol>
        
        <p><strong>Server running on:</strong> <code>http://localhost:8080</code></p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/success")
async def success_endpoint():
    """Always succeeds - use for testing successful requests"""
    global request_count
    request_count += 1
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Request completed successfully!",
            "request_id": request_count,
            "timestamp": time.time()
        }
    )

@app.get("/fail")
async def fail_endpoint():
    """Always fails - use for testing error handling"""
    global request_count, failure_count
    request_count += 1
    failure_count += 1
    
    raise HTTPException(
        status_code=500,
        detail={
            "status": "error",
            "message": "This endpoint always fails for testing purposes",
            "error_code": "INTENTIONAL_FAILURE",
            "request_id": request_count,
            "timestamp": time.time()
        }
    )

@app.post("/json")
async def json_endpoint(payload: JsonPayload):
    """Requires JSON payload - use for testing POST with JSON data"""
    global request_count
    request_count += 1
    
    # Simulate some processing time
    await asyncio.sleep(0.1)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "JSON payload processed successfully",
            "received_data": {
                "data": payload,
                "processed_at": time.time()
            },
            "request_id": request_count
        }
    )

@app.get("/slow")
async def slow_endpoint():
    """Simulates slow responses for testing response time monitoring"""
    global request_count
    request_count += 1
    
    # Random delay between 1-3 seconds
    delay = random.uniform(1.0, 3.0)
    await asyncio.sleep(delay)
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"Slow response completed after {delay:.2f} seconds",
            "delay_seconds": delay,
            "request_id": request_count,
            "timestamp": time.time()
        }
    )

@app.get("/random")
async def random_endpoint():
    """Random success/failure for realistic testing (70% success rate)"""
    global request_count, failure_count
    request_count += 1
    
    # 70% success rate
    if random.random() < 0.7:
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Random endpoint succeeded",
                "probability": "70%",
                "request_id": request_count,
                "timestamp": time.time()
            }
        )
    else:
        failure_count += 1
        # Vary the error codes
        error_code = random.choice([400, 404, 500, 503])
        error_messages = {
            400: "Bad Request - Random validation error",
            404: "Not Found - Random resource missing",
            500: "Internal Server Error - Random server failure",
            503: "Service Unavailable - Random overload"
        }
        
        raise HTTPException(
            status_code=error_code,
            detail={
                "status": "error",
                "message": error_messages[error_code],
                "error_code": f"RANDOM_ERROR_{error_code}",
                "probability": "30%",
                "request_id": request_count,
                "timestamp": time.time()
            }
        )

@app.post("/users")
async def create_user(user: UserData):
    """Create user endpoint - test complex JSON payloads"""
    global request_count
    request_count += 1
    
    # Simulate validation
    if len(user.username) < 3:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Username must be at least 3 characters long",
                "field": "username",
                "request_id": request_count
            }
        )
    
    if "@" not in user.email:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "Invalid email format",
                "field": "email",
                "request_id": request_count
            }
        )
    
    # Generate fake user ID
    user_id = random.randint(1000, 9999)
    
    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "message": "User created successfully",
            "user": {
                "id": user_id,
                "username": user.username,
                "email": user.email,
                "age": user.age,
                "preferences": user.preferences,
                "created_at": time.time()
            },
            "request_id": request_count
        }
    )

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get user by ID - test parameterized routes"""
    global request_count
    request_count += 1
    
    # Simulate some users not existing
    if user_id % 10 == 0:  # Every 10th user doesn't exist
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "message": f"User with ID {user_id} not found",
                "user_id": user_id,
                "request_id": request_count
            }
        )
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "user": {
                "id": user_id,
                "username": f"user_{user_id}",
                "email": f"user_{user_id}@example.com",
                "age": random.randint(18, 80),
                "preferences": {
                    "theme": random.choice(["dark", "light"]),
                    "notifications": random.choice([True, False])
                },
                "created_at": time.time() - random.randint(86400, 31536000)  # 1 day to 1 year ago
            },
            "request_id": request_count
        }
    )

@app.put("/users/{user_id}")
async def update_user(user_id: int, user: UserData):
    """Update user - test PUT method"""
    global request_count
    request_count += 1
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"User {user_id} updated successfully",
            "updated_user": {
                "id": user_id,
                "username": user.username,
                "email": user.email,
                "age": user.age,
                "preferences": user.preferences,
                "updated_at": time.time()
            },
            "request_id": request_count
        }
    )

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete user - test DELETE method"""
    global request_count
    request_count += 1
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": f"User {user_id} deleted successfully",
            "deleted_user_id": user_id,
            "deleted_at": time.time(),
            "request_id": request_count
        }
    )

@app.get("/stats")
async def get_stats():
    """Get server statistics"""
    success_count = request_count - failure_count
    success_rate = (success_count / request_count * 100) if request_count > 0 else 0
    
    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "stats": {
                "total_requests": request_count,
                "successful_requests": success_count,
                "failed_requests": failure_count,
                "success_rate_percentage": round(success_rate, 2),
                "server_uptime_seconds": time.time(),
                "endpoints": {
                    "/success": "Always succeeds (200)",
                    "/fail": "Always fails (500)",
                    "/json": "Requires JSON payload",
                    "/slow": "1-3 second delays",
                    "/random": "70% success rate",
                    "/users": "CRUD operations",
                }
            },
            "timestamp": time.time()
        }
    )

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Load Test Server...")
    print("📊 Access the dashboard at: http://localhost:8080")
    print("📚 API Documentation at: http://localhost:8080/docs")
    uvicorn.run(app, host="0.0.0.0", port=80)
