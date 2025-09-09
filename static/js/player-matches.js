/**
 * Player Matches JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Set quality fill widths from data attributes
    const qualityBars = document.querySelectorAll('.quality-fill');
    qualityBars.forEach(bar => {
        const width = bar.getAttribute('data-width');
        bar.style.width = width + '%';
    });
});