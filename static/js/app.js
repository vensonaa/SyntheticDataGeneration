// Synthetic Data Generator Web App JavaScript

// Global variables
let currentResults = null;
let schemaTemplates = {};
let availableModels = {};
let currentDatasets = [];
let currentPage = 0;
let datasetsPerPage = 10;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    try {
        // Load configuration
        await loadConfiguration();
        
        // Load schema templates
        await loadSchemaTemplates();
        
        // Setup event listeners
        setupEventListeners();
        
        // Add initial field
        addField();
        
        // Load database stats
        await loadDatabaseStats();
        
        console.log('App initialized successfully');
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showAlert('Failed to initialize application. Please refresh the page.', 'danger');
    }
}

async function loadConfiguration() {
    try {
        const response = await fetch('/api/config');
        const data = await response.json();
        
        if (data.success) {
            availableModels = data.models;
            populateModelSelect(data.models);
            updateConfigurationDisplay(data.config);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load configuration:', error);
        showAlert('Failed to load configuration. Please check your .env file.', 'warning');
    }
}

async function loadSchemaTemplates() {
    try {
        const response = await fetch('/api/schema/templates');
        const data = await response.json();
        
        if (data.success) {
            schemaTemplates = data.templates;
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load schema templates:', error);
    }
}

function populateModelSelect(models) {
    const modelSelect = document.getElementById('modelSelect');
    modelSelect.innerHTML = '';
    
    Object.entries(models).forEach(([modelId, modelInfo]) => {
        const option = document.createElement('option');
        option.value = modelId;
        option.textContent = `${modelId} - ${modelInfo.description}`;
        modelSelect.appendChild(option);
    });
}

function updateConfigurationDisplay(config) {
    // Update any configuration-dependent UI elements
    if (!config.groq_api_key) {
        showAlert('Groq API key not configured. Please set GROQ_API_KEY in your .env file.', 'warning');
    }
}

function setupEventListeners() {
    // Temperature slider
    const temperatureSlider = document.getElementById('temperatureSlider');
    const temperatureValue = document.getElementById('temperatureValue');
    
    temperatureSlider.addEventListener('input', function() {
        temperatureValue.textContent = this.value;
    });
    
    // Schema template selector
    const schemaTemplate = document.getElementById('schemaTemplate');
    schemaTemplate.addEventListener('change', function() {
        if (this.value) {
            loadSchemaTemplate(this.value);
        }
    });
    
    // Field type changes
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('field-type')) {
            updateFieldOptions(e.target.closest('.field-item'));
        }
    });
}

function addField() {
    const fieldsContainer = document.getElementById('fieldsContainer');
    const template = document.getElementById('fieldTemplate');
    const fieldItem = template.content.cloneNode(true);
    
    fieldsContainer.appendChild(fieldItem);
    
    // Update field options for the new field
    const newField = fieldsContainer.lastElementChild;
    updateFieldOptions(newField);
}

function removeField(button) {
    const fieldItem = button.closest('.field-item');
    fieldItem.remove();
}

function updateFieldOptions(fieldItem) {
    const fieldType = fieldItem.querySelector('.field-type').value;
    const optionsContainer = fieldItem.querySelector('.field-options');
    
    // Clear existing options
    optionsContainer.innerHTML = '';
    
    // Add type-specific options
    switch (fieldType) {
        case 'STRING':
            addStringOptions(optionsContainer);
            break;
        case 'INTEGER':
        case 'FLOAT':
            addNumericOptions(optionsContainer);
            break;
        case 'STRING':
            addStringOptions(optionsContainer);
            break;
    }
    
    // Show options container if it has content
    optionsContainer.style.display = optionsContainer.children.length > 0 ? 'block' : 'none';
}

