/**
 * Tennis Calendar JavaScript Module
 * Interactive calendar for booking management
 */

class TennisCalendar {
    constructor() {
        this.currentDate = new Date();
        this.currentMonth = this.currentDate.getMonth();
        this.currentYear = this.currentDate.getFullYear();
        this.bookings = window.bookingsData || [];
        this.selectedDate = null;
        this.modal = null;
        
        this.init();
    }

    init() {
        this.setupModal();
        this.setupEventListeners();
        this.processBookingsData();
        this.renderCalendar();
        this.updateTodaySchedule();
        this.updateMonthDisplay();
    }

    setupModal() {
        const modalElement = document.getElementById('bookingModal');
        if (modalElement) {
            this.modal = new bootstrap.Modal(modalElement);
        }
    }

    setupEventListeners() {
        // Navigation buttons
        document.getElementById('prevMonth')?.addEventListener('click', () => {
            this.navigateMonth(-1);
        });

        document.getElementById('nextMonth')?.addEventListener('click', () => {
            this.navigateMonth(1);
        });

        document.getElementById('todayBtn')?.addEventListener('click', () => {
            this.goToToday();
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
            
            switch(e.key) {
                case 'ArrowLeft':
                    this.navigateMonth(-1);
                    break;
                case 'ArrowRight':
                    this.navigateMonth(1);
                    break;
                case 'Home':
                    this.goToToday();
                    break;
            }
        });
    }

