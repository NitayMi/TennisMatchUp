/**
 * TennisMatchUp - Owner Court Calendar Management
 * Extracted from template to maintain proper MVC separation
 */

let calendar;
let allEvents = [];
let currentCourts = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeCalendar();
    loadCalendarData();
});

function initializeCalendar() {
    const calendarEl = document.getElementById('calendar');
    
    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: false, // We have custom toolbar
        height: 'auto',
        firstDay: 1, // Monday
        businessHours: {
            daysOfWeek: [1, 2, 3, 4, 5, 6, 0], // Monday - Sunday
            startTime: '08:00',
            endTime: '22:00'
        },
        slotMinTime: '06:00',
        slotMaxTime: '23:00',
        expandRows: true,
        dayMaxEvents: 3,
        moreLinkClick: 'popover',
        eventClick: function(info) {
            showBookingDetails(info.event);
        },
        datesSet: function(info) {
            updateCalendarTitle(info);
            updateQuickStats();
        },
        eventDidMount: function(info) {
            // Add tooltip
            info.el.setAttribute('title', 
                `${info.event.title}\n${info.event.extendedProps.court_name}\n${info.event.extendedProps.time_range}`
            );
        }
    });
    
    calendar.render();
}

async function loadCalendarData() {
    try {
        // Load bookings data
        const response = await fetch('/api/calendar/events');
        const data = await response.json();
        
        if (data.success) {
            allEvents = data.events.map(event => ({
                id: event.id,
                title: event.title,
                start: event.start,
                end: event.end,
                backgroundColor: event.color,
                borderColor: event.color,
                textColor: '#fff',
                extendedProps: {
                    status: event.status,
                    player_name: event.player_name,
                    court_name: event.court_name,
                    court_id: event.court_id,
                    cost: event.cost,
                    time_range: `${new Date(event.start).toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'})} - ${new Date(event.end).toLocaleTimeString('en-US', {hour: '2-digit', minute: '2-digit'})}`
                }
            }));
            
            // Extract unique courts for filter
            currentCourts = [...new Set(data.events.map(e => ({
                id: e.court_id,
                name: e.court_name
            })))];
            
            populateCourtFilter();
            calendar.removeAllEvents();
            calendar.addEventSource(allEvents);
            updateQuickStats();
        } else {
            console.error('Failed to load calendar data:', data.error);
            showError('Failed to load calendar data');
        }
    } catch (error) {
        console.error('Error loading calendar data:', error);
        showError('Error loading calendar data');
    }
}

function populateCourtFilter() {
    const courtFilter = document.getElementById('court-filter');
    courtFilter.innerHTML = '<option value="">All Courts</option>';
    
    currentCourts.forEach(court => {
        const option = document.createElement('option');
        option.value = court.id;
        option.textContent = court.name;
        courtFilter.appendChild(option);
    });
}

function filterByGroup() {
    const selectedCourtId = document.getElementById('court-filter').value;
    
    calendar.removeAllEvents();
    
    if (selectedCourtId) {
        const filteredEvents = allEvents.filter(event => 
            event.extendedProps.court_id == selectedCourtId
        );
        calendar.addEventSource(filteredEvents);
    } else {
        calendar.addEventSource(allEvents);
    }
    
    updateQuickStats();
}

function updateCalendarTitle(info) {
    const titleEl = document.getElementById('calendar-title');
    if (titleEl) {
        titleEl.textContent = info.view.title;
    }
}

function updateQuickStats() {
    const visibleEvents = calendar.getEvents();
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    
    // Filter events for current month
    const monthlyEvents = visibleEvents.filter(event => {
        const eventDate = new Date(event.start);
        return eventDate.getMonth() === currentMonth && eventDate.getFullYear() === currentYear;
    });
    
    const confirmedBookings = monthlyEvents.filter(e => e.extendedProps.status === 'confirmed');
    const pendingBookings = monthlyEvents.filter(e => e.extendedProps.status === 'pending');
    
    // Update counters
    document.getElementById('confirmed-count').textContent = confirmedBookings.length;
    document.getElementById('pending-count').textContent = pendingBookings.length;
    
    // Calculate revenue
    const totalRevenue = confirmedBookings.reduce((sum, event) => 
        sum + (event.extendedProps.cost || 0), 0
    );
    document.getElementById('revenue-total').textContent = `${totalRevenue.toFixed(0)}`;
    
    // Calculate utilization (simplified)
    const totalPossibleSlots = currentCourts.length * 30 * 14; // courts * days * hours per day
    const bookedSlots = confirmedBookings.length * 2; // average 2 hours per booking
    const utilization = totalPossibleSlots > 0 ? (bookedSlots / totalPossibleSlots * 100) : 0;
    document.getElementById('utilization-rate').textContent = `${utilization.toFixed(0)}%`;
}

