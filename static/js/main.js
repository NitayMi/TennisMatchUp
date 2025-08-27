// TennisMatchUp Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Confirm delete actions
    var deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Loading spinner for forms
    var forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            var submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                submitBtn.disabled = true;
            }
        });
    });

    // Real-time search
    var searchInputs = document.querySelectorAll('[data-search]');
    searchInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var searchTerm = this.value.toLowerCase();
            var targetSelector = this.getAttribute('data-search');
            var targets = document.querySelectorAll(targetSelector);
            
            targets.forEach(function(target) {
                var text = target.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    target.style.display = '';
                } else {
                    target.style.display = 'none';
                }
            });
        });
    });
});

// Utility Functions
const TennisApp = {
    // Show loading state
    showLoading: function(element) {
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        if (element) {
            element.innerHTML = '<div class="text-center"><div class="loading-spinner mx-auto"></div><p class="mt-2">Loading...</p></div>';
        }
    },

    // Show error message
    showError: function(message, container) {
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        if (container) {
            container.innerHTML = `<div class="alert alert-danger">${message}</div>`;
        }
    },

    // Format currency
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
    },

    // Format date
    formatDate: function(date) {
        return new Intl.DateTimeFormat('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        }).format(new Date(date));
    },

    // Format time
    formatTime: function(time) {
        return new Intl.DateTimeFormat('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        }).format(new Date('2000-01-01 ' + time));
    },

    // AJAX helper
    ajax: function(url, options) {
        const defaults = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        const config = Object.assign({}, defaults, options);
        
        return fetch(url, config)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            });
    },

    // Get CSRF token (if needed)
    getCSRFToken: function() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : null;
    },

    // Debounce function for search inputs
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 350px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
    },

    // Validate form
    validateForm: function(form) {
        if (typeof form === 'string') {
            form = document.querySelector(form);
        }
        
        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
            }
        });
        
        // Email validation
        const emailFields = form.querySelectorAll('input[type="email"]');
        emailFields.forEach(field => {
            if (field.value && !this.isValidEmail(field.value)) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        });
        
        return isValid;
    },

    // Email validation
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Phone validation
    isValidPhone: function(phone) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
    },

    // Initialize DataTables (if present)
    initDataTables: function() {
        if (typeof DataTable !== 'undefined') {
            document.querySelectorAll('.data-table').forEach(table => {
                new DataTable(table, {
                    pageLength: 25,
                    responsive: true,
                    order: [[0, 'desc']]
                });
            });
        }
    },

    // Initialize date pickers
    initDatePickers: function() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            // Set minimum date to today
            if (input.hasAttribute('data-min-today')) {
                input.min = new Date().toISOString().split('T')[0];
            }
            
            // Set maximum date
            if (input.hasAttribute('data-max-days')) {
                const maxDays = parseInt(input.getAttribute('data-max-days'));
                const maxDate = new Date();
                maxDate.setDate(maxDate.getDate() + maxDays);
                input.max = maxDate.toISOString().split('T')[0];
            }
        });
    }
};

// Global error handler
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    // In production, might send to logging service
});

// Initialize common features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    TennisApp.initDatePickers();
    TennisApp.initDataTables();
});

// Export for use in other scripts
window.TennisApp = TennisApp;