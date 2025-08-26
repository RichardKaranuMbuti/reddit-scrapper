// static/js/components.js
// Reusable components and utilities

// Toast notifications
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toastContainer');
    const toastId = 'toast-' + Date.now();
    
    const bgClass = {
        'success': 'bg-success',
        'error': 'bg-danger', 
        'warning': 'bg-warning',
        'info': 'bg-info'
    }[type] || 'bg-info';
    
    const iconClass = {
        'success': 'bi-check-circle',
        'error': 'bi-exclamation-triangle',
        'warning': 'bi-exclamation-triangle', 
        'info': 'bi-info-circle'
    }[type] || 'bi-info-circle';
    
    const toastHTML = `
        <div class="toast ${bgClass} text-white" id="${toastId}" role="alert">
            <div class="toast-header ${bgClass} text-white border-0">
                <i class="${iconClass} me-2"></i>
                <strong class="me-auto">Reddit Job Scraper</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: duration });
    toast.show();
    
    // Remove from DOM after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Loading spinner controls
function showLoadingSpinner() {
    document.getElementById('loadingSpinner').style.display = 'block';
}

function hideLoadingSpinner() {
    document.getElementById('loadingSpinner').style.display = 'none';
}

// Bookmark management
let bookmarks = JSON.parse(localStorage.getItem('reddit-job-bookmarks') || '[]');

function bookmarkJob(url, title) {
    const bookmark = { url, title, timestamp: new Date().toISOString() };
    
    // Check if already bookmarked
    const existingIndex = bookmarks.findIndex(b => b.url === url);
    
    if (existingIndex >= 0) {
        // Remove bookmark
        bookmarks.splice(existingIndex, 1);
        showToast(`Removed "${title}" from bookmarks`, 'info');
    } else {
        // Add bookmark
        bookmarks.push(bookmark);
        showToast(`Added "${title}" to bookmarks`, 'success');
    }
    
    // Save to localStorage
    localStorage.setItem('reddit-job-bookmarks', JSON.stringify(bookmarks));
    updateBookmarksUI();
}

function isBookmarked(url) {
    return bookmarks.some(b => b.url === url);
}

function updateBookmarksUI() {
    const bookmarkCard = document.getElementById('bookmarksCard');
    const bookmarkCount = document.getElementById('bookmarkCount');
    
    if (bookmarks.length > 0) {
        bookmarkCard.style.display = 'block';
        if (bookmarkCount) bookmarkCount.textContent = bookmarks.length;
    } else {
        bookmarkCard.style.display = 'none';
    }
}

function showBookmarks() {
    if (bookmarks.length === 0) {
        showToast('No bookmarks saved', 'info');
        return;
    }
    
    // Filter current jobs to show only bookmarked ones
    const bookmarkedUrls = bookmarks.map(b => b.url);
    window.showBookmarksOnly = true;
    
    // Trigger filter update
    if (typeof applyFilters === 'function') {
        applyFilters();
    }
    
    showToast(`Showing ${bookmarks.length} bookmarked jobs`, 'info');
}

function clearBookmarks() {
    if (bookmarks.length === 0) {
        showToast('No bookmarks to clear', 'info');
        return;
    }
    
    if (confirm(`Are you sure you want to clear all ${bookmarks.length} bookmarks?`)) {
        bookmarks = [];
        localStorage.removeItem('reddit-job-bookmarks');
        updateBookmarksUI();
        showToast('All bookmarks cleared', 'success');
        
        // Reset bookmark filter if active
        window.showBookmarksOnly = false;
        if (typeof applyFilters === 'function') {
            applyFilters();
        }
    }
}

// Scraper controls
async function runScraper() {
    try {
        showLoadingSpinner();
        
        // Check current status first
        const statusResponse = await fetch('/api/scraper/status');
        const status = await statusResponse.json();
        
        if (status.is_running) {
            showToast('Scraper is already running', 'warning');
            return;
        }
        
        // Start scraper
        const response = await fetch('/api/scraper/run', { method: 'POST' });
        
        if (response.ok) {
            const result = await response.json();
            showToast('Scraper started successfully! This may take a few minutes.', 'success');
            
            // Update scraper status
            updateScraperStatus();
            
            // Show modal with progress
            showScraperModal();
            
        } else {
            throw new Error('Failed to start scraper');
        }
        
    } catch (error) {
        console.error('Error running scraper:', error);
        showToast('Failed to start scraper. Please try again.', 'error');
    } finally {
        hideLoadingSpinner();
    }
}

async function updateScraperStatus() {
    try {
        const response = await fetch('/api/scraper/status');
        const status = await response.json();
        
        const statusElement = document.getElementById('scraper-status');
        if (!statusElement) return;
        
        if (status.is_running) {
            statusElement.innerHTML = `
                <i class="bi bi-circle-fill text-warning me-1"></i>
                <small>Running...</small>
            `;
        } else {
            const lastRun = status.last_run ? new Date(status.last_run).toLocaleTimeString() : 'Never';
            statusElement.innerHTML = `
                <i class="bi bi-circle-fill text-success me-1"></i>
                <small>Last run: ${lastRun}</small>
            `;
        }
        
    } catch (error) {
        console.error('Error updating scraper status:', error);
        const statusElement = document.getElementById('scraper-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <i class="bi bi-circle-fill text-danger me-1"></i>
                <small>Error</small>
            `;
        }
    }
}

