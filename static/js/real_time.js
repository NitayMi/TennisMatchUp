/**
 * Live Messaging System for TennisMatchUp
 * Real-time chat with polling, typing indicators, and read receipts
 */
class LiveMessaging {
    constructor() {
        this.conversationId = null;
        this.otherUserId = null;
        this.currentUserId = null;
        this.lastMessageId = 0;
        this.pollingInterval = null;
        this.typingTimeout = null;
        this.isTyping = false;
        this.pageVisible = true;
        
        this.init();
    }
    
    init() {
        // Get conversation data from page
        this.extractConversationData();
        
        if (this.otherUserId) {
            this.setupEventListeners();
            this.startPolling();
            this.setupVisibilityDetection();
            this.markConversationAsRead();
        }
    }
    
    extractConversationData() {
        // Extract data from URL or page elements
        const path = window.location.pathname;
        const match = path.match(/\/messaging\/conversation\/(\d+)/);
        
        if (match) {
            this.otherUserId = parseInt(match[1]);
        }
        
        // Get current user ID from session or meta tag
        const userMeta = document.querySelector('meta[name="current-user-id"]');
        if (userMeta) {
            this.currentUserId = parseInt(userMeta.getAttribute('content'));
        }
        
        // Get last message ID for polling
        const messages = document.querySelectorAll('.message[data-message-id]');
        if (messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            this.lastMessageId = parseInt(lastMessage.getAttribute('data-message-id')) || 0;
        }
    }
    
    setupEventListeners() {
        const messageForm = document.getElementById('messageForm');
        const messageInput = document.getElementById('messageInput');
        
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }
        
