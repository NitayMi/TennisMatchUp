/**
 * Dashboard Widgets JavaScript for TennisMatchUp
 * Handles all dashboard interactions and real-time updates
 */

class DashboardWidgetManager {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.charts = {};
        this.intervalId = null;
        this.isVisible = true;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeWidgets();
        this.startAutoRefresh();
        this.setupVisibilityHandling();
    }
    
    bindEvents() {
        // Widget refresh buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.widget-refresh')) {
                const widgetId = e.target.closest('.dashboard-widget').id;
                this.refreshWidget(widgetId);
            }
        });
        
        // Stats card animations on scroll
        this.setupScrollAnimations();
        
        // Chart filter changes
        document.addEventListener('change', (e) => {
            if (e.target.matches('.chart-filter')) {
                const chartId = e.target.dataset.chartId;
                this.updateChart(chartId, e.target.value);
            }
        });
        
        // Quick action buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.dashboard-action-btn[data-action]')) {
                e.preventDefault();
                this.handleQuickAction(e.target.dataset.action, e.target);
            }
        });
        
        // Widget settings
        document.addEventListener('click', (e) => {
            if (e.target.matches('.widget-settings')) {
                const widgetId = e.target.closest('.dashboard-widget').id;
                this.showWidgetSettings(widgetId);
            }
        });
    }
    
    initializeWidgets() {
        // Initialize all dashboard widgets
        this.initializeStatsCards();
        this.initializeCharts();
        this.initializeActivityFeed();
        this.initializeQuickActions();
        
        // Animate on load
        this.animateWidgetsOnLoad();
    }
    
    initializeStatsCards() {
        const statsCards = document.querySelectorAll('.dashboard-stat-card');
        
        statsCards.forEach((card, index) => {
            // Add loading animation
            setTimeout(() => {
                card.classList.add('dashboard-fade-in');
                this.animateCounter(card);
            }, index * 100);
            
            // Add click interaction for detailed view
            card.addEventListener('click', () => {
                const statType = card.dataset.statType;
                if (statType) {
                    this.showStatDetails(statType);
                }
            });
        });
    }
    
    animateCounter(card) {
        const numberElement = card.querySelector('.dashboard-stat-number');
        if (!numberElement) return;
        
        const finalValue = parseInt(numberElement.textContent.replace(/[^0-9.-]+/g, ''));
        if (isNaN(finalValue)) return;
        
        const duration = 1500;
        const startValue = 0;
        const increment = finalValue / (duration / 16);
        let currentValue = startValue;
        
        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(timer);
            }
            
            // Format the number appropriately
            const formatted = this.formatStatNumber(Math.floor(currentValue), card.dataset.statType);
            numberElement.textContent = formatted;
        }, 16);
    }
    
    formatStatNumber(value, statType) {
        switch (statType) {
            case 'revenue':
                return `$${value.toLocaleString()}`;
            case 'percentage':
                return `${value}%`;
            case 'rating':
                return (value / 10).toFixed(1);
            default:
                return value.toLocaleString();
        }
    }
    
    initializeCharts() {
        // Initialize Chart.js charts
        this.initializeRevenueChart();
        this.initializeBookingsChart();
        this.initializeActivityChart();
        this.initializePerformanceChart();
    }
    
    initializeRevenueChart() {
        const canvas = document.getElementById('revenueChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.revenue = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.getLast7Days(),
                datasets: [{
                    label: 'Daily Revenue',
                    data: [],
                    borderColor: 'rgb(44, 85, 48)',
                    backgroundColor: 'rgba(44, 85, 48, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + value;
                            }
                        }
                    }
                }
            }
        });
        
        this.loadChartData('revenue');
    }
    
    initializeBookingsChart() {
        const canvas = document.getElementById('bookingsChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.bookings = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Confirmed', 'Pending', 'Cancelled'],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#28a745',
                        '#ffc107',
                        '#dc3545'
                    ],
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
        
        this.loadChartData('bookings');
    }
    
    initializeActivityChart() {
        const canvas = document.getElementById('activityChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.activity = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                datasets: [{
                    label: 'Daily Activity',
                    data: [],
                    backgroundColor: 'rgba(44, 85, 48, 0.8)',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
        
        this.loadChartData('activity');
    }
    
    initializePerformanceChart() {
        const canvas = document.getElementById('performanceChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        this.charts.performance = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: ['Bookings', 'Revenue', 'Users', 'Courts', 'Rating', 'Growth'],
                datasets: [{
                    label: 'Performance',
                    data: [],
                    borderColor: 'rgb(44, 85, 48)',
                    backgroundColor: 'rgba(44, 85, 48, 0.2)',
                    pointBackgroundColor: 'rgb(44, 85, 48)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        this.loadChartData('performance');
    }
    
    async loadChartData(chartType) {
        try {
            const response = await fetch(`/api/dashboard/chart-data?type=${chartType}`);
            const data = await response.json();
            
            if (data.success && this.charts[chartType]) {
                this.charts[chartType].data.datasets[0].data = data.data;
                this.charts[chartType].update();
            }
        } catch (error) {
            console.error(`Error loading ${chartType} chart data:`, error);
        }
    }
    
    initializeActivityFeed() {
        const activityFeed = document.getElementById('activity-feed');
        if (!activityFeed) return;
        
        // Load initial activity data
        this.loadActivityFeed();
        
        // Setup real-time updates
        this.setupActivityUpdates();
    }
    
    async loadActivityFeed() {
        try {
            const response = await fetch('/api/dashboard/recent-activity');
            const data = await response.json();
            
            if (data.success) {
                this.renderActivityItems(data.activities);
            }
        } catch (error) {
            console.error('Error loading activity feed:', error);
        }
    }
    
    renderActivityItems(activities) {
        const container = document.getElementById('activity-feed');
        if (!container) return;
        
        container.innerHTML = '';
        
        activities.forEach((activity, index) => {
            const item = this.createActivityItem(activity);
            item.style.opacity = '0';
            item.style.transform = 'translateX(-20px)';
            container.appendChild(item);
            
            // Animate in
            setTimeout(() => {
                item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, index * 50);
        });
    }
    
    createActivityItem(activity) {
        const item = document.createElement('div');
        item.className = 'dashboard-activity-item';
        
        const iconClass = this.getActivityIcon(activity.type);
        const timeAgo = this.formatTimeAgo(new Date(activity.created_at));
        
        item.innerHTML = `
            <div class="dashboard-activity-icon">
                <i class="${iconClass}"></i>
            </div>
            <div class="dashboard-activity-content">
                <div class="dashboard-activity-title">${activity.title}</div>
                <div class="dashboard-activity-meta">${activity.description}</div>
            </div>
            <div class="dashboard-activity-time">${timeAgo}</div>
        `;
        
        return item;
    }
    
    getActivityIcon(type) {
        const icons = {
            booking: 'fas fa-calendar-plus',
            user: 'fas fa-user-plus',
            court: 'fas fa-tennis-ball',
            message: 'fas fa-envelope',
            payment: 'fas fa-credit-card',
            match: 'fas fa-handshake'
        };
        return icons[type] || 'fas fa-circle';
    }
    
    initializeQuickActions() {
        // Setup quick action buttons
        const quickActions = document.querySelectorAll('.dashboard-action-btn');
        
        quickActions.forEach(button => {
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px)';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
            });
        });
    }
    
    handleQuickAction(action, button) {
        const originalText = button.innerHTML;
        
        // Show loading state
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
        
        switch (action) {
            case 'book-court':
                this.quickBookCourt();
                break;
            case 'find-matches':
                this.quickFindMatches();
                break;
            case 'add-court':
                this.quickAddCourt();
                break;
            case 'view-reports':
                this.quickViewReports();
                break;
            default:
                console.log(`Unknown action: ${action}`);
        }
        
        // Reset button state
        setTimeout(() => {
            button.disabled = false;
            button.innerHTML = originalText;
        }, 1000);
    }
    
    quickBookCourt() {
        // Redirect to booking with suggested date/time
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        const suggestedDate = tomorrow.toISOString().split('T')[0];
        
        window.location.href = `/player/book-court?date=${suggestedDate}&suggested=true`;
    }
    
    quickFindMatches() {
        window.location.href = '/player/find-matches?quick=true';
    }
    
    quickAddCourt() {
        window.location.href = '/owner/add-court';
    }
    
    quickViewReports() {
        window.location.href = '/owner/reports';
    }
    
    startAutoRefresh() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        this.intervalId = setInterval(() => {
            if (this.isVisible) {
                this.refreshDashboardData();
            }
        }, this.refreshInterval);
    }
    
    async refreshDashboardData() {
        try {
            // Refresh stats
            await this.refreshStats();
            
            // Refresh charts
            Object.keys(this.charts).forEach(chartType => {
                this.loadChartData(chartType);
            });
            
            // Refresh activity feed
            await this.loadActivityFeed();
            
            // Show refresh indicator
            this.showRefreshIndicator();
            
        } catch (error) {
            console.error('Error refreshing dashboard:', error);
        }
    }
    
    async refreshStats() {
        try {
            const response = await fetch('/api/dashboard/quick-stats');
            const data = await response.json();
            
            if (data.success) {
                this.updateStatsCards(data.stats);
            }
        } catch (error) {
            console.error('Error refreshing stats:', error);
        }
    }
    
    updateStatsCards(newStats) {
        Object.keys(newStats).forEach(statKey => {
            const card = document.querySelector(`[data-stat-type="${statKey}"]`);
            if (card) {
                const numberElement = card.querySelector('.dashboard-stat-number');
                const oldValue = parseInt(numberElement.textContent.replace(/[^0-9.-]+/g, ''));
                const newValue = newStats[statKey];
                
                if (oldValue !== newValue) {
                    this.animateStatChange(numberElement, oldValue, newValue, statKey);
                }
            }
        });
    }
    
    animateStatChange(element, oldValue, newValue, statType) {
        // Highlight the change
        element.parentNode.classList.add('stat-updated');
        
        // Animate the number change
        const duration = 800;
        const increment = (newValue - oldValue) / (duration / 16);
        let currentValue = oldValue;
        
        const timer = setInterval(() => {
            currentValue += increment;
            
            if ((increment > 0 && currentValue >= newValue) || 
                (increment < 0 && currentValue <= newValue)) {
                currentValue = newValue;
                clearInterval(timer);
                
                // Remove highlight after animation
                setTimeout(() => {
                    element.parentNode.classList.remove('stat-updated');
                }, 1000);
            }
            
            element.textContent = this.formatStatNumber(Math.floor(currentValue), statType);
        }, 16);
    }
    
    showRefreshIndicator() {
        const indicator = document.getElementById('refresh-indicator');
        if (indicator) {
            indicator.style.opacity = '1';
            setTimeout(() => {
                indicator.style.opacity = '0';
            }, 2000);
        }
    }
    
    setupScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('dashboard-slide-in');
                }
            });
        }, {
            threshold: 0.1
        });
        
        // Observe all widgets
        document.querySelectorAll('.dashboard-widget, .dashboard-stat-card').forEach(widget => {
            observer.observe(widget);
        });
    }
    
    setupVisibilityHandling() {
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            
            if (this.isVisible) {
                // Refresh data when tab becomes visible
                this.refreshDashboardData();
            }
        });
    }
    
    animateWidgetsOnLoad() {
        const widgets = document.querySelectorAll('.dashboard-widget');
        
        widgets.forEach((widget, index) => {
            widget.style.opacity = '0';
            widget.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                widget.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                widget.style.opacity = '1';
                widget.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }
    
    showStatDetails(statType) {
        // Show detailed modal or redirect to detailed page
        const modal = document.getElementById('stat-details-modal');
        if (modal) {
            this.loadStatDetails(statType, modal);
            new bootstrap.Modal(modal).show();
        }
    }
    
    async loadStatDetails(statType, modal) {
        try {
            const response = await fetch(`/api/dashboard/stat-details?type=${statType}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderStatDetails(data.details, modal);
            }
        } catch (error) {
            console.error('Error loading stat details:', error);
        }
    }
    
    getLast7Days() {
        const days = [];
        for (let i = 6; i >= 0; i--) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            days.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
        }
        return days;
    }
    
    formatTimeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    }
    
    destroy() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart.destroy) {
                chart.destroy();
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.dashboard-container')) {
        window.dashboardManager = new DashboardWidgetManager();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.dashboardManager) {
        window.dashboardManager.destroy();
    }
});

// Export for use in other scripts
window.DashboardWidgetManager = DashboardWidgetManager;