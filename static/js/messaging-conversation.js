// Messaging Conversation JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('messageForm');
    const messageInput = document.getElementById('messageInput');
    const messagesArea = document.getElementById('messagesArea');
    
    // Get other user ID from URL
    const pathParts = window.location.pathname.split('/');
    const otherUserId = pathParts[pathParts.length - 1];
    
    if (messageForm && messageInput) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const messageContent = messageInput.value.trim();
            if (!messageContent) return;
            
            // Show sending state
            const submitBtn = messageForm.querySelector('button[type="submit"]');
            const originalHTML = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            submitBtn.disabled = true;
            
            // Send message via AJAX
            fetch('/messaging/api/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    receiver_id: parseInt(otherUserId),
                    content: messageContent,
                    message_type: 'text'
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear input
                    messageInput.value = '';
                    
                    // Add message to chat immediately for better UX
                    addMessageToChat({
                        content: messageContent,
                        is_from_me: true,
                        time_display: 'Just now'
                    });
                    
                    // Scroll to bottom
                    scrollToBottom();
                } else {
                    alert('Error sending message: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Network error. Please try again.');
            })
            .finally(() => {
                // Reset button
                submitBtn.innerHTML = originalHTML;
                submitBtn.disabled = false;
            });
        });
    }
    
    // Function to add message to chat UI
    function addMessageToChat(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-3 ${message.is_from_me ? 'text-end' : ''}`;
        
        messageDiv.innerHTML = `
            <div class="d-inline-block p-2 rounded ${message.is_from_me ? 'bg-primary text-white' : 'bg-light'}" 
                 style="max-width: 70%;">
                ${message.content}
                <br><small class="${message.is_from_me ? 'text-light' : 'text-muted'}">
                    ${message.time_display}
                </small>
            </div>
        `;
        
        messagesArea.appendChild(messageDiv);
    }
    
    // Function to scroll to bottom
    function scrollToBottom() {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    }
    
    // Auto-scroll to bottom on page load
    scrollToBottom();
    
    // Auto-refresh messages every 5 seconds (simple polling)
    let lastMessageId = 0;
    setInterval(function() {
        refreshMessages();
    }, 5000);
    
    function refreshMessages() {
        fetch(`/messaging/api/conversation/${otherUserId}/messages?since_id=${lastMessageId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.messages.length > 0) {
                    data.messages.forEach(message => {
                        if (message.id > lastMessageId) {
                            addMessageToChat(message);
                            lastMessageId = message.id;
                        }
                    });
                    scrollToBottom();
                }
            })
            .catch(error => {
                console.error('Error refreshing messages:', error);
            });
    }
});