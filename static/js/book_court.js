/**
 * Book Court JavaScript Module - Complete Fixed Version
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
                const hourlyRate = parseFloat(e.target.dataset.hourlyRate || 0);
                
                console.log('Book court clicked:', { courtId, courtName, hourlyRate });
                this.openBookingModal(courtId, courtName, hourlyRate);
            });
        });

        // Time change listeners for cost calculation
        const startTimeInput = document.getElementById('start_time');
        const endTimeInput = document.getElementById('end_time');
        const dateInput = document.getElementById('booking_date');

        if (startTimeInput) {
            startTimeInput.addEventListener('change', () => this.updateCostCalculation());
        }

        if (endTimeInput) {
            endTimeInput.addEventListener('change', () => this.updateCostCalculation());
        }

        // Date change listener for availability check
        if (dateInput) {
            dateInput.addEventListener('change', (e) => {
                if (this.currentCourtId) {
                    this.checkAvailability(this.currentCourtId, e.target.value);
                }
            });
        }

        // Form submission
        const bookingForm = document.getElementById('bookingForm');
        if (bookingForm) {
            bookingForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitBooking();
            });
        }

        // Filter form submission
        const filterForm = document.getElementById('filterForm');
        if (filterForm) {
            filterForm.addEventListener('submit', (e) => {
                // Let the form submit normally for server-side filtering
                console.log('Filter form submitted');
            });
        }
    }

    setupModal() {
        const modalElement = document.getElementById('bookingModal');
        if (modalElement && typeof bootstrap !== 'undefined') {
            this.modal = new bootstrap.Modal(modalElement);
            console.log('Booking modal initialized');
        }
    }

    openBookingModal(courtId, courtName, hourlyRate) {
        console.log('Opening booking modal:', { courtId, courtName, hourlyRate });
        
        this.currentCourtId = courtId;
        this.currentCourtName = courtName;
        this.currentHourlyRate = hourlyRate;

        // Update modal content
        const modalTitle = document.getElementById('bookingModalLabel');
        const courtIdInput = document.getElementById('court_id');
        const courtNameSpan = document.getElementById('selectedCourtName');
        const rateSpan = document.getElementById('selectedCourtRate');

        if (modalTitle) {
            modalTitle.textContent = `Book Court - ${courtName}`;
        }
        
        if (courtIdInput) {
            courtIdInput.value = courtId;
        }
        
        if (courtNameSpan) {
            courtNameSpan.textContent = courtName;
        }
        
        if (rateSpan) {
            rateSpan.textContent = `$${hourlyRate}/hour`;
        }

        // Reset form
        this.resetBookingForm();

        // Check availability if date is selected
        const dateInput = document.getElementById('booking_date');
        if (dateInput && dateInput.value) {
            this.checkAvailability(courtId, dateInput.value);
        }

        // Show modal
        if (this.modal) {
            this.modal.show();
        } else {
            console.error('Modal not initialized');
        }
    }

    resetBookingForm() {
        const form = document.getElementById('bookingForm');
        if (!form) return;

        // Reset form fields but keep court_id
        const courtId = document.getElementById('court_id').value;
        form.reset();
        document.getElementById('court_id').value = courtId;

        // Reset cost display
        const costInfo = document.getElementById('costInfo');
        if (costInfo) {
            costInfo.style.display = 'none';
        }

        // Clear availability info
        const availabilityInfo = document.getElementById('availabilityInfo');
        if (availabilityInfo) {
            availabilityInfo.innerHTML = '';
        }
    }

    populateTimeSlots() {
        const startTimeSelect = document.getElementById('start_time');
        const endTimeSelect = document.getElementById('end_time');

        if (!startTimeSelect || !endTimeSelect) return;

        // Clear existing options (except first default option)
        startTimeSelect.innerHTML = '<option value="">Select start time</option>';
        endTimeSelect.innerHTML = '<option value="">Select end time</option>';

        // Generate time slots from 6 AM to 10 PM
        for (let hour = 6; hour <= 22; hour++) {
            for (let minute = 0; minute < 60; minute += 60) { // Hourly slots
                const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
                const displayTime = this.formatTime(hour, minute);
                
                const startOption = new Option(displayTime, timeString);
                const endOption = new Option(displayTime, timeString);
                
                startTimeSelect.add(startOption);
                endTimeSelect.add(endOption);
            }
        }
    }

    formatTime(hour, minute) {
        const period = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour > 12 ? hour - 12 : (hour === 0 ? 12 : hour);
        return `${displayHour}:${minute.toString().padStart(2, '0')} ${period}`;
    }

    setMinDate() {
        const dateInput = document.getElementById('booking_date');
        if (dateInput) {
            const today = new Date();
            const minDate = today.toISOString().split('T')[0];
            dateInput.min = minDate;
            
            // Set default to today if empty
            if (!dateInput.value) {
                dateInput.value = minDate;
            }
        }
    }

    checkAvailability(courtId, date) {
        if (!courtId || !date) return;

        console.log('Checking availability for court:', courtId, 'date:', date);

        const availabilityInfo = document.getElementById('availabilityInfo');
        if (availabilityInfo) {
            availabilityInfo.innerHTML = '<div class="text-info"><i class="fas fa-spinner fa-spin me-2"></i>Checking availability...</div>';
        }

        fetch(`/player/api/available-slots/${courtId}?date=${date}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displayAvailability(data.available_slots);
                } else {
                    this.displayAvailabilityError(data.error || 'Failed to check availability');
                }
            })
            .catch(error => {
                console.error('Availability check error:', error);
                this.displayAvailabilityError('Network error checking availability');
            });
    }

    displayAvailability(availableSlots) {
        const availabilityInfo = document.getElementById('availabilityInfo');
        if (!availabilityInfo) return;

        if (availableSlots.length === 0) {
            availabilityInfo.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No time slots available for this date. Please select another date.
                </div>
            `;
            return;
        }

        let html = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>
                ${availableSlots.length} time slot(s) available:
            </div>
            <div class="row">
        `;

        availableSlots.forEach(slot => {
            html += `
                <div class="col-md-4 mb-2">
                    <button type="button" class="btn btn-outline-success btn-sm w-100 time-slot-btn" 
                            data-start="${slot.start_time}" data-end="${slot.end_time}">
                        ${this.formatTimeSlot(slot.start_time)} - ${this.formatTimeSlot(slot.end_time)}
                    </button>
                </div>
            `;
        });

        html += '</div>';
        availabilityInfo.innerHTML = html;

        // Add click listeners to time slot buttons
        availabilityInfo.querySelectorAll('.time-slot-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const startTime = e.target.dataset.start;
                const endTime = e.target.dataset.end;
                this.selectTimeSlot(startTime, endTime);
            });
        });
    }

    displayAvailabilityError(error) {
        const availabilityInfo = document.getElementById('availabilityInfo');
        if (availabilityInfo) {
            availabilityInfo.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${error}
                </div>
            `;
        }
    }

    formatTimeSlot(timeString) {
        const [hours, minutes] = timeString.split(':').map(Number);
        return this.formatTime(hours, minutes);
    }

    selectTimeSlot(startTime, endTime) {
        const startTimeSelect = document.getElementById('start_time');
        const endTimeSelect = document.getElementById('end_time');

        if (startTimeSelect && endTimeSelect) {
            startTimeSelect.value = startTime;
            endTimeSelect.value = endTime;
            
            // Update cost calculation
            this.updateCostCalculation();
            
            // Highlight selected slot
            document.querySelectorAll('.time-slot-btn').forEach(btn => {
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-success');
            });
            
            const selectedBtn = document.querySelector(`[data-start="${startTime}"][data-end="${endTime}"]`);
            if (selectedBtn) {
                selectedBtn.classList.remove('btn-outline-success');
                selectedBtn.classList.add('btn-success');
            }
            
            console.log('Time slot selected:', { startTime, endTime });
        }
    }

    updateCostCalculation() {
        const startTimeElement = document.getElementById('start_time');
        const endTimeElement = document.getElementById('end_time');
        
        if (!startTimeElement || !endTimeElement) return;

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
                totalCostElement.textContent = `${totalCost.toFixed(2)}`;
            }
            
            if (costInfo) {
                costInfo.style.display = 'block';
            }

            console.log('Cost calculated:', { durationHours, totalCost });

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
            this.showError('Booking form not found');
            return;
        }

        // Validate form
        if (!this.validateBookingForm(form)) {
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
            submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Booking...';
        }

        // Submit to server
        fetch('/player/submit-booking', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Booking response:', data);
            
            if (data.success) {
                // Success feedback
                this.showSuccess(data.message || 'Booking successful!');
                
                if (this.modal) {
                    this.modal.hide();
                }
                
                // Redirect after short delay
                setTimeout(() => {
                    window.location.href = '/player/my-calendar';
                }, 1500);
                
            } else {
                // Error feedback
                this.showError(data.error || 'Booking failed');
            }
        })
        .catch(error => {
            console.error('Booking submission error:', error);
            this.showError('Network error. Please check your connection and try again.');
        })
        .finally(() => {
            // Restore button state
            if (submitButton) {
                submitButton.disabled = false;
                submitButton.innerHTML = originalText;
            }
        });
    }

    validateBookingForm(form) {
        const requiredFields = [
            { id: 'court_id', name: 'Court' },
            { id: 'booking_date', name: 'Date' },
            { id: 'start_time', name: 'Start time' },
            { id: 'end_time', name: 'End time' }
        ];

        for (const field of requiredFields) {
            const element = form.querySelector(`#${field.id}`);
            if (!element || !element.value.trim()) {
                this.showError(`${field.name} is required`);
                if (element) element.focus();
                return false;
            }
        }

        // Validate time range
        const startTime = form.querySelector('#start_time').value;
        const endTime = form.querySelector('#end_time').value;
        
        if (startTime && endTime) {
            const start = new Date(`2000-01-01 ${startTime}`);
            const end = new Date(`2000-01-01 ${endTime}`);
            
            if (end <= start) {
                this.showError('End time must be after start time');
                return false;
            }
            
            const durationHours = (end - start) / (1000 * 60 * 60);
            if (durationHours < 1) {
                this.showError('Minimum booking duration is 1 hour');
                return false;
            }
            
            if (durationHours > 8) {
                this.showError('Maximum booking duration is 8 hours');
                return false;
            }
        }

        // Validate date is not in the past
        const bookingDate = form.querySelector('#booking_date').value;
        if (bookingDate) {
            const selectedDate = new Date(bookingDate);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate < today) {
                this.showError('Cannot book courts for past dates');
                return false;
            }
        }

        return true;
    }

    showSuccess(message) {
        this.showToast(message, 'success');
        console.log('Success:', message);
    }

    showError(message) {
        this.showToast(message, 'error');
        console.error('Error:', message);
    }

    showToast(message, type = 'info') {
        // Remove existing toasts
        document.querySelectorAll('.tennis-toast').forEach(toast => toast.remove());

        const toastContainer = this.getToastContainer();
        
        const toast = document.createElement('div');
        const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
        
        toast.className = `tennis-toast alert ${bgClass} text-white alert-dismissible fade show position-relative`;
        toast.style.cssText = 'margin-bottom: 10px; animation: slideIn 0.3s ease-out;';
        
        toast.innerHTML = `
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-triangle' : 'fa-info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert"></button>
        `;
        
        toastContainer.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    getToastContainer() {
        let container = document.getElementById('tennis-toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'tennis-toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        return container;
    }
}

// Add CSS animation for toasts
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('BookCourtManager initializing...');
    window.bookCourtManager = new BookCourtManager();
    console.log('BookCourtManager ready');
});