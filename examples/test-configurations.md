# 🧪 Test Configurations Examples

This document provides example configurations for testing different scenarios with the Multi-User Load Tester using the included test server.

## 🚀 Starting the Test Server

### Option 1: Docker Compose (Recommended)
```bash
docker-compose up --build
```
This starts both the load tester (port 8000) and test server (port 8080).

### Option 2: Local Development
```bash
# Terminal 1: Start test server
cd test_server
pip install -r requirements.txt
python main.py

# Terminal 2: Start load tester
cd ..
python -m app.main
```

## 📊 Test Scenarios

### 1. 🟢 Basic Success Test
**Objective**: Test successful requests and baseline performance

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `GET`
- **Route**: `/success`
- **Number of Users**: `10`
- **Spawn Rate**: `2`
- **Wait Time**: `1.0`
- **JSON Payload**: *(leave empty)*

**Expected Results**:
- ✅ 100% success rate
- 📈 Consistent response times
- 📊 Stable RPS

---

### 2. 🔴 Failure Rate Test
**Objective**: Test error handling and failure monitoring

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `GET`
- **Route**: `/fail`
- **Number of Users**: `5`
- **Spawn Rate**: `1`
- **Wait Time**: `2.0`
- **JSON Payload**: *(leave empty)*

**Expected Results**:
- ❌ 100% failure rate (HTTP 500)
- 📊 Fail ratio should show 100%
- 🔍 Error handling in logs

---

### 3. 📤 JSON POST Test
**Objective**: Test POST requests with JSON payloads

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `POST`
- **Route**: `/json`
- **Number of Users**: `8`
- **Spawn Rate**: `2`
- **Wait Time**: `1.5`
- **JSON Payload**:
```json
{
  "message": "Load test from Multi-User Tester",
  "data": {
    "test_id": "json_test_001",
    "environment": "testing",
    "load_users": 8
  },
  "timestamp": 1234567890
}
```

**Expected Results**:
- ✅ Successful JSON processing
- 📝 Payload validation working
- ⏱️ Slightly higher response times due to processing

---

### 4. 🐌 Performance Test (Slow Responses)
**Objective**: Test response time monitoring with slow endpoints

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `GET`
- **Route**: `/slow`
- **Number of Users**: `6`
- **Spawn Rate**: `1`
- **Wait Time**: `5.0`
- **JSON Payload**: *(leave empty)*

**Expected Results**:
- 📈 Response times: 1000-3000ms
- ⏱️ Variable response time charts
- 📊 Lower RPS due to slow responses

---

### 5. 🎲 Mixed Load Test (Random Results)
**Objective**: Test realistic mixed success/failure scenarios

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `GET`
- **Route**: `/random`
- **Number of Users**: `15`
- **Spawn Rate**: `3`
- **Wait Time**: `1.0`
- **JSON Payload**: *(leave empty)*

**Expected Results**:
- ✅ ~70% success rate
- ❌ ~30% failure rate (various HTTP codes)
- 📊 Realistic failure patterns

---

### 6. 👥 User Management Test (Complex JSON)
**Objective**: Test complex POST requests with validation

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `POST`
- **Route**: `/users`
- **Number of Users**: `12`
- **Spawn Rate**: `2`
- **Wait Time**: `2.0`
- **JSON Payload**:
```json
{
  "username": "loadtest_user",
  "email": "loadtest@example.com",
  "age": 25,
  "preferences": {
    "theme": "dark",
    "notifications": true,
    "language": "en"
  }
}
```

**Expected Results**:
- ✅ User creation responses (HTTP 201)
- 🔍 Validation working (try invalid email to test)
- 📊 Consistent performance with complex JSON

---

### 7. 🔍 RESTful API Test (GET with Parameters)
**Objective**: Test parameterized routes

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `GET`
- **Route**: `/users/123`
- **Number of Users**: `10`
- **Spawn Rate**: `2`
- **Wait Time**: `1.0`
- **JSON Payload**: *(leave empty)*

**Expected Results**:
- ✅ Most requests succeed
- ❌ Some 404s (every 10th user ID)
- 📊 Mixed success/failure pattern

---

### 8. 🗑️ DELETE Method Test
**Objective**: Test DELETE HTTP method

**Configuration**:
- **Target Host**: `http://localhost:8080`
- **HTTP Method**: `DELETE`
- **Route**: `/users/456`
- **Number of Users**: `5`
- **Spawn Rate**: `1`
- **Wait Time**: `3.0`
- **JSON Payload**: *(leave empty)*

**Expected Results**:
- ✅ Successful deletions (HTTP 200)
- 📊 Low RPS due to longer wait time
- 🔍 DELETE method handling

---

## 🎯 Multi-User Testing Scenarios

### Scenario A: Concurrent Different Tests
1. **User 1**: Run success test (10 users)
2. **User 2**: Run failure test (5 users) *simultaneously*
3. **User 3**: Run JSON test (8 users) *simultaneously*

**Objective**: Verify user isolation - each should see only their own stats.

### Scenario B: Same Test, Different Users
1. **User 1**: Run `/random` test (10 users)
2. **User 2**: Run `/random` test (10 users) *simultaneously*

**Objective**: Same endpoint, different isolated statistics and results.

### Scenario C: Resource Stress Test
1. Start 5+ concurrent tests with high user counts
2. Monitor resource usage and port allocation
3. Verify no interference between sessions

## 📊 Monitoring Tips

### What to Watch For:
- **RPS (Requests Per Second)**: Should be consistent based on users × (1/wait_time)
- **Response Times**: Vary by endpoint (/slow should be 1-3s, others <100ms)
- **Failure Rates**: Should match expected patterns
- **User Isolation**: Each browser tab should show different stats

### Test Server Stats:
Visit `http://localhost:8080/stats` to see server-side statistics and verify your load tests are hitting the server correctly.

## 🐳 Docker Testing

To test the complete Docker setup:

```bash
# Start everything
docker-compose up --build

# Test from outside containers
curl http://localhost:8080/success
curl http://localhost:8000  # Load tester UI

# View logs
docker-compose logs test-server
docker-compose logs locust-web-app
```

## 🔧 Troubleshooting

### Common Issues:
1. **Connection Refused**: Make sure test server is running on port 8080
2. **JSON Validation Errors**: Check JSON syntax in payload field
3. **High Response Times**: Expected for `/slow` endpoint
4. **Mixed Results**: Expected for `/random` endpoint

### Debug Commands:
```bash
# Check if test server is running
curl http://localhost:8080/

# Test specific endpoints
curl http://localhost:8080/success
curl -X POST http://localhost:8080/json -H "Content-Type: application/json" -d '{"message": "test"}'

# View server stats
curl http://localhost:8080/stats | jq
```

Happy Load Testing! 🚀
