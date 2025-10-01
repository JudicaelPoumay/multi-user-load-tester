# Locust Web App

A multi-user, web-based load testing application powered by FastAPI and Locust. This application provides a user-friendly interface to configure and run isolated load tests, with real-time statistics and custom test scenarios.

## Key Features

-   **Multi-User Isolation**: Each user session gets a dedicated and isolated Locust instance.
-   **Dynamic Test Configuration**: Configure HTTP method, target route, user count, spawn rate, and JSON payloads directly from the web UI.
-   **Real-Time Statistics**: View real-time load testing metrics (RPS, average response time, failure rate) streamed via WebSockets.
-   **Session-based Logging**: Access and review logs for each test session.
-   **Containerized**: Comes with a `Dockerfile` for easy deployment.
-   **10-Minute Timeout & Peak Usage Estimator**: Automatically stops tests after 10 minutes and provides a peak usage estimation.
-   **AAD Token Generator & JWT Decoder**: Includes tools for generating Azure Active Directory tokens and decoding JWTs for testing authenticated endpoints.

## How to Run

You can run the application using Docker (recommended) or locally.

### Environment Variables

Before running the application, you may need to configure the following environment variables. You can create a `.env` file in the root of the project to manage these settings.

-   **`SSO_ENABLED`**: Set to `true` to enable Azure AD SSO or `false` to disable it for local development. Defaults to `true`.
-   **`TENANT_ID`**: Your Azure AD tenant ID. Required if SSO is enabled.
-   **`CLIENT_ID`**: The Application (client) ID of your Azure AD app registration. Required if SSO is enabled.
-   **`ALLOWED_USERS`**: A comma-separated list of user principal names (UPNs) that are allowed to access the application (e.g., `"user1@example.com,user2@example.com"`). Required if SSO is enabled.

### Using Docker

**Prerequisites:**
- Docker installed and running.

1.  **Build the Docker image:**
    ```sh
    docker build -t locust-web-app .
    ```

2.  **Run the Docker container:**
    ```sh
    docker run -p 8000:8000 locust-web-app
    ```
    The application will be available at `http://localhost:8000`.

When running with Docker, you can pass the environment variables using the `--env-file` option:

```sh
docker run -p 8000:8000 --env-file .env locust-web-app
```

### Locally

**Prerequisites:**
- Python 3.11+
- `pip`

1.  **Create a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2.  **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```sh
    python -m app.main
    ```
    The application will be available at `http://localhost:8000`.

## How to Use

1.  Open your web browser and navigate to `http://localhost:8000`.
2.  Fill in the load test configuration form:
    -   **Host**: The target host to run the load test against (e.g., `http://api.example.com`).
    -   **Number of Users**: The total number of concurrent users to simulate.
    -   **Spawn Rate**: The number of users to spawn per second.
    -   **HTTP Method**: The HTTP method for the requests (GET, POST, etc.).
    -   **Route**: The API endpoint or route to test (e.g., `/users`).
    -   **Wait Time**: The time (in seconds) each simulated user will wait between tasks.
    -   **JSON Payload**: (Optional) For POST/PUT requests, you can provide a JSON body.
3.  Click **Start Load Test**.
4.  You will see real-time statistics for your load test.
5.  You can view the request logs in the "Logs" tab.
6.  Click **Stop Load Test** to stop the test. When you close the browser tab, the test will also stop and resources will be cleaned up.

## Project Structure

```
.
├── app/                  # Main application source code
│   ├── main.py           # FastAPI application, WebSocket handling
│   ├── locust_runner.py # Manages Locust subprocesses
│   ├── locust_file_factory.py # Dynamically generates locustfiles
│   ├── port_manager.py   # Manages ports for Locust instances
│   ├── static/           # CSS and JavaScript files
│   └── templates/        # HTML templates
├── locustfile.py         # Default/example locustfile
├── Dockerfile            # Docker configuration
├── requirements.txt      # Python dependencies
└── README.md             # This file
```
