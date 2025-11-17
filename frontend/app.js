// API Configuration
const API_URL = 'http://localhost:9000';
const API_BASE = 'http://localhost:9000';  // Alias for compatibility

// Global State
let selectedFile = null;
let selectedFiles = []; // Array for multiple files
let currentResults = null;
let currentTab = 'upload';

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Init] Starting application initialization...');

    try {
        initializeEventListeners();
        console.log('[Init] Event listeners initialized');
    } catch(e) {
        console.error('[Init] Error initializing event listeners:', e);
    }

    try {
        loadPayslips();
        console.log('[Init] Loading payslips...');
    } catch(e) {
        console.error('[Init] Error loading payslips:', e);
    }

    try {
        updateAgentStatus();
        console.log('[Init] Updating agent status...');
    } catch(e) {
        console.error('[Init] Error updating agent status:', e);
    }

    // Load analytics if on analytics tab
    if (currentTab === 'analytics') {
        console.log('[DOMContentLoaded] Loading analytics data...');
        loadAnalyticsData();
    }

    // Start real-time updates
    setInterval(updateAgentStatus, 5000);
    console.log('[Init] Application initialized successfully');
});

// Initialize Event Listeners
function initializeEventListeners() {
    console.log('[Listeners] Initializing event listeners...');

    // Tab Navigation
    const tabs = document.querySelectorAll('.tab');
    console.log('[Listeners] Found', tabs.length, 'tabs');
    tabs.forEach(tab => {
        console.log('[Listeners] Attaching listener to tab:', tab.dataset.tab);
        tab.addEventListener('click', (e) => {
            console.log('[Tab] Clicked:', e.target.dataset.tab);
            switchTab(e.target.dataset.tab);
        });
    });

    // File Upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');

    uploadArea.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        handleMultipleFiles(e.target.files);
    });

    // Drag and Drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        handleMultipleFiles(e.dataTransfer.files);
    });

    // Upload Button
    uploadBtn.addEventListener('click', uploadFile);

    // Clear Files
    const clearBtn = document.getElementById('clearFiles');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            selectedFiles = [];
            selectedFile = null;
            document.getElementById('selectedFiles').style.display = 'none';
            document.getElementById('uploadBtn').disabled = true;
            fileInput.value = '';
            updateFilesList();
        });
    }

    // Chat
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');

    chatSend.addEventListener('click', sendChatMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

// Tab Switching
function switchTab(tabName) {
    console.log('[switchTab] Called with tabName:', tabName);

    // Update tab buttons
    const tabs = document.querySelectorAll('.tab');
    console.log('[switchTab] Found', tabs.length, 'tab buttons');
    tabs.forEach(tab => {
        const isActive = tab.dataset.tab === tabName;
        tab.classList.toggle('active', isActive);
        console.log(`[switchTab]   Tab ${tab.dataset.tab}: ${isActive ? 'ACTIVE' : 'inactive'}`);
    });

    // Update tab panels
    const panels = document.querySelectorAll('.tab-panel');
    console.log('[switchTab] Found', panels.length, 'tab panels');
    panels.forEach(panel => {
        const expectedId = `${tabName}-tab`;
        const isActive = panel.id === expectedId;
        panel.classList.toggle('active', isActive);
        console.log(`[switchTab]   Panel ${panel.id}: ${isActive ? 'ACTIVE (should be visible)' : 'inactive (should be hidden)'}`);
    });

    currentTab = tabName;
    console.log('[switchTab] Current tab set to:', currentTab);

    // Load data based on active tab
    if (tabName === 'analysis') {
        console.log('[switchTab] Loading analytics data...');
        loadAnalyticsData();
    } else if (tabName === 'results') {
        console.log('[switchTab] Loading results data...');
        loadAllPayslipsForResults();
    }
}

// Handle Multiple Files
function handleMultipleFiles(files) {
    if (!files || files.length === 0) return;

    // Filter only PDF files
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');

    if (pdfFiles.length === 0) {
        showNotification('אנא בחר קבצי PDF בלבד', 'error');
        return;
    }

    if (pdfFiles.length !== files.length) {
        showNotification(`${files.length - pdfFiles.length} קבצים לא PDF דולגו`, 'warning');
    }

    selectedFiles = pdfFiles;
    updateFilesList();
    document.getElementById('selectedFiles').style.display = 'block';
    document.getElementById('uploadBtn').disabled = false;

    const btnText = document.getElementById('uploadBtnText');
    btnText.textContent = `נתח ${selectedFiles.length} תלושים`;
}

// Update Files List Display
function updateFilesList() {
    const filesList = document.getElementById('filesList');
    if (!filesList) return;

    if (selectedFiles.length === 0) {
        filesList.innerHTML = '';
        return;
    }

    filesList.innerHTML = selectedFiles.map((file, index) => `
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: var(--bg-tertiary); border-radius: 6px; margin-bottom: 0.5rem;">
            <span style="color: var(--text-primary);">${index + 1}. ${file.name}</span>
            <button onclick="removeFile(${index})" style="background: none; border: none; color: var(--error-color); cursor: pointer; font-size: 1.2rem;">✕</button>
        </div>
    `).join('');
}

// Remove single file from list
function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateFilesList();

    if (selectedFiles.length === 0) {
        document.getElementById('selectedFiles').style.display = 'none';
        document.getElementById('uploadBtn').disabled = true;
    }

    const btnText = document.getElementById('uploadBtnText');
    btnText.textContent = selectedFiles.length > 0 ? `נתח ${selectedFiles.length} תלושים` : 'נתח תלושים';
}

