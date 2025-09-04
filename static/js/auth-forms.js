/**
 * Authentication Forms JavaScript
 * Handles form validation and interactions for auth pages
 */

document.addEventListener('DOMContentLoaded', function() {
    // User type toggle for registration
    const userTypeSelect = document.getElementById('user_type');
    const playerFields = document.getElementById('player_fields');
    const skillLevel = document.getElementById('skill_level');
    
    if (userTypeSelect && playerFields) {
        userTypeSelect.addEventListener('change', function() {
            if (this.value === 'player') {
                playerFields.style.display = 'block';
                if (skillLevel) skillLevel.required = true;
            } else {
                playerFields.style.display = 'none';
                if (skillLevel) skillLevel.required = false;
            }
        });
    }
    
    // Password confirmation validation
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (password && confirmPassword) {
        function validatePassword() {
            if (password.value !== confirmPassword.value) {
                confirmPassword.setCustomValidity('Passwords do not match');
            } else {
                confirmPassword.setCustomValidity('');
            }
        }
        
        password.addEventListener('change', validatePassword);
        confirmPassword.addEventListener('keyup', validatePassword);
    }
    
    // Form submission handling
    const authForms = document.querySelectorAll('form');
    authForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Add loading state
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processing...';
            }
        });
    });
});