function showScraperModal() {
    const modal = document.getElementById('scraperModal');
    if (!modal) return;
    
    const modalBody = document.getElementById('scraperModalBody');
    modalBody.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary mb-3" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <h5>Scraper Running</h5>
            <p class="text-muted">The scraper is currently running. This process may take 5-15 minutes depending on the number of subreddits and posts.</p>
            <div class="progress mb-3">
                <div class="progress-bar progress-bar-striped progress-bar-animated" role="progressbar" style="width: 100%"></div>
            </div>
        </div>
        
        <div class="mt-3">
            <h6>What's happening:</h6>
            <ul class="list-unstyled">
                <li><i class="bi bi-1-circle me-2"></i>Scraping job posts from Reddit</li>
                <li><i class="bi bi-2-circle me-2"></i>Analyzing posts with AI</li>
                <li><i class="bi bi-3-circle me-2"></i>Saving results to database</li>
                <li><i class="bi bi-4-circle me-2"></i>Updating dashboard</li>
            </ul>
        </div>
        
        <div class="alert alert-info mt-3">
            <i class="bi bi-info-circle me-2"></i>
            <strong>Tip:</strong> You can close this modal and continue using the dashboard. 
            The scraper will run in the background.
        </div>
    `;
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    // Poll for completion
    const checkInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/scraper/status');
            const status = await response.json();
            
            if (!status.is_running) {
                clearInterval(checkInterval);
                
                // Update modal content
                modalBody.innerHTML = `
                    <div class="text-center">
                        <i class="bi bi-check-circle-fill text-success fa-3x mb-3"></i>
                        <h5>Scraper Completed!</h5>
                        <p class="text-muted">Found ${status.jobs_scraped_last_run || 0} new job posts.</p>
                    </div>
                    
                    <div class="d-grid gap-2 mt-3">
                        <a href="/jobs" class="btn btn-primary">View New Jobs</a>
                        <button class="btn btn-outline-secondary" onclick="location.reload()">Refresh Dashboard</button>
                    </div>
                `;
                
                // Auto-close after 5 seconds
                setTimeout(() => {
                    bootstrapModal.hide();
                    location.reload(); // Refresh to show new data
                }, 5000);
            }
        } catch (error) {
            console.error('Error checking scraper status:', error);
            clearInterval(checkInterval);
        }
    }, 5000); // Check every 5 seconds
}

// Export functions
async function exportJobs(format) {
    try {
        showLoadingSpinner();
        
        // Get current filters
        const filters = getCurrentFilters ? getCurrentFilters() : {
            hours_back: 24,
            worth_checking_only: true
        };
        
        const queryParams = new URLSearchParams(filters);
        const response = await fetch(`/api/jobs/export/${format}?${queryParams}`);
        
        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }
        
        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Get filename from response headers or generate one
        const contentDisposition = response.headers.get('content-disposition');
        let filename = `reddit_jobs_${new Date().toISOString().split('T')[0]}.${format}`;
        
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.download = filename;
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

// Cleanup old jobs
async function cleanupOldJobs(days = 14) {
    if (!confirm(`Are you sure you want to delete jobs older than ${days} days?`)) {
        return;
    }
    
    try {
        showLoadingSpinner();
        
        const response = await fetch(`/api/scraper/cleanup?days=${days}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const result = await response.json();
            showToast(`Cleanup completed! Deleted ${result.deleted_jobs} old jobs.`, 'success');
        } else {
            throw new Error('Cleanup failed');
        }
        
    } catch (error) {
        console.error('Error cleaning up jobs:', error);
        showToast('Failed to cleanup old jobs', 'error');
    } finally {
        hideLoadingSpinner();
    }
}

