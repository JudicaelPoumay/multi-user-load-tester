# Multi-User Load Tester 🚀

A modern, web-based load testing platform built with FastAPI and Locust that allows multiple users to run isolated load tests simultaneously with custom configurations.

![Load Testing Dashboard](https://img.shields.io/badge/Load%20Testing-Dashboard-blue)
![Python](https://img.shields.io/badge/Python-3.11+-green)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-red)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

## ✨ Features

### 🔒 **Multi-User Isolation**
- Each user gets their own isolated Locust instance
- Separate statistics and real-time monitoring per session
- No interference between concurrent users
- Docker-safe with localhost-bound services

### 🎛️ **Custom Test Configuration**
- **HTTP Methods**: GET, POST, PUT, DELETE, PATCH support
- **Custom Routes**: Target specific API endpoints
- **JSON Payloads**: Manual input or file upload support
- **Wait Times**: Configurable delays between requests
- **Real-time Validation**: Live JSON validation with visual feedback

### 📊 **Real-Time Monitoring**
- Live statistics dashboard with WebSocket updates
- Interactive charts for RPS and response times
- Pan and zoom functionality for detailed analysis
- Color-coded status indicators

### 🐳 **Production Ready**
- Docker containerization with security best practices
- Resource limits and health checks
- Non-root user execution
- Automatic cleanup of temporary files

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/JudicaelPoumay/multi-user-load-tester.git
cd multi-user-load-tester

# Run with Docker Compose (includes test server)
docker-compose up --build

# Access the applications
open http://localhost:8000  # Load Tester Dashboard
open http://localhost:8080  # Test Server Dashboard
```

### Local Development

```bash
# Clone and setup
git clone https://github.com/yourusername/multi-user-load-tester.git
cd multi-user-load-tester

# Install dependencies
pip install -r requirements.txt

# Run the load tester
python -m app.main

# In another terminal, run the test server
cd test_server
pip install -r requirements.txt
python main.py
```

## 🧪 Test Server

The project includes a comprehensive test server to demonstrate and validate all load testing features.

### Available Test Endpoints

| Endpoint | Method | Purpose | Expected Result |
|----------|--------|---------|-----------------|
| `/success` | GET | Always succeeds | 100% success rate |
| `/fail` | GET | Always fails | 100% failure rate (HTTP 500) |
| `/json` | POST | Requires JSON payload | Tests JSON handling |
| `/slow` | GET | 1-3 second delays | Tests response time monitoring |
| `/random` | GET | 70% success rate | Realistic mixed results |
| `/users` | POST | Create users | Complex JSON validation |
| `/users/{id}` | GET | Get user by ID | Parameterized routes |
| `/users/{id}` | DELETE | Delete user | DELETE method testing |

### Quick Test Examples

```bash
# Test the included server
curl http://localhost:8080/success  # ✅ Always succeeds
curl http://localhost:8080/fail     # ❌ Always fails
curl -X POST http://localhost:8080/json \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "data": {"key": "value"}}'
```

For comprehensive test scenarios, see [examples/test-configurations.md](examples/test-configurations.md).

## 🎯 Usage Guide

### Basic Load Test
1. **Target Host**: Enter your target URL (e.g., `https://api.example.com`)
2. **Users & Spawn Rate**: Configure the number of virtual users and spawn rate
3. **HTTP Method**: Select the request method from dropdown
4. **Route**: Specify the endpoint to test (e.g., `/api/users`)
5. **Wait Time**: Set delay between requests (seconds)
6. **Start Test**: Click "Start Load Test" and monitor real-time results

### Advanced Configuration

#### JSON Payloads
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "data": {
    "key": "value"
  }
}
```

#### File Upload
- Click "📁 Upload JSON File" to load JSON from file
- Supports `.json` files with automatic validation
- Use "Clear" button to reset payload

#### Custom Routes
```
/api/v1/users          # GET user list
/api/v1/users/123      # GET specific user
/api/v1/auth/login     # POST authentication
/api/v1/orders         # POST create order
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │◄──►│   FastAPI App   │◄──►│ Locust Instance │
│                 │    │                 │    │   (Port 8090+)  │
│  (Port 8000)    │    │  WebSocket +    │    │                 │
│                 │    │  REST API       │    │  Custom Tests   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Port Manager   │
                       │                 │
                       │ Session Isolation│
                       └─────────────────┘
```

### Key Components

- **FastAPI Backend**: Handles WebSocket connections and API endpoints
- **Port Manager**: Allocates unique ports for each user session
- **Locust Runner**: Manages individual Locust subprocesses
- **Dynamic Locustfile Generator**: Creates custom test scripts on-the-fly
- **Real-time Dashboard**: Live monitoring with charts and statistics

## 🔧 Configuration

### Environment Variables

```bash
# Application Settings
PYTHONPATH=/app
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1

# Resource Limits (Docker)
MEMORY_LIMIT=4g
CPU_LIMIT=2.0
```

### Port Configuration

- **Main Application**: 8000 (exposed)
- **Locust Instances**: 8090+ (localhost only)
- **Available Range**: ~57,000 concurrent users

## 📈 Performance & Scaling

### Concurrent User Limits

| Server Size | RAM | CPU Cores | Concurrent Users | Notes |
|-------------|-----|-----------|------------------|-------|
| Small | 2-4 GB | 2-4 | 20-50 | Development/Testing |
| Medium | 8-16 GB | 8 | 100-200 | Small Production |
| Large | 32+ GB | 16+ | 500-1000+ | Enterprise Scale |

### Resource Usage
- **Memory**: ~50-100MB per concurrent user
- **CPU**: Scales with request rate and test complexity
- **Ports**: One unique port per user session
- **Storage**: Temporary files auto-cleaned

## 🔒 Security Features

### Docker Security
- ✅ Non-root user execution
- ✅ Resource limits (CPU/Memory)
- ✅ Health checks for reliability
- ✅ Localhost-only Locust binding
- ✅ No external port exposure for subprocesses

### Application Security
- ✅ Session isolation
- ✅ Input validation and sanitization
- ✅ Automatic cleanup of temporary files
- ✅ Error handling and logging

## 🛠️ Development

### Project Structure

```
multi-user-load-tester/
├── app/
│   ├── main.py              # FastAPI application
│   ├── locust_runner.py     # Locust subprocess management
│   ├── static/
│   │   ├── script.js        # Frontend JavaScript
│   │   └── styles.css       # UI Styling
│   └── templates/
│       └── index.html       # Main dashboard
├── test_server/
│   ├── main.py              # Test server with various endpoints
│   ├── requirements.txt     # Test server dependencies
│   └── Dockerfile          # Test server container
├── examples/
│   └── test-configurations.md  # Comprehensive test scenarios
├── locustfile.py           # Default Locust test
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-container setup
└── README.md              # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run the application locally
python -m app.main

# Test with multiple browser tabs for concurrent users
```

## 📋 Requirements

### System Requirements
- **Python**: 3.11+ (3.13 recommended)
- **RAM**: 2GB minimum (4GB+ recommended)
- **CPU**: 2+ cores recommended
- **Storage**: 1GB for application and temp files

### Python Dependencies
- `fastapi` - Web framework
- `locust` - Load testing engine
- `uvicorn` - ASGI server
- `python-socketio` - WebSocket support
- `aiohttp` - HTTP client for stats polling
- `jinja2` - Template engine

## 🐛 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Check running processes
lsof -i :8000
kill -9 <PID>
```

**Memory Issues**
```bash
# Reduce concurrent users or increase container memory
docker-compose up --scale app=1 --memory 4g
```

**JSON Validation Errors**
- Ensure JSON is properly formatted
- Use the file upload feature for complex JSON
- Check browser console for detailed error messages

### Logs and Debugging

```bash
# View application logs
docker-compose logs -f

# Access container shell
docker-compose exec app bash

# Check locust processes
ps aux | grep locust
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Locust**: Powerful load testing framework
- **FastAPI**: Modern, fast web framework
- **Socket.IO**: Real-time communication
- **Chart.js**: Beautiful, responsive charts

---

**Happy Load Testing!** 🎯

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/yourusername/multi-user-load-tester).