function addStringOptions(container) {
    const options = [
        { label: 'Min Length', type: 'number', name: 'min_length' },
        { label: 'Max Length', type: 'number', name: 'max_length' },
        { label: 'Pattern (Regex)', type: 'text', name: 'pattern' },
        { label: 'Choices (comma-separated)', type: 'text', name: 'choices' }
    ];
    
    addOptionsToContainer(container, options);
}

function addNumericOptions(container) {
    const options = [
        { label: 'Min Value', type: 'number', name: 'min_value' },
        { label: 'Max Value', type: 'number', name: 'max_value' },
        { label: 'Default Value', type: 'number', name: 'default_value' }
    ];
    
    addOptionsToContainer(container, options);
}

function addOptionsToContainer(container, options) {
    options.forEach(option => {
        const row = document.createElement('div');
        row.className = 'row mb-2';
        
        row.innerHTML = `
            <div class="col-md-6">
                <label class="form-label">${option.label}</label>
                <input type="${option.type}" class="form-control field-option" data-option="${option.name}">
            </div>
        `;
        
        container.appendChild(row);
    });
}

function loadSchemaTemplate(templateId) {
    const template = schemaTemplates[templateId];
    if (!template) return;
    
    // Set schema name and description
    document.getElementById('schemaName').value = template.name;
    document.getElementById('schemaDescription').value = template.description;
    
    // Clear existing fields
    document.getElementById('fieldsContainer').innerHTML = '';
    
    // Add template fields
    template.fields.forEach(field => {
        addField();
        const fieldItem = document.getElementById('fieldsContainer').lastElementChild;
        
        // Set field values
        fieldItem.querySelector('.field-name').value = field.name;
        fieldItem.querySelector('.field-type').value = field.data_type;
        fieldItem.querySelector('.field-required').checked = field.required;
        
        // Update options and set values
        updateFieldOptions(fieldItem);
        
        // Set option values
        Object.entries(field).forEach(([key, value]) => {
            if (key !== 'name' && key !== 'data_type' && key !== 'required') {
                const optionInput = fieldItem.querySelector(`[data-option="${key}"]`);
                if (optionInput) {
                    optionInput.value = value;
                }
            }
        });
    });
}

async function validateSchema() {
    const schema = collectSchemaData();
    
    if (!schema.fields || schema.fields.length === 0) {
        showAlert('Please add at least one field to the schema.', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/validate-schema', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ schema })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const validation = data.validation;
            
            if (validation.is_valid) {
                showAlert('Schema is valid! ✅', 'success');
            } else {
                let errorMessage = 'Schema validation failed:\n';
                validation.errors.forEach(error => {
                    errorMessage += `• ${error}\n`;
                });
                showAlert(errorMessage, 'danger');
            }
            
            if (validation.warnings && validation.warnings.length > 0) {
                let warningMessage = 'Schema warnings:\n';
                validation.warnings.forEach(warning => {
                    warningMessage += `• ${warning}\n`;
                });
                showAlert(warningMessage, 'warning');
            }
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Schema validation failed:', error);
        showAlert('Failed to validate schema: ' + error.message, 'danger');
    }
}

async function generateData() {
    const schema = collectSchemaData();
    const generationParams = collectGenerationParams();
    
    if (!schema.fields || schema.fields.length === 0) {
        showAlert('Please add at least one field to the schema.', 'warning');
        return;
    }
    
    if (!schema.name) {
        showAlert('Please enter a schema name.', 'warning');
        return;
    }
    
    // Show loading indicator
    showLoading(true);
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                schema,
                generation_params: generationParams
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentResults = data;
            displayResults(data);
            showAlert(`Successfully generated ${data.total_records} records! 🎉`, 'success');
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Data generation failed:', error);
        showAlert('Failed to generate data: ' + error.message, 'danger');
    } finally {
        showLoading(false);
    }
}

