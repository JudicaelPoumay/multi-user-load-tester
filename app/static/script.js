document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const form = document.getElementById('locust-form');
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const statsDiv = document.getElementById('stats');
    const errorContainer = document.getElementById('error-container');
    const stopWarningContainer = document.getElementById('stop-warning-container');
    const chartWarning = document.getElementById('chart-warning');
    const jsonFileInput = document.getElementById('json_file');
    const jsonPayloadTextarea = document.getElementById('json_payload');
    const clearJsonBtn = document.getElementById('clear-json');
    const logContainer = document.getElementById('log-container');
    const formToggle = document.getElementById('form-toggle');
    const collapsibleContent = document.getElementById('collapsible-content');
    const toggleArrow = document.getElementById('toggle-arrow');

    formToggle.addEventListener('click', () => {
        collapsibleContent.classList.toggle('collapsed');
        toggleArrow.classList.toggle('arrow-down');
        toggleArrow.classList.toggle('arrow-up');
    });

    let rpsChart, responseTimeChart;
    let logPollingInterval = null;
    let shouldPollLogs = false; // Flag to indicate if polling should start
    const chartData = {
        labels: [],
        rps: [],
        avgResponseTime: [],
    };

    const resetChartData = () => {
        chartData.labels = [];
        chartData.rps = [];
        chartData.avgResponseTime = [];
        if (rpsChart) {
            rpsChart.data.labels = chartData.labels;
            rpsChart.data.datasets[0].data = chartData.rps;
            rpsChart.update();
        }
        if (responseTimeChart) {
            responseTimeChart.data.labels = chartData.labels;
            responseTimeChart.data.datasets[0].data = chartData.avgResponseTime;
            responseTimeChart.update();
        }
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
                    },
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    zoom: {
                        pan: {
                            enabled: false,
                            mode: 'x'
                        },
                        zoom: {
                            wheel: {
                                enabled: false,
                            },
                            pinch: {
                                enabled: false
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
                    },
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    zoom: {
                        pan: {
                            enabled: false,
                            mode: 'x'
                        },
                        zoom: {
                            wheel: {
                                enabled: false,
                            },
                            pinch: {
                                enabled: false
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
        
        resetChartData(); // Reset charts
        socket.emit('start_load_test', data);
        startBtn.disabled = true;
        stopBtn.disabled = false;
        errorContainer.style.display = 'none';
        stopWarningContainer.style.display = 'none';
        document.getElementById('error-report-container').innerHTML = ''; // Clear previous errors
        // Clear previous logs but keep the structure
        const logContent = logContainer?.querySelector('.log-content');
        if (logContent) logContent.innerHTML = '';
        startLogPolling(); // Start polling logs

        // Collapse the form
        if (!collapsibleContent.classList.contains('collapsed')) {
            collapsibleContent.classList.add('collapsed');
            toggleArrow.classList.remove('arrow-down');
            toggleArrow.classList.add('arrow-up');
        }
    });

    stopBtn.addEventListener('click', () => {
        socket.emit('stop_load_test');
        startBtn.disabled = false;
        stopBtn.disabled = true;
        stopLogPolling(); // Stop polling logs
        if (chartWarning) chartWarning.style.display = 'none';
    });

    socket.on('connect', () => {
        console.log('Connected to server with ID:', socket.id);
        if (shouldPollLogs) {
            startLogPolling();
        }
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
        stopLogPolling(); // Stop polling logs on error
        if (chartWarning) chartWarning.style.display = 'none';
    });

    socket.on('test_stopped', (data) => {
        stopWarningContainer.textContent = data.message;
        stopWarningContainer.style.display = 'block';
        startBtn.disabled = false;
        stopBtn.disabled = true;
        stopLogPolling();
    });

    const updateUI = (data) => {
        if (chartWarning) {
            if (data.total_rps === 0 || data.total_avg_response_time === 0) {
                chartWarning.style.display = 'block';
            } else {
                chartWarning.style.display = 'none';
            }
        }

        const statsHTML = `
            <div class="stat-card"><h3>Users</h3><p>${data.user_count}</p></div>
            <div class="stat-card"><h3>RPS</h3><p>${parseFloat(data.total_rps).toFixed(2)}</p></div>
            <div class="stat-card"><h3>Fails</h3><p>${parseFloat(data.fail_ratio).toFixed(2)}%</p></div>
            <div class="stat-card"><h3>Avg. Resp. Time</h3><p>${parseFloat(data.total_avg_response_time).toFixed(2)} ms</p></div>
        `;
        statsDiv.innerHTML = statsHTML;
        
        const now = new Date();
        updateCharts(now, data.total_rps, data.total_avg_response_time);

        if (data.errors && data.errors.length > 0) {
            renderErrors(data.errors);
        }
    };

    const renderErrors = (errors) => {
        const errorContainer = document.getElementById('error-report-container');
        let errorsHTML = '<h2>Error Report</h2><table><tr><th>Occurrences</th><th>Error</th></tr>';
        errors.forEach(error => {
            errorsHTML += `<tr><td>${error.occurrences}</td><td><pre>${error.error}</pre></td></tr>`;
        });
        errorsHTML += '</table>';
        errorContainer.innerHTML = errorsHTML;
    };

    const startLogPolling = () => {
        if (logPollingInterval) {
            clearInterval(logPollingInterval);
        }
        
        if (!socket.id) {
            console.log('Socket not connected yet, waiting for connection...');
            shouldPollLogs = true;
            return;
        }

        shouldPollLogs = false; // Reset flag

        const pollLogs = async () => {
            try {
                if (!socket.id) {
                    console.error('Socket ID is not available, stopping polling.');
                    stopLogPolling();
                    return;
                }
                const response = await fetch(`/logs/${socket.id}`);
                const data = await response.json();
                
                if (data.logs && data.logs.length > 0) {
                    displayLogs(data.logs);
                }
            } catch (error) {
                console.error('Error polling logs:', error);
            }
        };
        
        // Poll every 2 seconds
        logPollingInterval = setInterval(pollLogs, 2000);
        pollLogs(); // Initial call
    };

    const stopLogPolling = () => {
        if (logPollingInterval) {
            clearInterval(logPollingInterval);
            logPollingInterval = null;
        }
        shouldPollLogs = false; // Also reset flag when stopping
    };

    const displayLogs = (logs) => {
        if (!logContainer) return;
        
        const logContent = logContainer.querySelector('.log-content');
        if (!logContent) return;
        
        // Clear existing logs and add new ones
        let logsHTML = '';
        logs.forEach(log => {
            logsHTML += `<div class="log-line">${log}</div>`;
        });
        logContent.innerHTML = logsHTML;
        
        // Auto-scroll to bottom
        logContent.scrollTop = logContent.scrollHeight;
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
    
    // Peak Usage Estimator
    const calculateBtn = document.getElementById('calculate-btn');
    const estimatorResultDiv = document.getElementById('estimator-result');

    calculateBtn.addEventListener('click', () => {
        const dau = parseInt(document.getElementById('dau').value);
        const sessionLength = parseInt(document.getElementById('session-length').value);
        const activeHours = parseInt(document.getElementById('active-hours').value);
        const peakFactor = parseInt(document.getElementById('peak-factor').value);

        if (dau > 0 && sessionLength > 0 && activeHours > 0 && peakFactor > 0) {
            const activeHoursMin = activeHours * 60;
            const ccuAvg = (dau * sessionLength) / activeHoursMin;
            let ccuPeak = ccuAvg * peakFactor;

            // Cap the peak usage to the number of daily active users
            if (ccuPeak > dau) {
                ccuPeak = dau;
            }

            estimatorResultDiv.innerHTML = `
                <h3>Estimated Peak Concurrent Users:</h3>
                <p>${Math.ceil(ccuPeak)}</p>
            `;
        } else {
            estimatorResultDiv.innerHTML = `
                <h3>Error:</h3>
                <p>Please enter valid values for all fields.</p>
            `;
        }
    });

    // Tab switching logic
    window.openTool = (evt, toolName) => {
        const toolContents = document.getElementsByClassName('tool-content');
        for (let i = 0; i < toolContents.length; i++) {
            toolContents[i].style.display = 'none';
        }

        const tabLinks = document.getElementsByClassName('tab-link');
        for (let i = 0; i < tabLinks.length; i++) {
            tabLinks[i].className = tabLinks[i].className.replace(' active', '');
        }

        document.getElementById(toolName).style.display = 'block';
        evt.currentTarget.className += ' active';
    };
});
