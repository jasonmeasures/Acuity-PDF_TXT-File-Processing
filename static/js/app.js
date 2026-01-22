// API Configuration
const API_BASE = '/api';

// State
let currentDownloadFilename = null;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    setupFileUpload();
});

// Event Listeners
function setupEventListeners() {
    const uploadForm = document.getElementById('uploadForm');
    const processBtn = document.getElementById('processBtn');
    const previewBtn = document.getElementById('previewBtn');
    const downloadBtn = document.getElementById('downloadBtn');
    const processAnotherBtn = document.getElementById('processAnotherBtn');

    uploadForm.addEventListener('submit', handleFormSubmit);
    previewBtn.addEventListener('click', handlePreview);
    downloadBtn.addEventListener('click', handleDownload);
    processAnotherBtn.addEventListener('click', resetForm);
}

// File Upload UI
function setupFileUpload() {
    const fileInput = document.getElementById('dataFile');
    const fileNameDisplay = document.getElementById('fileName');
    const fileUploadLabel = document.querySelector('.file-upload-label');

    fileInput.addEventListener('change', function(e) {
        const fileName = e.target.files[0]?.name || 'Choose file or drag here';
        fileNameDisplay.textContent = fileName;
    });

    // Drag and drop
    fileUploadLabel.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = 'var(--primary-color)';
        this.style.background = 'var(--bg-tertiary)';
    });

    fileUploadLabel.addEventListener('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '';
        this.style.background = '';
    });

    fileUploadLabel.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        this.style.borderColor = '';
        this.style.background = '';

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            fileNameDisplay.textContent = files[0].name;
        }
    });
}

// Form Submission
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('dataFile');
    const invoiceNumber = document.getElementById('invoiceNumber').value;
    
    if (!fileInput.files[0]) {
        showError('Please select a file to upload');
        return;
    }
    
    const formData = new FormData();
    formData.append('data_file', fileInput.files[0]);
    if (invoiceNumber) {
        formData.append('invoice_number', invoiceNumber);
    }
    
    try {
        showLoading(true);
        hideError();
        hideSuccess();
        
        const response = await fetch(`${API_BASE}/process`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Processing failed');
        }
        
        // Store download filename
        currentDownloadFilename = data.download_filename;
        
        // Display results
        displayResults(data);
        showSuccess(data.message);
        
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Preview Data
async function handlePreview(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('dataFile');
    
    if (!fileInput.files[0]) {
        showError('Please select a file to preview');
        return;
    }
    
    const formData = new FormData();
    formData.append('data_file', fileInput.files[0]);
    
    try {
        showLoading(true);
        hideError();
        
        const response = await fetch(`${API_BASE}/preview`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Preview failed');
        }
        
        displayPreview(data);
        
    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Display Preview
function displayPreview(data) {
    const message = `
        File contains ${data.columns.length} columns:
        ${data.columns.join(', ')}
        
        Showing first ${data.sample_data.length} rows of data.
    `;
    
    showSuccess(message);
}

// Display Results
function displayResults(data) {
    const resultsSection = document.getElementById('resultsSection');
    const summaryStats = document.getElementById('summaryStats');
    const countryBreakdown = document.getElementById('countryBreakdown');
    const htsBreakdown = document.getElementById('htsBreakdown');
    
    const summary = data.summary;
    
    // Summary Stats
    summaryStats.innerHTML = `
        <div class="stat-card">
            <div class="stat-label">Invoice Number</div>
            <div class="stat-value">${summary.invoice_number}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Line Items</div>
            <div class="stat-value">${summary.total_lines}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Quantity</div>
            <div class="stat-value">
                ${formatNumber(summary.total_quantity)}
                <span class="stat-unit">EA</span>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Net Weight</div>
            <div class="stat-value">
                ${formatNumber(summary.total_net_weight, 2)}
                <span class="stat-unit">kg</span>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Value</div>
            <div class="stat-value">
                ${formatCurrency(summary.total_value)}
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Unique HTS Codes</div>
            <div class="stat-value">${summary.unique_hts_codes}</div>
        </div>
    `;
    
    // Country Breakdown
    countryBreakdown.innerHTML = '';
    for (const [country, count] of Object.entries(summary.countries)) {
        const item = document.createElement('div');
        item.className = 'breakdown-item';
        item.innerHTML = `
            <span class="breakdown-label">${country}</span>
            <span class="breakdown-value">${count} lines</span>
        `;
        countryBreakdown.appendChild(item);
    }
    
    // HTS Breakdown
    htsBreakdown.innerHTML = '';
    for (const [hts, value] of Object.entries(summary.top_hts_codes)) {
        const item = document.createElement('div');
        item.className = 'breakdown-item';
        item.innerHTML = `
            <span class="breakdown-label">${hts}</span>
            <span class="breakdown-value">${formatCurrency(value)}</span>
        `;
        htsBreakdown.appendChild(item);
    }
    
    // Show results section
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Download Handler
async function handleDownload() {
    if (!currentDownloadFilename) {
        showError('No file available for download');
        return;
    }
    
    try {
        window.location.href = `${API_BASE}/download/${currentDownloadFilename}`;
        showSuccess('Download started successfully');
    } catch (error) {
        showError('Failed to download file');
    }
}

// Reset Form
function resetForm() {
    document.getElementById('uploadForm').reset();
    document.getElementById('fileName').textContent = 'Choose file or drag here';
    document.getElementById('resultsSection').style.display = 'none';
    currentDownloadFilename = null;
    hideError();
    hideSuccess();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// UI Helper Functions
function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const processBtn = document.getElementById('processBtn');
    const previewBtn = document.getElementById('previewBtn');
    
    loadingIndicator.style.display = show ? 'block' : 'none';
    processBtn.disabled = show;
    previewBtn.disabled = show;
    
    if (show) {
        loadingIndicator.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function showError(message) {
    const errorAlert = document.getElementById('errorAlert');
    const errorMessage = document.getElementById('errorMessage');
    
    errorMessage.textContent = message;
    errorAlert.style.display = 'flex';
    errorAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
    document.getElementById('errorAlert').style.display = 'none';
}

function showSuccess(message) {
    const successAlert = document.getElementById('successAlert');
    const successMessage = document.getElementById('successMessage');
    
    successMessage.textContent = message;
    successAlert.style.display = 'flex';
    successAlert.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideSuccess() {
    document.getElementById('successAlert').style.display = 'none';
}

function closeAlert() {
    hideError();
    hideSuccess();
}

// Formatting Functions
function formatNumber(num, decimals = 0) {
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(num);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Health Check (Optional)
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/health`);
        const data = await response.json();
        console.log('API Health:', data.status);
    } catch (error) {
        console.error('API health check failed:', error);
    }
}

// Run health check on load
checkHealth();