// File Upload - supports multiple files
async function uploadFile() {
    // Check if we have multiple files selected
    if (selectedFiles.length > 0) {
        await uploadMultipleFiles();
        return;
    }

    // Fallback to single file (legacy support)
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    // Show loading
    document.getElementById('loading').style.display = 'flex';
    document.getElementById('uploadBtn').disabled = true;

    try {
        const response = await fetch(`${API_URL}/api/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            console.error('Upload failed with status:', response.status);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            showNotification(`שגיאה בשרת: ${response.status}`, 'error');
            return;
        }

        const data = await response.json();
        console.log('Upload response:', data);

        if (data.success) {
            if (data.multiple_payslips) {
                console.log('Multiple payslips detected:', data.count);
                showNotification(data.message || `נותחו בהצלחה ${data.count} תלושים!`, 'success');
                displayMultipleResults(data);
                loadPayslips();
            } else {
                console.log('Single payslip detected');
                currentResults = data.result;
                displayResults(data.result);
                showNotification('התלוש נותח בהצלחה!', 'success');
                loadPayslips();
                updateStats(data.result);
            }
        } else {
            if (data.error === 'duplicates') {
                showNotification(data.message || 'כל התלושים כבר קיימים במערכת', 'warning');
                if (data.multiple_payslips) {
                    displayDuplicatesMessage(data);
                }
            } else {
                showNotification(data.message || 'שגיאה בניתוח התלוש', 'error');
            }
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification(`שגיאה בהעלאת הקובץ: ${error.message}`, 'error');
    } finally {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('uploadBtn').disabled = false;
    }
}

// Upload Multiple Files
async function uploadMultipleFiles() {
    if (selectedFiles.length === 0) return;

    const progressDiv = document.getElementById('uploadProgress');
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const uploadBtn = document.getElementById('uploadBtn');

    progressDiv.style.display = 'block';
    uploadBtn.disabled = true;

    let completed = 0;
    let successful = 0;
    let failed = 0;
    const total = selectedFiles.length;

    try {
        // Upload files in parallel (max 3 at a time)
        const batchSize = 3;
        for (let i = 0; i < total; i += batchSize) {
            const batch = selectedFiles.slice(i, i + batchSize);

            await Promise.all(batch.map(async (file) => {
                try {
                    const formData = new FormData();
                    formData.append('file', file);

                    const response = await fetch(`${API_URL}/api/upload`, {
                        method: 'POST',
                        body: formData
                    });

                    const data = await response.json();

                    if (response.ok && data.success) {
                        successful++;
                    } else {
                        failed++;
                        console.error(`Failed to upload ${file.name}:`, data.message);
                    }
                } catch (error) {
                    failed++;
                    console.error(`Error uploading ${file.name}:`, error);
                }

                completed++;
                const progress = (completed / total) * 100;
                progressBar.style.width = `${progress}%`;
                progressText.textContent = `מעלה ${completed}/${total} קבצים...`;
            }));
        }

        // Show final result
        if (successful > 0) {
            showNotification(`הועלו בהצלחה ${successful} מתוך ${total} תלושים`, 'success');
            loadPayslips();
            loadAllPayslipsForResults();
        }

        if (failed > 0) {
            showNotification(`${failed} תלושים נכשלו`, 'error');
        }

        // Clear selection
        selectedFiles = [];
        updateFilesList();
        document.getElementById('selectedFiles').style.display = 'none';
        document.getElementById('uploadBtnText').textContent = 'נתח תלושים';

    } finally {
        setTimeout(() => {
            progressDiv.style.display = 'none';
            progressBar.style.width = '0%';
        }, 2000);
        uploadBtn.disabled = false;
    }
}

// Display Results
function displayResults(result) {
    const resultsDiv = document.getElementById('analysisResults');

    // Check if result exists
    if (!result) {
        console.error('No result data received');
        showNotification('שגיאה: לא התקבלו נתונים מהשרת', 'error');
        return;
    }

    const parsed = result.parsed_data || {};
    const validation = result.validation || {};
    const analysis = result.analysis || {};

    let html = '<div class="results-grid">';

    // Employee Info Card
    html += `
        <div class="result-card employee-info">
            <h4>פרטי עובד</h4>
            <div class="info-row">
                <span>שם:</span>
                <strong>${parsed.employee?.name || '❌ לא זוהה'}</strong>
            </div>
            <div class="info-row">
                <span>מספר עובד:</span>
                <strong>${parsed.employee?.id || '❌ לא זוהה'}</strong>
            </div>
            <div class="info-row">
                <span>תקופה:</span>
                <strong>${parsed.period?.month || '?'}/${parsed.period?.year || '?'}</strong>
            </div>
        </div>
    `;

    // Salary Card
    html += `
        <div class="result-card salary-info">
            <h4>פרטי שכר</h4>
            <div class="info-row">
                <span>שכר בסיס:</span>
                <strong>${formatCurrency(parsed.salary?.base)}</strong>
            </div>
            <div class="info-row">
                <span>ברוטו:</span>
                <strong>${formatCurrency(parsed.salary?.gross)}</strong>
            </div>
            <div class="info-row highlight">
                <span>נטו לתשלום:</span>
                <strong>${formatCurrency(parsed.salary?.net)}</strong>
            </div>
        </div>
    `;

    // Work Hours Card
    if (parsed.work_hours) {
        html += `
            <div class="result-card hours-info">
                <h4>שעות עבודה</h4>
                <div class="big-number">${parsed.work_hours}</div>
                <div class="info-label">שעות החודש</div>
            </div>
        `;
    }

    // Validation Card
    const issuesCount = validation.issues_found || 0;
    html += `
        <div class="result-card validation-info ${issuesCount > 0 ? 'has-issues' : 'valid'}">
            <h4>תוצאות אימות</h4>
            ${issuesCount > 0 ?
                `<div class="issues-count">${issuesCount} בעיות נמצאו</div>
                 <div class="issues-list">${formatIssues(validation.issues)}</div>` :
                '<div class="valid-message">✅ התלוש תקין</div>'
            }
        </div>
    `;

    html += '</div>';

    // Analysis Summary
    if (analysis.anomalies && analysis.anomalies.length > 0) {
        html += `
            <div class="anomalies-section">
                <h4>אנומליות שזוהו</h4>
                <ul class="anomalies-list">
                    ${analysis.anomalies.map(a => `<li>${a.description}</li>`).join('')}
                </ul>
            </div>
        `;
    }

    resultsDiv.innerHTML = html;
    document.getElementById('resultsSection').style.display = 'block';

    // Switch to results tab
    switchTab('results');
}

// Display message when all payslips are duplicates
function displayDuplicatesMessage(data) {
    const resultsDiv = document.getElementById('analysisResults');
    const count = data.count || 0;

    let html = '<div class="multiple-results">';
    html += `
        <div class="summary-card" style="text-align: center;">
            <h3>⚠️ תלושים כפולים</h3>
            <p style="color: var(--brown-dark); font-size: 1.1rem; margin: 1rem 0;">
                נמצאו ${count} תלושים בקובץ, אך <strong>כולם כבר קיימים במערכת</strong>.
            </p>
            <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                לא נוספו תלושים חדשים. אם ברצונך להעלות תלושים חדשים, בחר קובץ אחר.
            </p>
        </div>
    `;
    html += '</div>';

    resultsDiv.innerHTML = html;
    document.getElementById('resultsSection').style.display = 'block';

    // Switch to results tab
    switchTab('results');
}

// Display Multiple Payslips Results
function displayMultipleResults(data) {
    console.log('[displayMultipleResults] Called with data:', data);
    const resultsDiv = document.getElementById('analysisResults');
    console.log('[displayMultipleResults] resultsDiv:', resultsDiv);
    const payslips = data.payslips || [];
    console.log('[displayMultipleResults] payslips:', payslips);
    const count = data.count || payslips.length;
    console.log('[displayMultipleResults] count:', count);

    let html = '<div class="multiple-results">';

    // Summary card
    html += `
        <div class="summary-card">
            <h3>סיכום ניתוח ${count} תלושים</h3>
            <div class="summary-stats">
                <div class="stat">
                    <span class="stat-label">סה"כ תלושים:</span>
                    <span class="stat-value">${count}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">עובדים:</span>
                    <span class="stat-value">${payslips.length}</span>
                </div>
            </div>
        </div>
    `;

    // Payslips details - Table format
    if (payslips && payslips.length > 0) {
        // Extract unique months for filter
        const months = new Set();
        payslips.forEach(ps => {
            const parsed = ps.parsed_data || {};
            const period = parsed.period || {};
            if (period.month && period.year) {
                months.add(`${period.month}/${period.year}`);
            } else if (ps.period) {
                months.add(ps.period);
            }
        });
        const sortedMonths = Array.from(months).sort();

        html += `
        <div style="margin-bottom: 1rem;">
            <label for="monthFilter" style="margin-left: 0.5rem; font-weight: 600;">סנן לפי חודש:</label>
            <select id="monthFilter" style="padding: 0.5rem; border-radius: 6px; border: 1px solid #000000; background: white; color: #000000; font-size: 0.875rem;">
                <option value="">כל החודשים</option>
                ${sortedMonths.map(m => `<option value="${m}">${m}</option>`).join('')}
            </select>
        </div>
        <div class="payslips-table-container">
            <table class="payslips-table">
                <thead>
                    <tr>
                        <th>שם עובד</th>
                        <th>מספר עובד</th>
                        <th>חודש</th>
                        <th>שעות רגילות</th>
                        <th>שעות 150%</th>
                        <th>שעות 125%</th>
                        <th>פרמיה</th>
                        <th>נסיעות</th>
                        <th>שכר לתשלום</th>
                    </tr>
                </thead>
                <tbody id="payslipsTableBody">
        `;

        payslips.forEach((ps, index) => {
            const parsed = ps.parsed_data || {};
            const employee = parsed.employee || {};
            const salary = parsed.salary || {};
            const additional = parsed.additional_payments || {};
            const hours = parsed.hours_breakdown || {};
            const period = parsed.period || {};

            const formatCurrency = (value) => {
                if (!value) return '-';
                return '₪' + parseFloat(value).toLocaleString('he-IL', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            };

            // Format month/year
            const monthYear = period.month && period.year ? `${period.month}/${period.year}` : (ps.period || '-');

            html += `
                <tr data-month="${period.month || ''}" data-year="${period.year || ''}">
                    <td class="employee-name">${employee.name || ps.employee_name || 'לא זוהה'}</td>
                    <td>${employee.id || ps.employee_id || '---'}</td>
                    <td>${monthYear}</td>
                    <td>${hours.regular_hours || '-'}</td>
                    <td>${hours.hours_150 ? hours.hours_150.toFixed(2) : '-'}</td>
                    <td>${hours.hours_125 ? hours.hours_125.toFixed(2) : '-'}</td>
                    <td class="salary">${formatCurrency(additional.premium)}</td>
                    <td class="salary">${formatCurrency(additional.travel_allowance)}</td>
                    <td class="salary">${formatCurrency(salary.final_payment || salary.net)}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        </div>
        `;
    }

    html += '</div>';

    resultsDiv.innerHTML = html;
    document.getElementById('resultsSection').style.display = 'block';

    // Switch to results tab
    switchTab('results');

    // Add month filter event listener
    const monthFilter = document.getElementById('monthFilter');
    if (monthFilter) {
        monthFilter.addEventListener('change', function() {
            const selectedMonth = this.value;
            const rows = document.querySelectorAll('#payslipsTableBody tr');

            rows.forEach(row => {
                if (!selectedMonth) {
                    row.style.display = '';
                } else {
                    const monthCell = row.querySelector('td:nth-child(3)');
                    if (monthCell && monthCell.textContent === selectedMonth) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        });
    }

    // Store first payslip as current for chat context (convert to expected format)
    if (payslips && payslips.length > 0) {
        const firstPayslip = payslips[0];
        currentResults = {
            parsed_data: {
                employee: {
                    name: firstPayslip.employee_name,
                    id: firstPayslip.employee_id
                },
                period: {
                    month: firstPayslip.period ? firstPayslip.period.split('/')[0] : null,
                    year: firstPayslip.period ? firstPayslip.period.split('/')[1] : null
                },
                salary: {
                    gross: firstPayslip.gross_salary,
                    net: firstPayslip.net_salary
                },
                work_hours: firstPayslip.work_hours,
                vacation_days: firstPayslip.vacation_days,
                deductions: firstPayslip.deductions
            }
        };
    }
}

// Format Issues
function formatIssues(issues) {
    if (!issues || issues.length === 0) return '';

    return issues.slice(0, 3).map(issue => `
        <div class="issue-item ${issue.severity}">
            <span class="issue-desc">${issue.description}</span>
            ${issue.details ? `<span class="issue-details">${issue.details}</span>` : ''}
        </div>
    `).join('');
}

// Chat session management
let chatSessionId = null;

// Chat Functions
async function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message
    addChatMessage('user', message);
    input.value = '';

    // Show typing indicator
    const typingId = Date.now();
    addChatMessage('agent', '🤖 מחשב...', 'System', typingId);

    try {
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: chatSessionId,  // Send session_id to maintain conversation
                context: currentResults ? {
                    parsed_data: currentResults.parsed_data,
                    validation: currentResults.validation,
                    analysis: currentResults.analysis
                } : null
            })
        });

        const data = await response.json();

        // Remove typing indicator
        removeMessage(typingId);

        // Save session_id from response
        if (data.session_id) {
            chatSessionId = data.session_id;
            console.log('[Chat] Session ID:', chatSessionId);
        }

        // Add agent response with tools info
        if (data.success) {
            let responseText = data.response;

            // Show which tools were used (if any)
            if (data.tools_used && data.tools_used.length > 0) {
                const toolNames = data.tools_used.map(t => t.name).join(', ');
                console.log('[Chat] Tools used:', toolNames);

                // Auto-refresh KPIs if analyzer agent was called for KPI creation
                const kpiToolUsed = data.tools_used.some(t =>
                    t.name === 'call_analyzer_agent' && t.input && t.input.task === 'create_kpi'
                );
                if (kpiToolUsed) {
                    console.log('[Chat] KPI created - auto-refreshing KPIs list');
                    // Wait a bit for DB to update, then refresh
                    setTimeout(() => {
                        loadKPIs();
                        // Show notification
                        showNotification('✓ KPI נוצר! נטען בטאב הניתוח', 'success');
                    }, 1000);
                }
            }

            addChatMessage('agent', responseText, 'AI Assistant');
        } else {
            addChatMessage('agent', 'מצטער, לא הצלחתי לעבד את ההודעה.', 'System');
        }
    } catch (error) {
        removeMessage(typingId);
        addChatMessage('agent', 'שגיאה בתקשורת עם השרת.', 'System');
    }
}

function addChatMessage(type, content, agent = null, id = null) {
    const messagesDiv = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    if (id) messageDiv.dataset.messageId = id;

    if (agent) {
        // Add correction button for agent messages (not system messages)
        const correctionButton = type === 'agent' && agent === 'AI Assistant' ?
            `<button class="correction-btn" onclick="showCorrectionInput(this)" title="תקן תשובה זו">✏️ תקן</button>` : '';

        messageDiv.innerHTML = `
            <span class="message-agent">${agent}</span>
            <div class="message-content">${content}</div>
            ${correctionButton}
        `;
    } else {
        messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    }

    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function removeMessage(id) {
    const message = document.querySelector(`[data-message-id="${id}"]`);
    if (message) message.remove();
}

// Correction functions
function showCorrectionInput(button) {
    const messageDiv = button.closest('.chat-message');
    const contentDiv = messageDiv.querySelector('.message-content');
    const currentContent = contentDiv.textContent;

    // Create correction input
    const correctionHTML = `
        <div class="correction-input-container" style="margin-top: 0.5rem;">
            <textarea
                class="correction-textarea"
                placeholder="הכנס את התשובה הנכונה..."
                style="width: 100%; min-height: 60px; padding: 0.5rem; border-radius: 4px; border: 1px solid var(--border-color); font-family: inherit;"
            ></textarea>
            <div style="margin-top: 0.5rem; display: flex; gap: 0.5rem;">
                <button onclick="submitCorrection(this)" style="background: var(--primary-color); color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">שלח תיקון</button>
                <button onclick="cancelCorrection(this)" style="background: var(--bg-secondary); border: 1px solid var(--border-color); padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;">ביטול</button>
            </div>
        </div>
    `;

    // Hide correction button and add input
    button.style.display = 'none';
    messageDiv.insertAdjacentHTML('beforeend', correctionHTML);
}

function cancelCorrection(button) {
    const messageDiv = button.closest('.chat-message');
    const correctionContainer = messageDiv.querySelector('.correction-input-container');
    const correctionBtn = messageDiv.querySelector('.correction-btn');

    correctionContainer.remove();
    correctionBtn.style.display = 'inline-block';
}

async function submitCorrection(button) {
    const messageDiv = button.closest('.chat-message');
    const textarea = messageDiv.querySelector('.correction-textarea');
    const correction = textarea.value.trim();

    if (!correction) {
        alert('נא להזין תיקון');
        return;
    }

    if (!chatSessionId) {
        alert('אין session פעיל - התחל שיחה חדשה');
        return;
    }

    try {
        // Disable button during submit
        button.disabled = true;
        button.textContent = 'שולח...';

        const response = await fetch(`${API_URL}/api/agent/correction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: chatSessionId,
                correction: correction
            })
        });

        const data = await response.json();

        if (data.success) {
            // Show success message
            const successMsg = document.createElement('div');
            successMsg.style.cssText = 'background: #4caf50; color: white; padding: 0.5rem; border-radius: 4px; margin-top: 0.5rem;';
            successMsg.textContent = '✓ התיקון נשמר - הסוכן למד ממנו!';
            messageDiv.appendChild(successMsg);

            // Remove correction input after 2 seconds
            setTimeout(() => {
                const correctionContainer = messageDiv.querySelector('.correction-input-container');
                if (correctionContainer) correctionContainer.remove();
                successMsg.remove();
            }, 2000);

            console.log('[Learning] Correction submitted successfully');
        } else {
            alert('שגיאה בשמירת התיקון');
            button.disabled = false;
            button.textContent = 'שלח תיקון';
        }
    } catch (error) {
        console.error('Error submitting correction:', error);
        alert('שגיאה בתקשורת עם השרת');
        button.disabled = false;
        button.textContent = 'שלח תיקון';
    }
}

