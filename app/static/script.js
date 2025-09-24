document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const form = document.getElementById('locust-form');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const statsDiv = document.getElementById('stats');
    const errorContainer = document.getElementById('error-container');
    const jsonFileInput = document.getElementById('json_file');
    const jsonPayloadTextarea = document.getElementById('json_payload');
    const clearJsonBtn = document.getElementById('clear-json');

    let rpsChart, responseTimeChart;
    const chartData = {
        labels: [],
        rps: [],
        avgResponseTime: [],
    };

    const initCharts = () => {
        const rpsCtx = document.getElementById('rpsChart').getContext('2d');
        rpsChart = new Chart(rpsCtx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Requests per Second',
                    data: chartData.rps,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    fill: true,
                }]
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'second',
                            tooltipFormat: 'HH:mm:ss',
                            displayFormats: {
                                second: 'HH:mm:ss'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                },
                plugins: {
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'x'
                        },
                        zoom: {
                            wheel: {
                                enabled: true,
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x',
                        }
                    }
                }
            }
        });

        const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
        responseTimeChart = new Chart(responseTimeCtx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'Average Response Time (ms)',
                    data: chartData.avgResponseTime,
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    fill: true,
                }]
            },
            options: {
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'second',
                            tooltipFormat: 'HH:mm:ss',
                            displayFormats: {
                                second: 'HH:mm:ss'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                },
                plugins: {
                    zoom: {
                        pan: {
                            enabled: true,
                            mode: 'x'
                        },
                        zoom: {
                            wheel: {
                                enabled: true,
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x',
                        }
                    }
                }
            }
        });
    };
    
    const updateCharts = (time, rps, avgResponseTime) => {
        chartData.labels.push(time);
        chartData.rps.push(rps);
        chartData.avgResponseTime.push(avgResponseTime);

        // Limit data points to avoid performance issues
        if (chartData.labels.length > 100) {
            chartData.labels.shift();
            chartData.rps.shift();
            chartData.avgResponseTime.shift();
        }

        rpsChart.update();
        responseTimeChart.update();
    };

    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        
        socket.emit('start_load_test', data);
        startBtn.disabled = true;
        stopBtn.disabled = false;
        errorContainer.style.display = 'none';
    });

    stopBtn.addEventListener('click', () => {
        socket.emit('stop_load_test');
        startBtn.disabled = false;
        stopBtn.disabled = true;
    });

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });

    socket.on('stats', (data) => {
        updateUI(data);
    });

    socket.on('error', (data) => {
        errorContainer.textContent = `Error: ${data.message}`;
        errorContainer.style.display = 'block';
        startBtn.disabled = false;
        stopBtn.disabled = true;
    });

    const updateUI = (data) => {
        const statsHTML = `
            <div class="stat-card"><h3>Users</h3><p>${data.user_count}</p></div>
            <div class="stat-card"><h3>RPS</h3><p>${parseFloat(data.total_rps).toFixed(2)}</p></div>
            <div class="stat-card"><h3>Fails</h3><p>${parseFloat(data.fail_ratio).toFixed(2)}%</p></div>
            <div class="stat-card"><h3>Avg. Resp. Time</h3><p>${parseFloat(data.total_avg_response_time).toFixed(2)} ms</p></div>
        `;
        statsDiv.innerHTML = statsHTML;
        
        const now = new Date();
        updateCharts(now, data.total_rps, data.total_avg_response_time);
    };

    // JSON file upload handling
    jsonFileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/json') {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const jsonData = JSON.parse(e.target.result);
                    jsonPayloadTextarea.value = JSON.stringify(jsonData, null, 2);
                } catch (error) {
                    alert('Invalid JSON file. Please select a valid JSON file.');
                    jsonFileInput.value = '';
                }
            };
            reader.readAsText(file);
        }
    });

    // Clear JSON button
    clearJsonBtn.addEventListener('click', () => {
        jsonPayloadTextarea.value = '';
        jsonFileInput.value = '';
    });

    // Validate JSON as user types
    jsonPayloadTextarea.addEventListener('input', (e) => {
        const value = e.target.value.trim();
        if (value) {
            try {
                JSON.parse(value);
                e.target.style.borderColor = '#28a745'; // Green for valid
            } catch (error) {
                e.target.style.borderColor = '#dc3545'; // Red for invalid
            }
        } else {
            e.target.style.borderColor = '#ced4da'; // Default
        }
    });

    initCharts();
});