    processBookingsData() {
        // Convert date strings to Date objects and organize by date
        this.bookingsByDate = {};
        
        this.bookings.forEach(booking => {
            const dateKey = booking.booking_date;
            if (!this.bookingsByDate[dateKey]) {
                this.bookingsByDate[dateKey] = [];
            }
            this.bookingsByDate[dateKey].push(booking);
        });
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

    renderCalendar() {
        const grid = document.getElementById('calendarGrid');
        if (!grid) return;

        // Clear previous calendar
        grid.innerHTML = '<div class="calendar-loading"><i class="fas fa-spinner"></i></div>';

        // Calculate calendar layout
        const firstDay = new Date(this.currentYear, this.currentMonth, 1);
        const lastDay = new Date(this.currentYear, this.currentMonth + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const today = new Date();
        const isCurrentMonth = (date) => date.getMonth() === this.currentMonth;
        const isToday = (date) => 
            date.getDate() === today.getDate() &&
            date.getMonth() === today.getMonth() &&
            date.getFullYear() === today.getFullYear();

        // Generate calendar days
        const calendarDays = [];
        const currentDate = new Date(startDate);

        for (let i = 0; i < 42; i++) { // 6 weeks * 7 days
            const dateKey = this.formatDateKey(currentDate);
            const dayBookings = this.bookingsByDate[dateKey] || [];
            
            calendarDays.push({
                date: new Date(currentDate),
                dateKey: dateKey,
                dayNumber: currentDate.getDate(),
                bookings: dayBookings,
                isCurrentMonth: isCurrentMonth(currentDate),
                isToday: isToday(currentDate),
                hasBookings: dayBookings.length > 0
            });

            currentDate.setDate(currentDate.getDate() + 1);
        }

        // Render days
        setTimeout(() => {
            grid.innerHTML = '';
            calendarDays.forEach(day => {
                grid.appendChild(this.createDayElement(day));
            });
        }, 100);
    }

    createDayElement(day) {
        const dayElement = document.createElement('div');
        dayElement.className = 'calendar-day';
        
        if (!day.isCurrentMonth) dayElement.classList.add('other-month');
        if (day.isToday) dayElement.classList.add('today');
        if (day.hasBookings) dayElement.classList.add('has-bookings');

        dayElement.addEventListener('click', () => {
            this.selectDate(day);
        });

        // Day number
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = day.dayNumber;
        dayElement.appendChild(dayNumber);

        // Bookings container
        const bookingsContainer = document.createElement('div');
        bookingsContainer.className = 'day-bookings';

        // Show up to 3 bookings as dots
        const visibleBookings = day.bookings.slice(0, 3);
        visibleBookings.forEach(booking => {
            const bookingDot = document.createElement('span');
            bookingDot.className = `booking-dot ${booking.status}`;
            bookingDot.textContent = `${booking.start_time} ${booking.court.name}`;
            bookingDot.title = `${booking.court.name} at ${booking.start_time} - ${booking.end_time}`;
            bookingsContainer.appendChild(bookingDot);
        });

        dayElement.appendChild(bookingsContainer);

        // Booking count badge
        if (day.bookings.length > 3) {
            const countBadge = document.createElement('div');
            countBadge.className = 'booking-count';
            countBadge.textContent = `+${day.bookings.length - 3}`;
            dayElement.appendChild(countBadge);
        }

        return dayElement;
    }

    selectDate(day) {
        this.selectedDate = day;
        
        if (day.hasBookings) {
            this.showBookingDetails(day);
        } else if (day.isCurrentMonth) {
            // Could redirect to booking page with date pre-filled
            const dateParam = this.formatDateKey(day.date);
            window.location.href = `/player/book-court?date=${dateParam}`;
        }
    }

    showBookingDetails(day) {
        if (!this.modal) return;

        const modalContent = document.getElementById('modalContent');
        if (!modalContent) return;

        const dateString = day.date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        let content = `<h6 class="mb-3">${dateString}</h6>`;

        day.bookings.forEach(booking => {
            const statusColor = this.getStatusColor(booking.status);
            content += `
                <div class="booking-detail mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${booking.court.name}</strong>
                            <div class="text-muted small">
                                <i class="fas fa-clock me-1"></i>
                                ${booking.start_time} - ${booking.end_time}
                            </div>
                            <div class="text-muted small">
                                <i class="fas fa-map-marker-alt me-1"></i>
                                ${booking.court.location}
                            </div>
                            ${booking.notes ? `<div class="text-muted small mt-1">${booking.notes}</div>` : ''}
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${statusColor}">${booking.status}</span>
                            ${booking.total_cost ? `<div class="text-muted small mt-1">₪${Math.round(booking.total_cost)}</div>` : ''}
                        </div>
                    </div>
                </div>
            `;
        });

        modalContent.innerHTML = content;
        this.modal.show();
    }

    updateTodaySchedule() {
        const todayKey = this.formatDateKey(new Date());
        const todayBookings = this.bookingsByDate[todayKey] || [];
        
        const scheduleContainer = document.getElementById('todaySchedule');
        const countElement = document.getElementById('todayCount');
        
        if (countElement) {
            countElement.textContent = todayBookings.length;
        }

        if (!scheduleContainer) return;

        if (todayBookings.length === 0) {
            scheduleContainer.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-tennis-ball fa-2x mb-2"></i>
                    <p>No bookings today</p>
                    <a href="/player/book-court" class="btn btn-sm btn-tennis">Book a Court</a>
                </div>
            `;
            return;
        }

        let scheduleHtml = '';
        todayBookings.forEach(booking => {
            const statusColor = this.getStatusColor(booking.status);
            scheduleHtml += `
                <div class="d-flex justify-content-between align-items-center mb-2 p-2 border rounded">
                    <div>
                        <strong class="d-block">${booking.court.name}</strong>
                        <small class="text-muted">
                            ${booking.start_time} - ${booking.end_time}
                        </small>
                    </div>
                    <span class="badge bg-${statusColor}">${booking.status}</span>
                </div>
            `;
        });

        scheduleContainer.innerHTML = scheduleHtml;
    }

    getStatusColor(status) {
        const statusColors = {
            'confirmed': 'success',
            'pending': 'warning',
            'cancelled': 'danger',
            'rejected': 'secondary'
        };
        return statusColors[status] || 'secondary';
    }

    formatDateKey(date) {
        return date.toISOString().split('T')[0];
    }
}

// Initialize calendar when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TennisCalendar();
});

// Export for potential external use
window.TennisCalendar = TennisCalendar;