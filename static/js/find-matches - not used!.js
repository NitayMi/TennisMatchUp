// static/js/matching.js - PROFESSIONAL UI INTERACTIONS ENHANCEMENT

document.addEventListener('DOMContentLoaded', function() {
    
    // ========== Message Modal Handler ==========
    const messageModal = document.getElementById('messageModal');
    const modalPlayerName = document.getElementById('modal-player-name');
    const modalPlayerId = document.getElementById('modal-player-id');
    
    if (messageModal) {
        // Handle message button clicks
        document.addEventListener('click', function(e) {
            if (e.target.matches('[data-bs-target="#messageModal"]') || 
                e.target.closest('[data-bs-target="#messageModal"]')) {
                
                const button = e.target.closest('[data-bs-target="#messageModal"]');
                const playerId = button.getAttribute('data-player-id');
                const playerName = button.getAttribute('data-player-name');
                
                if (modalPlayerName && modalPlayerId) {
                    modalPlayerName.textContent = playerName;
                    modalPlayerId.value = playerId;
                }
            }
        });
    }
    
    // ========== Search Form Enhancement ==========
    const searchForm = document.getElementById('match-search-form');
    if (searchForm) {
        // Add loading state during search
        searchForm.addEventListener('submit', function() {
            const submitButton = this.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Searching...';
                submitButton.disabled = true;
            }
        });
    }
    
    // ========== Card Animations ==========
    const playerCards = document.querySelectorAll('.player-match-card');
    
    // Add staggered animation for cards on load
    playerCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // ========== Enhanced Button Interactions ==========
    const primaryButtons = document.querySelectorAll('.btn-primary-action');
    
    primaryButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // ========== Match Quality Bar Animation ==========
    const qualityBars = document.querySelectorAll('.quality-fill');
    
    // Animate quality bars on scroll into view
    const animateQualityBars = () => {
        qualityBars.forEach(bar => {
            const rect = bar.getBoundingClientRect();
            if (rect.top < window.innerHeight && rect.bottom > 0) {
                const width = bar.style.width;
                bar.style.width = '0%';
                setTimeout(() => {
                    bar.style.width = width;
                }, 100);
            }
        });
    };
    
    // Trigger animation on load and scroll
    setTimeout(animateQualityBars, 500);
    window.addEventListener('scroll', animateQualityBars);
    
    // ========== Filter Persistence ==========
    // Save filter state to localStorage for better UX
    const filterInputs = searchForm?.querySelectorAll('select, input');
    
    filterInputs?.forEach(input => {
        // Load saved values
        const savedValue = localStorage.getItem(`filter_${input.name}`);
        if (savedValue && !input.value) {
            input.value = savedValue;
        }
        
        // Save on change
        input.addEventListener('change', function() {
            localStorage.setItem(`filter_${this.name}`, this.value);
        });
    });
    
    // ========== Responsive Card Layout ==========
    const adjustCardLayout = () => {
        const container = document.querySelector('#match-results .row');
        if (!container) return;
        
        const cards = container.querySelectorAll('.player-match-card');
        const containerWidth = container.offsetWidth;
        
        // Adjust column classes based on screen size and number of cards
        if (window.innerWidth >= 1200 && cards.length >= 3) {
            cards.forEach(card => {
                const col = card.closest('[class*="col-"]');
                if (col) {
                    col.className = 'col-lg-6 col-xl-4 mb-4';
                }
            });
        } else if (window.innerWidth >= 768) {
            cards.forEach(card => {
                const col = card.closest('[class*="col-"]');
                if (col) {
                    col.className = 'col-md-6 mb-4';
                }
            });
        }
    };
    
    // Adjust layout on load and resize
    adjustCardLayout();
    window.addEventListener('resize', adjustCardLayout);
    
    // ========== Accessibility Enhancements ==========
    
    // Add keyboard navigation for cards
    playerCards.forEach(card => {
        card.setAttribute('tabindex', '0');
        
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const primaryButton = this.querySelector('.btn-primary-action');
                if (primaryButton) {
                    primaryButton.click();
                }
            }
        });
    });
    
    // ========== Performance Optimization ==========
    
    // Lazy load card interactions
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '50px'
    };
    
    const cardObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const card = entry.target;
                card.classList.add('visible');
                cardObserver.unobserve(card);
            }
        });
    }, observerOptions);
    
    playerCards.forEach(card => {
        cardObserver.observe(card);
    });
    
    // ========== Error Handling ==========
    
    // Handle form submission errors gracefully
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Form submission error:', e.reason);
        
        // Reset any loading buttons
        const loadingButtons = document.querySelectorAll('button[disabled]');
        loadingButtons.forEach(button => {
            button.disabled = false;
            button.innerHTML = button.innerHTML.replace(/fa-spinner fa-spin/, 'fa-search');
        });
    });
    
    // ========== Analytics Tracking (Optional) ==========
    
    // Track user interactions for UX improvement
    const trackInteraction = (action, element) => {
        // Only log to console in development
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            console.log(`User interaction: ${action}`, element);
        }
        
        // In production, this would send to analytics service
        // analytics.track(action, { element: element.className });
    };
    
    // Track button clicks
    document.addEventListener('click', function(e) {
        if (e.target.matches('.btn-primary-action')) {
            trackInteraction('suggest_court_clicked', e.target);
        } else if (e.target.matches('.btn-secondary-action')) {
            trackInteraction('send_message_clicked', e.target);
        }
    });
    
    // Track search form usage
    if (searchForm) {
        searchForm.addEventListener('submit', function() {
            trackInteraction('search_performed', this);
        });
    }
    
});