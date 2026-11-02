/**
 * AWS Cloud Deployment Dashboard - Interactive Scripting
 * Real-time metrics polling, Chart.js visualizations, and deployment management.
 */

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    setupEventListeners();
    startMetricsPolling();
});

let systemChart = null;
let deploymentsChart = null;

/**
 * Initialize Chart.js diagrams for Resource Utilization and Deployment Metrics.
 */
function initCharts() {
    const resourceCtx = document.getElementById('resourceChart');
    if (resourceCtx) {
        systemChart = new Chart(resourceCtx, {
            type: 'doughnut',
            data: {
                labels: ['CPU %', 'Memory %', 'Disk %'],
                datasets: [{
                    data: [
                        window.serverMetrics?.cpu_percent || 15,
                        window.serverMetrics?.memory_percent || 42,
                        window.serverMetrics?.disk_percent || 35
                    ],
                    backgroundColor: [
                        '#2563eb', // Blue
                        '#06b6d4', // Cyan
                        '#8b5cf6'  // Purple
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            padding: 15,
                            font: { family: 'Inter', size: 12 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return ` ${context.label}: ${context.raw}%`;
                            }
                        }
                    }
                },
                cutout: '72%'
            }
        });
    }

    const deployCtx = document.getElementById('deploymentTrendsChart');
    if (deployCtx) {
        deploymentsChart = new Chart(deployCtx, {
            type: 'bar',
            data: {
                labels: ['Build #1', 'Build #2', 'Build #3', 'Current'],
                datasets: [{
                    label: 'Pipeline Duration (s)',
                    data: [52, 45, 38, 40],
                    backgroundColor: 'rgba(37, 99, 235, 0.85)',
                    borderRadius: 6,
                    borderColor: '#2563eb',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Seconds' },
                        grid: { color: '#f1f5f9' }
                    },
                    x: {
                        grid: { display: false }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

/**
 * Configure UI event listeners.
 */
function setupEventListeners() {
    // Health check test button
    const testHealthBtn = document.getElementById('testHealthBtn');
    if (testHealthBtn) {
        testHealthBtn.addEventListener('click', async () => {
            testHealthBtn.disabled = true;
            testHealthBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Checking...';
            try {
                const res = await fetch('/health');
                const data = await res.json();
                showHealthModal(data);
            } catch (err) {
                alert('Health check failed: ' + err.message);
            } finally {
                testHealthBtn.disabled = false;
                testHealthBtn.innerHTML = '<i class="fas fa-heartbeat"></i> Run Live Health Check';
            }
        });
    }

    // Refresh metrics button
    const refreshBtn = document.getElementById('refreshMetricsBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchLiveStatus(true);
        });
    }

    // Trigger deployment recording button
    const deployForm = document.getElementById('manualDeployForm');
    if (deployForm) {
        deployForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = deployForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Recording...';

            const payload = {
                details: document.getElementById('deployDetails').value || 'Manual verification deployment',
                branch: document.getElementById('deployBranch').value || 'main',
                status: 'SUCCESS'
            };

            try {
                const res = await fetch('/api/deployments', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.status === 'success') {
                    window.location.reload();
                } else {
                    alert('Error: ' + result.message);
                }
            } catch (err) {
                alert('Failed to register deployment: ' + err.message);
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-rocket"></i> Trigger Deployment';
            }
        });
    }
}

/**
 * Periodically poll live status every 10 seconds.
 */
function startMetricsPolling() {
    setInterval(() => {
        fetchLiveStatus(false);
    }, 10000);
}

/**
 * Fetch live system status & metrics from /api/status.
 */
async function fetchLiveStatus(isManual = false) {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) return;
        const data = await response.json();

        // Update DOM elements if available
        const cpuEl = document.getElementById('metricCpu');
        const memEl = document.getElementById('metricMem');
        const diskEl = document.getElementById('metricDisk');
        const uptimeEl = document.getElementById('metricUptime');

        if (cpuEl && data.system) cpuEl.textContent = `${data.system.cpu_percent}%`;
        if (memEl && data.system) memEl.textContent = `${data.system.memory_percent}% (${data.system.memory_used_gb} GB)`;
        if (diskEl && data.system) diskEl.textContent = `${data.system.disk_percent}%`;
        if (uptimeEl && data.system) uptimeEl.textContent = data.system.uptime_formatted;

        // Update charts
        if (systemChart && data.system) {
            systemChart.data.datasets[0].data = [
                data.system.cpu_percent,
                data.system.memory_percent,
                data.system.disk_percent
            ];
            systemChart.update();
        }

        if (isManual) {
            showToast('Metrics updated with latest telemetry.');
        }
    } catch (err) {
        console.error('Failed to poll system telemetry:', err);
    }
}

/**
 * Modal or Toast displaying raw JSON health response.
 */
function showHealthModal(data) {
    const jsonStr = JSON.stringify(data, null, 2);
    const existing = document.getElementById('healthModal');
    if (existing) existing.remove();

    const modalHtml = `
        <div class="modal fade show" id="healthModal" tabindex="-1" style="display: block; background: rgba(0,0,0,0.6);" aria-modal="true">
            <div class="modal-dialog modal-dialog-centered modal-lg">
                <div class="modal-content" style="border-radius: 12px; overflow: hidden; border: 1px solid #cbd5e1;">
                    <div class="modal-header bg-light">
                        <h5 class="modal-title font-monospace text-dark"><i class="fas fa-heartbeat text-danger me-2"></i>Live /health API Response</h5>
                        <button type="button" class="btn-close" onclick="document.getElementById('healthModal').remove()"></button>
                    </div>
                    <div class="modal-body p-3">
                        <div class="d-flex align-items-center justify-content-between mb-2">
                            <span class="badge bg-success"><i class="fas fa-check-circle"></i> HTTP 200 OK</span>
                            <span class="text-muted small">Endpoint: <code>/health</code></span>
                        </div>
                        <pre class="code-box mb-0" style="max-height: 400px; font-size: 0.85rem;">${escapeHtml(jsonStr)}</pre>
                    </div>
                    <div class="modal-footer bg-light">
                        <button type="button" class="btn btn-secondary btn-sm" onclick="document.getElementById('healthModal').remove()">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function escapeHtml(text) {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function showToast(message) {
    const toast = document.createElement('div');
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = '#1e293b';
    toast.style.color = '#ffffff';
    toast.style.padding = '12px 20px';
    toast.style.borderRadius = '8px';
    toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
    toast.style.zIndex = '9999';
    toast.style.fontSize = '0.88rem';
    toast.style.borderLeft = '4px solid #06b6d4';
    toast.innerHTML = `<i class="fas fa-info-circle text-info me-2"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}
