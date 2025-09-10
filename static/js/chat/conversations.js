/**
 * Chat Conversations Management
 * Handles conversation list, creation, real-time updates
 */
class ChatConversations {
    constructor() {
        this.socket = null;
        this.unreadCounts = {};
        this.init();
    }
    
    init() {
        console.log('🎾 Chat Conversations initialized');
        this.loadAvailableUsers();
        this.bindEvents();
        this.initializeSocket();
        this.startUnreadCountUpdates();
    }
    
    bindEvents() {
        // Handle conversation clicks
        document.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const conversationId = item.dataset.conversationId;
                this.selectConversation(conversationId);
            });
        });
        
        // New conversation form
        const form = document.getElementById('newConversationForm');
        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createConversation();
            });
        }
    }
    
    async loadAvailableUsers() {
        try {
            const response = await fetch('/api/users/available-for-chat');
            const data = await response.json();
            
            if (data.success) {
                this.populateUserSelect(data.users);
            }
        } catch (error) {
            console.error('Error loading available users:', error);
            // Fallback: populate with dummy data for development
            this.populateUserSelect([
                { id: 1, name: 'Demo Player', user_type: 'player' },
                { id: 2, name: 'Demo Owner', user_type: 'owner' }
            ]);
        }
    }
    
    populateUserSelect(users) {
        const select = document.querySelector('select[name="recipient_id"]');
        if (!select) return;
        
        // Clear existing options except first
        select.innerHTML = '<option value="">Choose a user...</option>';
        
        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.name} (${user.user_type})`;
            select.appendChild(option);
        });
    }
    
    async createConversation() {
        const form = document.getElementById('newConversationForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/chat/api/create-conversation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    recipient_id: parseInt(formData.get('recipient_id')),
                    first_message: formData.get('first_message')
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Close modal and redirect to conversation
                const modal = bootstrap.Modal.getInstance(document.getElementById('newConversationModal'));
                modal.hide();
                
                window.location.href = `/chat/conversation/${result.conversation_id}`;
            } else {
                this.showError(result.error || 'Failed to create conversation');
            }
        } catch (error) {
            console.error('Error creating conversation:', error);
            this.showError('Network error occurred');
        }
    }
    
    initializeSocket() {
        if (typeof io === 'undefined') {
            console.log('Socket.IO not available - using polling fallback');
            return;
        }
        
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to chat socket');
        });
        
        this.socket.on('conversation_updated', (data) => {
            this.updateConversationInList(data);
        });
        
        this.socket.on('new_message_notification', (data) => {
            this.handleNewMessageNotification(data);
        });
    }
    
    updateConversationInList(conversationData) {
        const conversationElement = document.querySelector(`[data-conversation-id="${conversationData.id}"]`);
        if (conversationElement) {
            // Update last message
            const lastMessageElement = conversationElement.querySelector('.last-message');
            if (lastMessageElement && conversationData.last_message) {
                lastMessageElement.textContent = conversationData.last_message.content;
            }
            
            // Update unread count
            this.updateUnreadCount(conversationData.id, conversationData.unread_count);
            
            // Move to top of list
            const conversationsList = document.querySelector('.conversations-list');
            conversationsList.insertBefore(conversationElement, conversationsList.firstChild);
        }
    }
    
    updateUnreadCount(conversationId, count) {
        const conversationElement = document.querySelector(`[data-conversation-id="${conversationId}"]`);
        if (!conversationElement) return;
        
        const unreadBadge = conversationElement.querySelector('.unread-count');
        const conversationItem = conversationElement.closest('.conversation-item');
        
        if (count > 0) {
            conversationItem.classList.add('unread');
            if (unreadBadge) {
                unreadBadge.textContent = count;
            } else {
                // Create badge
                const badge = document.createElement('span');
                badge.className = 'badge bg-primary unread-count';
                badge.textContent = count;
                conversationElement.querySelector('.d-flex.justify-content-between').appendChild(badge);
            }
        } else {
            conversationItem.classList.remove('unread');
            if (unreadBadge) {
                unreadBadge.remove();
            }
        }
        
        this.unreadCounts[conversationId] = count;
        this.updateTotalUnreadCount();
    }
    
    updateTotalUnreadCount() {
        const total = Object.values(this.unreadCounts).reduce((sum, count) => sum + count, 0);
        
        // Update page title
        if (total > 0) {
            document.title = `(${total}) Messages - TennisMatchUp`;
        } else {
            document.title = 'Messages - TennisMatchUp';
        }
        
        // Update navigation badge
        const navBadge = document.querySelector('.nav-messages-badge');
        if (navBadge) {
            if (total > 0) {
                navBadge.textContent = total;
                navBadge.style.display = 'inline';
            } else {
                navBadge.style.display = 'none';
            }
        }
    }
    
    async startUnreadCountUpdates() {
        // Poll for unread counts every 30 seconds
        setInterval(async () => {
            try {
                const response = await fetch('/chat/api/unread-counts');
                const data = await response.json();
                
                if (data.success) {
                    Object.entries(data.unread_counts).forEach(([conversationId, count]) => {
                        this.updateUnreadCount(parseInt(conversationId), count);
                    });
                }
            } catch (error) {
                console.error('Error updating unread counts:', error);
            }
        }, 30000);
    }
    
    handleNewMessageNotification(data) {
        // Show browser notification if supported
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('New message', {
                body: data.content,
                icon: '/static/images/logo-small.png'
            });
        }
        
        // Update conversation list
        this.updateConversationInList(data.conversation);
    }
    
    showError(message) {
        // Show error notification
        const toast = document.createElement('div');
        toast.className = 'toast align-items-center text-bg-danger border-0';
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        const toastContainer = document.querySelector('.toast-container') || document.body;
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Global functions for modal
function createConversation() {
    if (window.chatConversations) {
        window.chatConversations.createConversation();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatConversations = new ChatConversations();
});