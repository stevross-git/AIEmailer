/**
 * AI Email Assistant - Main JavaScript File
 */

// Global variables
let authStatus = null;
let tokenRefreshTimer = null;

// Initialize when document is ready
$(document).ready(function() {
    // Check authentication status
    checkAuthStatus();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Setup global event handlers
    setupGlobalEventHandlers();
    
    // Setup auto token refresh
    setupTokenRefresh();
    
    // Initialize page-specific functionality
    initializePageFunctionality();
});

/**
 * Check user authentication status
 */
function checkAuthStatus() {
    $.get('/auth/status')
        .done(function(data) {
            authStatus = data;
            if (data.authenticated) {
                updateUserInterface(data.user);
                
                // Setup token refresh if needed
                if (!data.token_valid && data.needs_refresh) {
                    refreshAuthToken();
                }
            }
        })
        .fail(function() {
            console.warn('Failed to check authentication status');
        });
}

/**
 * Update UI based on user authentication status
 */
function updateUserInterface(user) {
    if (user) {
        // Update user display name in navbar
        $('.navbar .dropdown-toggle').html(`<i class="bi bi-person-circle"></i> ${user.display_name}`);
        
        // Show user-specific elements
        $('.auth-required').show();
        $('.guest-only').hide();
    }
}

/**
 * Refresh authentication token
 */
function refreshAuthToken() {
    $.post('/auth/refresh-token')
        .done(function(data) {
            if (data.success) {
                console.log('Token refreshed successfully');
                authStatus.token_valid = true;
            } else {
                console.warn('Token refresh failed, redirecting to login');
                window.location.href = '/auth/login';
            }
        })
        .fail(function() {
            console.error('Token refresh request failed');
            window.location.href = '/auth/login';
        });
}

/**
 * Setup automatic token refresh
 */
