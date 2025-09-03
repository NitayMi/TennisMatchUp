// static/js/calendar.js - תיקון MVC נכון
// עבודה לפי עקרונות MVC - JavaScript רק לוגיקה, HTML בתבניות

class TennisCalendar {
    constructor() {
        this.currentDate = new Date();
        this.bookings = [];
        this.init();
    }

    init() {
        console.log('DOM loaded, initializing calendar...');
        
        // Load booking data from template
        if (window.bookingsData) {
            this.bookings = this.processBookingData(window.bookingsData);
            console.log('Processed bookings:', this.bookings);
        }
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Render initial calendar
        this.renderCalendar();
        
        console.log('Calendar initialization complete');
    }

    setupEventListeners() {
        const prevBtn = document.getElementById('prevMonth');
        const nextBtn = document.getElementById('nextMonth');
        const todayBtn = document.getElementById('todayBtn');

        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                this.currentDate.setMonth(this.currentDate.getMonth() - 1);
                this.renderCalendar();
            });
        }

        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                this.currentDate.setMonth(this.currentDate.getMonth() + 1);
                this.renderCalendar();
            });
        }

        if (todayBtn) {
            todayBtn.addEventListener('click', () => {
                this.currentDate = new Date();
                this.renderCalendar();
            });
        }
    }

    processBookingData(bookingsData) {
        const processed = {};
        bookingsData.forEach(booking => {
            const dateKey = booking.booking_date;
            if (!processed[dateKey]) {
                processed[dateKey] = [];
            }
            processed[dateKey].push(booking);
        });
        return processed;
    }

    renderCalendar() {
        this.updateHeader();
        this.renderCalendarGrid();
    }

    updateHeader() {
        const monthDisplay = document.getElementById('monthDisplay');
        if (monthDisplay) {
            const monthNames = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ];
            
            monthDisplay.textContent = `${monthNames[this.currentDate.getMonth()]} ${this.currentDate.getFullYear()}`;
        }
    }

    renderCalendarGrid() {
        const calendarGrid = document.getElementById('calendarGrid');
        if (!calendarGrid) {
            console.error('Calendar grid element not found');
            return;
        }

        // Clear existing calendar
        calendarGrid.innerHTML = '';

        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const firstDay = new Date(year, month, 1);
        const lastDay = new Date(year, month + 1, 0);
        const startDate = new Date(firstDay);
        startDate.setDate(startDate.getDate() - firstDay.getDay());

        const today = new Date();
        const isCurrentMonth = (today.getMonth() === month && today.getFullYear() === year);

        // Generate calendar cells
        for (let week = 0; week < 6; week++) {
            for (let day = 0; day < 7; day++) {
                const cellDate = new Date(startDate);
                cellDate.setDate(startDate.getDate() + (week * 7) + day);
                
                const cell = this.createCalendarCell(cellDate, month, today);
                calendarGrid.appendChild(cell);

                // Stop if we've reached the end of the month and filled the week
                if (cellDate.getMonth() !== month && cellDate > lastDay) {
                    if (day === 6) break;
                }
            }
            
            // Check if we need another week
            const checkDate = new Date(startDate);
            checkDate.setDate(startDate.getDate() + ((week + 1) * 7));
            if (checkDate.getMonth() !== month && checkDate > lastDay) {
                break;
            }
        }
    }

    createCalendarCell(cellDate, currentMonth, today) {
        const cell = document.createElement('div');
        cell.className = 'calendar-day';
        
        const isCurrentMonth = cellDate.getMonth() === currentMonth;
        const isToday = this.isSameDay(cellDate, today);
        const isPast = cellDate < today && !isToday;
        
        // Add classes based on cell state
        if (!isCurrentMonth) {
            cell.classList.add('other-month');
        }
        if (isToday) {
            cell.classList.add('today');
        }
        if (isPast) {
            cell.classList.add('past');
        }

        // Create day number
        const dayNumber = document.createElement('div');
        dayNumber.className = 'day-number';
        dayNumber.textContent = cellDate.getDate();
        cell.appendChild(dayNumber);

        // Check for bookings on this date
        const dateKey = this.formatDateKey(cellDate);
        const dayBookings = this.bookings[dateKey] || [];
        
        if (dayBookings.length > 0) {
            cell.classList.add('has-bookings');
            
            // Create booking indicators
            const bookingContainer = document.createElement('div');
            bookingContainer.className = 'booking-indicators';
            
            dayBookings.forEach((booking, index) => {
                if (index < 3) { // Show max 3 indicators
                    const indicator = document.createElement('div');
                    indicator.className = `booking-indicator status-${booking.status}`;
                    indicator.title = `${booking.court.name} - ${booking.start_time}`;
                    bookingContainer.appendChild(indicator);
                }
            });
            
            if (dayBookings.length > 3) {
                const moreIndicator = document.createElement('div');
                moreIndicator.className = 'booking-more';
                moreIndicator.textContent = `+${dayBookings.length - 3}`;
                bookingContainer.appendChild(moreIndicator);
            }
            
            cell.appendChild(bookingContainer);
        }

        // Add click event listener
        cell.addEventListener('click', () => {
            this.selectDate({
                date: new Date(cellDate),
                hasBookings: dayBookings.length > 0,
                bookings: dayBookings,
                isCurrentMonth: isCurrentMonth,
                isPast: isPast
            });
        });

        return cell;
    }

    selectDate(day) {
        console.log('Day clicked:', day);
        
        if (day.hasBookings) {
            // Show booking details for days with existing bookings
            this.showBookingDetails(day);
        } else if (day.isCurrentMonth && !day.isPast) {
            // Show booking modal for empty days (future dates only)
            this.showBookingModal(day);
        }
    }

    showBookingDetails(day) {
        // Populate existing modal with booking details
        const modal = document.getElementById('bookingModal');
        const modalContent = document.getElementById('modalContent');
        
        if (!modal || !modalContent) return;

        let html = '<div class="booking-details">';
        
        day.bookings.forEach(booking => {
            const statusClass = `status-${booking.status}`;
            html += `
                <div class="booking-item ${statusClass}">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h6 class="mb-0">${booking.court.name}</h6>
                        <span class="badge bg-${this.getStatusColor(booking.status)}">${booking.status}</span>
                    </div>
                    <p class="mb-1 text-muted">
                        <i class="fas fa-clock me-1"></i>
                        ${booking.start_time} - ${booking.end_time}
                    </p>
                    <p class="mb-1 text-muted">
                        <i class="fas fa-map-marker-alt me-1"></i>
                        ${booking.court.location}
                    </p>
                    ${booking.notes ? `<p class="mb-1 small"><i class="fas fa-sticky-note me-1"></i>${booking.notes}</p>` : ''}
                    <p class="mb-0 fw-bold">
                        <i class="fas fa-dollar-sign me-1"></i>
                        $${booking.total_cost}
                    </p>
                </div>
                <hr class="my-3">
            `;
        });
        
        html += '</div>';
        modalContent.innerHTML = html;
        
        // Show modal using Bootstrap
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    showBookingModal(day) {
        // Update the existing quick booking modal
        const quickModal = document.getElementById('quickBookingModal');
        const modalDateText = document.getElementById('modalDateText');
        const modalBookingLink = document.getElementById('modalBookingLink');
        
        if (!quickModal) return;

        const formattedDate = day.date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        const dateStr = this.formatDateKey(day.date);
        
        // Update modal content
        if (modalDateText) {
            modalDateText.textContent = `Book a court for ${formattedDate}`;
        }
        
        if (modalBookingLink) {
            // עברנו מעמוד redirect לפתיחת modal עם הזמנה
            modalBookingLink.href = `/player/book-court?date=${dateStr}`;
            modalBookingLink.textContent = `Book Court for ${formattedDate}`;
        }
        
        // Show modal
        const bootstrapModal = new bootstrap.Modal(quickModal);
        bootstrapModal.show();
    }

    getStatusColor(status) {
        const colors = {
            'confirmed': 'success',
            'pending': 'warning',
            'cancelled': 'danger',
            'rejected': 'secondary'
        };
        return colors[status] || 'secondary';
    }

    formatDateKey(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    isSameDay(date1, date2) {
        return date1.getDate() === date2.getDate() &&
               date1.getMonth() === date2.getMonth() &&
               date1.getFullYear() === date2.getFullYear();
    }
}

// Initialize calendar when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Calendar initializing...');
    window.tennisCalendar = new TennisCalendar();
});