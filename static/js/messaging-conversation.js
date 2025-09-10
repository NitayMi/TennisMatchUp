// Professional Messaging Conversation System
class MessagingConversation {
    constructor() {
        this.otherUserId = this.extractUserIdFromUrl();
        this.messageForm = document.getElementById('messageForm');
        this.messageInput = document.getElementById('messageInput');
        this.messagesArea = document.getElementById('messagesArea');
        this.submitBtn = this.messageForm?.querySelector('button[type="submit"]');
        this.sending = false;
        this.lastMessageId = 0;
        
        this.init();
    }
    
    init() {
        if (!this.messageForm || !this.messageInput) return;
        
        // Set up form submission
        this.messageForm.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Auto-scroll and get initial last message ID
        this.scrollToBottom();
        this.setInitialLastMessageId();
        
        // Start polling for new messages
        this.startPolling();
    }
    
    extractUserIdFromUrl() {
        const pathParts = window.location.pathname.split('/');
        return parseInt(pathParts[pathParts.length - 1]);
    }
    
    setInitialLastMessageId() {
        const messages = this.messagesArea.querySelectorAll('[data-message-id]');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            this.lastMessageId = parseInt(lastMessage.getAttribute('data-message-id')) || 0;
        }
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        // Prevent double sending
        if (this.sending) return;
        
        const content = this.messageInput.value.trim();
        if (!content) return;
        
        this.sending = true;
        this.setLoadingState(true);
        
        try {
            const response = await fetch('/messaging/api/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    receiver_id: this.otherUserId,
                    content: content,
                    message_type: 'text'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear input immediately
                this.messageInput.value = '';
                
                // Add message to UI immediately for better UX
                this.addMessageToUI({
                    id: data.message_id,
                    content: content,
                    is_from_me: true,
                    time_display: 'Just now',
                    sender_name: 'You'
                });
                
                this.scrollToBottom();
                this.lastMessageId = data.message_id;
            } else {
                this.showError(data.error || 'Failed to send message');
            }
        } catch (error) {
            console.error('Send error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.sending = false;
            this.setLoadingState(false);
        }
    }
    
    setLoadingState(loading) {
        if (!this.submitBtn) return;
        
        if (loading) {
            this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            this.submitBtn.disabled = true;
        } else {
            this.submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.submitBtn.disabled = false;
        }
    }
    
    addMessageToUI(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-3 ${message.is_from_me ? 'text-end' : ''}`;
        messageDiv.setAttribute('data-message-id', message.id);
        
        const bubbleClass = message.is_from_me ? 'bg-primary text-white' : 'bg-light';
        const timeClass = message.is_from_me ? 'text-light' : 'text-muted';
        
        messageDiv.innerHTML = `
            <div class="d-inline-block p-2 rounded ${bubbleClass}" style="max-width: 70%;">
                ${this.escapeHtml(message.content)}
                <br><small class="${timeClass}">
                    ${message.time_display}
                </small>
            </div>
        `;
        
        this.messagesArea.appendChild(messageDiv);
    }
    
    scrollToBottom() {
        if (this.messagesArea) {
            this.messagesArea.scrollTop = this.messagesArea.scrollHeight;
        }
    }
    
    startPolling() {
        // Poll every 3 seconds for new messages
        setInterval(() => {
            this.checkForNewMessages();
        }, 3000);
    }
    
    async checkForNewMessages() {
        if (this.sending) return; // Don't poll while sending
        
        try {
            const response = await fetch(`/messaging/api/conversation/${this.otherUserId}/messages?since_id=${this.lastMessageId}`);
            const data = await response.json();
            
            if (data.success && data.messages.length > 0) {
                data.messages.forEach(message => {
                    if (message.id > this.lastMessageId && !message.is_from_me) {
                        this.addMessageToUI(message);
                        this.lastMessageId = message.id;
                    }
                });
                this.scrollToBottom();
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }
    
    showError(message) {
        // Create a temporary error message
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        errorDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; max-width: 300px;';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(errorDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new MessagingConversation();
});