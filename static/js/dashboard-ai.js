/**
 * Enhanced AI Features for Player Dashboard
 * Combines existing advisory features with new action capabilities
 */
class DashboardAI {
    constructor() {
        this.quickActions = [];
        this.activeProposals = [];
        this.init();
    }
    
    init() {
        this.loadRecommendations();
        this.loadQuickActions();
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Existing advisory features
        const refreshBtn = document.getElementById('refresh-recommendations');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadRecommendations();
            });
        }
        
        const courtAdviceBtn = document.getElementById('get-court-advice');
        if (courtAdviceBtn) {
            courtAdviceBtn.addEventListener('click', () => {
                this.loadCourtRecommendations();
            });
        }
        
        // New action features
        const actionInput = document.getElementById('ai-action-input');
        const actionBtn = document.getElementById('ai-action-send');
        
        if (actionInput && actionBtn) {
            actionBtn.addEventListener('click', () => {
                this.handleActionRequest();
            });
            
            actionInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.handleActionRequest();
                }
            });
        }
    }
    
    // ===== EXISTING ADVISORY FUNCTIONS (UNCHANGED) =====
    
    async loadRecommendations() {
        const container = document.getElementById('ai-recommendations');
        if (!container) return;
        
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-success" role="status"><span class="sr-only">Loading...</span></div></div>';
        
        try {
            const response = await fetch('/ai/recommendations');
            const data = await response.json();
            
            if (data.success) {
                container.innerHTML = `
                    <div class="ai-recommendation">
                        <h6><i class="fas fa-lightbulb text-warning"></i> Personal Tennis Recommendations</h6>
                        <div class="recommendation-content">
                            ${data.recommendations.replace(/\n/g, '<br>')}
                        </div>
                    </div>
                `;
            } else {
                container.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> AI recommendations unavailable at the moment</div>';
            }
        } catch (error) {
            console.error('Error loading AI recommendations:', error);
            container.innerHTML = '<div class="alert alert-danger"><i class="fas fa-times-circle"></i> Error loading recommendations. Please try again later.</div>';
        }
    }
    
    async loadCourtRecommendations() {
        const container = document.getElementById('court-recommendations');
        if (!container) return;
        
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-success" role="status"><span class="sr-only">Loading...</span></div></div>';
        
        try {
            const response = await fetch('/ai/court-advisor');
            const data = await response.json();
            
            if (data.success) {
                container.innerHTML = `
                    <div class="court-advice">
                        <h6><i class="fas fa-brain text-info"></i> Smart Court Selection Advice</h6>
                        <div class="advice-content">
                            ${data.advice.replace(/\n/g, '<br>')}
                        </div>
                        <div class="mt-3">
                            <button id="get-court-advice" class="btn btn-outline-success btn-sm">
                                <i class="fas fa-refresh"></i> Get New Recommendations
                            </button>
                        </div>
                    </div>
                `;
                this.setupEventListeners(); // Re-attach event listeners
            } else {
                container.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> Court advisor unavailable at the moment</div>';
            }
        } catch (error) {
            console.error('Error loading court recommendations:', error);
            container.innerHTML = '<div class="alert alert-danger"><i class="fas fa-times-circle"></i> Error loading court advice. Please try again later.</div>';
        }
    }
    
    // ===== NEW ACTION FUNCTIONS =====
    
    async loadQuickActions() {
        const container = document.getElementById('ai-quick-actions');
        if (!container) return;
        
        try {
            const response = await fetch('/ai/quick-actions');
            const data = await response.json();
            
            if (data.success) {
                this.quickActions = data.actions;
                this.renderQuickActions(container);
            } else {
                container.innerHTML = '<div class="alert alert-warning">Quick actions unavailable</div>';
            }
        } catch (error) {
            console.error('Error loading quick actions:', error);
            container.innerHTML = '<div class="alert alert-danger">Error loading quick actions</div>';
        }
    }
    
    renderQuickActions(container) {
        const actionsHtml = this.quickActions.map(action => `
            <div class="col-md-6 mb-3">
                <div class="card quick-action-card" data-action-id="${action.id}" style="cursor: pointer;">
                    <div class="card-body text-center">
                        <i class="${action.icon} fa-2x text-success mb-2"></i>
                        <h6 class="card-title">${action.title}</h6>
                        <p class="card-text small text-muted">${action.description}</p>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = `
            <div class="row">
                ${actionsHtml}
            </div>
        `;
        
        // Add click handlers for quick actions
        container.querySelectorAll('.quick-action-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const actionId = e.currentTarget.dataset.actionId;
                this.executeQuickAction(actionId);
            });
        });
    }
    
    async executeQuickAction(actionId) {
        const action = this.quickActions.find(a => a.id === actionId);
        if (!action) return;
        
        // Map quick action to appropriate request
        let message = '';
        switch (action.action_type) {
            case 'FIND_PARTNER':
                message = 'Find me a tennis partner in my area for today or tomorrow';
                break;
            case 'FIND_MATCH_AND_COURT':
                message = 'Find me a complete match setup with partner and court for this weekend';
                break;
            case 'CHECK_AVAILABILITY':
                message = 'When am I available to play tennis this week?';
                break;
            case 'WEEKEND_SEARCH':
                message = 'Find me tennis matches for this weekend';
                break;
            default:
                message = `Execute ${action.title}`;
        }
        
        await this.handleActionRequest(message);
    }
    
    async handleActionRequest(customMessage = null) {
        const input = document.getElementById('ai-action-input');
        const container = document.getElementById('ai-action-results');
        
        if (!container) return;
        
        const message = customMessage || (input ? input.value.trim() : '');
        if (!message) return;
        
        if (input && !customMessage) {
            input.value = '';
        }
        
        container.innerHTML = '<div class="text-center"><div class="spinner-border text-primary" role="status"><span class="sr-only">Processing...</span></div><p class="mt-2">AI is finding matches for you...</p></div>';
        
        try {
            const response = await fetch('/ai/action-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayActionResults(data.action_result, container);
            } else {
                container.innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> ${data.error}</div>`;
            }
        } catch (error) {
            console.error('Error processing action request:', error);
            container.innerHTML = '<div class="alert alert-danger"><i class="fas fa-times-circle"></i> Connection error. Please try again.</div>';
        }
    }
    
    displayActionResults(result, container) {
        if (result.action_type === 'GENERAL_CHAT') {
            container.innerHTML = `
                <div class="alert alert-info">
                    <h6><i class="fas fa-robot"></i> AI Response</h6>
                    <p>${result.response.replace(/\n/g, '<br>')}</p>
                </div>
            `;
            return;
        }
        
        if (result.players_found) {
            this.displayPlayerResults(result, container);
        } else if (result.courts_found) {
            this.displayCourtResults(result, container);
        } else if (result.error) {
            container.innerHTML = `<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> ${result.error}</div>`;
        } else {
            container.innerHTML = '<div class="alert alert-info">No specific results found. Try a different request.</div>';
        }
    }
    
    displayPlayerResults(result, container) {
        const playersHtml = result.players_found.map(player => `
            <div class="col-md-4 mb-3">
                <div class="card player-result-card">
                    <div class="card-body">
                        <h6 class="card-title">${player.name}</h6>
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="fas fa-trophy"></i> ${player.skill_level}<br>
                                <i class="fas fa-map-marker-alt"></i> ${player.location}<br>
                                <i class="fas fa-percent"></i> ${player.compatibility_score}% match
                            </small>
                        </p>
                        <button class="btn btn-success btn-sm" onclick="dashboardAI.sendMatchRequest(${player.player_id}, '${player.name}')">
                            <i class="fas fa-paper-plane"></i> Send Match Request
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-users"></i> Found ${result.players_found.length} Available Players</h6>
                <p>Based on your location: ${result.search_params?.location || 'your area'}</p>
            </div>
            <div class="row">
                ${playersHtml}
            </div>
        `;
    }
    
    displayCourtResults(result, container) {
        const courtsHtml = result.courts_found.map(court => `
            <div class="col-md-4 mb-3">
                <div class="card court-result-card">
                    <div class="card-body">
                        <h6 class="card-title">${court.name}</h6>
                        <p class="card-text">
                            <small class="text-muted">
                                <i class="fas fa-map-marker-alt"></i> ${court.location}<br>
                                <i class="fas fa-layer-group"></i> ${court.surface_type}<br>
                                <i class="fas fa-dollar-sign"></i> $${court.hourly_rate}/hour
                            </small>
                        </p>
                        <button class="btn btn-primary btn-sm" onclick="dashboardAI.bookCourt(${court.court_id}, '${court.name}')">
                            <i class="fas fa-calendar-plus"></i> Book Court
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = `
            <div class="alert alert-success">
                <h6><i class="fas fa-building"></i> Found ${result.courts_found.length} Available Courts</h6>
                <p>In ${result.search_params?.location || 'your area'}</p>
            </div>
            <div class="row">
                ${courtsHtml}
            </div>
        `;
    }
    
    async sendMatchRequest(playerId, playerName) {
        if (!confirm(`Send a match request to ${playerName}?`)) {
            return;
        }
        
        try {
            // For demo purposes, show success message
            // In full implementation, this would create an actual match request
            const alertHtml = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <i class="fas fa-check-circle"></i> Match request sent to ${playerName}!
                    <button type="button" class="close" data-dismiss="alert">
                        <span>&times;</span>
                    </button>
                </div>
            `;
            
            document.querySelector('#ai-action-results').insertAdjacentHTML('afterbegin', alertHtml);
            
        } catch (error) {
            console.error('Error sending match request:', error);
            alert('Error sending match request. Please try again.');
        }
    }
    
    async bookCourt(courtId, courtName) {
        if (!confirm(`Book ${courtName}? You'll be redirected to the booking page.`)) {
            return;
        }
        
        try {
            // Redirect to court booking page with pre-selected court
            window.location.href = `/player/book-court?court_id=${courtId}`;
            
        } catch (error) {
            console.error('Error booking court:', error);
            alert('Error booking court. Please try again.');
        }
    }
    // ADD these methods to the existing DashboardAI class

    setupEventListeners() {
        // AI Recommendations refresh button
        const refreshBtn = document.getElementById('refresh-recommendations');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadRecommendations();
            });
        }
        
        // Court advisor button
        const courtAdviceBtn = document.getElementById('get-court-advice');
        if (courtAdviceBtn) {
            courtAdviceBtn.addEventListener('click', () => {
                this.loadCourtRecommendations();
            });
        }
        
        // NEW: Quick action buttons
        this.setupQuickActionButtons();
        
        // NEW: Tell AI form
        this.setupTellAIForm();
    }

    setupQuickActionButtons() {
        // Find Partner Now button
        const findPartnerBtn = document.querySelector('[onclick*="find_partner_now"]');
        if (findPartnerBtn) {
            findPartnerBtn.removeAttribute('onclick');
            findPartnerBtn.addEventListener('click', () => {
                this.handleQuickAction('find_partner_now');
            });
        }
        
        // Court + Partner button  
        const courtPartnerBtn = document.querySelector('[onclick*="court_and_partner"]');
        if (courtPartnerBtn) {
            courtPartnerBtn.removeAttribute('onclick');
            courtPartnerBtn.addEventListener('click', () => {
                this.handleQuickAction('court_and_partner');
            });
        }
        
        // Weekend Matches button
        const weekendBtn = document.querySelector('[onclick*="weekend_matches"]');
        if (weekendBtn) {
            weekendBtn.removeAttribute('onclick');
            weekendBtn.addEventListener('click', () => {
                this.handleQuickAction('weekend_matches');
            });
        }
    }

    setupTellAIForm() {
        const askAIBtn = document.getElementById('ask-ai-btn') || document.querySelector('.btn:contains("Ask AI")');
        if (askAIBtn) {
            askAIBtn.addEventListener('click', () => {
                const input = document.querySelector('input[placeholder*="beginner partner"]');
                if (input && input.value.trim()) {
                    this.handleTellAI(input.value.trim());
                    input.value = '';
                }
            });
        }
    }

    async handleQuickAction(actionType) {
        this.showActionLoading(actionType);
        
        try {
            const response = await fetch('/ai/action-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action_type: actionType,
                    message: ''
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayActionResults(data);
            } else {
                this.showActionError(data.message || 'Action failed');
            }
        } catch (error) {
            console.error('Action error:', error);
            this.showActionError('Connection error. Please try again.');
        }
    }

    async handleTellAI(message) {
        this.showActionLoading('tell_ai');
        
        try {
            const response = await fetch('/ai/action-request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action_type: 'tell_ai',
                    message: message
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.displayActionResults(data);
            } else {
                this.showActionError(data.message || 'Action failed');
            }
        } catch (error) {
            console.error('Tell AI error:', error);
            this.showActionError('Connection error. Please try again.');
        }
    }

    showActionLoading(actionType) {
        // Find the AI Action Center area
        const actionCenter = document.querySelector('.ai-action-center') || 
                            document.getElementById('ai-action-results') ||
                            document.querySelector('#ai-recommendations').parentNode;
        
        if (actionCenter) {
            const loadingHTML = `
                <div id="ai-action-loading" class="text-center py-4">
                    <div class="spinner-border text-success" role="status">
                        <span class="sr-only">Finding matches...</span>
                    </div>
                    <p class="mt-2">Searching for available players and courts...</p>
                </div>
            `;
            
            // Add loading section or replace existing results
            let resultsContainer = document.getElementById('ai-action-results');
            if (!resultsContainer) {
                resultsContainer = document.createElement('div');
                resultsContainer.id = 'ai-action-results';
                actionCenter.appendChild(resultsContainer);
            }
            resultsContainer.innerHTML = loadingHTML;
        }
    }

    displayActionResults(data) {
        const resultsContainer = document.getElementById('ai-action-results');
        if (!resultsContainer) return;
        
        if (!data.proposals || data.proposals.length === 0) {
            resultsContainer.innerHTML = `
                <div class="alert alert-warning">
                    <h6>No matches found</h6>
                    <p>No available players or courts for your criteria. Try different times or locations.</p>
                </div>
            `;
            return;
        }
        
        let resultsHTML = `
            <div class="ai-action-results">
                <h6><i class="fas fa-magic text-success"></i> Match Proposals Found</h6>
                <p class="text-muted">Found ${data.proposals.length} great options for ${data.parameters.date} at ${data.parameters.time}</p>
                <div class="proposals-grid">
        `;
        
        data.proposals.forEach((proposal, index) => {
            resultsHTML += `
                <div class="proposal-card border rounded p-3 mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${proposal.match_summary}</h6>
                            <div class="text-muted small">
                                <i class="fas fa-user"></i> ${proposal.player.name} (${proposal.player.compatibility} match)<br>
                                <i class="fas fa-map-marker-alt"></i> ${proposal.court.name} - ${proposal.court.surface}<br>
                                <i class="fas fa-clock"></i> ${proposal.date} at ${proposal.time}<br>
                                <i class="fas fa-money-bill"></i> $${proposal.total_cost} (${proposal.court.duration})
                            </div>
                        </div>
                        <div class="text-end">
                            <button class="btn btn-success btn-sm" 
                                    onclick="dashboardAI.executeProposal('${proposal.proposal_id}', ${JSON.stringify(proposal.booking_action).replace(/"/g, '&quot;')})">
                                <i class="fas fa-paper-plane"></i> Send Request
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });
        
        resultsHTML += '</div></div>';
        resultsContainer.innerHTML = resultsHTML;
    }

    async executeProposal(proposalId, bookingAction) {
        try {
            const response = await fetch('/ai/execute-proposal', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    proposal_id: proposalId,
                    booking_action: bookingAction
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Show success message
                const resultsContainer = document.getElementById('ai-action-results');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="alert alert-success">
                            <h6><i class="fas fa-check-circle"></i> Request Sent!</h6>
                            <p>${data.message}</p>
                            <ul class="mb-0">
                                ${data.next_steps.map(step => `<li>${step}</li>`).join('')}
                            </ul>
                        </div>
                    `;
                }
            } else {
                this.showActionError(data.message || 'Failed to send request');
            }
        } catch (error) {
            console.error('Execute proposal error:', error);
            this.showActionError('Connection error. Please try again.');
        }
    }

    showActionError(message) {
        const resultsContainer = document.getElementById('ai-action-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <h6><i class="fas fa-exclamation-triangle"></i> Action Failed</h6>
                    <p>${message}</p>
                </div>
            `;
        }
    }
}

// Make executeProposal available globally
window.dashboardAI = new DashboardAI();

// Initialize when DOM is ready
let dashboardAI;
document.addEventListener('DOMContentLoaded', () => {
    dashboardAI = new DashboardAI();
    
    // Add example suggestions that rotate on focus
    const examples = [
        "Find me a beginner partner in Tel Aviv for tomorrow evening",
        "Book a clay court for this weekend with a suitable partner", 
        "When am I free to play tennis this week?",
        "Complete match setup for Saturday morning"
    ];
    
    const input = document.getElementById('ai-action-input');
    if (input) {
        let exampleIndex = 0;
        input.addEventListener('focus', function() {
            if (!this.value) {
                this.placeholder = examples[exampleIndex % examples.length];
                exampleIndex++;
            }
        });
    }
});