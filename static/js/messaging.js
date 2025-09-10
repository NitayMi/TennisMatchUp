/**
 * TennisMatchUp Messaging JavaScript
 * WhatsApp-like functionality with real-time features
 */

class MessagingApp {
    constructor() {
        this.currentConversationId = null;
        this.lastMessageId = null;
        this.pollInterval = null;
        this.typingTimer = null;
        this.unreadCount = 0;
        
        // Configuration
        this.config = {
            pollIntervalMs: 5000,      // Check for new messages every 5 seconds
            typingTimeoutMs: 3000,     // Stop typing indicator after 3 seconds
            messageRetryAttempts: 3,   // Retry failed messages 3 times
            animationDuration: 300     // Animation duration in ms
        };
        
        this.init();
    }
    
    init() {
        console.log('🎾 TennisMatchUp Messaging App initialized');
        this.bindEvents();
        this.updateUnreadCount();
        
        // Start real-time updates if we're in a conversation
        if (this.isConversationPage()) {
            this.startConversationPolling();
        }
    }
    
    bindEvents() {
        // Message sending
        const messageForm = document.getElementById('messageForm');
        if (messageForm) {
            messageForm.addEventListener('submit', (e) => this.handleSendMessage(e));
        }
        
        // Real-time message input
        const messageInput = document.getElementById('messageInput');
        if (messageInput) {
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage(e);
                }
            });
            
            messageInput.addEventListener('input', () => this.handleTyping());
        }
        
        // Mark as read when scrolling
        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            messagesContainer.addEventListener('scroll', () => this.markVisibleMessagesAsRead());
        }
        
        // Auto-resize textarea
        this.setupAutoResizeTextarea();
        
        // Page visibility for pausing/resuming polling
        document.addEventListener('visibilitychange', () => this.handleVisibilityChange());
    }
    
    // ========================= MESSAGE SENDING =========================
    
    async handleSendMessage(event) {
        event.preventDefault();
        
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        if (!messageInput || !sendButton) return;
        
        const content = messageInput.value.trim();
        if (!content) return;
        
        // Disable input and button
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        const receiverId = this.getCurrentReceiverId();
        if (!receiverId) {
            this.showError('Receiver not found');
            this.enableMessageInput();
            return;
        }
        
        try {
            // Add optimistic message to UI
            const tempMessageId = this.addOptimisticMessage(content);
            
            // Send message via API
            const response = await fetch('/messaging/api/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    receiver_id: receiverId,
                    content: content,
                    message_type: 'text'
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Replace optimistic message with real one
                this.replaceOptimisticMessage(tempMessageId, result.message_id);
                
                // Clear input
                messageInput.value = '';
                this.adjustTextareaHeight(messageInput);
                
                // Scroll to bottom
                this.scrollToBottom();
                
                // Update last message ID for polling
                this.lastMessageId = result.message_id;
                
            } else {
                this.removeOptimisticMessage(tempMessageId);
                this.showError(result.error || 'Failed to send message');
            }
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Network error. Please check your connection.');
        } finally {
            this.enableMessageInput();
        }
    }
    
    addOptimisticMessage(content) {
        const tempId = 'temp_' + Date.now();
        const messagesContainer = document.querySelector('.messages-container');
        
        if (!messagesContainer) return tempId;
        
        const messageHtml = `
            <div class="message-group fade-in" data-temp-id="${tempId}">
                <div class="message-bubble message-from-me">
                    <div class="message-content">${this.escapeHtml(content)}</div>
                    <div class="message-meta">
                        <span class="message-time">Sending...</span>
                        <div class="message-status">
                            <i class="fas fa-clock text-warning"></i>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
        this.scrollToBottom();
        
        return tempId;
    }
    
    replaceOptimisticMessage(tempId, realMessageId) {
        const tempElement = document.querySelector(`[data-temp-id="${tempId}"]`);
        if (tempElement) {
            tempElement.setAttribute('data-message-id', realMessageId);
            tempElement.removeAttribute('data-temp-id');
            
            // Update status to sent
            const statusIcon = tempElement.querySelector('.message-status i');
            if (statusIcon) {
                statusIcon.className = 'fas fa-check text-success';
            }
            
            const timeElement = tempElement.querySelector('.message-time');
            if (timeElement) {
                timeElement.textContent = 'Just now';
            }
        }
    }
    
    removeOptimisticMessage(tempId) {
        const tempElement = document.querySelector(`[data-temp-id="${tempId}"]`);
        if (tempElement) {
            tempElement.remove();
        }
    }
    
    // ========================= REAL-TIME UPDATES =========================
    
    startConversationPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
        }
        
        // Poll for new messages
        this.pollInterval = setInterval(() => {
            this.checkForNewMessages();
        }, this.config.pollIntervalMs);
        
        console.log('Started conversation polling');
    }
    
    stopConversationPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
            console.log('Stopped conversation polling');
        }
    }
    
    async checkForNewMessages() {
        if (!this.isConversationPage()) return;
        
        const otherUserId = this.getCurrentReceiverId();
        if (!otherUserId) return;
        
        try {
            const url = `/messaging/api/conversation/${otherUserId}/messages` + 
                       (this.lastMessageId ? `?since_id=${this.lastMessageId}` : '');
            
            const response = await fetch(url);
            const result = await response.json();
            
            if (result.success && result.messages.length > 0) {
                this.addNewMessages(result.messages);
                
                // Update last message ID
                const lastMsg = result.messages[result.messages.length - 1];
                this.lastMessageId = lastMsg.id;
                
                // Mark as read if page is visible
                if (!document.hidden) {
                    this.markConversationAsRead(otherUserId);
                }
            }
            
        } catch (error) {
            console.error('Error checking for new messages:', error);
        }
    }
    
    addNewMessages(messages) {
        const messagesContainer = document.querySelector('.messages-container');
        if (!messagesContainer) return;
        
        const currentUserId = this.getCurrentUserId();
        
        messages.forEach(message => {
            // Check if message already exists
            if (document.querySelector(`[data-message-id="${message.id}"]`)) {
                return;
            }
            
            const isFromMe = message.sender_id === currentUserId;
            const messageClass = isFromMe ? 'message-from-me' : 'message-from-other';
            const bubbleClass = this.getMessageBubbleClass(message.message_type);
            
            const messageHtml = `
                <div class="message-group fade-in" data-message-id="${message.id}">
                    <div class="message-bubble ${messageClass} ${bubbleClass}">
                        ${this.getMessageTypeIndicator(message.message_type)}
                        <div class="message-content">${this.escapeHtml(message.content)}</div>
                        <div class="message-meta">
                            <span class="message-time">${message.time_display}</span>
                            ${isFromMe ? this.getMessageStatusIcon(message) : ''}
                        </div>
                    </div>
                </div>
            `;
            
            messagesContainer.insertAdjacentHTML('beforeend', messageHtml);
        });
        
        this.scrollToBottom();
        
        // Play notification sound if messages are from others
        const hasNewFromOthers = messages.some(msg => msg.sender_id !== this.getCurrentUserId());
        if (hasNewFromOthers) {
            this.playNotificationSound();
        }
    }
    
    // ========================= CONVERSATION MANAGEMENT =========================
    
    async refreshConversations() {
        const conversationsList = document.querySelector('.conversations-list');
        if (!conversationsList) return;
        
        try {
            const response = await fetch('/messaging/api/conversations');
            const result = await response.json();
            
            if (result.success) {
                this.updateConversationsList(result.conversations);
                this.updateUnreadCount();
            }
            
        } catch (error) {
            console.error('Error refreshing conversations:', error);
        }
    }
    
    updateConversationsList(conversations) {
        const conversationsList = document.querySelector('.conversations-list');
        if (!conversationsList) return;
        
        // Store current scroll position
        const scrollTop = conversationsList.scrollTop;
        
        // Update HTML (this would require generating the HTML from JS)
        // For now, we'll just update unread indicators
        conversations.forEach(conv => {
            const convElement = document.querySelector(`[data-user-id="${conv.other_user_id}"]`);
            if (convElement) {
                this.updateConversationElement(convElement, conv);
            }
        });
        
        // Restore scroll position
        conversationsList.scrollTop = scrollTop;
    }
    
    updateConversationElement(element, conversation) {
        // Update unread count
        const unreadElement = element.querySelector('.unread-count');
        if (conversation.unread_count > 0) {
            if (unreadElement) {
                unreadElement.textContent = conversation.unread_count;
            }
            element.classList.add('unread');
        } else {
            if (unreadElement) {
                unreadElement.style.display = 'none';
            }
            element.classList.remove('unread');
        }
        
        // Update last message
        const messageContent = element.querySelector('.message-content');
        if (messageContent && conversation.last_message) {
            messageContent.textContent = conversation.last_message.content;
        }
        
        // Update time
        const timeElement = element.querySelector('.conversation-time');
        if (timeElement && conversation.last_message) {
            timeElement.textContent = conversation.last_message.time_display;
        }
    }
    
    async markConversationAsRead(otherUserId) {
        try {
            const response = await fetch(`/messaging/mark_read/${otherUserId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Update UI to show messages as read
                this.updateMessagesReadStatus();
                this.updateUnreadCount();
            }
            
        } catch (error) {
            console.error('Error marking conversation as read:', error);
        }
    }
    
    // ========================= UTILITY FUNCTIONS =========================
    
    isConversationPage() {
        return window.location.pathname.includes('/messaging/conversation/');
    }
    
    getCurrentReceiverId() {
        // Extract receiver ID from URL path
        const match = window.location.pathname.match(/\/messaging\/conversation\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }
    
    getCurrentUserId() {
        // This should be set by the backend in a script tag or data attribute
        const userIdElement = document.querySelector('[data-current-user-id]');
        return userIdElement ? parseInt(userIdElement.dataset.currentUserId) : null;
    }
    
    enableMessageInput() {
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        
        if (messageInput) messageInput.disabled = false;
        if (sendButton) sendButton.disabled = false;
    }
    
    scrollToBottom() {
        const messagesContainer = document.querySelector('.messages-container');
        if (messagesContainer) {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    setupAutoResizeTextarea() {
        const messageInput = document.getElementById('messageInput');
        if (!messageInput) return;
        
        messageInput.addEventListener('input', () => {
            this.adjustTextareaHeight(messageInput);
        });
    }
    
    adjustTextareaHeight(textarea) {
        textarea.style.height = 'auto';
        const maxHeight = 100; // Max height in pixels
        const newHeight = Math.min(textarea.scrollHeight, maxHeight);
        textarea.style.height = newHeight + 'px';
    }
    
    handleTyping() {
        // Clear existing typing timer
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }
        
        // Set new timer to stop typing indicator
        this.typingTimer = setTimeout(() => {
            this.stopTypingIndicator();
        }, this.config.typingTimeoutMs);
        
        // Send typing indicator (could be implemented with WebSocket)
        this.sendTypingIndicator();
    }
    
    sendTypingIndicator() {
        // Placeholder for typing indicator functionality
        // Could send to /messaging/api/typing endpoint
    }
    
    stopTypingIndicator() {
        // Placeholder for stopping typing indicator
    }
    
    handleVisibilityChange() {
        if (document.hidden) {
            // Page is hidden, reduce polling frequency or stop
            this.stopConversationPolling();
        } else {
            // Page is visible, resume normal polling
            if (this.isConversationPage()) {
                this.startConversationPolling();
                
                // Mark conversation as read when user returns
                const otherUserId = this.getCurrentReceiverId();
                if (otherUserId) {
                    this.markConversationAsRead(otherUserId);
                }
            }
        }
    }
    
    markVisibleMessagesAsRead() {
        // Mark messages as read when they become visible
        // This could be enhanced with Intersection Observer API
        const otherUserId = this.getCurrentReceiverId();
        if (otherUserId && !document.hidden) {
            this.markConversationAsRead(otherUserId);
        }
    }
    
    updateMessagesReadStatus() {
        // Update UI to show messages as read
        const unreadMessages = document.querySelectorAll('.message-from-other:not(.read)');
        unreadMessages.forEach(message => {
            message.classList.add('read');
        });
    }
    
    async updateUnreadCount() {
        try {
            const response = await fetch('/messaging/api/unread_count');
            const result = await response.json();
            
            if (result.success) {
                this.unreadCount = result.unread_count;
                this.updateUnreadCountUI(result.unread_count);
            }
            
        } catch (error) {
            console.error('Error updating unread count:', error);
        }
    }
    
    updateUnreadCountUI(count) {
        // Update navigation badge
        const navBadge = document.querySelector('.nav-unread-badge');
        if (navBadge) {
            if (count > 0) {
                navBadge.textContent = count;
                navBadge.style.display = 'inline';
            } else {
                navBadge.style.display = 'none';
            }
        }
        
        // Update page title
        if (count > 0) {
            document.title = `(${count}) Messages - TennisMatchUp`;
        } else {
            document.title = 'Messages - TennisMatchUp';
        }
    }
    
    getMessageBubbleClass(messageType) {
        switch (messageType) {
            case 'match_request':
                return 'message-match-request';
            case 'booking_notification':
                return 'message-booking-notification';
            case 'system':
                return 'message-system';
            default:
                return '';
        }
    }
    
    getMessageTypeIndicator(messageType) {
        switch (messageType) {
            case 'match_request':
                return '<i class="fas fa-tennis-ball message-type-badge"></i>';
            case 'booking_notification':
                return '<i class="fas fa-calendar message-type-badge"></i>';
            case 'system':
                return '<i class="fas fa-info-circle message-type-badge"></i>';
            default:
                return '';
        }
    }
    
    getMessageStatusIcon(message) {
        if (message.is_read) {
            return '<div class="message-status read"><i class="fas fa-check-double"></i></div>';
        } else {
            return '<div class="message-status"><i class="fas fa-check"></i></div>';
        }
    }
    
    playNotificationSound() {
        // Play subtle notification sound
        try {
            const audio = new Audio('/static/sounds/notification.mp3');
            audio.volume = 0.3;
            audio.play().catch(e => {
                // Ignore autoplay policy errors
                console.log('Audio autoplay prevented');
            });
        } catch (error) {
            // Ignore audio errors
        }
    }
    
    showError(message) {
        // Show error message to user
        const errorContainer = document.getElementById('errorContainer');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    ${this.escapeHtml(message)}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        } else {
            // Fallback to console
            console.error('Messaging error:', message);
        }
    }
    
    showSuccess(message) {
        // Show success message to user
        const successContainer = document.getElementById('successContainer');
        if (successContainer) {
            successContainer.innerHTML = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    ${this.escapeHtml(message)}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }
    
    // ========================= MATCH REQUEST FUNCTIONALITY =========================
    
    showMatchRequestModal(otherUserId) {
        const modal = new bootstrap.Modal(document.getElementById('matchRequestModal'));
        
        // Set recipient ID in modal
        const recipientInput = document.getElementById('matchRequestRecipient');
        if (recipientInput) {
            recipientInput.value = otherUserId;
        }
        
        modal.show();
    }
    
    async sendMatchRequest(otherUserId, customMessage = '') {
        try {
            const response = await fetch('/messaging/send_match_request', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    receiver_id: otherUserId,
                    custom_message: customMessage
                })
            });
            
            if (response.ok) {
                this.showSuccess('Match request sent successfully!');
                // Refresh conversation if we're in one
                if (this.isConversationPage()) {
                    setTimeout(() => {
                        this.checkForNewMessages();
                    }, 1000);
                }
            } else {
                this.showError('Failed to send match request');
            }
            
        } catch (error) {
            console.error('Error sending match request:', error);
            this.showError('Network error while sending match request');
        }
    }
    
    // ========================= CLEANUP =========================
    
    destroy() {
        // Clean up intervals and event listeners
        this.stopConversationPolling();
        
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }
        
        console.log('MessagingApp destroyed');
    }
}

// Global instance
let MessagingAppInstance = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    MessagingAppInstance = new MessagingApp();
});

// Clean up on page unload
window.addEventListener('beforeunload', function() {
    if (MessagingAppInstance) {
        MessagingAppInstance.destroy();
    }
});

// Export for global access
window.MessagingApp = {
    init: () => {
        if (!MessagingAppInstance) {
            MessagingAppInstance = new MessagingApp();
        }
    },
    refreshConversations: () => {
        if (MessagingAppInstance) {
            MessagingAppInstance.refreshConversations();
        }
    },
    showMatchRequestModal: (otherUserId) => {
        if (MessagingAppInstance) {
            MessagingAppInstance.showMatchRequestModal(otherUserId);
        }
    },
    sendMatchRequest: (otherUserId, customMessage) => {
        if (MessagingAppInstance) {
            return MessagingAppInstance.sendMatchRequest(otherUserId, customMessage);
        }
    }
};