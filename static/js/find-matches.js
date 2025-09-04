/**
 * Find Matches JavaScript for TennisMatchUp
 * EXTRACTED from templates - no more embedded JS!
 */

class FindMatchesManager {
    constructor() {
        this.currentPage = 1;
        this.loading = false;
        this.hasMore = true;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.initializeAnimations();
    }
    
    bindEvents() {
        // Match request modal
        document.addEventListener('click', (e) => {
            if (e.target.closest('[data-bs-target="#matchRequestModal"]')) {
                const btn = e.target.closest('[data-bs-target="#matchRequestModal"]');
                this.showMatchRequestModal(
                    btn.dataset.playerId,
                    btn.dataset.playerName
                );
            }
        });
        
        // Send match request
        document.getElementById('send-request-btn')?.addEventListener('click', () => {
            this.sendMatchRequest();
        });
        
        // Load more matches
        document.getElementById('load-more-btn')?.addEventListener('click', () => {
            this.loadMoreMatches();
        });
        
        // Filter form submission
        document.getElementById('filter-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.applyFilters();
        });
        
        // View profile
        window.viewPlayerProfile = (playerId) => {
            this.viewPlayerProfile(playerId);
        };
    }
    
    showMatchRequestModal(playerId, playerName) {
        const modal = document.getElementById('matchRequestModal');
        const playerIdInput = document.getElementById('target-player-id');
        const modalTitle = modal.querySelector('.modal-title');
        
        playerIdInput.value = playerId;
        modalTitle.innerHTML = `<i class="fas fa-handshake me-2"></i>Send Match Request to ${playerName}`;
        
        // Set default message
        const messageTextarea = document.getElementById('match-message');
        if (!messageTextarea.value.trim()) {
            messageTextarea.value = `Hi ${playerName}! I saw your profile and would love to play tennis with you. Are you available for a match this week?`;
        }
    }
    
    async sendMatchRequest() {
        const form = document.getElementById('match-request-form');
        const sendBtn = document.getElementById('send-request-btn');
        const originalText = sendBtn.innerHTML;
        
        // Validate form
        const playerId = document.getElementById('target-player-id').value;
        const message = document.getElementById('match-message').value.trim();
        
        if (!playerId || !message) {
            this.showError('Please fill in all required fields');
            return;
        }
        
        // Update button state
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
        
        try {
            const response = await fetch('/player/send-match-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    target_player_id: playerId,
                    message: message
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccess(result.message);
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('matchRequestModal'));
                modal.hide();
                
                // Reset form
                form.reset();
                
                // Mark player as contacted
                this.markPlayerContacted(playerId);
                
            } else {
                this.showError(result.error || 'Failed to send match request');
            }
            
        } catch (error) {
            console.error('Error sending match request:', error);
            this.showError('Network error occurred');
        } finally {
            sendBtn.disabled = false;
            sendBtn.innerHTML = originalText;
        }
    }
    
    async loadMoreMatches() {
        if (this.loading || !this.hasMore) return;
        
        this.loading = true;
        const loadBtn = document.getElementById('load-more-btn');
        const originalText = loadBtn.innerHTML;
        
        loadBtn.disabled = true;
        loadBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
        
        try {
            const url = new URL(window.location.href);
            url.searchParams.set('page', this.currentPage + 1);
            url.searchParams.set('ajax', '1');
            
            const response = await fetch(url.toString());
            const html = await response.text();
            
            if (html.trim()) {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = html;
                
                const newMatches = tempDiv.querySelectorAll('.match-card').length;
                
                if (newMatches > 0) {
                    const container = document.getElementById('matches-container');
                    container.insertAdjacentHTML('beforeend', html);
                    
                    this.currentPage++;
                    this.initializeNewMatches();
                } else {
                    this.hasMore = false;
                    loadBtn.style.display = 'none';
                    this.showInfo('No more matches found');
                }
            } else {
                this.hasMore = false;
                loadBtn.style.display = 'none';
            }
            
        } catch (error) {
            console.error('Error loading more matches:', error);
            this.showError('Failed to load more matches');
        } finally {
            this.loading = false;
            loadBtn.disabled = false;
            loadBtn.innerHTML = originalText;
        }
    }
    
    async applyFilters() {
        const form = document.getElementById('filter-form');
        const formData = new FormData(form);
        const params = new URLSearchParams(formData);
        
        // Show loading state
        this.showLoadingState();
        
        try {
            const response = await fetch(`/player/find-matches?${params.toString()}`);
            const html = await response.text();
            
            // Update page content
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newContent = doc.querySelector('#matches-container');
            
            if (newContent) {
                document.getElementById('matches-container').innerHTML = newContent.innerHTML;
                this.initializeNewMatches();
            }
            
            // Reset pagination
            this.currentPage = 1;
            this.hasMore = true;
            
            // Update URL without page reload
            const url = new URL(window.location.href);
            for (const [key, value] of params) {
                if (value) {
                    url.searchParams.set(key, value);
                } else {
                    url.searchParams.delete(key);
                }
            }
            window.history.pushState({}, '', url.toString());
            
        } catch (error) {
            console.error('Error applying filters:', error);
            this.showError('Failed to apply filters');
        } finally {
            this.hideLoadingState();
        }
    }
    
    viewPlayerProfile(playerId) {
        // Open profile modal or navigate to profile page
        window.open(`/player/profile/${playerId}`, '_blank');
    }
    
    markPlayerContacted(playerId) {
        // Mark the player as contacted in the UI
        const matchCard = document.querySelector(`[data-player-id="${playerId}"]`)?.closest('.match-card');
        if (matchCard) {
            const connectBtn = matchCard.querySelector('.btn-connect');
            if (connectBtn) {
                connectBtn.innerHTML = '<i class="fas fa-check me-2"></i>Request Sent';
                connectBtn.disabled = true;
                connectBtn.classList.remove('btn-connect');
                connectBtn.classList.add('btn-success');
            }
        }
    }
    
    initializeAnimations() {
        // Animate match cards on load
        const matchCards = document.querySelectorAll('.match-card');
        matchCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                card.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
        
        // Animate compatibility bars
        setTimeout(() => {
            const compatibilityBars = document.querySelectorAll('.compatibility-fill');
            compatibilityBars.forEach(bar => {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.transition = 'width 1s ease';
                    bar.style.width = width;
                }, 500);
            });
        }, 500);
    }
    
    initializeNewMatches() {
        // Initialize animations for newly loaded matches
        const newCards = document.querySelectorAll('.match-card:not(.animated)');
        newCards.forEach((card, index) => {
            card.classList.add('animated');
            card.classList.add('match-card-enter');
            
            setTimeout(() => {
                card.classList.add('match-card-enter-active');
            }, index * 50);
        });
    }
    
    showLoadingState() {
        const container = document.getElementById('matches-container');
        if (container) {
            container.style.opacity = '0.5';
            container.style.pointerEvents = 'none';
        }
        
        // Show loading spinner
        let loader = document.getElementById('matches-loader');
        if (!loader) {
            loader = document.createElement('div');
            loader.id = 'matches-loader';
            loader.className = 'loading-matches';
            loader.innerHTML = `
                <div class="loading-spinner"></div>
                <p>Finding your perfect tennis matches...</p>
            `;
            container?.parentNode.insertBefore(loader, container);
        }
        loader.style.display = 'block';
    }
    
    hideLoadingState() {
        const container = document.getElementById('matches-container');
        if (container) {
            container.style.opacity = '1';
            container.style.pointerEvents = 'auto';
        }
        
        const loader = document.getElementById('matches-loader');
        if (loader) {
            loader.style.display = 'none';
        }
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showInfo(message) {
        this.showMessage(message, 'info');
    }
    
    showMessage(message, type) {
        // Remove existing messages
        document.querySelectorAll('.find-matches-message').forEach(el => el.remove());
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `alert alert-${type === 'error' ? 'danger' : type === 'info' ? 'info' : 'success'} find-matches-message`;
        messageEl.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'info' ? 'info-circle' : 'check-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.container');
        container.insertBefore(messageEl, container.firstChild);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.remove();
            }
        }, 5000);
        
        // Scroll to message
        messageEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('matches-container')) {
        window.findMatchesManager = new FindMatchesManager();
    }
});

// Export for use in other scripts
window.FindMatchesManager = FindMatchesManager;