        if (messageInput) {
            // Typing indicator
            messageInput.addEventListener('input', () => {
                this.handleTyping();
            });
            
            messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });
        }
        
        // Mark as read when scrolling to bottom
        const messagesArea = document.getElementById('messagesArea');
        if (messagesArea) {
            messagesArea.addEventListener('scroll', () => {
                if (this.isScrolledToBottom(messagesArea)) {
                    this.markConversationAsRead();
                }
            });
        }
    }
    
    setupVisibilityDetection() {
        document.addEventListener('visibilitychange', () => {
            this.pageVisible = !document.hidden;
            if (this.pageVisible) {
                this.markConversationAsRead();
                this.startPolling();
            } else {
                this.stopPolling();
            }
        });
        
        window.addEventListener('focus', () => {
            this.pageVisible = true;
            this.markConversationAsRead();
            this.startPolling();
        });
        
        window.addEventListener('blur', () => {
            this.pageVisible = false;
        });
    }
    
    startPolling() {
        if (this.pollingInterval) return;
        
        // Poll every 3 seconds for new messages
        this.pollingInterval = setInterval(() => {
            this.checkForNewMessages();
        }, 3000);
        
        // Check immediately
        this.checkForNewMessages();
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }
    
    async checkForNewMessages() {
        if (!this.otherUserId) return;
        
        try {
            const response = await fetch(`/api/messages/conversation/${this.otherUserId}?since=${this.lastMessageId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) throw new Error('Failed to fetch messages');
            
            const data = await response.json();
            
            if (data.success && data.messages && data.messages.length > 0) {
                data.messages.forEach(message => {
                    this.addMessageToUI(message);
                    this.lastMessageId = Math.max(this.lastMessageId, message.id);
                });
                
                // Auto-scroll if user is at bottom
                const messagesArea = document.getElementById('messagesArea');
                if (messagesArea && this.isScrolledToBottom(messagesArea, 100)) {
                    this.scrollToBottom();
                }
                
                // Mark as read if page is visible
                if (this.pageVisible) {
                    this.markConversationAsRead();
                }
                
                // Show browser notification if page not visible
                if (!this.pageVisible && 'Notification' in window) {
                    this.showNotification(data.messages[data.messages.length - 1]);
                }
            }
            
            // Update typing indicator
            if (data.typing_info) {
                this.updateTypingIndicator(data.typing_info);
            }
            
        } catch (error) {
            console.error('Error checking for new messages:', error);
        }
    }
    
    async sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const content = messageInput.value.trim();
        
        if (!content || !this.otherUserId) return;
        
        // Disable input while sending
        messageInput.disabled = true;
        
        try {
            const response = await fetch('/api/messages/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    receiver_id: this.otherUserId,
                    content: content
                })
            });
            
            if (!response.ok) throw new Error('Failed to send message');
            
            const data = await response.json();
            
            if (data.success) {
                // Clear input
                messageInput.value = '';
                
                // Add message to UI immediately
                this.addMessageToUI(data.message, true);
                this.lastMessageId = Math.max(this.lastMessageId, data.message.id);
                
                // Scroll to bottom
                this.scrollToBottom();
                
                // Clear typing indicator
                this.clearTyping();
                
            } else {
                throw new Error(data.error || 'Failed to send message');
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message. Please try again.');
        } finally {
            messageInput.disabled = false;
            messageInput.focus();
        }
    }
    
    addMessageToUI(message, isFromCurrentUser = null) {
        const messagesArea = document.getElementById('messagesArea');
        if (!messagesArea) return;
        
        // Determine if message is from current user
        if (isFromCurrentUser === null) {
            isFromCurrentUser = message.sender_id === this.currentUserId;
        }
        
        // Check if message already exists
        if (document.querySelector(`[data-message-id="${message.id}"]`)) {
            return;
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-3 ${isFromCurrentUser ? 'text-end' : ''}`;
        messageDiv.setAttribute('data-message-id', message.id);
        
        const bubbleClass = isFromCurrentUser ? 'bg-primary text-white' : 'bg-light';
        const timeClass = isFromCurrentUser ? 'text-light' : 'text-muted';
        
        messageDiv.innerHTML = `
            <div class="d-inline-block p-2 rounded ${bubbleClass}" style="max-width: 70%;">
                ${this.escapeHtml(message.content)}
                <br><small class="${timeClass}">
                    ${this.formatTime(message.created_at)}
                    ${isFromCurrentUser ? this.getReadStatus(message) : ''}
                </small>
            </div>
        `;
        
        messagesArea.appendChild(messageDiv);
    }
    
    getReadStatus(message) {
        // Show read receipts for sent messages
        if (message.is_read) {
            return '<i class="fas fa-check-double text-info" title="Read"></i>';
        } else {
            return '<i class="fas fa-check" title="Sent"></i>';
        }
    }
    
    handleTyping() {
        if (!this.isTyping) {
            this.isTyping = true;
            this.sendTypingIndicator(true);
        }
        
        // Clear existing timeout
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
        }
        
        // Set new timeout
        this.typingTimeout = setTimeout(() => {
            this.clearTyping();
        }, 2000);
    }
    
    clearTyping() {
        if (this.isTyping) {
            this.isTyping = false;
            this.sendTypingIndicator(false);
        }
        
        if (this.typingTimeout) {
            clearTimeout(this.typingTimeout);
            this.typingTimeout = null;
        }
    }
    
    async sendTypingIndicator(isTyping) {
        try {
            await fetch('/api/messages/typing', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    receiver_id: this.otherUserId,
                    is_typing: isTyping
                })
            });
        } catch (error) {
            console.error('Error sending typing indicator:', error);
        }
    }
    
    updateTypingIndicator(typingInfo) {
        let indicator = document.getElementById('typing-indicator');
        
        if (typingInfo.is_typing && typingInfo.user_id !== this.currentUserId) {
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'typing-indicator';
                indicator.className = 'text-muted small mb-2';
                indicator.innerHTML = '<i class="fas fa-ellipsis-h"></i> Typing...';
                
                const messagesArea = document.getElementById('messagesArea');
                if (messagesArea) {
                    messagesArea.appendChild(indicator);
                    this.scrollToBottom();
                }
            }
        } else {
            if (indicator) {
                indicator.remove();
            }
        }
    }
    
    async markConversationAsRead() {
        if (!this.otherUserId) return;
        
        try {
            await fetch(`/api/messages/mark-read/${this.otherUserId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
        } catch (error) {
            console.error('Error marking conversation as read:', error);
        }
    }
    
    scrollToBottom() {
        const messagesArea = document.getElementById('messagesArea');
        if (messagesArea) {
            messagesArea.scrollTop = messagesArea.scrollHeight;
        }
    }
    
    isScrolledToBottom(element, threshold = 50) {
        return element.scrollHeight - element.clientHeight <= element.scrollTop + threshold;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showNotification(message) {
        if (Notification.permission === 'granted') {
            new Notification('New message', {
                body: message.content,
                icon: '/static/images/logo.png'
            });
        }
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        errorDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 350px;';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
    
    // Clean up when leaving page
    destroy() {
        this.stopPolling();
        this.clearTyping();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize on conversation pages
    if (window.location.pathname.includes('/messaging/conversation/')) {
        window.liveMessaging = new LiveMessaging();
        
        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
});

// Clean up when leaving page
window.addEventListener('beforeunload', () => {
    if (window.liveMessaging) {
        window.liveMessaging.destroy();
    }
});