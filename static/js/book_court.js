/**
 * Book Court JavaScript Module - FIXED VERSION
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
        
        if (dateParam) {
            const dateInput = document.querySelector('input[type="date"]');
            if (dateInput) {
                dateInput.value = dateParam;
            }
            
            const bookingDateInput = document.getElementById('booking_date');
            if (bookingDateInput) {
                bookingDateInput.value = dateParam;
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
        const startSelect = document.getElementById('start_time');
        const endSelect = document.getElementById('end_time');
        
        if (!startSelect || !endSelect) return;

        // Generate time slots from 8:00 to 22:00
        for (let hour = 8; hour <= 22; hour++) {
            const timeValue = `${hour.toString().padStart(2, '0')}:00`;
            const timeText = this.formatTime(timeValue);
            
            const startOption = new Option(timeText, timeValue);
            const endOption = new Option(timeText, timeValue);
            
            startSelect.appendChild(startOption);
            endSelect.appendChild(endOption);
        }
    }

    formatTime(timeString) {
        const [hour, minute] = timeString.split(':');
        const hourNum = parseInt(hour);
        const ampm = hourNum >= 12 ? 'PM' : 'AM';
        const displayHour = hourNum > 12 ? hourNum - 12 : (hourNum === 0 ? 12 : hourNum);
        return `${displayHour}:${minute} ${ampm}`;
    }

    showBookingModal(courtId, courtName, hourlyRate) {
        this.currentCourtId = courtId;
        this.currentCourtName = courtName;
        this.currentHourlyRate = hourlyRate;

        // Set modal title and form data
        const modalTitle = document.getElementById('modalCourtName');
        const modalCourtId = document.getElementById('modalCourtId');
        
        if (modalTitle) modalTitle.textContent = courtName;
        if (modalCourtId) modalCourtId.value = courtId;

        // Reset form
        const form = document.getElementById('bookingForm');
        if (form) form.reset();
        if (modalCourtId) modalCourtId.value = courtId;
        
        const costInfo = document.getElementById('costInfo');
        if (costInfo) costInfo.style.display = 'none';

        // Show modal
        if (this.modal) {
            this.modal.show();
        }
    }

    calculateCost() {
        const startTime = document.getElementById('start_time');
        const endTime = document.getElementById('end_time');
        const costInfo = document.getElementById('costInfo');
        
        if (!startTime || !endTime || !costInfo) return;
        
        if (!startTime.value || !endTime.value) {
            costInfo.style.display = 'none';
            return;
        }

        // Calculate duration
        const start = new Date(`2000-01-01 ${startTime.value}`);
        const end = new Date(`2000-01-01 ${endTime.value}`);

        if (end <= start) {
            costInfo.style.display = 'none';
            return;
        }

        const durationHours = (end - start) / (1000 * 60 * 60);
        const totalCost = durationHours * this.currentHourlyRate;

        // Display cost info
        const durationEl = document.getElementById('duration');
        const totalCostEl = document.getElementById('totalCost');
        
        if (durationEl) {
            durationEl.textContent = durationHours === 1 ? '1 hour' : `${durationHours} hours`;
        }
        if (totalCostEl) {
            totalCostEl.textContent = `₪${totalCost.toFixed(2)}`;
        }
        
        costInfo.style.display = 'block';
    }

    
    async submitBooking() {
        const form = document.getElementById('bookingForm');
        if (!form) return;

        const submitBtn = document.getElementById('submitBookingBtn');
        if (!submitBtn) return;
        
        const submitText = submitBtn.querySelector('.submit-text');
        const loadingText = submitBtn.querySelector('.loading-text');

        // Show loading state - עם בדיקות null
        if (submitText) submitText.style.display = 'none';
        if (loadingText) loadingText.style.display = 'block';
        submitBtn.disabled = true;

        try {
            const formData = new FormData(form);
            const response = await fetch('/player/submit-booking', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                // Success - reload page or redirect
                window.location.reload();
            } else {
                // Show error
                alert(result.error || 'Booking failed. Please try again.');
            }
        } catch (error) {
            console.error('Booking error:', error);
            alert('Network error. Please try again.');
        } finally {
            // Reset button state - עם בדיקות null
            if (submitText) submitText.style.display = 'block';
            if (loadingText) loadingText.style.display = 'none';
            submitBtn.disabled = false;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.bookCourtManager = new BookCourtManager();
});

// Global function for template compatibility
function openBookingModal(courtId, courtName, hourlyRate) {
    if (window.bookCourtManager) {
        window.bookCourtManager.showBookingModal(courtId, courtName, hourlyRate);
    }
}