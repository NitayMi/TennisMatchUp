/**
 * AI Features for Player Dashboard - Working Version
 */
class DashboardAI {
    constructor() {
        this.init();
    }
    
    init() {
        this.loadRecommendations();
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
        
        // Quick Action Buttons
        document.querySelectorAll('.quick-action').forEach(button => {
            button.addEventListener('click', (e) => {
                const action = e.target.dataset.action || e.target.closest('.quick-action').dataset.action;
                this.handleQuickAction(action);
            });
        });
        
        // Ask AI Button
        const askAIBtn = document.getElementById('ask-ai-btn');
        const aiInput = document.getElementById('ai-action-input');
        
        if (askAIBtn && aiInput) {
            askAIBtn.addEventListener('click', () => {
                if (aiInput.value.trim()) {
                    this.handleTellAI(aiInput.value.trim());
                    aiInput.value = '';
                }
            });
            
            aiInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && aiInput.value.trim()) {
                    this.handleTellAI(aiInput.value.trim());
                    aiInput.value = '';
                }
            });
        }
    }
    
    // ===== EXISTING ADVISORY FUNCTIONS =====
    
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
                    </div>
                `;
            } else {
                container.innerHTML = '<div class="alert alert-warning">Court recommendations unavailable</div>';
            }
        } catch (error) {
            console.error('Error loading court recommendations:', error);
            container.innerHTML = '<div class="alert alert-danger">Error loading court advice</div>';
        }
    }
    
    // ===== NEW ACTION FUNCTIONS =====
    
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
        const resultsContainer = document.getElementById('ai-action-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-success" role="status">
                        <span class="sr-only">Finding matches...</span>
                    </div>
                    <p class="mt-2">Searching for available players and courts...</p>
                </div>
            `;
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

// Initialize when DOM is ready
let dashboardAI;
document.addEventListener('DOMContentLoaded', () => {
    dashboardAI = new DashboardAI();
    
    // Add rotating placeholder examples
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

// Make executeProposal available globally for onclick handlers
window.dashboardAI = dashboardAI;