// Load Payslips
async function loadPayslips() {
    try {
        const response = await fetch(`${API_URL}/api/payslips?limit=10`);
        const data = await response.json();

        if (data.payslips) {
            displayPayslips(data.payslips);
        }
    } catch (error) {
        console.error('Error loading payslips:', error);
    }
}

function displayPayslips(payslips) {
    const tbody = document.getElementById('payslipsList');

    // Element might not be visible yet (in different tab)
    if (!tbody) {
        console.log('[Payslips] Table not found - might be in different tab');
        return;
    }

    if (!payslips || payslips.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 2rem;">אין תלושים להצגה</td></tr>';
        return;
    }

    tbody.innerHTML = payslips.map(slip => {
        const parsed = slip.parsed_data || {};
        const employee = parsed.employee || {};

        // Extract month/year from period or created_at
        let month = '-';
        if (slip.period) {
            month = slip.period; // Assuming format like "10/2025"
        } else if (slip.created_at) {
            const date = new Date(slip.created_at);
            month = `${date.getMonth() + 1}/${date.getFullYear()}`;
        }

        return `
        <tr>
            <td>${employee.name || slip.employee_name || 'לא זוהה'}</td>
            <td>${employee.id || slip.employee_id || 'לא זוהה'}</td>
            <td>${month}</td>
            <td>
                <button class="btn-primary" onclick="viewPayslip(${slip.id})" style="padding: 0.4rem 1rem; font-size: 0.875rem;">
                    צפה בתלוש
                </button>
            </td>
        </tr>
    `}).join('');
}

