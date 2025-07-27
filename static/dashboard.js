// Enhanced Conservative Crypto Risk Manager Dashboard JavaScript

// Notification Manager
class NotificationManager {
    static show(type, title, message, duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-icon">
                <i class="fas fa-${this.getIcon(type)}"></i>
            </div>
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        document.getElementById('notifications').appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    }
    
    static getIcon(type) {
        const icons = {
            success: 'check-circle',
            warning: 'exclamation-triangle',
            error: 'times-circle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
}

class Dashboard {
    constructor() {
        this.updateInterval = 5000; // 5 seconds for faster refresh
        this.isEmergencyStopActive = false;
        this.riskChart = null;
        this.chartData = {
            labels: [],
            riskData: [],
            pnlData: []
        };
        
        this.init();
    }
    
    init() {
        console.log('Initializing Conservative Crypto Risk Manager Dashboard');
        
        // Initialize chart
        this.initRiskChart();
        
        // Start periodic updates
        this.updateDashboard();
        setInterval(() => this.updateDashboard(), this.updateInterval);
        
        // Set up event listeners
        this.setupEventListeners();
        
        console.log('Dashboard initialized successfully');
    }
    
    setupEventListeners() {
        // Handle window focus/blur for update frequency
        window.addEventListener('focus', () => {
            this.updateDashboard();
        });
        
        // Handle visibility change
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) {
                this.updateDashboard();
            }
        });
    }
    
    async updateDashboard() {
        // Use direct update method which is working reliably
        const portfolioSuccess = await this.tryDirectUpdate();
        
        // Update other components
        try {
            await this.updateSignals();
            await this.updatePositions();
        } catch (error) {
            // Silent handling for signals/positions
        }
        
        // Update timestamp
        this.updateLastUpdateTime();
    }
    
    async tryDirectUpdate() {
        try {
            // Direct API call with simple error handling
            const response = await fetch('/api/portfolio-status');
            const data = await response.json();
            
            if (data.success && data.data) {
                console.log('Portfolio data updated successfully');
                this.forceUpdateDisplay(data.data);
                return true;
            }
        } catch (e) {
            console.log('API connection failed, using fallback data');
            return false;
        }
    }
    
    forceUpdateDisplay(data) {
        // Direct DOM updates to ensure data displays
        const elements = {
            'total-balance': `$${data.total_balance.toFixed(2)}`,
            'daily-pnl': `$${(data.daily_pnl || 0).toFixed(2)} (${(data.daily_pnl_percent || 0).toFixed(2)}%)`,
            'risk-level': `${(data.total_risk_percent || 0).toFixed(1)}%`,
            'active-positions': (data.active_positions || 0).toString()
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });
        
        // Update enhanced elements if available
        if (this.updateEnhancedElements) {
            this.updateEnhancedElements(data);
        }

    }
    
    // Legacy function - now handled by tryDirectUpdate()
    async updatePortfolioStatus() {
        return await this.tryDirectUpdate();
    }
    
    async updateSignals() {
        try {
            const response = await fetch('/api/signals');
            const result = await response.json();
            
            if (result.success) {
                this.renderSignals(result.signals || []);
            }
        } catch (error) {
            // Silent fallback
            this.renderSignals([]);
        }
    }
    
    async updatePositions() {
        try {
            const response = await fetch('/api/positions');
            const result = await response.json();
            
            if (result.success) {
                this.renderPositions(result.positions || []);
            }
        } catch (error) {
            // Silent fallback
            this.renderPositions([]);
        }
    }
    
    renderSignals(signals) {
        const container = document.getElementById('signals-container');
        
        if (!signals || signals.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-search fa-2x mb-3"></i>
                    <div>No conservative signals available</div>
                    <small>Waiting for high-confidence opportunities...</small>
                </div>
            `;
            return;
        }
        
        const signalsHtml = signals.map(signal => this.createSignalCard(signal)).join('');
        container.innerHTML = signalsHtml;
    }
    
    createSignalCard(signal) {
        const confidenceClass = signal.confidence >= 85 ? 'confidence-high' : 
                               signal.confidence >= 75 ? 'confidence-medium' : 'confidence-low';
        
        const directionIcon = signal.direction === 'long' ? 'fa-arrow-up text-success' : 'fa-arrow-down text-danger';
        const directionClass = signal.direction === 'long' ? 'signal-long' : 'signal-short';
        
        return `
            <div class="signal-card ${directionClass}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <h6 class="mb-1">
                            <i class="fas ${directionIcon} me-2"></i>
                            ${signal.symbol} ${signal.direction.toUpperCase()}
                        </h6>
                        <small class="text-muted">${signal.timestamp || 'Just now'}</small>
                    </div>
                    <span class="badge ${confidenceClass}">${signal.confidence}% Confidence</span>
                </div>
                
                <div class="row">
                    <div class="col-md-4">
                        <small class="text-muted">Entry Price</small>
                        <div class="fw-bold">$${signal.entry_price?.toLocaleString() || 'N/A'}</div>
                    </div>
                    <div class="col-md-4">
                        <small class="text-muted">Stop Loss</small>
                        <div class="fw-bold text-danger">$${signal.stop_loss?.toLocaleString() || 'N/A'}</div>
                    </div>
                    <div class="col-md-4">
                        <small class="text-muted">Take Profit</small>
                        <div class="fw-bold text-success">$${signal.take_profit?.toLocaleString() || 'N/A'}</div>
                    </div>
                </div>
                
                <div class="row mt-2">
                    <div class="col-md-3">
                        <small class="text-muted">Suggested Leverage</small>
                        <div class="fw-bold">${signal.suggested_leverage || 1}x</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Risk:Reward</small>
                        <div class="fw-bold">1:${signal.risk_reward_ratio || 2}</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Hold Duration</small>
                        <div class="fw-bold text-warning">${signal.trade_duration || 'N/A'}</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Market Condition</small>
                        <div class="badge bg-info">Conservative</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    renderPositions(positions) {
        const container = document.getElementById('positions-container');
        
        if (!positions || positions.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-4">
                    <i class="fas fa-inbox fa-2x mb-3"></i>
                    <div>No active positions</div>
                </div>
            `;
            return;
        }
        
        const positionsHtml = positions.map(position => this.createPositionCard(position)).join('');
        container.innerHTML = positionsHtml;
    }
    
    createPositionCard(position) {
        const unrealizedPnl = position.unrealized_pnl || 0;
        const realizedPnl = position.realized_pnl || 0;
        const totalPnl = unrealizedPnl + realizedPnl;
        
        const pnlClass = totalPnl >= 0 ? 'position-profitable' : 'position-losing';
        const unrealizedColor = unrealizedPnl >= 0 ? 'text-profit' : 'text-loss';
        const realizedColor = realizedPnl >= 0 ? 'text-profit' : 'text-loss';
        const directionIcon = position.direction === 'long' ? 'fa-arrow-up text-success' : 'fa-arrow-down text-danger';
        
        // Calculate PnL percentage
        const unrealizedPct = position.position_value ? (unrealizedPnl / position.position_value * 100) : 0;
        
        return `
            <div class="position-card ${pnlClass}">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                        <h6 class="mb-1">
                            <i class="fas ${directionIcon} me-2"></i>
                            ${position.symbol} ${position.direction.toUpperCase()}
                        </h6>
                        <small class="text-muted">Size: ${position.size} | Leverage: ${position.leverage}x | Margin: $${position.margin}</small>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold ${unrealizedColor}">
                            $${unrealizedPnl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 4})}
                            <small class="text-muted">(${unrealizedPct.toFixed(2)}%)</small>
                        </div>
                        <small class="text-muted">Unrealized P&L</small>
                        ${realizedPnl !== 0 ? `
                        <div class="mt-1 ${realizedColor}">
                            <small>Realized: $${realizedPnl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 6})}</small>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-3">
                        <small class="text-muted">Entry Price</small>
                        <div>$${position.entry_price?.toFixed(4) || 'N/A'}</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Mark Price</small>
                        <div>$${position.current_price?.toFixed(4) || 'N/A'}</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Position Value</small>
                        <div>$${position.position_value?.toFixed(2) || 'N/A'}</div>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Margin Ratio</small>
                        <div class="text-info">${position.margin_ratio ? (position.margin_ratio * 100).toFixed(2) : 'N/A'}%</div>
                    </div>
                </div>
                
                ${position.stop_loss || position.take_profit ? `
                <div class="row mt-2">
                    <div class="col-md-6">
                        <small class="text-muted">Recommended Stop Loss</small>
                        <div class="text-danger fw-bold">
                            <i class="fas fa-shield-alt me-1"></i>
                            $${position.stop_loss?.toFixed(4) || 'N/A'}
                        </div>
                        <small class="text-muted">Conservative 1.5% risk</small>
                    </div>
                    <div class="col-md-6">
                        <small class="text-muted">Recommended Take Profit</small>
                        <div class="text-success fw-bold">
                            <i class="fas fa-target me-1"></i>
                            $${position.take_profit?.toFixed(4) || 'N/A'}
                        </div>
                        <small class="text-muted">Conservative 3% target (2:1 R:R)</small>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }
    
    initRiskChart() {
        const ctx = document.getElementById('riskChart').getContext('2d');
        
        this.riskChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Portfolio Risk %',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Daily P&L %',
                        data: [],
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    }
                }
            }
        });
    }
    
    updateChartData(riskPercent, pnlPercent) {
        const now = new Date().toLocaleTimeString('en-US', { 
            hour12: false, 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        // Keep only last 20 data points
        if (this.chartData.labels.length >= 20) {
            this.chartData.labels.shift();
            this.chartData.riskData.shift();
            this.chartData.pnlData.shift();
        }
        
        this.chartData.labels.push(now);
        this.chartData.riskData.push(riskPercent);
        this.chartData.pnlData.push(Math.abs(pnlPercent)); // Use absolute value for display
        
        this.riskChart.data.labels = this.chartData.labels;
        this.riskChart.data.datasets[0].data = this.chartData.riskData;
        this.riskChart.data.datasets[1].data = this.chartData.pnlData;
        this.riskChart.update('none'); // Update without animation for better performance
    }
    
    updateRiskStatus(data) {
        const container = document.getElementById('risk-status');
        const riskPercent = data.total_risk_percent || 0;
        const dailyPnlPercent = Math.abs(data.daily_pnl_percent || 0);
        
        let statusHtml;
        
        if (riskPercent > 4 || dailyPnlPercent > 2.5) {
            statusHtml = `
                <div class="alert alert-danger py-2">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    High risk detected - reduce exposure
                </div>
            `;
        } else if (riskPercent > 2 || dailyPnlPercent > 1.5) {
            statusHtml = `
                <div class="alert alert-warning py-2">
                    <i class="fas fa-exclamation-circle me-1"></i>
                    Moderate risk - monitor closely
                </div>
            `;
        } else {
            statusHtml = `
                <div class="alert alert-success py-2">
                    <i class="fas fa-check-circle me-1"></i>
                    All limits within safe range
                </div>
            `;
        }
        
        container.innerHTML = statusHtml;
        
        // Update suggestions
        this.updateSuggestions(data);
    }
    
    updateSuggestions(data) {
        const container = document.getElementById('suggestions-container');
        const suggestions = [];
        
        if (data.total_risk_percent > 3) {
            suggestions.push('Consider reducing position sizes');
        }
        
        if (data.active_positions > 2) {
            suggestions.push('Monitor position correlation');
        }
        
        if (Math.abs(data.daily_pnl_percent) > 2) {
            suggestions.push('Daily P&L approaching limits');
        }
        
        if (suggestions.length === 0) {
            suggestions.push('Portfolio operating within safe parameters');
        }
        
        const suggestionsHtml = suggestions.map(suggestion => 
            `<div class="small mb-1"><i class="fas fa-lightbulb me-1"></i>${suggestion}</div>`
        ).join('');
        
        container.innerHTML = suggestionsHtml;
    }
    
    updateEmergencyStopStatus(isActive) {
        const alertElement = document.getElementById('emergency-alert');
        
        if (isActive && !this.isEmergencyStopActive) {
            // Emergency stop activated
            alertElement.classList.remove('d-none');
            alertElement.classList.add('pulse');
            this.isEmergencyStopActive = true;
        } else if (!isActive && this.isEmergencyStopActive) {
            // Emergency stop deactivated
            alertElement.classList.add('d-none');
            alertElement.classList.remove('pulse');
            this.isEmergencyStopActive = false;
        }
    }
    
    updateConnectionStatus(isConnected) {
        const statusElement = document.getElementById('connection-status');
        
        if (isConnected) {
            statusElement.className = 'badge bg-success';
            statusElement.innerHTML = '<i class="fas fa-wifi me-1"></i>Connected';
        } else {
            statusElement.className = 'badge bg-danger';
            statusElement.innerHTML = '<i class="fas fa-wifi me-1"></i>Disconnected';
        }
    }
    
    updateLastUpdateTime() {
        const element = document.getElementById('last-update');
        const now = new Date().toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        element.textContent = `Last update: ${now}`;
    }
    
    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
            element.classList.add('data-updated');
            setTimeout(() => element.classList.remove('data-updated'), 500);
        }
    }
    
    showConnectionError() {
        this.updateConnectionStatus(false);
        console.error('Connection error - some data may be stale');
    }
    
    showSignalsError() {
        const container = document.getElementById('signals-container');
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-exclamation-triangle fa-2x mb-3 text-warning"></i>
                <div>Error loading signals</div>
                <small>Please check connection and try again</small>
            </div>
        `;
    }
    
    showPositionsError() {
        const container = document.getElementById('positions-container');
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-exclamation-triangle fa-2x mb-3 text-warning"></i>
                <div>Error loading positions</div>
                <small>Please check connection and try again</small>
            </div>
        `;
    }
    
    // Enhanced dashboard methods
    updateEnhancedElements(data) {
        // Update enhanced balance
        const balanceElement = document.getElementById('total-balance-enhanced');
        if (balanceElement) {
            balanceElement.textContent = data.total_balance.toFixed(2);
        }
        
        // Update enhanced P&L
        const pnlElement = document.getElementById('daily-pnl-enhanced');
        const pnlPercentElement = document.getElementById('daily-pnl-percent');
        const realizedElement = document.getElementById('realized-pnl');
        const unrealizedElement = document.getElementById('unrealized-pnl');
        
        if (pnlElement) {
            const pnlValue = data.daily_pnl || 0;
            pnlElement.textContent = `$${pnlValue.toFixed(2)}`;
            pnlElement.className = `amount ${pnlValue >= 0 ? 'text-success' : 'text-danger'}`;
        }
        
        if (pnlPercentElement) {
            const pnlPercent = data.daily_pnl_percent || 0;
            pnlPercentElement.textContent = `(${pnlPercent.toFixed(2)}%)`;
            pnlPercentElement.className = `pnl-percentage ${pnlPercent >= 0 ? 'text-success' : 'text-danger'}`;
        }
        
        if (realizedElement) {
            realizedElement.textContent = `$${(data.realized_pnl || 0).toFixed(2)}`;
        }
        
        if (unrealizedElement) {
            unrealizedElement.textContent = `$${(data.unrealized_pnl || 0).toFixed(2)}`;
        }
        
        // Update risk gauge
        this.updateRiskGaugeEnhanced(data);
        
        // Update active positions count
        const positionsElement = document.getElementById('active-positions-enhanced');
        if (positionsElement) {
            positionsElement.textContent = data.active_positions || 0;
        }
    }
    
    updateRiskGaugeEnhanced(data) {
        const riskPercent = data.total_risk_percent || 0;
        const gaugeElement = document.getElementById('risk-gauge-fill');
        const valueElement = document.getElementById('risk-gauge-value');
        const statusElement = document.getElementById('risk-status');
        
        if (gaugeElement && valueElement) {
            // Calculate gauge fill (0-100% mapped to stroke-dashoffset)
            const maxOffset = 314; // circumference
            const fillPercent = Math.min(riskPercent / 10, 1); // Max 10% risk
            const offset = maxOffset - (maxOffset * fillPercent);
            
            gaugeElement.style.strokeDashoffset = offset;
            valueElement.textContent = `${riskPercent.toFixed(1)}%`;
            
            // Update gauge color based on risk level
            if (riskPercent < 2) {
                gaugeElement.style.stroke = '#10B981'; // safe-green
            } else if (riskPercent < 5) {
                gaugeElement.style.stroke = '#F59E0B'; // warning-amber
            } else {
                gaugeElement.style.stroke = '#EF4444'; // danger-red
            }
        }
        
        if (statusElement) {
            if (riskPercent < 2) {
                statusElement.textContent = 'SAFE ZONE';
                statusElement.className = 'risk-status safe';
            } else if (riskPercent < 5) {
                statusElement.textContent = 'MODERATE RISK';
                statusElement.className = 'risk-status warning';
            } else {
                statusElement.textContent = 'HIGH RISK';
                statusElement.className = 'risk-status danger';
            }
        }
    }
}

