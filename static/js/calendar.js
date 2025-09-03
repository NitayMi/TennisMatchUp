
/**
 * Tennis Calendar JavaScript Module
 */

/**
 * Tennis Calendar JavaScript Module
 */
class TennisCalendar {
    constructor() {
        console.log('TennisCalendar constructor called');
        console.log('window.bookingsData:', window.bookingsData);
        
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
            bookingDot.textContent = `${booking.start_time} ${booking.court.name}`;
            bookingDot.title = `${booking.court.name} at ${booking.start_time} - ${booking.end_time}`;
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
// -------------------
// selectDate(day) {
//     console.log('Day clicked:', day);
    
//     if (day.hasBookings) {
//         this.showBookingDetails(day);
//     } else if (day.isCurrentMonth) {
//         // פשוט נעביר לעמוד עם התאריך
//         const dateStr = this.formatDateKey(day.date);
//         console.log('Navigating to book-court with date:', dateStr);
//         window.location.href = `/player/book-court?date=${dateStr}`;
//     }
// }

// -----------------------עד כאן ישן
selectDate(day) {
    console.log('Day clicked:', day);
    
    if (day.hasBookings) {
        // Show booking details for days with existing bookings
        this.showBookingDetails(day);
    } else if (day.isCurrentMonth) {
        // Show booking modal for empty days
        this.showBookingModal(day);
    }
}

// הוסף פונקציה חדשה:
showBookingModal(day) {
    const dateStr = this.formatDateKey(day.date);
    const formattedDate = day.date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    // Create modal HTML
    const modalHtml = `
        <div class="modal fade" id="quickBookingModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-calendar-plus me-2"></i>
                            Book Court for ${formattedDate}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body p-0">
                        <div id="bookingFrameContainer" style="height: 70vh;">
                            <div class="d-flex justify-content-center align-items-center h-100">
                                <div class="spinner-border text-tennis" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <span class="ms-2">Loading booking options...</span>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <a href="/player/book-court?date=${dateStr}" class="btn btn-tennis" target="_blank">
                            <i class="fas fa-external-link-alt me-1"></i>Open in New Tab
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('quickBookingModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('quickBookingModal'));
    modal.show();
    
    // Load content after modal is shown
    setTimeout(() => {
        this.loadBookingContent(dateStr);
    }, 300);
}

// הוסף פונקציה נוספת:
loadBookingContent(dateStr) {
    const container = document.getElementById('bookingFrameContainer');
    if (!container) return;
    
    // Load the booking page content via fetch
    fetch(`/player/book-court?date=${dateStr}`)
        .then(response => response.text())
        .then(html => {
            // Extract main content from the response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const mainContent = doc.querySelector('main') || doc.querySelector('.container');
            
            if (mainContent) {
                container.innerHTML = mainContent.innerHTML;
                
                // Re-initialize any JavaScript for the loaded content
                this.initializeBookingForm();
            } else {
                container.innerHTML = `
                    <div class="text-center p-4">
                        <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                        <h5>Unable to load booking form</h5>
                        <p>Please use the "Open in New Tab" button instead.</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading booking content:', error);
            container.innerHTML = `
                <div class="text-center p-4">
                    <i class="fas fa-exclamation-triangle fa-3x text-warning mb-3"></i>
                    <h5>Error loading booking form</h5>
                    <p>Please try opening in a new tab.</p>
                </div>
            `;
        });
}

// הוסף פונקציה אחרונה:
initializeBookingForm() {
    // Re-initialize any JavaScript needed for the booking form
    const bookingButtons = document.querySelectorAll('.book-court-btn');
    bookingButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            // Handle booking within the modal
            const courtId = e.target.dataset.courtId;
            const courtName = e.target.dataset.courtName;
            console.log('Court selected:', courtId, courtName);
            // Add your booking logic here
        });
    });
}

// --------------עד כאן חדש לא מופרד MVC

    showBookingDetails(day) {
        // Simple alert for now - can enhance later
        let details = `${day.date.toDateString()}\n\n`;
        day.bookings.forEach(booking => {
            details += `${booking.court.name}\n${booking.start_time} - ${booking.end_time}\nStatus: ${booking.status}\n\n`;
        });
        alert(details);
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
            'rejected': 'secondary'
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