/**
 * Booking Form Management for TennisMatchUp
 * Handles form validation, cost calculation, and submission
 */

class BookingFormManager {
    constructor() {
        this.form = null;
        this.selectedCourt = null;
        this.calculatedCost = 0;
        this.isSubmitting = false;
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupValidation();
        this.initializeDatePicker();
    }
    
    bindEvents() {
        // Court selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.court-option')) {
                this.selectCourt(e.target.closest('.court-option'));
            }
        });
        
        // Time slot selection
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('time-slot') && !e.target.classList.contains('booked')) {
                this.selectTimeSlot(e.target);
            }
        });
        
        // Form field changes
        document.addEventListener('change', (e) => {
            if (e.target.matches('[name="booking_date"]')) {
                this.onDateChange(e.target.value);
            } else if (e.target.matches('[name="start_time"], [name="end_time"]')) {
                this.onTimeChange();
            } else if (e.target.matches('[name="court_id"]')) {
                this.onCourtChange(e.target.value);
            }
        });
        
        // Form submission
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('booking-form')) {
                e.preventDefault();
                this.handleSubmit(e.target);
            }
        });
        
        // Real-time validation
        document.addEventListener('input', (e) => {
            if (e.target.closest('.booking-form')) {
                this.validateField(e.target);
            }
        });
        
        // Cost calculation triggers
        document.addEventListener('change', (e) => {
            if (e.target.matches('[name="court_id"], [name="start_time"], [name="end_time"]')) {
                this.calculateCost();
            }
        });
    }
    
    /**
     * Select a court option
     */
    selectCourt(courtElement) {
        // Remove previous selection
        document.querySelectorAll('.court-option.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Select current court
        courtElement.classList.add('selected');
        this.selectedCourt = {
            id: courtElement.dataset.courtId,
            name: courtElement.querySelector('.court-name').textContent,
            rate: parseFloat(courtElement.dataset.hourlyRate),
            location: courtElement.querySelector('.court-details').textContent
        };
        
        // Update hidden input
        const courtInput = document.querySelector('[name="court_id"]');
        if (courtInput) {
            courtInput.value = this.selectedCourt.id;
        }
        
        // Update availability for selected date
        const dateInput = document.querySelector('[name="booking_date"]');
        if (dateInput && dateInput.value) {
            this.loadCourtAvailability(this.selectedCourt.id, dateInput.value);
        }
        
        // Recalculate cost
        this.calculateCost();
    }
    
    /**
     * Select a time slot
     */
    selectTimeSlot(slotElement) {
        if (slotElement.classList.contains('booked') || slotElement.classList.contains('unavailable')) {
            return;
        }
        
        // Remove previous selections
        document.querySelectorAll('.time-slot.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Select current slot
        slotElement.classList.add('selected');
        
        const startTime = slotElement.dataset.time;
        const startHour = parseInt(startTime.split(':')[0]);
        const endTime = `${(startHour + 1).toString().padStart(2, '0')}:00`;
        
        // Update form fields
        const startInput = document.querySelector('[name="start_time"]');
        const endInput = document.querySelector('[name="end_time"]');
        
        if (startInput) startInput.value = startTime;
        if (endInput) endInput.value = endTime;
        
        // Update cost
        this.calculateCost();
        
        // Show booking summary
        this.updateBookingSummary();
    }
    
    /**
     * Handle date change
     */
    async onDateChange(selectedDate) {
        if (!selectedDate) return;
        
        // Validate date is not in the past
        const today = new Date().toISOString().split('T')[0];
        if (selectedDate < today) {
            this.showError('Cannot book dates in the past');
            return;
        }
        
        // Clear time selection
        this.clearTimeSelection();
        
        // Load availability for selected court and date
        if (this.selectedCourt) {
            await this.loadCourtAvailability(this.selectedCourt.id, selectedDate);
        }
        
        // Load all courts availability for the date
        await this.loadDateAvailability(selectedDate);
    }
    
    /**
     * Handle time change
     */
    onTimeChange() {
        const startInput = document.querySelector('[name="start_time"]');
        const endInput = document.querySelector('[name="end_time"]');
        
        if (!startInput || !endInput || !startInput.value || !endInput.value) return;
        
        // Validate time range
        const startTime = startInput.value;
        const endTime = endInput.value;
        
        if (startTime >= endTime) {
            this.showFieldError(endInput, 'End time must be after start time');
            return;
        }
        
        // Validate minimum duration (1 hour)
        const startHour = parseInt(startTime.split(':')[0]);
        const endHour = parseInt(endTime.split(':')[0]);
        const duration = endHour - startHour;
        
        if (duration < 1) {
            this.showFieldError(endInput, 'Minimum booking duration is 1 hour');
            return;
        }
        
        // Clear any previous errors
        this.clearFieldError(startInput);
        this.clearFieldError(endInput);
        
        // Calculate cost
        this.calculateCost();
        this.updateBookingSummary();
    }
    
    /**
     * Handle court change
     */
    async onCourtChange(courtId) {
        if (!courtId) return;
        
        try {
            const response = await fetch(`/api/courts/${courtId}`);
            const data = await response.json();
            
            if (data.success) {
                this.selectedCourt = data.court;
                
                // Update availability if date is selected
                const dateInput = document.querySelector('[name="booking_date"]');
                if (dateInput && dateInput.value) {
                    await this.loadCourtAvailability(courtId, dateInput.value);
                }
                
                this.calculateCost();
            }
        } catch (error) {
            console.error('Error loading court details:', error);
        }
    }
    
    /**
     * Load court availability for a specific date
     */
    async loadCourtAvailability(courtId, date) {
        try {
            const response = await fetch(`/api/courts/${courtId}/availability?date=${date}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderTimeSlots(data.availability[date] || {});
            }
        } catch (error) {
            console.error('Error loading court availability:', error);
            this.showError('Failed to load availability');
        }
    }
    
    /**
     * Load availability for all courts on a date
     */
    async loadDateAvailability(date) {
        // This would show general availability across all courts
        // Implementation depends on specific UI requirements
    }
    
    /**
     * Render time slots based on availability
     */
    renderTimeSlots(dayAvailability) {
        const slotsContainer = document.getElementById('time-slots');
        if (!slotsContainer) return;
        
        slotsContainer.innerHTML = '';
        
        // Create slots from 8 AM to 10 PM
        for (let hour = 8; hour < 22; hour++) {
            const timeKey = `${hour.toString().padStart(2, '0')}:00`;
            const slotData = dayAvailability.slots && dayAvailability.slots[timeKey];
            
            const slotElement = document.createElement('div');
            slotElement.className = 'time-slot';
            slotElement.dataset.time = timeKey;
            slotElement.textContent = timeKey;
            
            if (slotData && !slotData.available) {
                slotElement.classList.add('booked');
                slotElement.title = 'Time slot not available';
            } else {
                slotElement.classList.add('available');
                slotElement.title = 'Click to select this time';
            }
            
            slotsContainer.appendChild(slotElement);
        }
    }
    
    /**
     * Calculate booking cost
     */
    async calculateCost() {
        const courtId = document.querySelector('[name="court_id"]')?.value;
        const startTime = document.querySelector('[name="start_time"]')?.value;
        const endTime = document.querySelector('[name="end_time"]')?.value;
        
        if (!courtId || !startTime || !endTime) {
            this.updateCostDisplay(null);
            return;
        }
        
        try {
            const response = await fetch('/api/calculate-cost', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    court_id: courtId,
                    start_time: startTime,
                    end_time: endTime
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.calculatedCost = data.total_cost;
                this.updateCostDisplay(data);
            } else {
                this.showError('Failed to calculate cost');
            }
        } catch (error) {
            console.error('Cost calculation error:', error);
            this.showError('Error calculating cost');
        }
    }
    
    /**
     * Update cost display
     */
    updateCostDisplay(costData) {
        const costContainer = document.getElementById('booking-cost');
        if (!costContainer) return;
        
        if (!costData) {
            costContainer.innerHTML = '';
            return;
        }
        
        costContainer.innerHTML = `
            <div class="booking-summary">
                <div class="summary-row">
                    <span>Duration:</span>
                    <span>${costData.duration_hours} hour(s)</span>
                </div>
                <div class="summary-row">
                    <span>Hourly Rate:</span>
                    <span>$${costData.hourly_rate}/hour</span>
                </div>
                <div class="summary-row total">
                    <span>Total Cost:</span>
                    <span class="fw-bold">${costData.formatted_cost}</span>
                </div>
            </div>
        `;
    }
    
    /**
     * Update booking summary
     */
    updateBookingSummary() {
        const summaryContainer = document.getElementById('booking-summary');
        if (!summaryContainer) return;
        
        const courtName = this.selectedCourt?.name || 'No court selected';
        const date = document.querySelector('[name="booking_date"]')?.value || '';
        const startTime = document.querySelector('[name="start_time"]')?.value || '';
        const endTime = document.querySelector('[name="end_time"]')?.value || '';
        
        if (!date || !startTime || !endTime) {
            summaryContainer.innerHTML = '<p class="text-muted">Complete the form to see booking summary</p>';
            return;
        }
        
        const formattedDate = new Date(date).toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        summaryContainer.innerHTML = `
            <h5>Booking Summary</h5>
            <div class="summary-details">
                <p><strong>Court:</strong> ${courtName}</p>
                <p><strong>Date:</strong> ${formattedDate}</p>
                <p><strong>Time:</strong> ${startTime} - ${endTime}</p>
                <p><strong>Cost:</strong> $${this.calculatedCost.toFixed(2)}</p>
            </div>
        `;
    }
    
    /**
     * Setup form validation
     */
    setupValidation() {
        const forms = document.querySelectorAll('.booking-form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    }
    
    /**
     * Validate form
     */
    validateForm(form) {
        let isValid = true;
        
        // Required fields
        const requiredFields = ['court_id', 'booking_date', 'start_time', 'end_time'];
        requiredFields.forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field && !field.value.trim()) {
                this.showFieldError(field, 'This field is required');
                isValid = false;
            }
        });
        
        // Date validation
        const dateField = form.querySelector('[name="booking_date"]');
        if (dateField && dateField.value) {
            const selectedDate = new Date(dateField.value);
            const today = new Date();
            today.setHours(0, 0, 0, 0);
            
            if (selectedDate < today) {
                this.showFieldError(dateField, 'Cannot book dates in the past');
                isValid = false;
            }
        }
        
        // Time validation
        const startTimeField = form.querySelector('[name="start_time"]');
        const endTimeField = form.querySelector('[name="end_time"]');
        
        if (startTimeField && endTimeField && startTimeField.value && endTimeField.value) {
            if (startTimeField.value >= endTimeField.value) {
                this.showFieldError(endTimeField, 'End time must be after start time');
                isValid = false;
            }
        }
        
        return isValid;
    }
    
    /**
     * Validate individual field
     */
    validateField(field) {
        const value = field.value.trim();
        
        // Clear previous errors
        this.clearFieldError(field);
        
        // Required validation
        if (field.required && !value) {
            this.showFieldError(field, 'This field is required');
            return false;
        }
        
        // Field-specific validation
        switch (field.name) {
            case 'booking_date':
                if (value) {
                    const selectedDate = new Date(value);
                    const today = new Date();
                    today.setHours(0, 0, 0, 0);
                    
                    if (selectedDate < today) {
                        this.showFieldError(field, 'Cannot book dates in the past');
                        return false;
                    }
                }
                break;
                
            case 'start_time':
            case 'end_time':
                if (value && !/^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/.test(value)) {
                    this.showFieldError(field, 'Please enter a valid time (HH:MM)');
                    return false;
                }
                break;
        }
        
        return true;
    }
    
    /**
     * Show field error
     */
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'invalid-feedback';
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
    }
    
    /**
     * Clear field error
     */
    clearFieldError(field) {
        field.classList.remove('is-invalid');
        
        const errorElement = field.parentNode.querySelector('.invalid-feedback');
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    /**
     * Clear time selection
     */
    clearTimeSelection() {
        document.querySelectorAll('.time-slot.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        const startInput = document.querySelector('[name="start_time"]');
        const endInput = document.querySelector('[name="end_time"]');
        
        if (startInput) startInput.value = '';
        if (endInput) endInput.value = '';
        
        this.updateCostDisplay(null);
    } }