// Update Agent Status - Simplified (no dynamic updates for now)
async function updateAgentStatus() {
    // Sidebar now only shows static agent descriptions
    // No dynamic status updates needed
    return;
}

// Update Stats
function updateStats(result) {
    // Check if result exists
    if (!result) {
        console.warn('updateStats: No result data');
        return;
    }

    // Update stats in the UI based on analysis results
    const validation = result.validation || {};
    const issuesCount = validation.issues_found || 0;

    // Update agent cards with real data
    const validatorCard = document.querySelector('[data-agent="validator"]');
    if (validatorCard) {
        const statsDiv = validatorCard.querySelector('.agent-stats');
        if (statsDiv) {
            statsDiv.innerHTML = `
                <span>בעיות: ${issuesCount}</span>
                <span>סטטוס: ${issuesCount > 0 ? 'נמצאו בעיות' : 'תקין'}</span>
            `;
        }
    }
}

// Utility Functions
function formatCurrency(amount) {
    if (!amount && amount !== 0) return '❌ לא זוהה';
    return `₪${amount.toLocaleString('he-IL', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('he-IL');
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        left: 50%;
        transform: translateX(-50%);
        padding: 1rem 2rem;
        background: ${type === 'success' ? '#22c55e' : type === 'error' ? '#ef4444' : '#06b6d4'};
        color: white;
        border-radius: 8px;
        font-weight: 500;
        z-index: 1000;
        animation: slideDown 0.3s ease;
    `;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideUp 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// View Payslip Details
async function viewPayslip(id) {
    // Open PDF in new tab
    const pdfUrl = `${API_BASE}/api/payslips/${id}/pdf`;
    window.open(pdfUrl, '_blank');
}

// Toggle Visualization Prompt Display
function toggleVisualizationPrompt() {
    const container = document.getElementById('visualizationPromptContainer');
    if (container.style.display === 'none') {
        container.style.display = 'block';
    } else {
        container.style.display = 'none';
    }
}

// Generate Visualization using Template Library
async function generateVisualization() {
    const promptInput = document.getElementById('visualizationPrompt');
    const monthSelect = document.getElementById('visualizationMonthSelect');
    const content = document.getElementById('monthlyAnalysisContent');

    if (!promptInput || !promptInput.value.trim()) {
        showNotification('נא להזין הנחיה לתצוגה', 'error');
        return;
    }

    const selectedMonth = monthSelect ? monthSelect.value : '';
    if (!selectedMonth) {
        showNotification('נא לבחור חודש לניתוח', 'error');
        return;
    }

    const prompt = promptInput.value.trim();

    try {
        // Show loading indicator
        const loadingId = 'loading_' + Date.now();
        const loadingHtml = `<p id="${loadingId}" style="text-align: center; padding: 2rem;">⏳ יוצר תצוגה...</p>`;

        // If content is empty, replace it, otherwise append
        if (content.innerHTML.includes('בחר חודש')) {
            content.innerHTML = loadingHtml;
        } else {
            content.innerHTML += loadingHtml;
        }

        // Call the new API endpoint
        const response = await fetch(`${API_BASE}/api/generate-visualization`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                month: selectedMonth
            })
        });

        // Remove loading indicator
        const loadingEl = document.getElementById(loadingId);
        if (loadingEl) loadingEl.remove();

        if (!response.ok) {
            throw new Error('Failed to generate visualization');
        }

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Unknown error');
        }

        console.log('Visualization result:', result);

        // Create a unique ID for this visualization
        const chartId = `chart_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // Create container HTML - full viewport width
        const containerHtml = `
            <div class="visualization-card" style="margin: 2rem calc(-2rem - 2px); background: white; border: 2px solid #000000; border-radius: 0; padding: 1.5rem 2rem; width: 100vw; max-width: 100vw; position: relative; left: 50%; right: 50%; margin-left: -50vw; margin-right: -50vw;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: #000000; font-weight: 700;">${result.config.title || 'תצוגה'}</h3>
                    <div>
                        <button onclick="this.closest('.visualization-card').remove()" class="btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.875rem;">
                            ✕ הסר
                        </button>
                    </div>
                </div>
                ${result.type === 'table' ?
                    `<div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; border: 2px solid #000000;">
                            <thead>
                                <tr style="background: #000000; color: #FFFFFF;">
                                    ${(result.config.columns || []).map(col =>
                                        `<th style="padding: 12px; text-align: right; font-weight: 600; border: 2px solid #000000;">${col}</th>`
                                    ).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${(result.config.rows || []).map((row, idx) => `
                                    <tr>
                                        ${row.map(cell =>
                                            `<td style="padding: 12px; text-align: right; border: 2px solid #000000;">${cell}</td>`
                                        ).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>`
                    :
                    `<div style="position: relative; height: 500px; width: 100%;">
                        <canvas id="${chartId}"></canvas>
                    </div>`
                }
            </div>
        `;

        // Append HTML to content
        content.innerHTML += containerHtml;

        // If it's a chart, create it now
        if (result.type !== 'table') {
            // Wait a bit for DOM to update
            setTimeout(() => {
                const ctx = document.getElementById(chartId);
                if (!ctx) {
                    console.error('Canvas not found:', chartId);
                    return;
                }

                // Single color for all bars - purple
                const singleColor = 'rgba(168, 85, 247, 0.9)'; // #A855F7

                // For pie charts - purple shades
                const pieColors = [
                    'rgba(168, 85, 247, 0.9)',  // purple
                    'rgba(147, 51, 234, 0.9)',  // purple-dark
                    'rgba(233, 213, 255, 0.9)', // purple-light
                    'rgba(0, 0, 0, 0.9)',       // black
                    'rgba(168, 85, 247, 0.7)',
                    'rgba(147, 51, 234, 0.7)',
                    'rgba(233, 213, 255, 0.7)',
                    'rgba(0, 0, 0, 0.7)',
                    'rgba(168, 85, 247, 0.5)',
                    'rgba(147, 51, 234, 0.5)'
                ];

                const chartConfig = {
                    type: result.type,
                    data: {
                        labels: result.config.labels || [],
                        datasets: [{
                            label: result.config.dataLabel || 'ערך',
                            data: result.config.data || [],
                            backgroundColor: result.type === 'pie' ? pieColors : singleColor,
                            borderColor: result.type === 'pie' ? 'white' : singleColor,
                            borderWidth: result.type === 'pie' ? 2 : 0,
                            borderRadius: result.type === 'bar' ? 6 : 0,
                            barThickness: result.type === 'bar' ? 'flex' : undefined,
                            maxBarThickness: result.type === 'bar' ? 80 : undefined
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: result.type === 'pie',
                                position: 'bottom'
                            }
                        }
                    }
                };

                // Add scale config for bar/line charts
                if (result.type === 'bar' || result.type === 'line') {
                    chartConfig.options.scales = {
                        x: {
                            grid: {
                                display: false  // No grid on X axis
                            },
                            ticks: {
                                font: {
                                    size: 10,
                                    weight: 600
                                },
                                maxRotation: 45,
                                minRotation: 45,
                                autoSkip: false  // Show all labels
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                display: false  // No grid on Y axis
                            },
                            border: {
                                display: false
                            },
                            ticks: {
                                font: {
                                    size: 12
                                },
                                callback: function(value) {
                                    if (result.config.formatValue) {
                                        return '₪' + value.toLocaleString('he-IL');
                                    }
                                    return value;
                                }
                            }
                        }
                    };
                }

                // Line chart specific
                if (result.type === 'line') {
                    chartConfig.data.datasets[0].fill = true;
                    chartConfig.data.datasets[0].tension = 0.4;
                }

                new Chart(ctx, chartConfig);
            }, 100);
        }

        // Clear input
        promptInput.value = '';

        showNotification('תצוגה נוצרה בהצלחה! 🎉', 'success');

    } catch (error) {
        console.error('Error generating visualization:', error);
        content.innerHTML = `<p style="text-align: center; color: red; padding: 2rem;">❌ שגיאה: ${error.message}</p>`;
        showNotification('שגיאה ביצירת תצוגה', 'error');
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translate(-50%, -20px);
        }
        to {
            opacity: 1;
            transform: translate(-50%, 0);
        }
    }

    @keyframes slideUp {
        from {
            opacity: 1;
            transform: translate(-50%, 0);
        }
        to {
            opacity: 0;
            transform: translate(-50%, -20px);
        }
    }

    .results-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }

    .result-card {
        background: var(--blue-light);
        border: 1px solid #000000;
        border-radius: 12px;
        padding: 1.5rem;
    }

    .result-card h4 {
        margin-bottom: 1rem;
        color: #000000;
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .info-row {
        display: flex;
        justify-content: space-between;
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-color);
    }

    .info-row:last-child {
        border-bottom: none;
    }

    .info-row span {
        color: #000000;
        font-size: 0.875rem;
    }

    .info-row strong {
        color: #000000;
        font-weight: 600;
    }

    .info-row.highlight strong {
        color: var(--blue-accent);
        font-size: 1.125rem;
    }

    .big-number {
        font-size: 3rem;
        font-weight: 700;
        color: #000000;
        margin-bottom: 0.5rem;
    }

    .info-label {
        color: #000000;
        font-size: 0.875rem;
    }

    .validation-info.has-issues {
        border-color: rgba(239, 68, 68, 0.3);
        background: rgba(239, 68, 68, 0.05);
    }

    .validation-info.valid {
        border-color: rgba(34, 197, 94, 0.3);
        background: rgba(34, 197, 94, 0.05);
    }

    .issues-count {
        color: #000000;
        font-size: 1.25rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    .valid-message {
        color: #000000;
        font-size: 1.125rem;
        font-weight: 600;
        text-align: center;
        padding: 1rem;
    }

    .issue-item {
        padding: 0.5rem;
        margin-bottom: 0.5rem;
        border-radius: 6px;
        background: rgba(0, 0, 0, 0.3);
    }

    .issue-item.high {
        border-right: 3px solid #f87171;
    }

    .issue-item.medium {
        border-right: 3px solid #facc15;
    }

    .issue-desc {
        display: block;
        font-size: 0.875rem;
        margin-bottom: 0.25rem;
    }

    .issue-details {
        display: block;
        font-size: 0.75rem;
        color: #000000;
    }

    .anomalies-section {
        background: var(--blue-light);
        border: 1px solid #000000;
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
    }

    .anomalies-list {
        list-style: none;
        padding: 0;
    }

    .anomalies-list li {
        padding: 0.5rem 0;
        border-bottom: 1px solid var(--border-color);
        color: #000000;
        font-size: 0.875rem;
    }

    .anomalies-list li:last-child {
        border-bottom: none;
    }

    .btn-icon {
        background: transparent;
        border: none;
        cursor: pointer;
        font-size: 1.25rem;
        padding: 0.25rem;
    }

    .btn-icon:hover {
        transform: scale(1.1);
    }

    /* Multiple Payslips Results */
    .multiple-results {
        padding: 1rem;
    }

    .summary-card {
        background: var(--blue-light);
        border: 2px solid #000000;
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        color: #000000;
    }

    .summary-card h3 {
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
    }

    .summary-stats {
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
    }

    .summary-stats .stat {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }

    .stat-label {
        font-size: 0.875rem;
        opacity: 0.9;
    }

    .stat-value {
        font-size: 2rem;
        font-weight: 700;
    }

    .stat-value.success {
        color: #000000;
    }

    .stat-value.warning {
        color: #000000;
    }

    .employees-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 1rem;
    }

    .employee-card {
        background: var(--blue-light);
        border: 1px solid #000000;
        border-radius: 12px;
        padding: 1.5rem;
        transition: all 0.3s ease;
    }

    .employee-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
    }

    .employee-card.valid {
        border-color: rgba(34, 197, 94, 0.3);
        background: rgba(34, 197, 94, 0.05);
    }

    .employee-card.has-issues {
        border-color: rgba(239, 68, 68, 0.3);
        background: rgba(239, 68, 68, 0.05);
    }

    .employee-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }

    .employee-header h4 {
        font-size: 1.125rem;
        font-weight: 600;
        color: #000000;
    }

    .employee-id {
        font-size: 0.875rem;
        color: #000000;
    }

    .employee-details {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    .detail-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .detail-row span {
        color: #000000;
        font-size: 0.875rem;
    }

    .detail-row strong {
        color: #000000;
        font-size: 1.125rem;
    }

    .status-valid {
        color: #000000;
        font-weight: 600;
    }

    .status-invalid {
        color: #000000;
        font-weight: 600;
    }

    .issues-preview {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }

    .issues-count {
        background: rgba(239, 68, 68, 0.1);
        color: #f87171;
        padding: 0.25rem 0.75rem;
        border-radius: 6px;
        font-size: 0.875rem;
    }
`;
document.head.appendChild(style);

// Load Analytics Data - Stats, Trends, and Department Analytics
async function loadAnalyticsData() {
    // Load statistics only - הסרתי loadTrendsData ו-loadDepartmentAnalytics
    // כי האלמנטים שלהם לא קיימים ב-HTML
    loadStatistics();
}

// Load Statistics
async function loadStatistics() {
    console.log('[loadStatistics] Starting...');
    try {
        const response = await fetch(`${API_URL}/api/stats`);
        console.log('[loadStatistics] Response status:', response.status);
        const data = await response.json();
        console.log('[loadStatistics] Data:', data);

        // Update stat cards
        const totalEl = document.getElementById('stat-total-payslips');
        const validEl = document.getElementById('stat-valid-payslips');
        const invalidEl = document.getElementById('stat-invalid-payslips');
        const anomaliesEl = document.getElementById('stat-anomalies');

        console.log('[loadStatistics] Elements found:', {totalEl, validEl, invalidEl, anomaliesEl});

        if (totalEl) totalEl.textContent = data.total_payslips || 0;
        if (validEl) validEl.textContent = data.valid_payslips || 0;
        if (invalidEl) invalidEl.textContent = data.invalid_payslips || 0;
        if (anomaliesEl) anomaliesEl.textContent = data.with_anomalies || 0;

        console.log('[loadStatistics] Updated successfully');
    } catch (error) {
        console.error('[loadStatistics] Error:', error);
    }
}

// Load Trends Data for Analytics Tab
async function loadTrendsData() {
    try {
        const response = await fetch(`${API_URL}/api/analytics/trends`);
        const data = await response.json();

        if (data.trends && data.trends.length > 0) {
            displayTrendsChart(data);
        } else {
            document.querySelector('.chart-placeholder').innerHTML = '<span>📊 אין מספיק נתונים לניתוח מגמות (נדרש לפחות חודש אחד)</span>';
        }
    } catch (error) {
        console.error('Error loading trends:', error);
        document.querySelector('.chart-placeholder').innerHTML = '<span>⚠️ שגיאה בטעינת נתוני מגמות</span>';
    }
}

// Display Trends Chart
function displayTrendsChart(data) {
    const container = document.querySelector('.chart-placeholder');
    const trends = data.trends;
    const summary = data.summary;

    // Build simple text-based chart
    let html = '<div class="trends-display" style="text-align: right; padding: 1rem;">';

    // Summary
    html += `<div style="margin-bottom: 1.5rem;">`;
    html += `<h4 style="color: var(--beige-light); margin-bottom: 0.75rem;">סיכום כללי</h4>`;
    html += `<div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">`;
    html += `<div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 8px;">`;
    html += `<div style="color: var(--text-secondary); font-size: 0.875rem;">חודשים</div>`;
    html += `<div style="color: var(--beige-accent); font-size: 1.5rem; font-weight: 600;">${summary.total_months}</div>`;
    html += `</div>`;
    html += `<div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 8px;">`;
    html += `<div style="color: var(--text-secondary); font-size: 0.875rem;">ממוצע ברוטו</div>`;
    html += `<div style="color: var(--beige-accent); font-size: 1.5rem; font-weight: 600;">₪${summary.avg_gross_overall.toLocaleString('he-IL')}</div>`;
    html += `</div>`;
    html += `<div style="background: var(--bg-tertiary); padding: 1rem; border-radius: 8px;">`;
    html += `<div style="color: var(--text-secondary); font-size: 0.875rem;">ממוצע לתשלום</div>`;
    html += `<div style="color: var(--beige-accent); font-size: 1.5rem; font-weight: 600;">₪${summary.avg_final_payment_overall.toLocaleString('he-IL')}</div>`;
    html += `</div>`;
    html += `</div>`;
    html += `</div>`;

    // Trends table
    html += `<div style="margin-top: 1.5rem;">`;
    html += `<h4 style="color: var(--beige-light); margin-bottom: 0.75rem;">מגמות לפי חודשים</h4>`;
    html += `<table style="width: 100%; border-collapse: collapse;">`;
    html += `<thead style="background: var(--bg-tertiary); border-bottom: 2px solid rgba(212, 197, 160, 0.2);">`;
    html += `<tr>`;
    html += `<th style="padding: 0.75rem; text-align: right; color: var(--beige-accent); font-size: 0.875rem;">חודש</th>`;
    html += `<th style="padding: 0.75rem; text-align: right; color: var(--beige-accent); font-size: 0.875rem;">תלושים</th>`;
    html += `<th style="padding: 0.75rem; text-align: right; color: var(--beige-accent); font-size: 0.875rem;">ברוטו ממוצע</th>`;
    html += `<th style="padding: 0.75rem; text-align: right; color: var(--beige-accent); font-size: 0.875rem;">לתשלום ממוצע</th>`;
    html += `<th style="padding: 0.75rem; text-align: right; color: var(--beige-accent); font-size: 0.875rem;">שעות ממוצע</th>`;
    html += `</tr>`;
    html += `</thead>`;
    html += `<tbody>`;

    trends.forEach((trend, index) => {
        html += `<tr style="border-bottom: 1px solid var(--border-color);">`;
        html += `<td style="padding: 0.75rem; color: var(--text-primary);">${trend.period}</td>`;
        html += `<td style="padding: 0.75rem; color: var(--text-primary);">${trend.count}</td>`;
        html += `<td style="padding: 0.75rem; color: var(--beige-accent); font-weight: 600;">₪${trend.avg_gross.toLocaleString('he-IL')}</td>`;
        html += `<td style="padding: 0.75rem; color: var(--beige-accent); font-weight: 600;">₪${trend.avg_final_payment.toLocaleString('he-IL')}</td>`;
        html += `<td style="padding: 0.75rem; color: var(--text-primary);">${trend.avg_hours}</td>`;
        html += `</tr>`;
    });

    html += `</tbody>`;
    html += `</table>`;
    html += `</div>`;

    html += '</div>';

    container.innerHTML = html;
}

