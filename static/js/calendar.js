/**
 * Tennis Calendar JavaScript Module
 */
class TennisCalendar {
    constructor() {
        console.log('TennisCalendar constructor called');
        console.log('window.bookingsData:', window.bookingsData);
        // Read data from HTML data attributes (MVC compliant)
        const calendarDataEl = document.getElementById('calendarData');
        if (calendarDataEl) {
            window.bookingsData = JSON.parse(calendarDataEl.dataset.bookings || '[]');
            window.currentPlayer = calendarDataEl.dataset.playerId || '0';
        }
        
        this.currentDate = new Date();
        this.currentMonth = this.currentDate.getMonth();
        this.currentYear = this.currentDate.getFullYear();
        
        // Make sure we have data
        this.bookings = window.bookingsData || [];
        console.log('this.bookings:', this.bookings);
        
        this.selectedDate = null;
        this.modal = null;
        
        this.init();
    }

    init() {
        console.log('Calendar initializing...', this.bookings);
        this.setupModal();
        this.setupEventListeners();
        this.processBookingsData();
        this.renderCalendar();
        this.updateTodaySchedule();
        this.updateMonthDisplay();
    }

    setupEventListeners() {
        const prevBtn = document.getElementById('prevMonth');
        const nextBtn = document.getElementById('nextMonth');
        const todayBtn = document.getElementById('todayBtn');
        
        if (prevBtn) prevBtn.addEventListener('click', () => this.navigateMonth(-1));
        if (nextBtn) nextBtn.addEventListener('click', () => this.navigateMonth(1));
        if (todayBtn) todayBtn.addEventListener('click', () => this.goToToday());
    }

    processBookingsData() {
        this.bookingsByDate = {};
        
        this.bookings.forEach(booking => {
            const dateKey = booking.booking_date;
            if (!this.bookingsByDate[dateKey]) {
                this.bookingsByDate[dateKey] = [];
            }
            this.bookingsByDate[dateKey].push(booking);
        });
        
        console.log('Processed bookings:', this.bookingsByDate);
    }

    renderCalendar() {
        const grid = document.getElementById('calendarGrid');
        if (!grid) {
            console.error('Calendar grid not found');
            return;
        }

        grid.innerHTML = '';

        const firstDay = new Date(this.currentYear, this.currentMonth, 1);
        const lastDay = new Date(this.currentYear, this.currentMonth + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const today = new Date();
        
        for (let i = 0; i < 42; i++) {
            const currentDate = new Date(startDate);
            currentDate.setDate(startDate.getDate() + i);
            
            const dateKey = this.formatDateKey(currentDate);
            const dayBookings = this.bookingsByDate[dateKey] || [];
            
            const dayElement = this.createDayElement({
                date: currentDate,
                dateKey: dateKey,
                dayNumber: currentDate.getDate(),
                bookings: dayBookings,
                isCurrentMonth: currentDate.getMonth() === this.currentMonth,
                isToday: this.isSameDate(currentDate, today),
                hasBookings: dayBookings.length > 0
            });
            
            grid.appendChild(dayElement);
        }
    }

    createDayElement(day) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        
        if (!day.isCurrentMonth) dayElement.classList.add('other-month');
        if (day.isToday) dayElement.classList.add('today');
        if (day.hasBookings) dayElement.classList.add('has-bookings');

        dayElement.addEventListener('click', () => this.selectDate(day));

        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = day.dayNumber;
        dayElement.appendChild(dayNumber);

        const bookingsContainer = document.createElement('div');
        bookingsContainer.className = 'day-bookings';

        const visibleBookings = day.bookings.slice(0, 3);
        visibleBookings.forEach(booking => {
            const bookingDot = document.createElement('span');
            bookingDot.className = `booking-dot ${booking.status}`;
            
            // UNIFIED DISPLAY LOGIC
            const displayData = this.getBookingDisplayData(booking);
            bookingDot.textContent = displayData.text;
            bookingDot.title = displayData.tooltip;
            
            bookingsContainer.appendChild(bookingDot);
        });

        dayElement.appendChild(bookingsContainer);

        if (day.bookings.length > 3) {
            const countBadge = document.createElement('div');
            countBadge.className = 'booking-count';
            countBadge.textContent = `+${day.bookings.length - 3}`;
            dayElement.appendChild(countBadge);
        }

        return dayElement;
    }

    getBookingDisplayData(booking) {
        if (booking.type === 'shared') {
            const partnerFirstName = booking.partner ? booking.partner.split(' ')[0] : 'Partner';
            return {
                text: `👥 ${booking.start_time}`,
                tooltip: `Shared with ${booking.partner} at ${booking.court.name} (${booking.start_time} - ${booking.end_time})`
            };
        } else {
            const courtShortName = booking.court.name.split(' ')[0];
            return {
                text: `🎾 ${booking.start_time}`,
                tooltip: `${booking.court.name} at ${booking.start_time} - ${booking.end_time}`
            };
        }
    }

selectDate(day) {
    console.log('Day clicked:', day);
    
    if (day.hasBookings) {
        // Show booking details for days with existing bookings
        this.showBookingDetails(day);
    } else if (day.isCurrentMonth) {
        // Navigate to booking page with pre-selected date (MVC compliant)
        const dateStr = this.formatDateKey(day.date);
        this.showQuickBookingModal(day.date, dateStr);
    }
}

showQuickBookingModal(date, dateStr) {
    // Use existing modal from template (MVC compliant)
    const modal = document.getElementById('quickBookingModal');
    const modalDateText = document.getElementById('modalDateText');
    const modalBookingLink = document.getElementById('modalBookingLink');
    
    if (modal && modalDateText && modalBookingLink) {
        // Set date text
        const formattedDate = date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        modalDateText.textContent = `Selected date: ${formattedDate}`;
        
        // Set booking link
        modalBookingLink.href = `/player/book-court?date=${dateStr}`;
        
        // Show modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    } else {
        // Fallback: direct navigation
        window.location.href = `/player/book-court?date=${dateStr}`;
    }
}


