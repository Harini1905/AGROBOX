// Application State
// const state = {
//     sensorData: {
//         moisture: 45,
//         light: 650,
//         temperature: 24.5,
//         humidity: 60
//     },
//     historicalData: {
//         moisture: [],
//         light: [],
//         temperature: [],
//         humidity: []
//     },
//     controls: {
//         pump: { active: false },
//         uvLamp: { active: false },
//         peltier: { active: false, heating: true }
//     }
// };

// const MAX_DATA_POINTS = 20;
let charts = {};

// Initialize charts
function initCharts() {
    const chartConfig = {
        moisture: { color: '#4CAF50', label: 'Moisture %' },
        light: { color: '#03A9F4', label: 'Light (lux)' },
        temperature: { color: '#FFC107', label: 'Temp (°C)' },
        humidity: { color: '#8A2BE2', label: 'Humidity %' }
    };

    Object.keys(chartConfig).forEach(sensor => {
        const ctx = document.getElementById(`${sensor}-chart`).getContext('2d');
        charts[sensor] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: chartConfig[sensor].label,
                    data: [],
                    borderColor: chartConfig[sensor].color,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e242b',
                        borderColor: '#2d343f',
                        borderWidth: 1,
                        titleColor: '#e0e0e0',
                        bodyColor: '#e0e0e0',
                        callbacks: {
                            title: function(context) {
                                return context[0].label;
                            },
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(45, 52, 63, 0.5)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#9e9e9e',
                            font: { size: 10 }
                        }
                    },
                    y: {
                        grid: {
                            color: 'rgba(45, 52, 63, 0.5)',
                            drawBorder: false
                        },
                        ticks: {
                            color: '#9e9e9e',
                            font: { size: 10 }
                        }
                    }
                }
            }
        });
    });
}

// Update sensor display
function updateSensorDisplay(sensorData) {
    // Update moisture
    document.getElementById('moisture-value').textContent = sensorData.moisture.toFixed(1);
    document.getElementById('moisture-status').textContent = getMoistureStatus(sensorData.moisture);
    document.getElementById('moisture-status').className = `status-badge ${getMoistureStatus(sensorData.moisture)}`;

    // Update light
    document.getElementById('light-value').textContent = sensorData.light.toFixed(1);
    document.getElementById('light-status').textContent = getLightStatus(sensorData.light);
    document.getElementById('light-status').className = `status-badge ${getLightStatus(sensorData.light)}`;

    // Update temperature
    document.getElementById('temperature-value').textContent = sensorData.temperature.toFixed(1);
    document.getElementById('temperature-status').textContent = getTempStatus(sensorData.temperature);
    document.getElementById('temperature-status').className = `status-badge ${getTempStatus(sensorData.temperature)}`;

    // Update humidity
    document.getElementById('humidity-value').textContent = sensorData.humidity.toFixed(1);
    document.getElementById('humidity-status').textContent = getHumidityStatus(sensorData.humidity);
    document.getElementById('humidity-status').className = `status-badge ${getHumidityStatus(sensorData.humidity)}`;
}

// Status helpers
function getMoistureStatus(value) {
    if (value < 30) return 'critical';
    if (value < 50) return 'warning';
    return 'optimal';
}

function getLightStatus(value) {
    if (value < 400) return 'critical';
    if (value < 600) return 'warning';
    return 'optimal';
}

function getTempStatus(value) {
    if (value < 18 || value > 28) return 'critical';
    if (value < 20 || value > 26) return 'warning';
    return 'optimal';
}

function getHumidityStatus(value) {
    if (value < 40 || value > 80) return 'critical';
    if (value < 50 || value > 70) return 'warning';
    return 'optimal';
}

async function fetchHistoricalSensorData() {
    try {
        const response = await fetch('/api/sensors/history');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        updateCharts(data);
    } catch (error) {
        console.error('Error fetching historical sensor data:', error);
    }
}

// Update charts
function updateCharts(historicalData) {
    Object.keys(charts).forEach(sensor => {
        const chart = charts[sensor];

        // Update chart
        chart.data.labels = historicalData.timestamps.map(t => new Date(t).toLocaleTimeString());
        chart.data.datasets[0].data = historicalData[sensor];
        chart.update('none');
    });
}

