// TennisMatchUp - Enhanced Matching System JavaScript

const MatchingSystem = {
    
    // Send match request to another player
    sendMatchRequest: function(playerId, playerName) {
        if (confirm(`Send a match request to ${playerName}?`)) {
            // Show loading state
            this.updateMatchRequestButton(playerId, 'loading');
            
            fetch('/player/send-match-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_id: playerId,
                    message: `Hi ${playerName}, I'd like to play tennis with you. Are you available for a match?`
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showToast(data.message, 'success');
                    this.updateMatchRequestButton(playerId, 'sent');
                } else {
                    this.showToast(data.error || 'Failed to send request', 'error');
                    this.updateMatchRequestButton(playerId, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.showToast('Network error occurred', 'error');
                this.updateMatchRequestButton(playerId, 'error');
            });
        }
    },
    
    // Send message to another player (general messaging)
    sendMessage: function(playerId, playerName) {
        const message = prompt(`Send a message to ${playerName}:`);
        if (message && message.trim()) {
            fetch('/player/send-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'receiver_id': playerId,
                    'content': message.trim()
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showToast(`Message sent to ${playerName}!`, 'success');
                } else {
                    this.showToast(data.error || 'Failed to send message', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                this.showToast('Network error occurred', 'error');
            });
        }
    },
    
    // Update match request button state
    updateMatchRequestButton: function(playerId, state) {
        const button = document.querySelector(`[data-player-id="${playerId}"]`);
        if (button) {
            switch(state) {
                case 'loading':
                    button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
                    button.className = 'btn btn-outline-secondary btn-sm';
                    button.disabled = true;
                    break;
                case 'sent':
                    button.innerHTML = '<i class="fas fa-clock me-2"></i>Request Sent';
                    button.className = 'btn btn-outline-success btn-sm';
                    button.disabled = true;
                    break;
                case 'accepted':
                    button.innerHTML = '<i class="fas fa-check me-2"></i>Matched!';
                    button.className = 'btn btn-success btn-sm';
                    break;
                case 'error':
                    button.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Try Again';
                    button.className = 'btn btn-outline-danger btn-sm';
                    button.disabled = false;
                    break;
            }
        }
    },
    
    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast element if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
            `;
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        const bgColor = {
            'success': 'bg-success',
            'error': 'bg-danger', 
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';
        
        toast.className = `alert ${bgColor} text-white alert-dismissible fade show`;
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    },
    
    // Initialize matching page
    initMatchingPage: function() {
        // Add event listeners to match request buttons
        document.querySelectorAll('[data-action="suggest-match"]').forEach(button => {
            button.addEventListener('click', function() {
                const playerId = this.getAttribute('data-player-id');
                const playerName = this.getAttribute('data-player-name');
                MatchingSystem.sendMatchRequest(playerId, playerName);
            });
        });
        
        // Add event listeners to send message buttons
        document.querySelectorAll('[data-action="send-message"]').forEach(button => {
            button.addEventListener('click', function() {
                const playerId = this.getAttribute('data-player-id');
                const playerName = this.getAttribute('data-player-name');
                MatchingSystem.sendMessage(playerId, playerName);
            });
        });
        
        // Auto-refresh search results every 60 seconds
        setInterval(() => {
            const currentForm = document.querySelector('#match-search-form');
            if (currentForm && document.visibilityState === 'visible') {
                this.refreshMatches();
            }
        }, 60000);
    },
    
    // Refresh match results
    refreshMatches: function() {
        const form = document.querySelector('#match-search-form');
        if (form) {
            const formData = new FormData(form);
            const params = new URLSearchParams(formData);
            
            fetch(`/player/find-matches?${params}`)
            .then(response => response.text())
            .then(html => {
                // Update only the results section
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newResults = doc.querySelector('#match-results');
                const currentResults = document.querySelector('#match-results');
                
                if (newResults && currentResults) {
                    currentResults.innerHTML = newResults.innerHTML;
                    // Re-initialize event listeners for new content
                    this.initMatchingPage();
                }
            })
            .catch(error => {
                console.error('Error refreshing matches:', error);
            });
        }
    },
    
    // Save search preferences
    saveSearchPreferences: function() {
        const form = document.querySelector('#match-search-form');
        if (form) {
            const preferences = {};
            const formData = new FormData(form);
            
            for (let [key, value] of formData.entries()) {
                if (value) {
                    preferences[key] = value;
                }
            }
            
            try {
                localStorage.setItem('tennis_search_prefs', JSON.stringify(preferences));
            } catch (error) {
                console.warn('Could not save search preferences:', error);
            }
        }
    },
    
    // Load search preferences
    loadSearchPreferences: function() {
        try {
            const saved = localStorage.getItem('tennis_search_prefs');
            if (saved) {
                const preferences = JSON.parse(saved);
                const form = document.querySelector('#match-search-form');
                
                if (form) {
                    Object.keys(preferences).forEach(key => {
                        const field = form.querySelector(`[name="${key}"]`);
                        if (field && preferences[key]) {
                            field.value = preferences[key];
                        }
                    });
                }
            }
        } catch (error) {
            console.warn('Could not load search preferences:', error);
        }
    },
    
    // Expand search criteria
    expandSearch: function() {
        const form = document.querySelector('#match-search-form');
        if (form) {
            // Clear restrictive filters
            const skillSelect = form.querySelector('[name="skill_level"]');
            if (skillSelect) skillSelect.value = '';
            
            const locationInput = form.querySelector('[name="location"]');
            if (locationInput) locationInput.value = '';
            
            // Show message and submit
            this.showToast('Expanding search criteria...', 'info');
            form.submit();
        }
    }
};

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.match-card')) {
        MatchingSystem.initMatchingPage();
        MatchingSystem.loadSearchPreferences();
        
        // Save preferences when form changes
        const form = document.querySelector('#match-search-form');
        if (form) {
            form.addEventListener('change', () => {
                MatchingSystem.saveSearchPreferences();
            });
        }
    }
});

// Global functions for inline event handlers
window.suggestMatch = function(playerId, playerName) {
    MatchingSystem.sendMatchRequest(playerId, playerName);
};

window.sendMessage = function(playerId, playerName) {
    MatchingSystem.sendMessage(playerId, playerName);
};

window.expandSearch = function() {
    MatchingSystem.expandSearch();
};