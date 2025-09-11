/**
 * TennisMatchUp - Player Find Matches Form Handler
 * Extracted from template to maintain proper MVC separation
 */

// Handle form submission for message modal
document.addEventListener('DOMContentLoaded', function() {
    const messageModal = document.getElementById('messageModal');
    if (messageModal) {
        const form = messageModal.querySelector('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(this);
                const submitButton = this.querySelector('button[type="submit"]');
                const originalText = submitButton.innerHTML;
                
                // Show loading
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
                
                fetch(this.action, {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(result => {
                    if (result.success) {
                        // Close modal
                        const modal = bootstrap.Modal.getInstance(messageModal);
                        modal.hide();
                        
                        // Redirect to conversation
                        if (result.conversation_url) {
                            window.location.href = result.conversation_url;
                        }
                    } else {
                        alert('Error: ' + (result.error || 'Failed to send message'));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Network error. Please try again.');
                })
                .finally(() => {
                    // Reset button
                    submitButton.disabled = false;
                    submitButton.innerHTML = originalText;
                });
            });
        }
    }
});