/**
 * AI Chat Widget for TennisMatchUp
 */
class TennisAIChat {
    constructor() {
        this.isOpen = false;
        this.messages = [];
        this.init();
    }
    
    init() {
        this.createChatWidget();
        this.setupEventListeners();
    }
    
    createChatWidget() {
        const widget = document.createElement('div');
        widget.innerHTML = `
            <div id="ai-chat-widget" class="ai-chat-widget">
                <div id="chat-toggle" class="chat-toggle">
                    <i class="fas fa-robot"></i>
                    <span>Tennis AI</span>
                </div>
                <div id="chat-container" class="chat-container" style="display: none;">
                    <div class="chat-header">
                        <h4>TennisCoach AI</h4>
                        <button id="chat-close" class="btn-close"></button>
                    </div>
                    <div id="chat-messages" class="chat-messages"></div>
                    <div class="chat-input">
                        <input type="text" id="chat-input" placeholder="Ask about tennis...">
                        <button id="chat-send">Send</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(widget);
    }
    
    setupEventListeners() {
        document.getElementById('chat-toggle').addEventListener('click', () => {
            this.toggleChat();
        });
        
        document.getElementById('chat-close').addEventListener('click', () => {
            this.toggleChat();
        });
        
        document.getElementById('chat-send').addEventListener('click', () => {
            this.sendMessage();
        });
        
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
    }
    
    toggleChat() {
        const container = document.getElementById('chat-container');
        this.isOpen = !this.isOpen;
        container.style.display = this.isOpen ? 'block' : 'none';
    }
    
    async sendMessage() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        
        if (!message) return;
        
        this.addMessage('user', message);
        input.value = '';
        
        try {
            const response = await fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addMessage('ai', data.response);
            } else {
                this.addMessage('ai', 'Sorry, I encountered an error.');
            }
        } catch (error) {
            this.addMessage('ai', 'Connection error. Please try again.');
        }
    }
    
    addMessage(sender, content) {
        const messagesContainer = document.getElementById('chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
            <div class="message-time">${new Date().toLocaleTimeString()}</div>
        `;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new TennisAIChat();
});