function showBookingDetails(event) {
    const modalEl = document.getElementById('bookingModal');
    const detailsEl = document.getElementById('booking-details');
    const actionsEl = document.getElementById('booking-actions');
    
    const props = event.extendedProps;
    const startTime = new Date(event.start);
    const endTime = new Date(event.end);
    
    // Format booking details
    detailsEl.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fas fa-user me-2"></i>Player Information</h6>
                <p class="mb-1"><strong>Name:</strong> ${props.player_name}</p>
                <p class="mb-3"><strong>Status:</strong> 
                    <span class="badge" style="background-color: ${event.backgroundColor}">
                        ${props.status.charAt(0).toUpperCase() + props.status.slice(1)}
                    </span>
                </p>
                
                <h6><i class="fas fa-tennis-ball me-2"></i>Court Information</h6>
                <p class="mb-1"><strong>Court:</strong> ${props.court_name}</p>
                <p class="mb-3"><strong>Time:</strong> ${props.time_range}</p>
            </div>
            <div class="col-md-6">
                <h6><i class="fas fa-calendar me-2"></i>Booking Details</h6>
                <p class="mb-1"><strong>Date:</strong> ${startTime.toLocaleDateString()}</p>
                <p class="mb-1"><strong>Duration:</strong> ${Math.round((endTime - startTime) / (1000 * 60 * 60))} hours</p>
                <p class="mb-3"><strong>Cost:</strong> ${(props.cost || 0).toFixed(2)}</p>
                
                <h6><i class="fas fa-info-circle me-2"></i>Actions</h6>
                <p class="text-muted small">
                    ${props.status === 'pending' ? 'You can approve or reject this booking request.' :
                      props.status === 'confirmed' ? 'This booking is confirmed. You can cancel if needed.' :
                      'This booking has been processed.'}
                </p>
            </div>
        </div>
    `;
    
    // Set up action buttons based on status
    let actionButtons = '';
    if (props.status === 'pending') {
        actionButtons = `
            <button type="button" class="btn btn-success" onclick="updateBookingStatus('${event.id}', 'confirmed')">
                <i class="fas fa-check me-2"></i>Approve
            </button>
            <button type="button" class="btn btn-danger" onclick="updateBookingStatus('${event.id}', 'rejected')">
                <i class="fas fa-times me-2"></i>Reject
            </button>
        `;
    } else if (props.status === 'confirmed') {
        actionButtons = `
            <button type="button" class="btn btn-warning" onclick="updateBookingStatus('${event.id}', 'cancelled')">
                <i class="fas fa-ban me-2"></i>Cancel Booking
            </button>
        `;
    }
    
    actionsEl.innerHTML = actionButtons;
    
    // Show modal
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
}

async function updateBookingStatus(bookingId, newStatus) {
    try {
        const reason = newStatus === 'rejected' || newStatus === 'cancelled' ? 
            prompt(`Please provide a reason for ${newStatus}:`) : '';
        
        if ((newStatus === 'rejected' || newStatus === 'cancelled') && !reason) {
            return; // User cancelled
        }
        
        const response = await fetch(`/owner/booking/${bookingId}/${newStatus === 'confirmed' ? 'approve' : newStatus === 'rejected' ? 'reject' : 'cancel'}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: reason ? `reason=${encodeURIComponent(reason)}` : ''
        });
        
        if (response.ok) {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('bookingModal'));
            modal.hide();
            
            // Reload calendar data
            await loadCalendarData();
            
            showSuccess(`Booking ${newStatus} successfully!`);
        } else {
            showError(`Failed to ${newStatus} booking`);
        }
    } catch (error) {
        console.error('Error updating booking status:', error);
        showError('Error updating booking status');
    }
}

function showError(message) {
    // Simple error notification - in production, use a proper notification library
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 5000);
}

function showSuccess(message) {
    // Simple success notification
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.parentNode.removeChild(alertDiv);
        }
    }, 3000);
}

// Refresh calendar every 5 minutes
setInterval(loadCalendarData, 5 * 60 * 1000);