function collectSchemaData() {
    const fields = [];
    const fieldItems = document.querySelectorAll('.field-item');
    
    fieldItems.forEach(fieldItem => {
        const fieldName = fieldItem.querySelector('.field-name').value.trim();
        const fieldType = fieldItem.querySelector('.field-type').value;
        const fieldRequired = fieldItem.querySelector('.field-required').checked;
        
        if (fieldName) {
            const field = {
                name: fieldName,
                data_type: fieldType,
                required: fieldRequired
            };
            
            // Collect field options
            const optionInputs = fieldItem.querySelectorAll('.field-option');
            optionInputs.forEach(input => {
                if (input.value.trim()) {
                    const optionName = input.dataset.option;
                    let optionValue = input.value;
                    
                    // Convert numeric values
                    if (input.type === 'number') {
                        optionValue = parseFloat(optionValue);
                    }
                    
                    // Handle choices (comma-separated)
                    if (optionName === 'choices') {
                        optionValue = optionValue.split(',').map(c => c.trim()).filter(c => c);
                    }
                    
                    field[optionName] = optionValue;
                }
            });
            
            fields.push(field);
        }
    });
    
    return {
        name: document.getElementById('schemaName').value.trim(),
        description: document.getElementById('schemaDescription').value.trim(),
        fields: fields
    };
}

function collectGenerationParams() {
    return {
        model: document.getElementById('modelSelect').value,
        temperature: parseFloat(document.getElementById('temperatureSlider').value),
        record_count: parseInt(document.getElementById('recordCount').value),
        use_contextual_generation: document.getElementById('contextualGeneration').checked,
        quality_enhancement: document.getElementById('qualityEnhancement').checked
    };
}

function displayResults(data) {
    const resultsContainer = document.getElementById('resultsContainer');
    const exportButtons = document.getElementById('exportButtons');
    const qualityMetricsCard = document.getElementById('qualityMetricsCard');
    
    // Display data table
    if (data.generated_records && data.generated_records.length > 0) {
        const table = createDataTable(data.generated_records);
        resultsContainer.innerHTML = '';
        resultsContainer.appendChild(table);
        
        // Show export buttons
        exportButtons.classList.remove('d-none');
        
        // Display quality metrics
        if (data.quality_metrics) {
            displayQualityMetrics(data.quality_metrics);
            qualityMetricsCard.style.display = 'block';
        }
    } else {
        resultsContainer.innerHTML = '<div class="alert alert-warning">No data was generated.</div>';
    }
}