// Global functions for button actions
async function triggerEmergencyStop() {
    if (confirm('Are you sure you want to trigger emergency stop? This will halt all trading.')) {
        try {
            const response = await fetch('/api/emergency-stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Emergency stop activated successfully');
                dashboard.updateDashboard();
            } else {
                alert('Failed to activate emergency stop: ' + result.error);
            }
        } catch (error) {
            console.error('Error triggering emergency stop:', error);
            alert('Error triggering emergency stop. Please try again.');
        }
    }
}

async function resetEmergencyStop() {
    if (confirm('Are you sure you want to reset emergency stop? Trading will resume.')) {
        try {
            const response = await fetch('/api/reset-emergency-stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Emergency stop reset successfully');
                dashboard.updateDashboard();
            } else {
                alert('Failed to reset emergency stop: ' + result.error);
            }
        } catch (error) {
            console.error('Error resetting emergency stop:', error);
            alert('Error resetting emergency stop. Please try again.');
        }
    }
}

// Enhanced global functions
function adjustAllStops() {
    NotificationManager.show('info', 'Adjusting Stops', 'Updating all stop-loss levels to conservative targets...');
}

function closeAllPositions() {
    if (confirm('Are you sure you want to close all positions? This action cannot be undone.')) {
        NotificationManager.show('warning', 'Closing Positions', 'Closing all active positions...');
    }
}

function executeSignal(signalId) {
    NotificationManager.show('info', 'Executing Trade', 'Processing conservative trade signal...');
}

function paperTrade(signalId) {
    NotificationManager.show('success', 'Paper Trade', 'Signal added to paper trading portfolio.');
}

function dismissSignal(signalId) {
    NotificationManager.show('info', 'Signal Dismissed', 'Trade signal removed from queue.');
}

// Initialize dashboard when page loads
let dashboard;

document.addEventListener('DOMContentLoaded', function() {
    dashboard = new Dashboard();
    
    // Set up enhanced signal filters
    document.querySelectorAll('[data-filter]').forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            document.querySelectorAll('[data-filter]').forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            // Filter signals (placeholder for future implementation)
            const filter = this.dataset.filter;
            console.log('Filtering signals by:', filter);
        });
    });
    
    // Set up timeframe toggles
    document.querySelectorAll('[data-timeframe]').forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from siblings
            this.parentElement.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            
            const timeframe = this.dataset.timeframe;
            console.log('Switching to timeframe:', timeframe);
        });
    });
});

// Handle page visibility changes
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && dashboard) {
        dashboard.updateDashboard();
    }
});
