// תיקון מושלם ל-static/js/book_court.js
// החלף את כל הקוד עם:

/**
 * Book Court JavaScript Module - Fixed Version
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
        console.log('Initializing BookCourtManager...');
        this.setupEventListeners();
        this.setupModal();
        this.populateTimeSlots();
        this.setMinDate();
        this.setDateFromURL();
    }

    setDateFromURL() {
        const urlParams = new URLSearchParams(window.location.search);
        const dateParam = urlParams.get('date');
        
        console.log('URL date parameter:', dateParam);
        
        if (dateParam) {
            // Set the date filter in the main date input
            const dateFilters = document.querySelectorAll('input[name="date"], input[id="date"]');
            dateFilters.forEach(input => {
                if (input) {
                    input.value = dateParam;
                    console.log('Date filter set to:', dateParam);
                }
            });
            
            // Also set it in booking modal if it exists
            const bookingDateInput = document.getElementById('booking_date');
            if (bookingDateInput) {
                bookingDateInput.value = dateParam;
                console.log('Booking date set to:', dateParam);
            }
        }
    }

    setupEventListeners() {
        // Book court buttons
        document.querySelectorAll('.book-court-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const courtId = e.target.dataset.courtId;
                const courtName = e.target.dataset.courtName;
                const hourlyRate = parseFloat(e.target.dataset.hourlyRate) || 0;
                
                console.log('Book button clicked:', {courtId, courtName, hourlyRate});
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
        
        if (startTimeSelect) {
            startTimeSelect.addEventListener('change', () => this.calculateCost());
        }
        if (endTimeSelect) {
            endTimeSelect.addEventListener('change', () => this.calculateCost());
        }

        // Auto-submit filters with safety checks
        const locationFilter = document.getElementById('location');
        const dateFilter = document.getElementById('date');
        const filterForm = document.getElementById('filterForm');
        
        if (locationFilter && filterForm) {
            locationFilter.addEventListener('change', () => filterForm.submit());
        }
        
        if (dateFilter && filterForm) {
            dateFilter.addEventListener('change', () => filterForm.submit());
        }
    }

    setupModal() {
        const modalElement = document.getElementById('bookingModal');
        if (modalElement) {
            try {
                this.modal = new bootstrap.Modal(modalElement);
                console.log('Modal initialized successfully');
            } catch (error) {
                console.warn('Bootstrap Modal initialization failed:', error);
            }
        } else {
            console.warn('Booking modal element not found');
        }
    }

    setMinDate() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        const today = new Date().toISOString().split('T')[0];
        
        dateInputs.forEach(input => {
            if (input) {
                input.setAttribute('min', today);
            }
        });
    }

    populateTimeSlots() {
        const startTimeSelect = document.getElementById('start_time');
        const endTimeSelect = document.getElementById('end_time');
        
        if (!startTimeSelect || !endTimeSelect) {
            console.warn('Time select elements not found');
            return;
        }

        // Clear existing options (keep first "Select..." option)
        startTimeSelect.innerHTML = '<option value="">Select...</option>';
        endTimeSelect.innerHTML = '<option value="">Select...</option>';

        // Generate time slots from 6:00 AM to 11:00 PM
        for (let hour = 6; hour <= 23; hour++) {
            for (let minute = 0; minute < 60; minute += 30) {
                const timeValue = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
                const timeDisplay = this.formatTimeDisplay(hour, minute);
                
                const startOption = new Option(timeDisplay, timeValue);
                const endOption = new Option(timeDisplay, timeValue);
                
                startTimeSelect.add(startOption);
                endTimeSelect.add(endOption);
            }
        }

        console.log('Time slots populated');
    }

    formatTimeDisplay(hour, minute) {
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
        const minuteStr = minute.toString().padStart(2, '0');
        return `${displayHour}:${minuteStr} ${ampm}`;
    }

    showBookingModal(courtId, courtName, hourlyRate) {
        console.log('Showing booking modal for:', {courtId, courtName, hourlyRate});
        
        this.currentCourtId = courtId;
        this.currentCourtName = courtName;
        this.currentHourlyRate = hourlyRate;

        // Update modal content with null checks
        const modalCourtName = document.getElementById('modalCourtName');
        const modalCourtId = document.getElementById('modalCourtId');
        
        if (modalCourtName) {
            modalCourtName.textContent = courtName;
        }
        
        if (modalCourtId) {
            modalCourtId.value = courtId;
        }

        // Reset form safely
        const bookingForm = document.getElementById('bookingForm');
        if (bookingForm) {
            bookingForm.reset();
            // Restore court ID after reset
            if (modalCourtId) {
                modalCourtId.value = courtId;
            }
        }

        // Hide cost info if it exists
        const costInfo = document.getElementById('costInfo');
        if (costInfo) {
            costInfo.style.display = 'none';
        }

        // Show modal
        if (this.modal) {
            try {
                this.modal.show();
            } catch (error) {
                console.error('Error showing modal:', error);
                // Fallback: show modal manually if Bootstrap fails
                const modalElement = document.getElementById('bookingModal');
                if (modalElement) {
                    modalElement.style.display = 'block';
                    modalElement.classList.add('show');
                }
            }
        } else {
            console.warn('Modal not available');
        }
    }

    calculateCost() {
        const startTimeElement = document.getElementById('start_time');
        const endTimeElement = document.getElementById('end_time');
        
        if (!startTimeElement || !endTimeElement) {
            return; // Elements don't exist, exit gracefully
        }
        
        const startTime = startTimeElement.value;
        const endTime = endTimeElement.value;
        const costInfo = document.getElementById('costInfo');

        if (!startTime || !endTime) {
            if (costInfo) {
                costInfo.style.display = 'none';
            }
            return;
        }

        try {
            // Calculate duration
            const start = new Date(`2000-01-01 ${startTime}`);
            const end = new Date(`2000-01-01 ${endTime}`);

            if (end <= start) {
                if (costInfo) {
                    costInfo.style.display = 'none';
                }
                return;
            }

            const durationHours = (end - start) / (1000 * 60 * 60);
            const totalCost = durationHours * this.currentHourlyRate;

            // Update display elements if they exist
            const durationElement = document.getElementById('duration');
            const totalCostElement = document.getElementById('totalCost');
            
            if (durationElement) {
                durationElement.textContent = 
                    durationHours === 1 ? '1 hour' : `${durationHours} hours`;
            }
            
            if (totalCostElement) {
                totalCostElement.textContent = `$${totalCost.toFixed(2)}`;
            }
            
            if (costInfo) {
                costInfo.style.display = 'block';
            }

        } catch (error) {
            console.error('Error calculating cost:', error);
            if (costInfo) {
                costInfo.style.display = 'none';
            }
        }
    }

    submitBooking() {
        console.log('Submitting booking...');
        
        // Get form data
        const form = document.getElementById('bookingForm');
        if (!form) {
            console.error('Booking form not found');
            return;
        }

        const formData = new FormData(form);
        
        // Add CSRF token if available
        const csrfToken = document.querySelector('[name=csrf_token]');
        if (csrfToken) {
            formData.append('csrf_token', csrfToken.value);
        }

        // Show loading state
        const submitButton = form.querySelector('button[type="submit"]');
        const originalText = submitButton ? submitButton.textContent : '';
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Booking...';
        }

        // Submit to server
        fetch('/player/submit-booking', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Success feedback
                if (this.modal) {
                    this.modal.hide();
                }
                
                // Show success message
                alert('Booking successful! Redirecting to your calendar...');
                
                // Redirect to calendar
                window.location.href = '/player/my-calendar';
            } else {
                // Error feedback
                alert('Booking failed: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Booking submission error:', error);
            alert('An error occurred while booking. Please try again.');
        })
        .finally(() => {
            // Restore button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = originalText;
            }
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('BookCourtManager initializing...');
    window.bookCourtManager = new BookCourtManager();
    console.log('BookCourtManager ready');
});