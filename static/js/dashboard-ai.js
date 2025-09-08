/**
 * AI Features for Player Dashboard
 * Separate file to avoid conflicts with existing dashboard code
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
    }
    
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
                // Re-attach event listener for the new button
                document.getElementById('get-court-advice').addEventListener('click', () => {
                    this.loadCourtRecommendations();
                });
            } else {
                container.innerHTML = '<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> Court advisor unavailable at the moment</div>';
            }
        } catch (error) {
            console.error('Error loading court recommendations:', error);
            container.innerHTML = '<div class="alert alert-danger"><i class="fas fa-times-circle"></i> Error loading court advice. Please try again later.</div>';
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if we're on the player dashboard page
    if (document.getElementById('ai-recommendations') || document.getElementById('court-recommendations')) {
        new DashboardAI();
    }
});