// Fetch current sensor data from API
async function fetchCurrentSensorData() {
    try {
        const sensorResponse = await fetch('/api/sensors/current');
        if (!sensorResponse.ok) {
            throw new Error(`HTTP error! status: ${sensorResponse.status}`);
        }
        const sensorData = await sensorResponse.json();

        const controlsResponse = await fetch('/api/controls');
        if (!controlsResponse.ok) {
            throw new Error(`HTTP error! status: ${controlsResponse.status}`);
        }
        const currentControls = await controlsResponse.json();

        updateSensorDisplay(sensorData);
        const newControls = applyAutoControl(sensorData, currentControls);
        updateControls(newControls);
        sendControlUpdatesToBackend(newControls);
    } catch (error) {
        console.error('Error fetching current sensor data or controls:', error);
    }
}

async function sendControlUpdatesToBackend(newControls) {
    try {
        const response = await fetch('/api/controls', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                pump: newControls.pump.active,
                uvLamp: newControls.uvLamp.active,
                peltier: newControls.peltier.active
            }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        console.log('Control states updated successfully on backend.');
    } catch (error) {
        console.error('Error sending control updates to backend:', error);
    }
}

// Auto-control logic
function applyAutoControl(sensorData, currentControls) {
    const newControls = { ...currentControls };

    // Moisture control - Water pump
    newControls.pump.active = sensorData.moisture < 40;

    // Light control - UV lamp
    newControls.uvLamp.active = sensorData.light < 500;

    // Temperature control - Peltier
    if (sensorData.temperature > 26) {
        newControls.peltier.active = true;
        newControls.peltier.heating = false;
    } else if (sensorData.temperature < 20) {
        newControls.peltier.active = true;
        newControls.peltier.heating = true;
    } else {
        newControls.peltier.active = false;
    }

    return newControls;
}

// Update control displays
function updateControls(controls) {
    // Update pump
    const pumpSwitch = document.getElementById('pump-switch');
    const pumpIndicator = document.getElementById('pump-indicator');
    pumpSwitch.checked = controls.pump.active;
    pumpSwitch.disabled = true;
    if (controls.pump.active) {
        pumpIndicator.classList.add('active');
    } else {
        pumpIndicator.classList.remove('active');
    }

    // Update UV lamp
    const uvLampSwitch = document.getElementById('uvlamp-switch');
    const uvLampIndicator = document.getElementById('uvlamp-indicator');
    uvLampSwitch.checked = controls.uvLamp.active;
    uvLampSwitch.disabled = true;
    if (controls.uvLamp.active) {
        uvLampIndicator.classList.add('active');
    } else {
        uvLampIndicator.classList.remove('active');
    }

    // Update Peltier
    const peltierSwitch = document.getElementById('peltier-switch');
    const peltierIndicator = document.getElementById('peltier-indicator');
    const peltierLabel = document.getElementById('peltier-label');
    peltierSwitch.checked = controls.peltier.active;
    peltierSwitch.disabled = true;
    peltierLabel.textContent = `Peltier (${controls.peltier.heating ? 'Heating' : 'Cooling'})`;
    if (controls.peltier.active) {
        peltierIndicator.classList.add('active');
    } else {
        peltierIndicator.classList.remove('active');
    }
}

// Setup event listeners
function setupEventListeners() {
    // Mode badges
    document.querySelectorAll('.mode-badge').forEach(badge => {
        badge.addEventListener('click', function() {
            const control = this.dataset.control;
            
            // Update UI
            const siblings = this.parentElement.querySelectorAll('.mode-badge');
            siblings.forEach(s => s.classList.remove('active'));
            this.classList.add('active');
            
            // Apply auto control immediately
            applyAutoControl();
        });
    });
}

// Initialize application
function init() {
    initCharts();
    updateControls();
    setupEventListeners();

    // Start fetching data
    fetchCurrentSensorData(); // Initial fetch
    setInterval(fetchCurrentSensorData, 5000); // Fetch current every 5 seconds
    fetchHistoricalSensorData(); // Initial fetch for historical data
    setInterval(fetchHistoricalSensorData, 10000); // Fetch historical every 10 seconds
}

// Start when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
