/**
 * Book Court JavaScript Module
 * Handles client-side interactions for court booking
 */

class BookCourtManager {
    constructor() {
        this.modal = null;
        this.currentCourtId = null;
        this.currentCourtName = '';
        this.currentHourlyRate = 0;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupModal();
        this.populateTimeSlots();
        this.setMinDate();
        this.setDateFromURL();
    }

    setDateFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const dateParam = urlParams.get('date');
        
        console.log('URL date parameter:', dateParam); // Debug
        
        if (dateParam) {
            // Set the date filter
            const dateInput = document.querySelector('input[type="date"]');
            if (dateInput) {
                dateInput.value = dateParam;
                console.log('Date set to:', dateParam); // Debug
            }
            
            // Also set it in any booking modal that might be open
            const bookingDateInput = document.getElementById('booking_date');
            if (bookingDateInput) {
                bookingDateInput.value = dateParam;
                console.log('Booking date set to:', dateParam); // Debug
            }
        }
    }

    
    setupEventListeners() {
        // Book court buttons
        document.querySelectorAll('.book-court-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const courtId = e.target.dataset.courtId;
                const courtName = e.target.dataset.courtName;
                const hourlyRate = parseFloat(e.target.dataset.hourlyRate);
                this.showBookingModal(courtId, courtName, hourlyRate);
            });
        });

        // Form submission
        const bookingForm = document.getElementById('bookingForm');
        if (bookingForm) {
            bookingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitBooking();
            });
        }

        // Time change listeners for cost calculation
        const startTimeSelect = document.getElementById('start_time');
        const endTimeSelect = document.getElementById('end_time');
        
        if (startTimeSelect && endTimeSelect) {
            startTimeSelect.addEventListener('change', () => this.calculateCost());
            endTimeSelect.addEventListener('change', () => this.calculateCost());
        }

        // Auto-submit filters
        document.getElementById('location')?.addEventListener('change', () => {
            document.getElementById('filterForm').submit();
        });

        document.getElementById('date')?.addEventListener('change', () => {
            document.getElementById('filterForm').submit();
        });
    }

    setupModal() {
        const modalElement = document.getElementById('bookingModal');
        if (modalElement) {
            this.modal = new bootstrap.Modal(modalElement);
        }
    }

    setMinDate() {
        const dateInput = document.getElementById('booking_date');
        if (dateInput) {
            const today = new Date();
            const minDate = today.toISOString().split('T')[0];
            dateInput.setAttribute('min', minDate);
        }
    }

    populateTimeSlots() {
        const startTimeSelect = document.getElementById('start_time');
        const endTimeSelect = document.getElementById('end_time');
        
        if (!startTimeSelect || !endTimeSelect) return;

        // Clear existing options
        startTimeSelect.innerHTML = '<option value="">Select...</option>';
        endTimeSelect.innerHTML = '<option value="">Select...</option>';

        // Generate time slots (6 AM to 10 PM)
        for (let hour = 6; hour < 22; hour++) {
            const timeStr = `${hour.toString().padStart(2, '0')}:00`;
            const displayTime = this.formatTimeDisplay(timeStr);
            
            startTimeSelect.innerHTML += `<option value="${timeStr}">${displayTime}</option>`;
            
            // End time starts from 7 AM
            if (hour >= 7) {
                endTimeSelect.innerHTML += `<option value="${timeStr}">${displayTime}</option>`;
            }
        }

        // Add 30-minute slots
        for (let hour = 6; hour < 22; hour++) {
            const timeStr = `${hour.toString().padStart(2, '0')}:30`;
            const displayTime = this.formatTimeDisplay(timeStr);
            
            startTimeSelect.innerHTML += `<option value="${timeStr}">${displayTime}</option>`;
            
            if (hour >= 6) {
                endTimeSelect.innerHTML += `<option value="${timeStr}">${displayTime}</option>`;
            }
        }

        // Sort options
        this.sortSelectOptions(startTimeSelect);
        this.sortSelectOptions(endTimeSelect);
    }

    formatTimeDisplay(timeStr) {
        const [hour, minute] = timeStr.split(':');
        const hourNum = parseInt(hour);
        const ampm = hourNum >= 12 ? 'PM' : 'AM';
        const displayHour = hourNum > 12 ? hourNum - 12 : (hourNum === 0 ? 12 : hourNum);
        return `${displayHour}:${minute} ${ampm}`;
    }

    sortSelectOptions(selectElement) {
        const options = Array.from(selectElement.options).slice(1); // Skip first "Select..." option
        options.sort((a, b) => a.value.localeCompare(b.value));
        
        // Clear and rebuild
        selectElement.innerHTML = '<option value="">Select...</option>';
        options.forEach(option => selectElement.appendChild(option));
    }

    showBookingModal(courtId, courtName, hourlyRate) {
        this.currentCourtId = courtId;
        this.currentCourtName = courtName;
        this.currentHourlyRate = hourlyRate;

        // Set modal title and form data
        document.getElementById('modalCourtName').textContent = courtName;
        document.getElementById('modalCourtId').value = courtId;

        // Reset form
        document.getElementById('bookingForm').reset();
        document.getElementById('modalCourtId').value = courtId;
        document.getElementById('costInfo').style.display = 'none';

        // Show modal
        if (this.modal) {
            this.modal.show();
        }
    }

    calculateCost() {
        const startTime = document.getElementById('start_time').value;
        const endTime = document.getElementById('end_time').value;

        if (!startTime || !endTime) {
            document.getElementById('costInfo').style.display = 'none';
            return;
        }

        // Calculate duration (server will validate this)
        const start = new Date(`2000-01-01 ${startTime}`);
        const end = new Date(`2000-01-01 ${endTime}`);

        if (end <= start) {
            document.getElementById('costInfo').style.display = 'none';
            return;
        }

        const durationHours = (end - start) / (1000 * 60 * 60);
        const totalCost = durationHours * this.currentHourlyRate;

        // Display cost info
        document.getElementById('duration').textContent = 
            durationHours === 1 ? '1 hour' : `${durationHours} hours`;
        document.getElementById('totalCost').textContent = `₪${totalCost.toFixed(0)}`;
        document.getElementById('costInfo').style.display = 'block';
    }

    async submitBooking() {
        const form = document.getElementById('bookingForm');
        const submitBtn = document.getElementById('submitBookingBtn');
        
        if (!form) return;

        // Show loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        try {
            const formData = new FormData(form);
            
            const response = await fetch('/player/submit-booking', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const result = await response.json();

            if (result.success) {
                // Close modal
                this.modal.hide();
                
                // Show success message
                this.showFlashMessage(
                    'Booking request submitted successfully! You will receive confirmation once approved.',
                    'success'
                );

                // Optional: redirect to calendar
                setTimeout(() => {
                    window.location.href = '/player/my-calendar';
                }, 2000);
            } else {
                this.showFlashMessage(`Booking failed: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Booking submission error:', error);
            this.showFlashMessage('An error occurred. Please try again.', 'error');
        } finally {
            // Remove loading state
            submitBtn.classList.remove('loading');
            submitBtn.disabled = false;
        }
    }

    showFlashMessage(message, type) {
        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const alertHtml = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;

        // Insert at top of container
        const container = document.querySelector('.container');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
            
            // Auto-remove after 5 seconds
            setTimeout(() => {
                const alert = container.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new BookCourtManager();
});

// Export for potential external use
window.BookCourtManager = BookCourtManager;