// Load department analytics
async function loadDepartmentAnalytics() {
    console.log('[loadDepartmentAnalytics] Starting...');
    try {
        const response = await fetch(`${API_URL}/api/analytics/by-department`);
        const data = await response.json();
        console.log('[loadDepartmentAnalytics] Data:', data);

        const container = document.getElementById('departmentAnalytics');
        if (!container) {
            console.error('[loadDepartmentAnalytics] Container not found');
            return;
        }

        if (!data.departments || data.departments.length === 0) {
            container.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: 2rem;">אין נתוני מחלקות זמינים</p>';
            return;
        }

        let html = '';

        // Display each department
        data.departments.forEach((dept, index) => {
            html += `
            <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h3 style="color: var(--brown-dark); margin-bottom: 2rem; font-size: 1.5rem; border-bottom: 2px solid var(--border-color); padding-bottom: 1rem;">
                    📍 ${dept.department}
                    <span style="color: var(--text-muted); font-size: 1rem; font-weight: normal; margin-right: 1rem;">(${dept.employee_count} עובדים)</span>
                </h3>

                <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 1.5rem;">
                    <!-- העובד עם השכר הגבוה ביותר -->
                    <div style="background: var(--bg-primary); border: 1px solid rgba(168, 147, 120, 0.3); border-radius: 8px; padding: 1rem;">
                        <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">💰 שכר הגבוה ביותר</div>
                        ${dept.top_earner ? `
                            <div style="color: var(--brown-dark); font-weight: 600; margin-bottom: 0.25rem;">${dept.top_earner.employee_name}</div>
                            <div style="color: var(--beige-accent); font-size: 1.25rem; font-weight: 600;">₪${dept.top_earner.avg_salary.toLocaleString('he-IL')}</div>
                        ` : '<div style="color: var(--text-muted);">אין נתונים</div>'}
                    </div>

                    <!-- העובד עם שעות העבודה הגבוהות ביותר -->
                    <div style="background: var(--bg-primary); border: 1px solid rgba(168, 147, 120, 0.3); border-radius: 8px; padding: 1rem;">
                        <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">⏰ שעות עבודה גבוהות</div>
                        ${dept.top_worker ? `
                            <div style="color: var(--brown-dark); font-weight: 600; margin-bottom: 0.25rem;">${dept.top_worker.employee_name}</div>
                            <div style="color: var(--beige-accent); font-size: 1.25rem; font-weight: 600;">${dept.top_worker.avg_work_hours.toLocaleString('he-IL')} שעות</div>
                        ` : '<div style="color: var(--text-muted);">אין נתונים</div>'}
                    </div>

                    <!-- העובד עם הבונוס הגבוה ביותר -->
                    <div style="background: var(--bg-primary); border: 1px solid rgba(168, 147, 120, 0.3); border-radius: 8px; padding: 1rem;">
                        <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">🎁 בונוס הגבוה ביותר</div>
                        ${dept.top_bonus_earner ? `
                            <div style="color: var(--brown-dark); font-weight: 600; margin-bottom: 0.25rem;">${dept.top_bonus_earner.employee_name}</div>
                            <div style="color: var(--beige-accent); font-size: 1.25rem; font-weight: 600;">₪${dept.top_bonus_earner.total_bonus.toLocaleString('he-IL')}</div>
                        ` : '<div style="color: var(--text-muted);">אין נתוני בונוס</div>'}
                    </div>

                    <!-- ממוצע שכר במחלקה -->
                    <div style="background: var(--bg-primary); border: 1px solid rgba(168, 147, 120, 0.3); border-radius: 8px; padding: 1rem;">
                        <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">📊 ממוצע שכר</div>
                        <div style="color: var(--beige-accent); font-size: 1.25rem; font-weight: 600;">₪${dept.avg_salary.toLocaleString('he-IL')}</div>
                    </div>

                    <!-- ממוצע שעות במחלקה -->
                    <div style="background: var(--bg-primary); border: 1px solid rgba(168, 147, 120, 0.3); border-radius: 8px; padding: 1rem;">
                        <div style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 0.5rem;">📈 ממוצע שעות</div>
                        <div style="color: var(--beige-accent); font-size: 1.25rem; font-weight: 600;">${dept.avg_work_hours.toLocaleString('he-IL')} שעות</div>
                    </div>
                </div>
            </div>
            `;
        });

        container.innerHTML = html;
        console.log('[loadDepartmentAnalytics] Loaded successfully');
    } catch (error) {
        console.error('[loadDepartmentAnalytics] Error:', error);
        const container = document.getElementById('departmentAnalytics');
        if (container) {
            container.innerHTML = '<p style="color: var(--error); text-align: center; padding: 2rem;">שגיאה בטעינת נתוני מחלקות</p>';
        }
    }
}
// ==================== KPIs Management ====================