    showBookingDetails(day) {
        // Use existing booking details modal (MVC compliant)
        const modal = document.getElementById('bookingModal');
        const modalContent = document.getElementById('modalContent');
        
        if (modal && modalContent) {
            // Create clean booking details HTML
            const formattedDate = day.date.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long', 
                day: 'numeric'
            });
            
            let contentHtml = `<h6 class="mb-3">${formattedDate}</h6>`;
            day.bookings.forEach(booking => {
                const statusColor = this.getStatusColor(booking.status);
                
                // Different display for shared bookings
                let bookingTitle = booking.court.name;
                let extraInfo = '';
                
                if (booking.status === 'shared') {
                    bookingTitle = `👥 Shared: ${booking.court.name}`;
                    extraInfo = `<br><small class="text-info">With: ${booking.partner}</small>`;
                }
                
                contentHtml += `
                    <div class="card mb-2">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="card-title mb-1">${bookingTitle}</h6>
                                    <p class="card-text">
                                        <small class="text-muted">
                                            <i class="fas fa-clock me-1"></i>
                                            ${booking.start_time} - ${booking.end_time}
                                        </small>
                                        <br>
                                        <small class="text-muted">
                                            <i class="fas fa-map-marker-alt me-1"></i>
                                            ${booking.court.location || 'Location not specified'}
                                        </small>
                                        ${extraInfo}
                                    </p>
                                </div>
                                <span class="badge bg-${statusColor}">${booking.status}</span>
                            </div>
                        </div>
                    </div>
                `;
            });

            modalContent.innerHTML = contentHtml;
            
            // Show modal
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        } else {
            // Fallback to alert if modal not found
            let details = `${day.date.toDateString()}\n\n`;
            day.bookings.forEach(booking => {
                details += `${booking.court.name}\n${booking.start_time} - ${booking.end_time}\nStatus: ${booking.status}\n\n`;
            });
            alert(details);
        }
    }

    navigateMonth(direction) {
        this.currentMonth += direction;
        
        if (this.currentMonth > 11) {
            this.currentMonth = 0;
            this.currentYear++;
        } else if (this.currentMonth < 0) {
            this.currentMonth = 11;
            this.currentYear--;
        }
        
        this.renderCalendar();
        this.updateMonthDisplay();
    }

    goToToday() {
        const today = new Date();
        this.currentMonth = today.getMonth();
        this.currentYear = today.getFullYear();
        
        this.renderCalendar();
        this.updateMonthDisplay();
    }

    updateMonthDisplay() {
        const monthNames = [
            'January', 'February', 'March', 'April', 'May', 'June',
            'July', 'August', 'September', 'October', 'November', 'December'
        ];
        
        const displayElement = document.getElementById('monthDisplay');
        if (displayElement) {
            displayElement.textContent = `${monthNames[this.currentMonth]} ${this.currentYear}`;
        }
    }

    updateTodaySchedule() {
        const todayKey = this.formatDateKey(new Date());
        const todayBookings = this.bookingsByDate[todayKey] || [];
        
        const countElement = document.getElementById('todayCount');
        const scheduleContainer = document.getElementById('todaySchedule');
        
        if (countElement) {
            countElement.textContent = todayBookings.length;
        }

        if (scheduleContainer) {
            if (todayBookings.length === 0) {
                scheduleContainer.innerHTML = `
                    <div class="text-center text-muted">
                        <i class="fas fa-tennis-ball fa-2x mb-2"></i>
                        <p>No bookings today</p>
                        <a href="/player/book-court" class="btn btn-sm btn-tennis">Book a Court</a>
                    </div>
                `;
            } else {
                let scheduleHtml = '';
                todayBookings.forEach(booking => {
                    const statusColor = this.getStatusColor(booking.status);
                    scheduleHtml += `
                        <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                            <div>
                                <strong class="d-block">${booking.court.name}</strong>
                                <small class="text-muted">${booking.start_time} - ${booking.end_time}</small>
                            </div>
                            <span class="badge bg-${statusColor}">${booking.status}</span>
                        </div>
                    `;
                });
                scheduleContainer.innerHTML = scheduleHtml;
            }
        }
    }

    getStatusColor(status) {
        const statusColors = {
            'confirmed': 'success',
            'pending': 'warning',
            'cancelled': 'danger',
            'rejected': 'secondary',
            'shared': 'primary'  // הוספה חדשה
        };
        return statusColors[status] || 'secondary';
    }

    formatDateKey(date) {
        return date.toISOString().split('T')[0];
    }

    isSameDate(date1, date2) {
        return date1.getDate() === date2.getDate() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getFullYear() === date2.getFullYear();
    }

    setupModal() {
        const modalElement = document.getElementById('bookingModal');
        if (modalElement) {
            this.modal = new bootstrap.Modal(modalElement);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing calendar...');
    new TennisCalendar();
});