/**
 * TennisMatchUp - Owner Booking Requests Management
 * Extracted from template to maintain proper MVC separation
 */

let allBookings = [];

document.addEventListener('DOMContentLoaded', function() {
    initializeBookings();
});

function initializeBookings() {
    // Store all booking rows for filtering
    allBookings = Array.from(document.querySelectorAll('.booking-row'));
    updateBulkActionVisibility();
}

function filterBookings() {
    const statusFilter = document.getElementById('status-filter').value;
    const courtFilter = document.getElementById('court-filter').value;
    const dateFilter = document.getElementById('date-filter').value;
    
    allBookings.forEach(row => {
        let showRow = true;
        
        // Status filter
        if (statusFilter && row.dataset.status !== statusFilter) {
            showRow = false;
        }
        
        // Court filter
        if (courtFilter && row.dataset.court !== courtFilter) {
            showRow = false;
        }
        
        // Date filter
        if (dateFilter && row.dataset.date !== dateFilter) {
            showRow = false;
        }
        
        // Show/hide row
        if (showRow) {
            row.classList.remove('filtered-out');
            row.style.display = '';
        } else {
            row.classList.add('filtered-out');
            row.style.display = 'none';
        }
    });
    
    updateBulkActionVisibility();
}

function clearFilters() {
    document.getElementById('status-filter').value = '';
    document.getElementById('court-filter').value = '';
    document.getElementById('date-filter').value = '';
    filterBookings();
}

function toggleSelectAll() {
    const selectAllBox = document.getElementById('select-all');
    const checkboxes = document.querySelectorAll('.booking-checkbox:not([style*="display: none"])');
    
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAllBox.checked;
    });
    
    updateBulkActionVisibility();
}

function updateBulkActionVisibility() {
    const checkboxes = document.querySelectorAll('.booking-checkbox:checked');
    const bulkApproveBtn = document.getElementById('bulk-approve-btn');
    
    if (checkboxes.length > 0) {
        bulkApproveBtn.style.display = 'block';
    } else {
        bulkApproveBtn.style.display = 'none';
    }
}

// Add event listeners to checkboxes
document.addEventListener('change', function(e) {
    if (e.target.classList.contains('booking-checkbox')) {
        updateBulkActionVisibility();
    }
});

async function updateBookingStatus(bookingId, action) {
    let reason = '';
    
    if (action === 'reject' || action === 'cancel') {
        reason = prompt(`Please provide a reason for ${action}ing this booking:`);
        if (!reason) return; // User cancelled
    }
    
    if (action === 'approve' && !confirm('Are you sure you want to approve this booking?')) {
        return;
    }
    
    try {
        const response = await fetch(`/owner/booking/${bookingId}/${action}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: reason ? `reason=${encodeURIComponent(reason)}` : ''
        });
        
        if (response.ok) {
            // Force complete page reload with cache busting
            window.location.href = window.location.pathname + '?updated=' + Date.now();
        } else {
            const errorText = await response.text();
            alert(`Failed to ${action} booking: ${errorText}`);
        }
    } catch (error) {
        console.error('Error updating booking status:', error);
        alert('An error occurred. Please try again.');
    }
}

async function bulkApprove() {
    const selectedCheckboxes = document.querySelectorAll('.booking-checkbox:checked');
    const bookingIds = Array.from(selectedCheckboxes).map(cb => cb.value);
    
    if (bookingIds.length === 0) {
        alert('Please select at least one booking to approve.');
        return;
    }
    
    if (!confirm(`Are you sure you want to approve ${bookingIds.length} booking(s)?`)) {
        return;
    }
    
    // Process each booking
    for (const bookingId of bookingIds) {
        try {
            await updateBookingStatus(bookingId, 'approve');
        } catch (error) {
            console.error(`Failed to approve booking ${bookingId}:`, error);
        }
    }
    
    location.reload();
}

async function approveAllPending() {
    const pendingBookings = document.querySelectorAll('[data-status="pending"]');
    
    if (pendingBookings.length === 0) {
        alert('No pending bookings to approve.');
        return;
    }
    
    if (!confirm(`Are you sure you want to approve all ${pendingBookings.length} pending booking(s)?`)) {
        return;
    }
    
    // Process each pending booking
    for (const row of pendingBookings) {
        const checkbox = row.querySelector('.booking-checkbox');
        if (checkbox) {
            try {
                await updateBookingStatus(checkbox.value, 'approve');
            } catch (error) {
                console.error(`Failed to approve booking ${checkbox.value}:`, error);
            }
        }
    }
    
    location.reload();
}