// Filter management
function updateConfidenceValue() {
    const slider = document.getElementById('minConfidence');
    const display = document.getElementById('confidenceValue');
    if (slider && display) {
        display.textContent = slider.value;
    }
}

function applySearchPreset() {
    const preset = document.getElementById('searchPreset');
    const searchTerms = document.getElementById('searchTerms');
    
    if (preset && searchTerms && preset.value) {
        searchTerms.value = preset.value;
        preset.value = ''; // Reset preset selection
        
        // Trigger filter update
        if (typeof applyFilters === 'function') {
            applyFilters();
        }
    }
}

function applyFilters() {
    // This will be overridden by page-specific implementations
    console.log('Applying filters...');
    
    // Dispatch event for other components to listen to
    document.dispatchEvent(new CustomEvent('filtersChanged'));
}

// Utility functions
function debounceSearch() {
    // This will be overridden by page-specific implementations
    console.log('Search debounced');
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) {
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        return `${diffMinutes} minutes ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hours ago`;
    } else if (diffDays < 7) {
        return `${diffDays} days ago`;
    } else {
        return date.toLocaleDateString();
    }
}

function truncateText(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function getConfidenceBadgeClass(score) {
    if (score >= 80) return 'bg-success';
    if (score >= 60) return 'bg-warning';
    if (score >= 40) return 'bg-secondary';
    return 'bg-danger';
}

function showError(message) {
    const container = document.getElementById('jobsContainer') || 
                     document.getElementById('mainContent') || 
                     document.body;
    
    container.innerHTML = `
        <div class="text-center py-5">
            <i class="bi bi-exclamation-triangle fa-3x text-danger mb-3"></i>
            <h5 class="text-danger">Error</h5>
            <p class="text-muted">${message}</p>
            <button class="btn btn-outline-primary" onclick="location.reload()">
                <i class="bi bi-arrow-clockwise me-1"></i>Retry
            </button>
        </div>
    `;
}

// Initialize components when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Update bookmarks UI
    updateBookmarksUI();
    
    // Set up confidence slider
    const confidenceSlider = document.getElementById('minConfidence');
    if (confidenceSlider) {
        confidenceSlider.addEventListener('input', updateConfidenceValue);
        updateConfidenceValue(); // Set initial value
    }
    
    // Set up search preset
    const searchPreset = document.getElementById('searchPreset');
    if (searchPreset) {
        searchPreset.addEventListener('change', applySearchPreset);
    }
});

// Auto-update scraper status every 30 seconds
setInterval(updateScraperStatus, 30000);