function createDataTable(records) {
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover fade-in';
    
    if (records.length === 0) return table;
    
    // Create header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const headers = Object.keys(records[0].data);
    
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create body
    const tbody = document.createElement('tbody');
    records.forEach(record => {
        const row = document.createElement('tr');
        headers.forEach(header => {
            const td = document.createElement('td');
            td.textContent = record.data[header] || '';
            row.appendChild(td);
        });
        tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
    return table;
}

function displayQualityMetrics(metrics) {
    const container = document.getElementById('qualityMetrics');
    container.innerHTML = '';
    
    const metricItems = [
        { key: 'completeness', label: 'Completeness', icon: 'fas fa-check-circle' },
        { key: 'validity', label: 'Validity', icon: 'fas fa-shield-alt' },
        { key: 'uniqueness', label: 'Uniqueness', icon: 'fas fa-fingerprint' },
        { key: 'total_records', label: 'Total Records', icon: 'fas fa-database' }
    ];
    
    metricItems.forEach(item => {
        if (metrics[item.key] !== undefined) {
            const metricCard = document.createElement('div');
            metricCard.className = 'col-md-3 mb-3';
            
            const value = typeof metrics[item.key] === 'number' && metrics[item.key] <= 100 
                ? `${metrics[item.key].toFixed(1)}%` 
                : metrics[item.key];
            
            metricCard.innerHTML = `
                <div class="metric-card">
                    <i class="${item.icon} fa-2x text-primary mb-2"></i>
                    <div class="metric-value">${value}</div>
                    <div class="metric-label">${item.label}</div>
                </div>
            `;
            
            container.appendChild(metricCard);
        }
    });
}

async function exportData(format) {
    if (!currentResults || !currentResults.generated_records) {
        showAlert('No data to export. Please generate data first.', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`/api/export/${format}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                records: currentResults.generated_records
            })
        });
        
        if (response.ok) {
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `synthetic_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert(`Data exported successfully as ${format.toUpperCase()}! 📁`, 'success');
        } else {
            const data = await response.json();
            throw new Error(data.error || 'Export failed');
        }
    } catch (error) {
        console.error('Export failed:', error);
        showAlert('Failed to export data: ' + error.message, 'danger');
    }
}

function showLoading(show) {
    const loadingIndicator = document.getElementById('loadingIndicator');
    const generateBtn = document.getElementById('generateBtn');
    
    if (show) {
        loadingIndicator.classList.remove('d-none');
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating...';
    } else {
        loadingIndicator.classList.add('d-none');
        generateBtn.disabled = false;
        generateBtn.innerHTML = '<i class="fas fa-magic me-1"></i>Generate Data';
    }
}

function showAlert(message, type = 'info') {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the results container
    const resultsContainer = document.getElementById('resultsContainer');
    resultsContainer.insertBefore(alertDiv, resultsContainer.firstChild);
    
    // Auto-dismiss after 5 seconds for success/info messages
    if (type === 'success' || type === 'info') {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Utility functions
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString();
}

function formatNumber(number) {
    return new Intl.NumberFormat().format(number);
}

// SQLite Database Functions

async function loadDatabaseStats() {
    try {
        const response = await fetch('/api/database/stats');
        const data = await response.json();
        
        if (data.success) {
            updateDatabaseStats(data.stats);
        }
    } catch (error) {
        console.error('Failed to load database stats:', error);
    }
}

function updateDatabaseStats(stats) {
    document.getElementById('totalDatasets').textContent = formatNumber(stats.total_datasets);
    document.getElementById('totalRecords').textContent = formatNumber(stats.total_records);
    
    if (stats.recent_datasets && stats.recent_datasets.length > 0) {
        const lastDataset = stats.recent_datasets[0];
        document.getElementById('lastGenerated').textContent = formatDate(lastDataset.created_at);
    } else {
        document.getElementById('lastGenerated').textContent = 'Never';
    }
}

async function loadDatasets(page = 0) {
    try {
        const offset = page * datasetsPerPage;
        const response = await fetch(`/api/datasets?limit=${datasetsPerPage}&offset=${offset}`);
        const data = await response.json();
        
        if (data.success) {
            currentDatasets = data.datasets;
            currentPage = page;
            displayDatasets(data.datasets);
            updateDatabaseStats({ 
                total_datasets: data.datasets.length, 
                total_records: data.datasets.reduce((sum, ds) => sum + ds.record_count, 0)
            });
        } else {
            showAlert(`Failed to load datasets: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Failed to load datasets:', error);
        showAlert('Failed to load datasets', 'danger');
    }
}

function displayDatasets(datasets) {
    const container = document.getElementById('datasetsList');
    
    if (!datasets || datasets.length === 0) {
        container.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-database fa-3x mb-3"></i>
                <h5>No Datasets Found</h5>
                <p>Generate some data to see saved datasets here.</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = datasets.map(dataset => `
        <div class="card mb-3">
            <div class="card-body">
                <div class="row align-items-center">
                    <div class="col">
                        <h6 class="card-title mb-1">${dataset.name}</h6>
                        <p class="card-text small text-muted mb-2">${dataset.description || 'No description'}</p>
                        <div class="d-flex gap-3 small text-muted">
                            <span><i class="fas fa-table me-1"></i>${formatNumber(dataset.record_count)} records</span>
                            <span><i class="fas fa-calendar me-1"></i>${formatDate(dataset.created_at)}</span>
                        </div>
                    </div>
                    <div class="col-auto">
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="viewDataset(${dataset.id})">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="exportDataset(${dataset.id})">
                                <i class="fas fa-download"></i> Export
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteDataset(${dataset.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

async function viewDataset(datasetId) {
    try {
        // Load dataset details
        const datasetResponse = await fetch(`/api/datasets/${datasetId}`);
        const datasetData = await datasetResponse.json();
        
        if (!datasetData.success) {
            showAlert(`Failed to load dataset: ${datasetData.error}`, 'danger');
            return;
        }
        
        // Load dataset records
        const recordsResponse = await fetch(`/api/datasets/${datasetId}/records?limit=50`);
        const recordsData = await recordsResponse.json();
        
        if (!recordsData.success) {
            showAlert(`Failed to load records: ${recordsData.error}`, 'danger');
            return;
        }
        
        // Switch to Generated Data tab and display the dataset
        const generatedTab = document.getElementById('generated-tab');
        generatedTab.click();
        
        // Display dataset as if it was just generated
        const fakeResults = {
            generated_records: recordsData.records.map(record => ({
                data: record.record_data,
                is_valid: record.is_valid,
                validation_errors: record.validation_errors,
                generation_metadata: record.generation_metadata
            })),
            quality_metrics: datasetData.dataset.quality_metrics,
            generation_metadata: datasetData.dataset.generation_metadata,
            total_records: recordsData.records.length
        };
        
        displayResults(fakeResults);
        showAlert(`Loaded dataset: ${datasetData.dataset.name}`, 'success');
        
    } catch (error) {
        console.error('Failed to view dataset:', error);
        showAlert('Failed to view dataset', 'danger');
    }
}

async function exportDataset(datasetId) {
    try {
        const response = await fetch(`/api/datasets/${datasetId}/export/csv`);
        
        if (response.ok) {
            // Create download link
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = response.headers.get('Content-Disposition')?.split('filename=')[1]?.replace(/"/g, '') || 'dataset.csv';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showAlert('Dataset exported successfully', 'success');
        } else {
            const errorData = await response.json();
            showAlert(`Export failed: ${errorData.error}`, 'danger');
        }
    } catch (error) {
        console.error('Failed to export dataset:', error);
        showAlert('Failed to export dataset', 'danger');
    }
}

async function deleteDataset(datasetId) {
    if (!confirm('Are you sure you want to delete this dataset? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/datasets/${datasetId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('Dataset deleted successfully', 'success');
            refreshDatasets();
            await loadDatabaseStats();
        } else {
            showAlert(`Failed to delete dataset: ${data.error}`, 'danger');
        }
    } catch (error) {
        console.error('Failed to delete dataset:', error);
        showAlert('Failed to delete dataset', 'danger');
    }
}

async function refreshDatasets() {
    await loadDatasets(currentPage);
    await loadDatabaseStats();
}

// Setup event listeners for datasets tab
function setupDatasetsEventListeners() {
    const datasetsTab = document.getElementById('datasets-tab');
    datasetsTab.addEventListener('shown.bs.tab', function() {
        loadDatasets(0);
    });
    
    const searchInput = document.getElementById('datasetSearch');
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const filteredDatasets = currentDatasets.filter(dataset => 
            dataset.name.toLowerCase().includes(searchTerm) ||
            (dataset.description && dataset.description.toLowerCase().includes(searchTerm))
        );
        displayDatasets(filteredDatasets);
    });
}

// Update the main setup function
const originalSetupEventListeners = setupEventListeners;
setupEventListeners = function() {
    originalSetupEventListeners();
    setupDatasetsEventListeners();
};

// Export functions for global access
window.addField = addField;
window.removeField = removeField;
window.validateSchema = validateSchema;
window.generateData = generateData;
window.exportData = exportData;
window.refreshDatasets = refreshDatasets;
window.viewDataset = viewDataset;
window.exportDataset = exportDataset;
window.deleteDataset = deleteDataset;
