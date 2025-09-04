/**
 * Calendar Data Management for TennisMatchUp
 * Handles calendar events, booking data, and user interactions
 */

class CalendarDataManager {
    constructor() {
        this.currentDate = new Date();
        this.selectedDate = null;
        this.bookingsData = {};
        this.events = [];
        this.viewMode = 'month'; // 'month', 'week', 'day'
        this.isLoading = false;
        
        this.init();
    }
    
    init() {
        this.loadBookingsData();
        this.setupEventListeners();
        this.renderCalendar();
    }
    
    /**
     * Load bookings data from the server
     */
    async loadBookingsData(startDate = null, endDate = null) {
        this.isLoading = true;
        this.showLoadingState();
        
        try {
            // Calculate date range if not provided
            if (!startDate) {
                const start = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth(), 1);
                const end = new Date(this.currentDate.getFullYear(), this.currentDate.getMonth() + 1, 0);
                startDate = this.formatDate(start);
                endDate = this.formatDate(end);
            }
            
            const response = await fetch(`/api/calendar/events?start=${startDate}&end=${endDate}`);
            const data = await response.json();
            
            if (data.success) {
                this.events = data.events;
                this.processEventsData();
                this.renderCalendar();
            } else {
                this.showError('Failed to load calendar events');
            }
        } catch (error) {
            console.error('Error loading calendar data:', error);
            this.showError('Error loading calendar data');
        } finally {
            this.isLoading = false;
            this.hideLoadingState();
        }
    }
    
    /**
     * Process events data into a more manageable format
     */
    processEventsData() {
        this.bookingsData = {};
        
        this.events.forEach(event => {
            const eventDate = new Date(event.start).toDateString();
            
            if (!this.bookingsData[eventDate]) {
                this.bookingsData[eventDate] = [];
            }
            
            this.bookingsData[eventDate].push({
                id: event.id,
                title: event.title,
                start: event.start,
                end: event.end,
                status: event.status,
                color: event.color,
                courtName: event.court_name || event.courtName,
                location: event.location,
                cost: event.cost,
                playerName: event.player_name || event.playerName
            });
        });
        
        // Sort events by start time for each date
        Object.keys(this.bookingsData).forEach(date => {
            this.bookingsData[date].sort((a, b) => new Date(a.start) - new Date(b.start));
        });
    }
    
    /**
     * Setup event listeners for calendar interactions
     */
    setupEventListeners() {
        // Navigation buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('calendar-prev')) {
                this.navigateMonth(-1);
            } else if (e.target.classList.contains('calendar-next')) {
                this.navigateMonth(1);
            } else if (e.target.classList.contains('calendar-today')) {
                this.goToToday();
            }
        });
        
        // Day selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.calendar-day')) {
                const dayElement = e.target.closest('.calendar-day');
                const dateStr = dayElement.dataset.date;
                
                if (dateStr) {
                    this.selectDate(new Date(dateStr));
                }
            }
        });
        
        // Event clicks
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('calendar-event')) {
                const eventId = e.target.dataset.eventId;
                this.showEventDetails(eventId);
            }
        });
        
        // View switcher
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('view-btn')) {
                const view = e.target.dataset.view;
                this.changeView(view);
            }
        });
        
        // Booking form submission
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('booking-form')) {
                e.preventDefault();
                this.handleBookingSubmit(e.target);
            }
        });
        
        // Real-time updates (if WebSocket is available)
        if (window.WebSocket) {
            this.setupWebSocketConnection();
        }
    }
    
    /**
     * Navigate calendar months
     */
    navigateMonth(direction) {
        this.currentDate.setMonth(this.currentDate.getMonth() + direction);
        this.loadBookingsData();
    }
    
    /**
     * Go to today's date
     */
    goToToday() {
        this.currentDate = new Date();
        this.selectedDate = new Date();
        this.loadBookingsData();
    }
    
    /**
     * Select a specific date
     */
    selectDate(date) {
        this.selectedDate = date;
        this.renderCalendar();
        this.showDayDetails(date);
    }
    
    /**
     * Change calendar view mode
     */
    changeView(view) {
        this.viewMode = view;
        this.updateViewButtons();
        this.renderCalendar();
    }
    
    /**
     * Render the calendar based on current view mode
     */
    renderCalendar() {
        switch (this.viewMode) {
            case 'month':
                this.renderMonthView();
                break;
            case 'week':
                this.renderWeekView();
                break;
            case 'day':
                this.renderDayView();
                break;
        }
        
        this.updateCalendarHeader();
    }
    
    /**
     * Render month view calendar
     */
    renderMonthView() {
        const container = document.getElementById('calendar-grid');
        if (!container) return;
        
        container.innerHTML = '';
        
        // Add day headers
        const dayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
        dayHeaders.forEach(day => {
            const headerElement = document.createElement('div');
            headerElement.className = 'calendar-day-header';
            headerElement.textContent = day;
            container.appendChild(headerElement);
        });
        
        // Calculate calendar days
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());
        
        // Render calendar days
        for (let i = 0; i < 42; i++) { // 6 weeks * 7 days
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            
            const dayElement = this.createDayElement(currentDate, month);
            container.appendChild(dayElement);
        }
    }
    
    /**
     * Create a calendar day element
     */
    createDayElement(date, currentMonth) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        dayElement.dataset.date = this.formatDate(date);
        
        // Add classes for different states
        if (date.getMonth() !== currentMonth) {
            dayElement.classList.add('other-month');
        }
        
        if (this.isToday(date)) {
            dayElement.classList.add('today');
        }
        
        if (this.selectedDate && this.isSameDay(date, this.selectedDate)) {
            dayElement.classList.add('selected');
        }
        
        // Add day number
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = date.getDate();
        dayElement.appendChild(dayNumber);
        
        // Add events for this day
        const dateStr = date.toDateString();
        if (this.bookingsData[dateStr]) {
            const events = this.bookingsData[dateStr];
            const maxVisible = 3;
            
            events.slice(0, maxVisible).forEach(event => {
                const eventElement = this.createEventElement(event);
                dayElement.appendChild(eventElement);
            });
            
            // Show "more events" indicator if needed
            if (events.length > maxVisible) {
                const moreElement = document.createElement('div');
                moreElement.className = 'more-events';
                moreElement.textContent = `+${events.length - maxVisible} more`;
                moreElement.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showAllEventsForDay(date);
                });
                dayElement.appendChild(moreElement);
            }
        }
        
        return dayElement;
    }
    
    /**
     * Create an event element
     */
    createEventElement(event) {
        const eventElement = document.createElement('div');
        eventElement.className = `calendar-event ${event.status}`;
        eventElement.style.backgroundColor = event.color;
        eventElement.dataset.eventId = event.id;
        
        // Format time
        const startTime = new Date(event.start).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        eventElement.textContent = `${startTime} ${event.title}`;
        eventElement.title = `${event.title} - ${startTime}`;
        
        return eventElement;
    }
    
    /**
     * Show details for a specific day
     */
    showDayDetails(date) {
        const dateStr = date.toDateString();
        const events = this.bookingsData[dateStr] || [];
        
        // Update day details panel (if exists)
        const detailsPanel = document.getElementById('day-details');
        if (detailsPanel) {
            detailsPanel.innerHTML = this.renderDayDetailsHTML(date, events);
        }
        
        // Show booking form for selected date
        this.showBookingForm(date);
    }
    
    /**
     * Show booking form for a specific date
     */
    showBookingForm(date) {
        const bookingForm = document.getElementById('booking-form');
        if (bookingForm && date) {
            // Set the date in the form
            const dateInput = bookingForm.querySelector('[name="booking_date"]');
            if (dateInput) {
                dateInput.value = this.formatDate(date);
            }
            
            // Load available courts and time slots
            this.loadAvailableSlots(date);
        }
    }
    
    /**
     * Load available time slots for a date
     */
    async loadAvailableSlots(date) {
        try {
            const response = await fetch(`/api/courts/availability?date=${this.formatDate(date)}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderTimeSlots(data.availability);
            }
        } catch (error) {
            console.error('Error loading time slots:', error);
        }
    }
    
    /**
     * Render time slots in the booking form
     */
    renderTimeSlots(availability) {
        const slotsContainer = document.getElementById('time-slots');
        if (!slotsContainer) return;
        
        slotsContainer.innerHTML = '';
        
        // Generate hourly slots from 8 AM to 10 PM
        for (let hour = 8; hour < 22; hour++) {
            const timeSlot = document.createElement('div');
            timeSlot.className = 'time-slot';
            timeSlot.dataset.time = `${hour.toString().padStart(2, '0')}:00`;
            
            const isAvailable = this.isTimeSlotAvailable(hour, availability);
            timeSlot.classList.add(isAvailable ? 'available' : 'booked');
            
            timeSlot.textContent = `${hour.toString().padStart(2, '0')}:00`;
            
            if (isAvailable) {
                timeSlot.addEventListener('click', () => {
                    this.selectTimeSlot(timeSlot);
                });
            }
            
            slotsContainer.appendChild(timeSlot);
        }
    }
    
    /**
     * Check if a time slot is available
     */
    isTimeSlotAvailable(hour, availability) {
        // Check against existing bookings
        const selectedDateStr = this.selectedDate?.toDateString();
        const events = this.bookingsData[selectedDateStr] || [];
        
        return !events.some(event => {
            const eventStart = new Date(event.start);
            const eventEnd = new Date(event.end);
            const slotTime = hour;
            
            return slotTime >= eventStart.getHours() && slotTime < eventEnd.getHours();
        });
    }
    
    /**
     * Select a time slot
     */
    selectTimeSlot(slotElement) {
        // Remove previous selection
        document.querySelectorAll('.time-slot.selected').forEach(slot => {
            slot.classList.remove('selected');
        });
        
        // Add selection to clicked slot
        slotElement.classList.add('selected');
        
        // Update form fields
        const startTime = slotElement.dataset.time;
        const startHour = parseInt(startTime.split(':')[0]);
        const endTime = `${(startHour + 1).toString().padStart(2, '0')}:00`;
        
        const form = document.getElementById('booking-form');
        if (form) {
            const startInput = form.querySelector('[name="start_time"]');
            const endInput = form.querySelector('[name="end_time"]');
            
            if (startInput) startInput.value = startTime;
            if (endInput) endInput.value = endTime;
            
            // Calculate and display cost
            this.calculateBookingCost();
        }
    }
    
    /**
     * Calculate booking cost
     */
    async calculateBookingCost() {
        const form = document.getElementById('booking-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const data = {
            court_id: formData.get('court_id'),
            start_time: formData.get('start_time'),
            end_time: formData.get('end_time')
        };
        
        if (!data.court_id || !data.start_time || !data.end_time) {
            return;
        }
        
        try {
            const response = await fetch('/api/calculate-cost', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayBookingCost(result);
            }
        } catch (error) {
            console.error('Error calculating cost:', error);
        }
    }
    
    /**
     * Display booking cost in the form
     */
    displayBookingCost(costData) {
        const costDisplay = document.getElementById('booking-cost');
        if (costDisplay) {
            costDisplay.innerHTML = `
                <div class="booking-summary">
                    <div class="summary-row">
                        <span>Duration:</span>
                        <span>${costData.duration_hours} hour(s)</span>
                    </div>
                    <div class="summary-row">
                        <span>Rate:</span>
                        <span>$${costData.hourly_rate}/hour</span>
                    </div>
                    <div class="summary-row total">
                        <span>Total:</span>
                        <span>${costData.formatted_cost}</span>
                    </div>
                </div>
            `;
        }
    }
    
    /**
     * Handle booking form submission
     */
    async handleBookingSubmit(form) {
        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn.textContent;
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        
        try {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            const response = await fetch('/api/bookings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSuccessMessage('Booking submitted successfully!');
                form.reset();
                this.loadBookingsData(); // Refresh calendar
                this.closeBookingModal();
            } else {
                this.showErrorMessage(result.error || 'Booking failed');
            }
        } catch (error) {
            console.error('Booking submission error:', error);
            this.showErrorMessage('Network error occurred');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
    
    /**
     * Utility methods
     */
    formatDate(date) {
        return date.toISOString().split('T')[0];
    }
    
    isToday(date) {
        const today = new Date();
        return this.isSameDay(date, today);
    }
    
    isSameDay(date1, date2) {
        return date1.toDateString() === date2.toDateString();
    }
    
    showLoadingState() {
        const calendar = document.getElementById('calendar-container');
        if (calendar) {
            calendar.classList.add('loading');
        }
    }
    
    hideLoadingState() {
        const calendar = document.getElementById('calendar-container');
        if (calendar) {
            calendar.classList.remove('loading');
        }
    }
    
    showSuccessMessage(message) {
        this.showMessage(message, 'success');
    }
    
    showErrorMessage(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type) {
        // Create or update message element
        let messageEl = document.getElementById('calendar-message');
        if (!messageEl) {
            messageEl = document.createElement('div');
            messageEl.id = 'calendar-message';
            document.body.appendChild(messageEl);
        }
        
        messageEl.className = `alert alert-${type === 'error' ? 'danger' : 'success'}`;
        messageEl.textContent = message;
        messageEl.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 300px;
        `;
        
        // Auto hide after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.parentNode.removeChild(messageEl);
            }
        }, 5000);
    }
    
    updateCalendarHeader() {
        const headerTitle = document.getElementById('calendar-title');
        if (headerTitle) {
            const monthNames = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            
            headerTitle.textContent = `${monthNames[this.currentDate.getMonth()]} ${this.currentDate.getFullYear()}`;
        }
    }
    
    updateViewButtons() {
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.view === this.viewMode) {
                btn.classList.add('active');
            }
        });
    }
    
    /**
     * WebSocket connection for real-time updates
     */
    setupWebSocketConnection() {
        // Implementation would depend on WebSocket setup
        // This is a placeholder for real-time booking updates
    }
}

// Initialize calendar when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('calendar-container')) {
        window.calendarManager = new CalendarDataManager();
    }
});

// Export for use in other scripts
window.CalendarDataManager = CalendarDataManager;