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
- **Persistent Request Log**: Pre-loaded log section visible before tests start
- **Server-side logging**: Real-time test server logs with request tracking
- **Enhanced error reporting**: Improved error rate display and detailed failure analysis
- **Modular Frontend**: Clean separation of concerns with improved maintainability

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
| `/` | GET | Server dashboard | HTML status page with real-time stats |
| `/success` | GET | Always succeeds | 100% success rate |
| `/fail` | GET | Always fails | 100% failure rate (HTTP 500) |
| `/json` | POST | Requires JSON payload | Tests JSON handling |
| `/slow` | GET | 1-3 second delays | Tests response time monitoring |
| `/random` | GET | 70% success rate | Realistic mixed results |
| `/users` | POST | Create users | Complex JSON validation |
| `/users/{id}` | GET | Get user by ID | Parameterized routes |
| `/users/{id}` | DELETE | Delete user | DELETE method testing |
| `/stats` | GET | Server statistics | JSON stats with request/failure counts |

### Quick Test Examples

```bash
# Test the included server
curl http://localhost:8080/success  # ✅ Always succeeds
curl http://localhost:8080/fail     # ❌ Always fails
curl -X POST http://localhost:8080/json \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "data": {"key": "value"}}'
```

### Server Monitoring & Logs
- **Real-time Dashboard**: Visit `http://localhost:8080` for live server status
- **Statistics API**: Access `http://localhost:8080/stats` for JSON metrics
- **Request Logging**: Server logs all requests with timestamps and response codes
- **Load Test Integration**: Automatic request/response tracking during load tests

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

- **FastAPI Backend** (`main.py`): Handles WebSocket connections and API endpoints
- **Port Manager** (`port_manager.py`): Allocates unique ports for each user session
- **Locust Runner** (`locust_runner_class.py`): Manages individual Locust subprocesses
- **Locust File Factory** (`locust_file_factory.py`): Creates custom test scripts on-the-fly
- **Real-time Dashboard** (`index.html`): Live monitoring with charts, statistics, and persistent log sections
- **Modular Architecture**: Each class is separated into its own file for better maintainability

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
│   ├── main.py                   # FastAPI application & WebSocket handlers
│   ├── locust_runner_class.py    # LocustRunner class (subprocess management)
│   ├── locust_file_factory.py    # Factory for generating custom test configs
│   ├── port_manager.py           # Port allocation management
│   ├── static/
│   │   ├── script.js             # Frontend JavaScript with real-time updates
│   │   └── styles.css            # UI Styling with log container styles
│   └── templates/
│       └── index.html            # Main dashboard with pre-built log sections
├── test_server/
│   ├── main.py                   # Test server with various endpoints
│   ├── requirements.txt          # Test server dependencies
│   └── Dockerfile               # Test server container
├── locustfile.py                # Simple default Locust test configuration
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── docker-compose.yml          # Multi-container setup
└── README.md                    # This file
```

### Recent Architecture Improvements

#### **Modular Class Structure** *(September 2025)*
- **Separated Components**: Each class now resides in its own dedicated file
- **Better Maintainability**: Easier to locate, modify, and test individual components
- **Clean Dependencies**: Clear import structure and reduced coupling
- **Single Responsibility**: Each file has a focused, specific purpose

#### **Enhanced Frontend** *(September 2025)*  
- **Persistent UI Elements**: Request log section is always visible
- **Improved UX**: Users can see where logs will appear before starting tests
- **Better Structure**: Clean separation between HTML structure and dynamic content
- **Consistent Layout**: Maintained functionality while improving organization

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

**Error Rate Display Issues** *(Recently Fixed)*
- Error rates now display correctly with improved calculation
- Failed requests are properly tracked and reported
- Real-time error statistics are more accurate

### Logs and Debugging

```bash
# View application logs
docker-compose logs -f

# View test server logs specifically
docker-compose logs -f test-server

# Access container shell
docker-compose exec app bash

# Check locust processes
ps aux | grep locust

# Monitor test server real-time (NEW)
curl http://localhost:8080/stats | jq
curl http://localhost:8080  # HTML dashboard
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

*Last Updated: September 2025 - Recent improvements include modular architecture refactoring, persistent request log UI, enhanced logging, and better error tracking*

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/yourusername/multi-user-load-tester).
