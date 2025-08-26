// static/js/dashboard.js
// Main dashboard functionality

// Global variables
let currentStats = {};

// Override base functions for dashboard-specific behavior
function applyFilters() {
    console.log('Dashboard filters applied');
    // Dashboard doesn't have job filtering, just update stats
    if (typeof updateCurrentStats === 'function') {
        updateCurrentStats();
    }
}

async function updateCurrentStats() {
    try {
        const response = await fetch('/api/stats');
        if (response.ok) {
            currentStats = await response.json();
            
            // Update sidebar stats if they exist
            updateSidebarStats();
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

function updateSidebarStats() {
    const statsElement = document.getElementById('currentStats');
    if (!statsElement || !currentStats) return;
    
    statsElement.innerHTML = `
        <div class="d-flex justify-content-between mb-1">
            <small>Total Jobs:</small>
            <small class="fw-bold">${currentStats.total_jobs || 0}</small>
        </div>
        <div class="d-flex justify-content-between mb-1">
            <small>Analyzed:</small>
            <small class="fw-bold">${currentStats.analyzed_jobs || 0}</small>
        </div>
        <div class="d-flex justify-content-between mb-1">
            <small>Worth Checking:</small>
            <small class="fw-bold text-success">${currentStats.worth_checking || 0}</small>
        </div>
        <div class="d-flex justify-content-between">
            <small>Analysis Rate:</small>
            <small class="fw-bold">${currentStats.analysis_rate || 0}%</small>
        </div>
    `;
}

// Initialize dashboard-specific functionality
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard loaded');
    
    // Initialize bookmarks
    updateBookmarksUI();
    
    // Load initial stats
    updateCurrentStats();
    
    // Set up auto-refresh for stats
    setInterval(updateCurrentStats, 60000); // Every minute
});

// Dashboard-specific export function
async function exportJobs(format) {
    try {
        showLoadingSpinner();
        
        // Get basic filters (worth checking jobs from last 24h)
        const params = new URLSearchParams({
            hours_back: 24,
            worth_checking_only: true
        });
        
        const response = await fetch(`/api/jobs/export/${format}?${params}`);
        
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        
        // Create download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `reddit_jobs_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast(`Jobs exported as ${format.toUpperCase()}`, 'success');
        
    } catch (error) {
        console.error('Error exporting jobs:', error);
        showToast(`Failed to export jobs as ${format.toUpperCase()}`, 'error');
    } finally {
        hideLoadingSpinner();
    }
}