// Load and Display KPIs
async function loadKPIs() {
    try {
        const response = await fetch(`${API_BASE}/api/kpis`);

        if (!response.ok) {
            throw new Error('Failed to fetch KPIs');
        }

        const data = await response.json();
        displayKPIs(data.kpis || []);

    } catch (error) {
        console.error('Error loading KPIs:', error);
        document.getElementById('kpisContainer').innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
                <p>שגיאה בטעינת KPIs</p>
            </div>
        `;
    }
}

function displayKPIs(kpis) {
    const container = document.getElementById('kpisContainer');

    if (!kpis || kpis.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; grid-column: 1/-1;">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="opacity: 0.3; margin-bottom: 1rem;">
                    <line x1="12" y1="20" x2="12" y2="10"></line>
                    <line x1="18" y1="20" x2="18" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="16"></line>
                </svg>
                <p style="color: var(--text-tertiary); font-size: 1.1rem;">אין KPIs עדיין</p>
                <p style="color: var(--text-tertiary); font-size: 0.9rem; margin-top: 0.5rem;">
                    בקש מהצ'אטבוט ליצור KPI חדש!
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = kpis.map(kpi => {
        const results = kpi.results || {};
        const entries = Object.entries(results);

        return `
            <div class="kpi-card">
                <div class="kpi-header">
                    <h3>${kpi.name}</h3>
                    <span class="kpi-badge">${getMetricLabel(kpi.metric)}</span>
                </div>
                ${kpi.description ? `<p class="kpi-description">${kpi.description}</p>` : ''}
                <div class="kpi-meta">
                    <span>📊 ${getAggregationLabel(kpi.aggregation)}</span>
                    <span>📁 ${getGroupByLabel(kpi.group_by)}</span>
                </div>
                <div class="kpi-results">
                    ${entries.map(([key, value]) => `
                        <div class="kpi-result-item">
                            <span class="kpi-result-label">${key}</span>
                            <span class="kpi-result-value">${formatKPIValue(value, kpi.metric)}</span>
                        </div>
                    `).join('')}
                </div>
                <div class="kpi-footer">
                    <small>נוצר: ${new Date(kpi.created_at).toLocaleDateString('he-IL')}</small>
                </div>
            </div>
        `;
    }).join('');
}

function getMetricLabel(metric) {
    const labels = {
        'sick_days': 'ימי מחלה',
        'vacation_days': 'ימי חופשה',
        'work_hours': 'שעות עבודה',
        'gross_salary': 'שכר ברוטו',
        'net_salary': 'שכר נטו'
    };
    return labels[metric] || metric;
}

function getAggregationLabel(agg) {
    const labels = {
        'average': 'ממוצע',
        'sum': 'סכום',
        'min': 'מינימום',
        'max': 'מקסימום',
        'count': 'ספירה'
    };
    return labels[agg] || agg;
}

function getGroupByLabel(group) {
    const labels = {
        'department': 'לפי מחלקה',
        'employee': 'לפי עובד',
        'month': 'לפי חודש',
        'none': 'כללי'
    };
    return labels[group] || group;
}

function formatKPIValue(value, metric) {
    if (metric && metric.includes('salary')) {
        return formatCurrency(value);
    }
    return typeof value === 'number' ? value.toFixed(2) : value;
}

function refreshKPIs() {
    loadKPIs();
    showNotification('KPIs עודכנו', 'success');
}

// ==================== MONTHLY ANALYSIS FUNCTIONS ====================

// Load available months on page load
async function loadAvailableMonths() {
    console.log('[loadAvailableMonths] Starting...');
    try {
        const response = await fetch(`${API_URL}/api/available-months`);
        const data = await response.json();
        console.log('[loadAvailableMonths] Data received:', data);

        if (data.success && data.months) {
            const monthNames = [
                'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
                'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר'
            ];

            // Populate main month selector
            const select = document.getElementById('monthSelect');
            console.log('[loadAvailableMonths] monthSelect element:', select);

            if (select) {
                select.innerHTML = '<option value="">בחר חודש...</option>';

                data.months.forEach(m => {
                    const option = document.createElement('option');
                    option.value = `${m.month}/${m.year}`;
                    const monthName = monthNames[parseInt(m.month) - 1];
                    option.textContent = `${monthName} ${m.year}`;
                    select.appendChild(option);
                });

                console.log('[loadAvailableMonths] Added', data.months.length, 'months to select');
            }

            // Populate visualization month selector
            const visualizationSelect = document.getElementById('visualizationMonthSelect');
            if (visualizationSelect) {
                visualizationSelect.innerHTML = '<option value="">-- בחר חודש --</option>';

                data.months.forEach(m => {
                    const option = document.createElement('option');
                    option.value = `${m.month}/${m.year}`;
                    const monthName = monthNames[parseInt(m.month) - 1];
                    option.textContent = `${monthName} ${m.year}`;
                    visualizationSelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('[loadAvailableMonths] Error:', error);
    }
}

// Load monthly analysis when button clicked
async function loadMonthlyAnalysis() {
    const select = document.getElementById('monthSelect');
    const selectedValue = select.value;

    if (!selectedValue) {
        showNotification('בחר חודש לניתוח', 'error');
        return;
    }

    const [month, year] = selectedValue.split('/');

    try {
        document.getElementById('loading').style.display = 'flex';

        const response = await fetch(`${API_URL}/api/monthly-analysis-direct/${month}/${year}`);
        const data = await response.json();

        if (data.success) {
            displayMonthlyAnalysis(data);
        } else {
            showNotification(data.message || 'שגיאה בטעינת הניתוח', 'error');
        }
    } catch (error) {
        console.error('Error loading monthly analysis:', error);
        showNotification('שגיאה בטעינת הניתוח החודשי', 'error');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

// Display monthly analysis
function displayMonthlyAnalysis(data) {
    const container = document.getElementById('monthlyAnalysisContent');

    let html = `
    <div style="margin-top: 2rem;">
        <h3 style="margin-bottom: 1.5rem; font-size: 1.5rem;">ניתוח לחודש ${data.month}/${data.year}</h3>
        <p style="color: var(--text-secondary); margin-bottom: 2rem;">סה"כ ${data.total_payslips} תלושים</p>

        <!-- 1. Highest Salary Per Department -->
        <div class="summary-card" style="margin-bottom: 2rem;">
            <h4 style="font-size: 1.125rem; margin-bottom: 1rem; color: #000000;">💰 עובד עם השכר הגבוה ביותר בכל מחלקה</h4>
            <div class="payslips-table-container">
                <table class="payslips-table">
                    <thead>
                        <tr>
                            <th>מחלקה</th>
                            <th>שם עובד</th>
                            <th>מספר עובד</th>
                            <th>שכר</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    for (const [dept, info] of Object.entries(data.highest_salary_per_department)) {
        html += `
        <tr>
            <td>${dept}</td>
            <td class="employee-name">${info.employee_name}</td>
            <td>${info.employee_id}</td>
            <td class="salary">${formatCurrency(info.salary)}</td>
        </tr>
        `;
    }

    html += `
                    </tbody>
                </table>
            </div>
        </div>

        <!-- 2. Top 3 Vacation Days -->
        <div class="summary-card" style="margin-bottom: 2rem;">
            <h4 style="font-size: 1.125rem; margin-bottom: 1rem; color: #000000;">🏖️ 3 עובדים עם ימי החופש הגבוהים ביותר</h4>
            <div class="payslips-table-container">
                <table class="payslips-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>שם עובד</th>
                            <th>מספר עובד</th>
                            <th>ימי חופש</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    data.top_vacation_days.forEach((emp, index) => {
        html += `
        <tr>
            <td>${index + 1}</td>
            <td class="employee-name">${emp.employee_name}</td>
            <td>${emp.employee_id}</td>
            <td>${emp.vacation_days}</td>
        </tr>
        `;
    });

    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // 3. Anomalies by Category - always show all 3 categories
    html += `
        <!-- 3. Anomalies Table -->
        <div class="summary-card">
            <h4 style="font-size: 1.125rem; margin-bottom: 1rem; color: #000000;">⚠️ אנומליות</h4>
    `;

    // Define the 3 categories in order
    const categories = [
        'שכר לתשלום מעל 16,000',
        'נסיעות מעל 300',
        'פרמיה מעל 1,000'
    ];

    if (data.anomalies_by_category) {
        categories.forEach(category => {
            const anomalies = data.anomalies_by_category[category] || [];

            html += `
                <div style="margin-bottom: 1.5rem;">
                    <h5 style="font-size: 1rem; margin-bottom: 0.75rem; color: var(--text-primary); font-weight: 600;">
                        ${category}
                    </h5>
            `;

            if (anomalies.length > 0) {
                html += `
                    <div class="payslips-table-container">
                        <table class="payslips-table">
                            <thead>
                                <tr>
                                    <th>שם עובד</th>
                                    <th>מספר עובד</th>
                                    <th>ערך</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                anomalies.forEach(anomaly => {
                    const valueDisplay = formatCurrency(anomaly.value);
                    html += `
                        <tr>
                            <td class="employee-name">${anomaly.employee_name}</td>
                            <td>${anomaly.employee_id}</td>
                            <td class="salary">${valueDisplay}</td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            } else {
                html += `
                    <p style="text-align: center; color: var(--text-secondary); padding: 1rem; background: var(--bg-secondary); border-radius: 0.5rem;">
                        לא נמצאו חריגות
                    </p>
                `;
            }

            html += `
                </div>
            `;
        });
    }

    html += `
        </div>
    `;

    html += `
    </div>
    `;

    container.innerHTML = html;
}

// Call loadAvailableMonths when page loads
setTimeout(() => {
    loadAvailableMonths();
    loadMonthFilterOptions();
}, 1000);

// ==================== Results Tab - All Payslips ====================

let allPayslipsData = [];

async function loadAllPayslipsForResults() {
    try {
        const response = await fetch(`${API_URL}/api/payslips?limit=100`);
        const data = await response.json();

        if (data.payslips) {
            allPayslipsData = data.payslips;
            displayPayslipsResults(allPayslipsData);
        }
    } catch (error) {
        console.error('Error loading payslips for results:', error);
        document.getElementById('analysisResults').innerHTML = `
            <div style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                שגיאה בטעינת נתונים
            </div>
        `;
    }
}

function displayPayslipsResults(payslips) {
    const container = document.getElementById('analysisResults');

    if (!payslips || payslips.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 3rem; color: var(--text-secondary);">
                <p>אין תלושים להצגה</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="table-container" style="overflow-x: auto;">
            <table class="payslips-table" style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: var(--bg-tertiary); border-bottom: 2px solid var(--border-color);">
                        <th style="padding: 1rem; text-align: right;">שם עובד</th>
                        <th style="padding: 1rem; text-align: right;">מספר עובד</th>
                        <th style="padding: 1rem; text-align: right;">חודש</th>
                        <th style="padding: 1rem; text-align: right;">שכר לתשלום</th>
                        <th style="padding: 1rem; text-align: right;">שעות רגילות</th>
                        <th style="padding: 1rem; text-align: right;">שעות 125%</th>
                        <th style="padding: 1rem; text-align: right;">שעות 150%</th>
                        <th style="padding: 1rem; text-align: right;">פרמיות</th>
                        <th style="padding: 1rem; text-align: right;">ימי חופש</th>
                    </tr>
                </thead>
                <tbody>
    `;

    payslips.forEach(slip => {
        const parsed = slip.parsed_data || {};
        const employee = parsed.employee || {};
        const hoursBreakdown = parsed.hours_breakdown || {};
        const additionalPayments = parsed.additional_payments || {};
        const salary = parsed.salary || {};

        // שם עובד
        const employeeName = employee.name || slip.employee_name || `עובד ${slip.employee_id}`;

        // מספר עובד
        const employeeId = slip.employee_id || employee.id || 'לא זוהה';

        // שכר לתשלום
        const finalPayment = salary.final_payment || slip.final_payment;

        // שעות רגילות
        const regularHours = hoursBreakdown.regular_hours;

        // שעות 125% ו-150% - Analyzer ב-Backend כבר סיכם אותן
        const hours125 = hoursBreakdown.hours_125;
        const hours150 = hoursBreakdown.hours_150;

        // פרמיות
        const premium = additionalPayments.premium;

        // ימי חופש
        const vacationDays = parsed.vacation_days || slip.vacation_days;

        // חודש/שנה
        const period = slip.period || '-';

        html += `
            <tr style="border-bottom: 1px solid var(--border-color);">
                <td style="padding: 1rem; font-weight: 600;">${employeeName}</td>
                <td style="padding: 1rem;">${employeeId}</td>
                <td style="padding: 1rem;">${period}</td>
                <td style="padding: 1rem; font-weight: 600;">${finalPayment ? Math.round(finalPayment).toLocaleString() + ' ₪' : '-'}</td>
                <td style="padding: 1rem;">${regularHours ? Number(regularHours.toFixed(2)) : '-'}</td>
                <td style="padding: 1rem;">${hours125 ? Number(hours125.toFixed(2)) : '-'}</td>
                <td style="padding: 1rem;">${hours150 ? Number(hours150.toFixed(2)) : '-'}</td>
                <td style="padding: 1rem;">${premium ? Math.round(premium).toLocaleString() + ' ₪' : '-'}</td>
                <td style="padding: 1rem;">${vacationDays ? Number(vacationDays.toFixed(2)) : '-'}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

async function loadMonthFilterOptions() {
    try {
        const response = await fetch(`${API_URL}/api/available-months`);
        const data = await response.json();

        if (data.success && data.months) {
            const select = document.getElementById('monthFilter');
            if (select) {
                data.months.forEach(month => {
                    const option = document.createElement('option');
                    option.value = month.label;
                    option.textContent = month.label;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Error loading month options:', error);
    }
}

function applyMonthFilter() {
    const selectedMonth = document.getElementById('monthFilter').value;

    if (!selectedMonth || selectedMonth === '') {
        // Show all payslips
        displayPayslipsResults(allPayslipsData);
    } else {
        // Filter by month
        const filtered = allPayslipsData.filter(slip => {
            // Try to get period from multiple sources
            let period = slip.period; // Direct field "10/2025"

            // If not available, construct from parsed_data
            if (!period && slip.parsed_data && slip.parsed_data.period) {
                const month = slip.parsed_data.period.month;
                const year = slip.parsed_data.period.year;
                if (month && year) {
                    period = `${month}/${year}`;
                }
            }

            return period === selectedMonth;
        });
        displayPayslipsResults(filtered);
    }
}
