/**
 * Shared Booking Proposal Form JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    const courtRadios = document.querySelectorAll('input[name="court_id"]');
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');
    const costPreview = document.getElementById('cost-preview');
    
    // Court selection styling
    courtRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            document.querySelectorAll('.court-option').forEach(card => {
                card.classList.remove('border-success');
            });
            if (this.checked) {
                this.closest('.court-option').classList.add('border-success');
                calculateCost();
            }
        });
    });
    
    // Time inputs
    startTimeInput.addEventListener('change', calculateCost);
    endTimeInput.addEventListener('change', calculateCost);
    
    function calculateCost() {
        const selectedCourt = document.querySelector('input[name="court_id"]:checked');
        const startTime = startTimeInput.value;
        const endTime = endTimeInput.value;
        
        if (selectedCourt && startTime && endTime) {
            // Get hourly rate from the selected court's data
            const courtCard = selectedCourt.closest('.card-body');
            const rateText = courtCard.querySelector('small').innerText;
            const hourlyRate = parseFloat(rateText.match(/₪(\d+)/)[1]);
            
            // Calculate duration
            const start = new Date(`1970-01-01T${startTime}:00`);
            const end = new Date(`1970-01-01T${endTime}:00`);
            const duration = (end - start) / (1000 * 60 * 60); // hours
            
            if (duration > 0) {
                const totalCost = hourlyRate * duration;
                const sharePerPlayer = totalCost / 2;
                
                document.getElementById('total-cost').textContent = `₪${totalCost.toFixed(2)}`;
                document.getElementById('your-share').textContent = `₪${sharePerPlayer.toFixed(2)}`;
                document.getElementById('partner-share').textContent = `₪${sharePerPlayer.toFixed(2)}`;
                
                costPreview.style.display = 'block';
            } else {
                costPreview.style.display = 'none';
            }
        }
    }
});