function setupTokenRefresh() {
    // Refresh token every 30 minutes
    tokenRefreshTimer = setInterval(function() {
        if (authStatus && authStatus.authenticated && authStatus.token_valid) {
            refreshAuthToken();
        }
    }, 1800000); // 30 minutes
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Setup global event handlers
 */
function setupGlobalEventHandlers() {
    // Handle AJAX errors globally
    $(document).ajaxError(function(event, xhr, settings, thrownError) {
        if (xhr.status === 401) {
            // Unauthorized - redirect to login
            window.location.href = '/auth/login';
        } else if (xhr.status === 403) {
            showAlert('danger', 'Access denied. You do not have permission for this action.');
        } else if (xhr.status >= 500) {
            showAlert('danger', 'Server error. Please try again later.');
        }
    });
    
    // Handle network errors
    $(document).ajaxError(function(event, xhr, settings, thrownError) {
        if (xhr.status === 0 && xhr.readyState === 0) {
            showAlert('warning', 'Network connection lost. Please check your internet connection.');
        }
    });
    
    // Auto-dismiss alerts after 5 seconds
    $(document).on('click', '.alert .btn-close', function() {
        $(this).closest('.alert').alert('close');
    });
    
    // Setup search functionality
    setupGlobalSearch();
}

/**
 * Setup global search functionality
 */
function setupGlobalSearch() {
    const searchInput = $('#globalSearch');
    if (searchInput.length) {
        let searchTimeout;
        
        searchInput.on('input', function() {
            const query = $(this).val().trim();
            
            // Clear previous timeout
            clearTimeout(searchTimeout);
            
            if (query.length >= 3) {
                // Debounce search by 500ms
                searchTimeout = setTimeout(function() {
                    performGlobalSearch(query);
                }, 500);
            } else {
                hideSearchResults();
            }
        });
        
        // Handle search on enter
        searchInput.on('keypress', function(e) {
            if (e.which === 13) {
                e.preventDefault();
                const query = $(this).val().trim();
                if (query.length >= 3) {
                    performGlobalSearch(query);
                }
            }
        });
    }
}

/**
 * Perform global search across emails
 */
function performGlobalSearch(query) {
    $.get('/api/email/search', { q: query, limit: 10 })
        .done(function(data) {
            displaySearchResults(data.emails, query);
        })
        .fail(function() {
            showAlert('danger', 'Search failed. Please try again.');
        });
}

/**
 * Display search results
 */
function displaySearchResults(emails, query) {
    const resultsContainer = $('#searchResults');
    if (!resultsContainer.length) return;
    
    let html = '';
    if (emails && emails.length > 0) {
        html = '<div class="dropdown-menu show" style="position: absolute; top: 100%; left: 0; right: 0;">';
        emails.forEach(function(email) {
            html += `
                <div class="dropdown-item cursor-pointer" onclick="openEmail(${email.id})">
                    <div class="d-flex justify-content-between">
                        <strong class="text-truncate">${highlightSearchTerm(email.subject, query)}</strong>
                        <small class="text-muted">${formatDate(email.received_date)}</small>
                    </div>
                    <small class="text-muted">From: ${email.sender_name || email.sender_email}</small>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html = '<div class="dropdown-menu show"><div class="dropdown-item-text">No results found</div></div>';
    }
    
    resultsContainer.html(html);
}

/**
 * Hide search results
 */
function hideSearchResults() {
    $('#searchResults').empty();
}

/**
 * Highlight search terms in text
 */
function highlightSearchTerm(text, term) {
    if (!text || !term) return text;
    const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
}

/**
 * Initialize page-specific functionality
 */
function initializePageFunctionality() {
    const page = getPageName();
    
    switch (page) {
        case 'dashboard':
            initializeDashboard();
            break;
        case 'emails':
            initializeEmailsPage();
            break;
        case 'chat':
            initializeChatPage();
            break;
        case 'settings':
            initializeSettingsPage();
            break;
    }
}

/**
 * Get current page name from URL
 */
function getPageName() {
    const path = window.location.pathname;
    if (path === '/' || path === '/dashboard') return 'dashboard';
    if (path.startsWith('/emails')) return 'emails';
    if (path.startsWith('/chat')) return 'chat';
    if (path.startsWith('/settings')) return 'settings';
    return 'unknown';
}

/**
 * Initialize dashboard functionality
 */
function initializeDashboard() {
    // Load recent activity
    loadRecentActivity();
    
    // Setup refresh buttons
    $('.refresh-btn').click(function() {
        const target = $(this).data('target');
        refreshDashboardSection(target);
    });
    
    // Auto-refresh dashboard every 2 minutes
    setInterval(function() {
        loadRecentActivity();
    }, 120000);
}

/**
 * Initialize emails page functionality
 */
function initializeEmailsPage() {
    // Setup email list interactions
    setupEmailListHandlers();
    
    // Setup folder navigation
    setupFolderNavigation();
    
    // Setup bulk actions
    setupBulkActions();
}

/**
 * Initialize chat page functionality
 */
function initializeChatPage() {
    // Chat functionality is handled in chat.html template
    console.log('Chat page initialized');
}

/**
 * Initialize settings page functionality
 */
function initializeSettingsPage() {
    // Setup settings form handlers
    setupSettingsHandlers();
    
    // Load user preferences
    loadUserPreferences();
}

/**
 * Setup email list event handlers
 */
function setupEmailListHandlers() {
    // Email item click handler
    $(document).on('click', '.email-item', function() {
        const emailId = $(this).data('email-id');
        if (emailId) {
            openEmail(emailId);
        }
    });
    
    // Mark as read/unread handler
    $(document).on('click', '.mark-read-btn', function(e) {
        e.stopPropagation();
        const emailId = $(this).data('email-id');
        const isRead = $(this).data('read') === true;
        markEmailRead(emailId, !isRead);
    });
    
    // Star/unstar handler
    $(document).on('click', '.star-btn', function(e) {
        e.stopPropagation();
        const emailId = $(this).data('email-id');
        toggleEmailStar(emailId);
    });
}

/**
 * Setup folder navigation
 */
function setupFolderNavigation() {
    $('.folder-item').click(function() {
        const folderName = $(this).data('folder');
        loadEmailsByFolder(folderName);
        
        // Update active folder
        $('.folder-item').removeClass('active');
        $(this).addClass('active');
    });
}

/**
 * Setup bulk email actions
 */
function setupBulkActions() {
    // Select all checkbox
    $('#selectAll').change(function() {
        const isChecked = $(this).is(':checked');
        $('.email-checkbox').prop('checked', isChecked);
        updateBulkActionBar();
    });
    
    // Individual email checkboxes
    $(document).on('change', '.email-checkbox', function() {
        updateBulkActionBar();
    });
    
    // Bulk action buttons
    $('#bulkMarkRead').click(function() {
        performBulkAction('mark_read');
    });
    
    $('#bulkMarkUnread').click(function() {
        performBulkAction('mark_unread');
    });
    
    $('#bulkDelete').click(function() {
        if (confirm('Are you sure you want to delete the selected emails?')) {
            performBulkAction('delete');
        }
    });
}

/**
 * Update bulk action bar visibility
 */
function updateBulkActionBar() {
    const selectedCount = $('.email-checkbox:checked').length;
    const bulkActionBar = $('#bulkActionBar');
    
    if (selectedCount > 0) {
        bulkActionBar.show();
        $('#selectedCount').text(selectedCount);
    } else {
        bulkActionBar.hide();
    }
}

/**
 * Open email in modal or new page
 */
function openEmail(emailId) {
    window.location.href = `/emails/${emailId}`;
}

/**
 * Mark email as read/unread
 */
function markEmailRead(emailId, isRead) {
    $.post(`/api/email/${emailId}/mark-read`, {
        is_read: isRead
    })
    .done(function(data) {
        if (data.success) {
            // Update UI
            const emailItem = $(`.email-item[data-email-id="${emailId}"]`);
            if (isRead) {
                emailItem.removeClass('unread').addClass('read');
            } else {
                emailItem.removeClass('read').addClass('unread');
            }
            
            // Update read button
            const button = $(`.mark-read-btn[data-email-id="${emailId}"]`);
            button.data('read', isRead);
            button.find('i').toggleClass('bi-envelope-open', isRead)
                           .toggleClass('bi-envelope', !isRead);
        }
    })
    .fail(function() {
        showAlert('danger', 'Failed to update email status');
    });
}

/**
 * Load emails by folder
 */
function loadEmailsByFolder(folderName) {
    const emailList = $('#emailList');
    
    // Show loading
    emailList.html('<div class="text-center py-4"><div class="spinner-border" role="status"></div></div>');
    
    $.get('/api/email/list', { folder: folderName })
        .done(function(data) {
            displayEmailList(data.emails);
        })
        .fail(function() {
            emailList.html('<div class="text-center py-4 text-danger">Failed to load emails</div>');
        });
}

/**
 * Display email list
 */
function displayEmailList(emails) {
    const emailList = $('#emailList');
    let html = '';
    
    if (emails && emails.length > 0) {
        emails.forEach(function(email) {
            html += createEmailListItem(email);
        });
    } else {
        html = '<div class="text-center py-4 text-muted">No emails found</div>';
    }
    
    emailList.html(html);
}

/**
 * Create email list item HTML
 */
function createEmailListItem(email) {
    const isUnread = !email.is_read;
    const senderName = email.sender_name || email.sender_email;
    const date = formatDate(email.received_date);
    const preview = email.body_preview || '';
    
    return `
        <div class="email-item ${isUnread ? 'unread' : 'read'} p-3 border-bottom cursor-pointer" 
             data-email-id="${email.id}">
            <div class="row align-items-center">
                <div class="col-md-1">
                    <input type="checkbox" class="form-check-input email-checkbox" 
                           value="${email.id}">
                </div>
                <div class="col-md-3">
                    <div class="d-flex align-items-center">
                        <div class="avatar bg-primary text-white rounded-circle me-2 d-flex align-items-center justify-content-center" 
                             style="width: 32px; height: 32px; font-size: 0.8rem;">
                            ${senderName.charAt(0).toUpperCase()}
                        </div>
                        <span class="${isUnread ? 'fw-bold' : ''}">${senderName}</span>
                    </div>
                </div>
                <div class="col-md-5">
                    <div class="${isUnread ? 'fw-bold' : ''}">${email.subject}</div>
                    <small class="text-muted text-truncate d-block">${preview}</small>
                </div>
                <div class="col-md-2 text-end">
                    <small class="text-muted">${date}</small>
                </div>
                <div class="col-md-1 text-end">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary mark-read-btn" 
                                data-email-id="${email.id}" data-read="${email.is_read}"
                                title="${isUnread ? 'Mark as read' : 'Mark as unread'}">
                            <i class="bi ${isUnread ? 'bi-envelope' : 'bi-envelope-open'}"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Utility function to show alerts
 */
function showAlert(type, message, duration = 5000) {
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert" 
             style="position: fixed; top: 20px; right: 20px; z-index: 1050; min-width: 300px;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    $('body').append(alertHtml);
    
    // Auto-dismiss after specified duration
    setTimeout(function() {
        $(`#${alertId}`).alert('close');
    }, duration);
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
        return date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    } else if (diffDays <= 7) {
        return date.toLocaleDateString([], {weekday: 'short'});
    } else {
        return date.toLocaleDateString([], {month: 'short', day: 'numeric'});
    }
}

/**
 * Escape regular expression special characters
 */
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
            document.execCommand('copy');
            document.body.removeChild(textArea);
            return Promise.resolve();
        } catch (err) {
            document.body.removeChild(textArea);
            return Promise.reject(err);
        }
    }
}

/**
 * Download content as file
 */
function downloadFile(content, filename, contentType = 'text/plain') {
    const blob = new Blob([content], { type: contentType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

/**
 * Debounce function execution
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;
        const later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Cleanup on page unload
$(window).on('beforeunload', function() {
    if (tokenRefreshTimer) {
        clearInterval(tokenRefreshTimer);
    }
});
// Email sending function
function sendEmail(to, subject, body, cc = null, bcc = null) {
    return fetch('/api/email/send', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            to: to,
            subject: subject,
            body: body,
            cc: cc,
            bcc: bcc,
            importance: 'normal'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Email sent successfully:', data.message);
            showNotification('Email sent successfully!', 'success');
        } else {
            console.error('Email send failed:', data.error);
            showNotification('Failed to send email: ' + data.error, 'error');
        }
        return data;
    })
    .catch(error => {
        console.error('Email send error:', error);
        showNotification('Email send error: ' + error.message, 'error');
    });
}

// Show notification function
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.container') || document.body;
    container.insertBefore(notification, container.firstChild);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Chat message sending function
function sendChatMessage(message, sessionId = null) {
    return fetch('/api/chat/message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            message: message,
            session_id: sessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Chat response received:', data.response);
            return data;
        } else {
            console.error('Chat failed:', data.error);
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Chat error:', error);
        throw error;
    });
}

// Update chat form submission
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = chatInput.value.trim();
            if (!message) return;
            
            // Clear input
            chatInput.value = '';
            
            // Add user message to chat
            addChatMessage('user', message);
            
            // Show loading
            addChatMessage('assistant', 'Thinking...', true);
            
            // Send message
            sendChatMessage(message)
                .then(data => {
                    // Remove loading message
                    const loadingMsg = chatMessages.querySelector('.loading');
                    if (loadingMsg) {
                        loadingMsg.remove();
                    }
                    
                    // Add AI response
                    addChatMessage('assistant', data.response);
                })
                .catch(error => {
                    // Remove loading message
                    const loadingMsg = chatMessages.querySelector('.loading');
                    if (loadingMsg) {
                        loadingMsg.remove();
                    }
                    
                    // Add error message
                    addChatMessage('assistant', 'Sorry, I encountered an error: ' + error.message);
                });
        });
    }
});

// Add message to chat display
function addChatMessage(role, content, isLoading = false) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    if (isLoading) {
        messageDiv.classList.add('loading');
    }
    
    messageDiv.innerHTML = `
        <div class="message-content">
            ${content}
        </div>
        <div class="message-time">
            ${new Date().toLocaleTimeString()}
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
