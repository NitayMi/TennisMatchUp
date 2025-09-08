/**
 * Owner Statistics JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Set progress bar widths from data attributes
    const progressBars = document.querySelectorAll('.progress-bar-utilization');
    progressBars.forEach(bar => {
        const width = bar.getAttribute('data-width');
        bar.style.width = width + '%';
    });
});