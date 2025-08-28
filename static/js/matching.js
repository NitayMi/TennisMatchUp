// TennisMatchUp - Matching System JavaScript

const MatchingSystem = {
    
    // Send match request to another player
    sendMatchRequest: function(playerId, playerName) {
        if (confirm(`Send a match request to ${playerName}?`)) {
            fetch('/player/send-match-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    player_id: playerId,
                    message: `Hi ${playerName}, would you like to play tennis together?`
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    TennisApp.showToast(`Match request sent to ${playerName}!`, 'success');
                    // Update UI to show request sent
                    this.updateMatchRequestButton(playerId, 'sent');
                } else {
                    TennisApp.showToast(data.error || 'Failed to send request', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                TennisApp.showToast('Network error occurred', 'error');
            });
        }
    },
    
    // Update match request button state
    updateMatchRequestButton: function(playerId, state) {
        const button = document.querySelector(`[data-player-id="${playerId}"]`);
        if (button) {
            switch(state) {
                case 'sent':
                    button.innerHTML = '<i class="fas fa-clock me-2"></i>Request Sent';
                    button.className = 'btn btn-outline-secondary btn-sm';
                    button.disabled = true;
                    break;
                case 'accepted':
                    button.innerHTML = '<i class="fas fa-check me-2"></i>Matched!';
                    button.className = 'btn btn-success btn-sm';
                    break;
            }
        }
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
        
        // Auto-refresh search results every 30 seconds
        setInterval(() => {
            const currentForm = document.querySelector('#match-search-form');
            if (currentForm && document.visibilityState === 'visible') {
                this.refreshMatches();
            }
        }, 30000);
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
                    this.initMatchingPage(); // Re-initialize event listeners
                }
            })
            .catch(error => console.error('Refresh error:', error));
        }
    },
    
    // Save search preferences
    saveSearchPreferences: function() {
        const form = document.querySelector('#match-search-form');
        if (form) {
            const formData = new FormData(form);
            const preferences = {
                skill_level: formData.get('skill_level'),
                location: formData.get('location'),
                availability: formData.get('availability')
            };
            
            localStorage.setItem('tennis_search_prefs', JSON.stringify(preferences));
        }
    },
    
    // Load saved search preferences
    loadSearchPreferences: function() {
        try {
            const saved = localStorage.getItem('tennis_search_prefs');
            if (saved) {
                const preferences = JSON.parse(saved);
                const form = document.querySelector('#match-search-form');
                
                if (form) {
                    Object.keys(preferences).forEach(key => {
                        const input = form.querySelector(`[name="${key}"]`);
                        if (input && preferences[key]) {
                            input.value = preferences[key];
                        }
                    });
                }
            }
        } catch (error) {
            console.error('Error loading preferences:', error);
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
            TennisApp.showToast('Expanding search criteria...', 'info');
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

window.expandSearch = function() {
    MatchingSystem.expandSearch();
};