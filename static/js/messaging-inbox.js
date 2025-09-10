// Messaging Inbox JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchMessages');
    const conversationItems = document.querySelectorAll('.list-group-item');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            
            conversationItems.forEach(function(item) {
                const userName = item.querySelector('h6').textContent.toLowerCase();
                const lastMessage = item.querySelector('p').textContent.toLowerCase();
                
                if (userName.includes(searchTerm) || lastMessage.includes(searchTerm)) {
                    item.style.display = '';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});