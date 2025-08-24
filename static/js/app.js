// Synthetic Data Generator Web App JavaScript

// Global variables
let currentResults = null;
let schemaTemplates = {};
let availableModels = {};
let currentDatasets = [];
let currentPage = 0;
let datasetsPerPage = 10;
let currentSchema = null;

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
        
        // Initialize tables section to be hidden
        hideTablesSection();
        
        // Initialize results container to be hidden
        hideResultsContainer();
        
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
        console.log('Loading schema templates...');
        const response = await fetch('/api/schema-templates');
        const data = await response.json();
        
        console.log('Schema templates response:', data);
        
        if (data.success) {
            // Convert schema templates to the format expected by the dropdown
            const templates = {};
            data.templates.forEach((template, index) => {
                const key = `template_${template.id}`;
                templates[key] = {
                    name: template.name,
                    description: template.description,
                    schema_definition: template.schema_definition
                };
            });
            
            console.log('Converted templates:', templates);
            schemaTemplates = templates;
            populateSchemaTemplateDropdown(templates);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load schema templates:', error);
        // Create a default template if loading fails
        console.log('Creating default template due to loading failure');
        const defaultTemplate = {
            'template_default': {
                name: 'Default Schema',
                description: 'Default schema template',
                schema_definition: {
                    name: 'default_table',
                    fields: [
                        { name: 'id', type: 'INTEGER', required: true },
                        { name: 'name', type: 'STRING', required: true },
                        { name: 'email', type: 'EMAIL', required: false }
                    ]
                }
            }
        };
        schemaTemplates = defaultTemplate;
        populateSchemaTemplateDropdown(defaultTemplate);
    }
}

function populateSchemaTemplateDropdown(templates) {
    console.log('Populating schema template dropdown with:', templates);
    const schemaNameSelect = document.getElementById('schemaName');
    if (!schemaNameSelect) {
        console.error('Schema name dropdown not found in populateSchemaTemplateDropdown');
        return;
    }
    
    console.log('Found schema name dropdown, clearing and populating...');
    schemaNameSelect.innerHTML = '<option value="">Choose a schema...</option>';
    
    if (Object.keys(templates).length === 0) {
        // No templates available
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'No schemas available - Create one in Schema Admin';
        option.disabled = true;
        schemaNameSelect.appendChild(option);
        console.log('No templates available, showing placeholder message');
    } else {
        Object.entries(templates).forEach(([key, template]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = `🔧 ${template.name}`;
            option.style.fontWeight = 'bold';
            schemaNameSelect.appendChild(option);
            console.log('Added option:', key, template.name);
        });
    }
    
    console.log('Dropdown populated with', Object.keys(templates).length, 'options');
}

async function refreshSchemaTemplates() {
    try {
        await loadSchemaTemplates();
        showAlert('Schema templates refreshed successfully!', 'success');
    } catch (error) {
        console.error('Failed to refresh schema templates:', error);
        showAlert('Failed to refresh schema templates', 'danger');
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
    
    // Schema name selector
    const schemaNameSelect = document.getElementById('schemaName');
    if (schemaNameSelect) {
        console.log('Schema name dropdown found, attaching event listener');
        schemaNameSelect.addEventListener('change', function() {
            console.log('Schema name dropdown changed:', this.value);
            if (this.value) {
                loadSchemaTemplate(this.value);
                showSchemaConfiguration();
                showTablesSection();
            } else {
                clearSchemaConfiguration();
                hideSchemaConfiguration();
                hideTablesSection();
            }
        });
    } else {
        console.error('Schema name dropdown not found!');
    }
    
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

function addFieldToTableElement(fieldsContainer) {
    const template = document.getElementById('fieldTemplate');
    
    if (!template) {
        console.error('Field template not found!');
        return;
    }
    
    const fieldElement = template.content.cloneNode(true);
    
    // Set unique field name
    const fieldNameInput = fieldElement.querySelector('.field-name');
    const fieldCount = fieldsContainer.children.length + 1;
    fieldNameInput.value = `field_${fieldCount}`;
    
    console.log('Adding field to container:', fieldsContainer);
    console.log('Field element:', fieldElement);
    
    fieldsContainer.appendChild(fieldElement);
}

function addTableToSchema() {
    console.log('=== ADD TABLE DEBUG ===');
    const container = document.getElementById('schemaTablesContainer');
    console.log('Container:', container);
    
    const tableCount = container.querySelectorAll('.nav-item').length + 1;
    const defaultName = `table_${tableCount}`;
    const tableId = `table_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    console.log('Table count:', tableCount, 'Default name:', defaultName, 'Table ID:', tableId);
    
    // Initialize tabs structure if it doesn't exist
    if (!container.querySelector('.nav-tabs')) {
        console.log('Initializing tabs structure...');
        container.innerHTML = `
            <ul class="nav nav-tabs" id="schemaTabs" role="tablist">
            </ul>
            <div class="tab-content" id="schemaTabContent">
            </div>
        `;
        console.log('Tabs structure initialized. Container HTML:', container.innerHTML);
    } else {
        console.log('Tabs structure already exists');
    }
    
    const tabList = container.querySelector('.nav-tabs');
    const tabContent = container.querySelector('.tab-content');
    
    // Create tab navigation item
    const tabItem = document.createElement('li');
    tabItem.className = 'nav-item';
    tabItem.role = 'presentation';
    tabItem.innerHTML = `
        <button class="nav-link active" 
                id="tab-${tableId}" 
                data-bs-toggle="tab" 
                data-bs-target="#content-${tableId}" 
                type="button" 
                role="tab" 
                aria-controls="content-${tableId}" 
                aria-selected="true">
            <span class="table-name">${defaultName}</span>
            <button type="button" class="remove-table-btn" onclick="removeTableFromSchema('${tableId}')" title="Remove Table">
                <i class="fas fa-times"></i>
            </button>
        </button>
    `;
    
    // Create tab content
    const tabPane = document.createElement('div');
    tabPane.className = 'tab-pane fade show active';
    tabPane.id = `content-${tableId}`;
    tabPane.setAttribute('role', 'tabpanel');
    tabPane.setAttribute('aria-labelledby', `tab-${tableId}`);
    tabPane.innerHTML = `
        <div class="table-config">
            <div class="row mb-3">
                <div class="col-md-6">
                    <label class="form-label fw-bold">Table Name</label>
                    <input type="text" class="form-control table-name" value="${defaultName}" 
                           onchange="updateTableName('${tableId}', this.value)">
                </div>
                <div class="col-md-6">
                    <label class="form-label fw-bold">Display Name</label>
                    <input type="text" class="form-control table-display-name" placeholder="Table Display Name">
                </div>
            </div>
            
            <div class="mb-3">
                <div class="mb-2">
                    <label class="form-label fw-bold mb-0">Fields</label>
                </div>
                <div class="fields-container">
                    <!-- Fields will be added here -->
                </div>
            </div>
        </div>
    `;
    
    // Add to DOM
    tabList.appendChild(tabItem);
    tabContent.appendChild(tabPane);
    
    console.log('Added tab to DOM. TabList children:', tabList.children.length);
    console.log('Added tabPane to DOM. TabContent children:', tabContent.children.length);
    
    // Add initial field
    const fieldsContainer = tabPane.querySelector('.fields-container');
    console.log('Found fieldsContainer:', fieldsContainer);
    addFieldToTableElement(fieldsContainer);
    
    // Update other tabs to not be active
    tabList.querySelectorAll('.nav-link').forEach(link => {
        if (link !== tabItem.querySelector('.nav-link')) {
            link.classList.remove('active');
            link.setAttribute('aria-selected', 'false');
        }
    });
    
    tabContent.querySelectorAll('.tab-pane').forEach(pane => {
        if (pane !== tabPane) {
            pane.classList.remove('show', 'active');
        }
    });
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

function addFieldToTable(tableId) {
    const tabPane = document.getElementById(`content-${tableId}`);
    const fieldsContainer = tabPane.querySelector('.fields-container');
    addFieldToTableElement(fieldsContainer);
}

function removeFieldFromTable(button) {
    button.closest('.field-item').remove();
}

function removeTableFromSchema(tableId) {
    const tabItem = document.querySelector(`#tab-${tableId}`).closest('.nav-item');
    const tabPane = document.getElementById(`content-${tableId}`);
    
    // Remove tab and content
    tabItem.remove();
    tabPane.remove();
    
    // If no tabs left, clear the container
    const container = document.getElementById('schemaTablesContainer');
    if (container.querySelectorAll('.nav-item').length === 0) {
        container.innerHTML = '';
    } else {
        // Activate the first remaining tab
        const firstTab = container.querySelector('.nav-link');
        const firstPane = container.querySelector('.tab-pane');
        if (firstTab && firstPane) {
            firstTab.classList.add('active');
            firstTab.setAttribute('aria-selected', 'true');
            firstPane.classList.add('show', 'active');
        }
    }
}

function removeFieldFromTable(button) {
    button.closest('.field-item').remove();
}

function updateTableName(tableId, newName) {
    const tabLink = document.querySelector(`#tab-${tableId} .table-name`);
    if (tabLink) {
        tabLink.textContent = newName || 'Unnamed Table';
    }
}

function addQuickTestTable() {
    console.log('=== QUICK START DEBUG ===');
    
    // Check if field template exists
    const fieldTemplate = document.getElementById('fieldTemplate');
    console.log('Field template found:', !!fieldTemplate);
    
    if (!fieldTemplate) {
        console.error('CRITICAL ERROR: Field template not found!');
        showAlert('Error: Field template not found. Please refresh the page.', 'danger');
        return;
    }
    
    // Show schema configuration if hidden
    showSchemaConfiguration();
    console.log('Schema configuration shown');
    
    // Clear any existing content
    const container = document.getElementById('schemaTablesContainer');
    console.log('Container before clear:', container.innerHTML);
    container.innerHTML = '';
    console.log('Container after clear:', container.innerHTML);
    
    // Add a table
    console.log('Adding table...');
    addTableToSchema();
    
    // Set a default schema name if empty
    const schemaNameInput = document.getElementById('schemaName');
    if (!schemaNameInput.value.trim()) {
        schemaNameInput.value = 'Test Schema';
    }
    
    // Set a default description if empty - removed since we simplified the interface
    // const schemaDescriptionInput = document.getElementById('schemaDescription');
    // if (!schemaDescriptionInput.value.trim()) {
    //     schemaDescriptionInput.value = 'Quick test schema for data generation';
    // }
    
    // Clear any existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    showAlert('Quick test table added! You can now modify the fields and generate data.', 'success');
    
    // Debug: Check if table was added
    setTimeout(() => {
        console.log('=== POST QUICK START DEBUG ===');
        const tabPanes = document.querySelectorAll('#schemaTablesContainer .tab-pane');
        console.log('After quick start - Found tabPanes:', tabPanes.length);
        console.log('TabPanes:', tabPanes);
        
        if (tabPanes.length > 0) {
            const fieldsContainer = tabPanes[0].querySelector('.fields-container');
            console.log('Fields container found:', !!fieldsContainer);
            console.log('Fields container HTML:', fieldsContainer?.innerHTML);
            
            const fieldItems = fieldsContainer.querySelectorAll('.field-item');
            console.log('After quick start - Found fieldItems:', fieldItems.length);
            console.log('Field items:', fieldItems);
            
            // Test schema collection
            const testSchema = collectSchemaData();
            console.log('Test schema collection result:', testSchema);
        } else {
            console.log('No tab panes found! Container HTML:', container.innerHTML);
        }
    }, 100);
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
    
    // Clear existing tables
    document.getElementById('schemaTablesContainer').innerHTML = '';
    
    // Handle schema definition structure
    if (template.schema_definition.tables && template.schema_definition.tables.length > 0) {
        // Multi-table schema
        template.schema_definition.tables.forEach(tableDef => {
            addTableToSchemaWithData(tableDef);
        });
    } else if (template.schema_definition.fields) {
        // Single table schema - convert to table format
        const singleTable = {
            name: template.schema_definition.name || 'table',
            display_name: template.schema_definition.name || 'Table',
            fields: template.schema_definition.fields
        };
        addTableToSchemaWithData(singleTable);
    }
}

function addTableToSchemaWithData(tableDef) {
    console.log('Adding table with data:', tableDef);
    
    const container = document.getElementById('schemaTablesContainer');
    const tableCount = container.querySelectorAll('.nav-item').length + 1;
    const tableId = `table_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Initialize tabs structure if it doesn't exist
    if (!container.querySelector('.nav-tabs')) {
        container.innerHTML = `
            <ul class="nav nav-tabs" id="schemaTabs" role="tablist">
            </ul>
            <div class="tab-content" id="schemaTabContent">
            </div>
        `;
    }
    
    const tabList = container.querySelector('.nav-tabs');
    const tabContent = container.querySelector('.tab-content');
    
    // Create tab navigation item
    const tabItem = document.createElement('li');
    tabItem.className = 'nav-item';
    tabItem.role = 'presentation';
    tabItem.innerHTML = `
        <button class="nav-link ${tableCount === 1 ? 'active' : ''}" 
                id="tab-${tableId}" 
                data-bs-toggle="tab" 
                data-bs-target="#content-${tableId}" 
                type="button" 
                role="tab" 
                aria-controls="content-${tableId}" 
                aria-selected="${tableCount === 1 ? 'true' : 'false'}">
            <span class="table-name">${tableDef.name || tableDef.display_name || `Table ${tableCount}`}</span>
        </button>
    `;
    
    // Create tab content
    const tabPane = document.createElement('div');
    tabPane.className = `tab-pane fade ${tableCount === 1 ? 'show active' : ''}`;
    tabPane.id = `content-${tableId}`;
    tabPane.setAttribute('role', 'tabpanel');
    tabPane.setAttribute('aria-labelledby', `tab-${tableId}`);
    
    // Add table name input (read-only)
    const tableNameHtml = `
        <div class="row mb-3">
            <div class="col-md-6">
                <label class="form-label">Table Name *</label>
                <input type="text" class="form-control table-name" value="${tableDef.name || ''}" placeholder="table_name" readonly>
            </div>
            <div class="col-md-6">
                <label class="form-label">Display Name</label>
                <input type="text" class="form-control table-display-name" value="${tableDef.display_name || ''}" placeholder="Table Display Name" readonly>
            </div>
        </div>
    `;
    
    // Add fields section
    const fieldsHtml = `
        <div class="mb-3">
            <div class="mb-2">
                <label class="form-label mb-0">Fields</label>
            </div>
            <div class="fields-container">
                ${tableDef.fields ? tableDef.fields.map(field => createFieldHtml(field)).join('') : ''}
            </div>
        </div>
    `;
    
    tabPane.innerHTML = tableNameHtml + fieldsHtml;
    
    // Add to DOM
    tabList.appendChild(tabItem);
    tabContent.appendChild(tabPane);
    
    // If no fields exist, show empty state
    if (!tableDef.fields || tableDef.fields.length === 0) {
        const fieldsContainer = tabPane.querySelector('.fields-container');
        if (fieldsContainer) {
            fieldsContainer.innerHTML = '<div class="text-muted text-center py-3">No fields defined in this template</div>';
        }
    }
}

function createFieldHtml(field) {
    return `
        <div class="field-item p-3">
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Field Name *</label>
                    <input type="text" class="form-control field-name" value="${field.name || ''}" placeholder="field_name" readonly>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Data Type</label>
                    <select class="form-select field-type" disabled>
                        <option value="STRING" ${field.type === 'STRING' ? 'selected' : ''}>String</option>
                        <option value="INTEGER" ${field.type === 'INTEGER' ? 'selected' : ''}>Integer</option>
                        <option value="FLOAT" ${field.type === 'FLOAT' ? 'selected' : ''}>Float</option>
                        <option value="BOOLEAN" ${field.type === 'BOOLEAN' ? 'selected' : ''}>Boolean</option>
                        <option value="DATE" ${field.type === 'DATE' ? 'selected' : ''}>Date</option>
                        <option value="DATETIME" ${field.type === 'DATETIME' ? 'selected' : ''}>DateTime</option>
                        <option value="EMAIL" ${field.type === 'EMAIL' ? 'selected' : ''}>Email</option>
                        <option value="PHONE" ${field.type === 'PHONE' ? 'selected' : ''}>Phone</option>
                        <option value="ADDRESS" ${field.type === 'ADDRESS' ? 'selected' : ''}>Address</option>
                        <option value="NAME" ${field.type === 'NAME' ? 'selected' : ''}>Name</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Required</label>
                    <div class="form-check mt-2">
                        <input class="form-check-input field-required" type="checkbox" ${field.required !== false ? 'checked' : ''} disabled>
                        <label class="form-check-label">Required</label>
                    </div>
                </div>
                <div class="col-md-2">
                    <label class="form-label">&nbsp;</label>
                    <!-- Field delete button removed - read-only display -->
                </div>
            </div>
        </div>
    `;
}

function showSchemaConfiguration() {
    // Show all schema configuration elements
    const schemaElements = [
        'schemaName'
    ];
    
    schemaElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.closest('.mb-3').style.display = 'block';
        }
    });
}

function showTablesSection() {
    const tablesSection = document.getElementById('tablesSection');
    if (tablesSection) {
        tablesSection.style.display = 'block';
    }
}

function hideTablesSection() {
    const tablesSection = document.getElementById('tablesSection');
    if (tablesSection) {
        tablesSection.style.display = 'none';
    }
}

function hideSchemaConfiguration() {
    // Hide all schema configuration elements
    const schemaElements = [
        'schemaName'
    ];
    
    schemaElements.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.closest('.mb-3').style.display = 'none';
        }
    });
}

function clearSchemaConfiguration() {
    // Clear schema name dropdown
    const schemaNameSelect = document.getElementById('schemaName');
    if (schemaNameSelect) {
        schemaNameSelect.value = '';
    }
    
    // Clear tables container
    document.getElementById('schemaTablesContainer').innerHTML = '';
}

function hideResultsContainer() {
    // Hide the results container and export buttons
    const resultsContainer = document.getElementById('resultsContainer');
    const exportButtons = document.getElementById('exportButtons');
    
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
    if (exportButtons) {
        exportButtons.classList.add('d-none');
    }
}

function showResultsContainer() {
    // Show the results container
    const resultsContainer = document.getElementById('resultsContainer');
    if (resultsContainer) {
        resultsContainer.style.display = 'block';
    }
}



async function generateData() {
    const schema = collectSchemaData();
    const generationParams = collectGenerationParams();
    
    console.log('Collected schema data:', schema);
    console.log('Collected generation params:', generationParams);
    
    // Check if we have any tables or fields
    const hasTables = schema.tables && schema.tables.length > 0;
    const hasFields = schema.fields && schema.fields.length > 0;
    
    console.log('Has tables:', hasTables, 'Has fields:', hasFields);
    
    if (!hasTables && !hasFields) {
        console.log('No schema configured, automatically creating basic schema...');
        
        // Show schema configuration
        showSchemaConfiguration();
        
        // Set default schema name if empty
        const schemaNameSelect = document.getElementById('schemaName');
        if (!schemaNameSelect.value) {
            // Create a default option if none selected
            const defaultOption = document.createElement('option');
            defaultOption.value = 'default';
            defaultOption.textContent = '🔧 Test Schema';
            defaultOption.style.fontWeight = 'bold';
            schemaNameSelect.appendChild(defaultOption);
            schemaNameSelect.value = 'default';
        }
        
        // Set default description if empty - removed since we simplified the interface
        // const schemaDescriptionInput = document.getElementById('schemaDescription');
        // if (!schemaDescriptionInput.value.trim()) {
        //     schemaDescriptionInput.value = 'Automatically created test schema';
        // }
        
        // Add a table automatically
        addTableToSchema();
        
        // Wait a moment for the table to be created, then retry
        setTimeout(() => {
            console.log('Retrying data generation with auto-created schema...');
            generateData(); // Recursive call to retry with the new schema
        }, 100);
        
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
            currentSchema = schema; // Store current schema for test database
            displayResults(data);
            showAlert(`Successfully generated ${data.total_records} records! 🎉`, 'success');
            
            // Automatically switch to Generated Data tab
            const generatedTab = document.getElementById('generated-tab');
            if (generatedTab) {
                generatedTab.click();
            }
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

function getSelectedSchemaName() {
    const schemaNameSelect = document.getElementById('schemaName');
    if (!schemaNameSelect || !schemaNameSelect.value) {
        return '';
    }
    
    // Get the selected option's text (schema name) instead of value (template ID)
    const selectedOption = schemaNameSelect.options[schemaNameSelect.selectedIndex];
    return selectedOption ? selectedOption.textContent.replace('🔧 ', '') : '';
}

function collectSchemaData() {
    console.log('=== COLLECT SCHEMA DATA DEBUG ===');
    
    // Check if schema configuration is visible
    const schemaConfig = document.querySelector('.schema-configuration');
    const isVisible = schemaConfig && schemaConfig.style.display !== 'none';
    console.log('Schema configuration visible:', isVisible);
    
    // Check schema tables container
    const container = document.getElementById('schemaTablesContainer');
    console.log('Schema tables container found:', !!container);
    console.log('Container HTML:', container?.innerHTML);
    
    const tabPanes = document.querySelectorAll('#schemaTablesContainer .tab-pane');
    
    console.log('Found tabPanes:', tabPanes.length);
    console.log('TabPanes:', tabPanes);
    
        if (tabPanes.length === 0) {
        console.log('No tab panes found, returning empty schema');
        return {
            name: getSelectedSchemaName(),
            fields: []
        };
    }

    if (tabPanes.length === 1) {
        // Single table schema
        const tabPane = tabPanes[0];
        const fields = collectTableFields(tabPane);
        
        return {
            name: getSelectedSchemaName(),
            fields: fields
        };
    } else {
        // Multi-table schema
        const tables = [];
        tabPanes.forEach(tabPane => {
            const tableNameInput = tabPane.querySelector('.table-name');
            const displayNameInput = tabPane.querySelector('.table-display-name');
            
            const tableName = tableNameInput ? tableNameInput.value.trim() : '';
            const displayName = displayNameInput ? displayNameInput.value.trim() : '';
            
            if (tableName) {
                const fields = collectTableFields(tabPane);
                tables.push({
                    name: tableName,
                    display_name: displayName || tableName,
                    fields: fields
                });
            }
        });
        
        return {
            name: getSelectedSchemaName(),
            tables: tables
        };
    }
}

function collectTableFields(tableItem) {
    const fields = [];
    const fieldItems = tableItem.querySelectorAll('.field-item');
    
    console.log('Collecting fields from tableItem:', tableItem);
    console.log('Found fieldItems:', fieldItems.length);
    
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
            
            console.log('Processing field:', field);
            
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
    
    return fields;
}

function collectGenerationParams() {
    return {
        model: document.getElementById('modelSelect').value,
        temperature: parseFloat(document.getElementById('temperatureSlider').value),
        record_count: parseInt(document.getElementById('recordCount').value),
        recursion_limit: parseInt(document.getElementById('recursionLimit').value),
        use_contextual_generation: document.getElementById('contextualGeneration').checked,
        save_to_database: false,  // Don't automatically save to database
        save_to_sqlite: false     // Don't automatically save to SQLite
    };
}

function displayResults(data) {
    console.log('displayResults called with data:', data);
    console.log('data.generated_records:', data.generated_records);
    console.log('data.generated_records type:', typeof data.generated_records);
    console.log('data.generated_records is array:', Array.isArray(data.generated_records));
    console.log('data.generated_records length:', data.generated_records ? data.generated_records.length : 'undefined');
    
    const resultsContainer = document.getElementById('resultsContainer');
    const exportButtons = document.getElementById('exportButtons');
    
    // Show the results container first
    showResultsContainer();
    
    // Check if this is multi-table data
    if (data.generated_records && typeof data.generated_records === 'object' && !Array.isArray(data.generated_records)) {
        // Multi-table data
        displayMultiTableResults(data, resultsContainer);
        exportButtons.classList.remove('d-none');
    } else if (data.generated_records && data.generated_records.length > 0) {
        // Single table data
        resultsContainer.innerHTML = '';
        
        // Add table header with info
        const tableHeader = document.createElement('div');
        tableHeader.className = 'd-flex justify-content-between align-items-center mb-3';
        tableHeader.innerHTML = `
            <div>
                <h6 class="mb-0">
                    <i class="fas fa-table me-2 text-primary"></i>
                    Generated Data
                </h6>
                <small class="text-muted">Showing ${data.generated_records.length} records</small>
            </div>
            <div class="table-badge primary">
                ${data.generated_records.length} records
            </div>
        `;
        resultsContainer.appendChild(tableHeader);
        
        // Create scrollable table container
        const tableContainer = document.createElement('div');
        tableContainer.className = 'data-table-container';
        
        const table = createDataTable(data.generated_records);
        tableContainer.appendChild(table);
        resultsContainer.appendChild(tableContainer);
        
        // Show export buttons
        exportButtons.classList.remove('d-none');
    } else {
        resultsContainer.innerHTML = '<div class="alert alert-warning">No data was generated.</div>';
    }
}

function displayMultiTableResults(data, container) {
    container.innerHTML = '';
    
    // Create enhanced tabs container for each table
    const tabContainer = document.createElement('div');
    tabContainer.className = 'multi-table-tabs';
    
    const tabList = document.createElement('ul');
    tabList.className = 'nav nav-tabs';
    tabList.id = 'multiTableTabs';
    
    const tabContent = document.createElement('div');
    tabContent.className = 'tab-content';
    tabContent.id = 'multiTableTabContent';
    
    let firstTab = true;
    Object.keys(data.generated_records).forEach((tableName, index) => {
        const records = data.generated_records[tableName];
        
        // Create tab with enhanced styling
        const tabItem = document.createElement('li');
        tabItem.className = 'nav-item';
        tabItem.innerHTML = `
            <button class="nav-link ${firstTab ? 'active' : ''}" 
                    data-bs-toggle="tab" 
                    data-bs-target="#table-${index}" 
                    type="button">
                <i class="fas fa-table me-2"></i>
                <span class="fw-bold">${tableName}</span>
                <span class="table-badge success ms-2">${records.length} records</span>
            </button>
        `;
        tabList.appendChild(tabItem);
        
        // Create tab content with scrollable table
        const tabPane = document.createElement('div');
        tabPane.className = `tab-pane fade ${firstTab ? 'show active' : ''}`;
        tabPane.id = `table-${index}`;
        
        if (records.length > 0) {
            // Add table header with info
            const tableHeader = document.createElement('div');
            tableHeader.className = 'd-flex justify-content-between align-items-center mb-3';
            tableHeader.innerHTML = `
                <div>
                    <h6 class="mb-0">
                        <i class="fas fa-table me-2 text-primary"></i>
                        Table: ${tableName}
                    </h6>
                    <small class="text-muted">Showing ${records.length} records</small>
                </div>
                <div class="table-badge primary">
                    ${records.length} records
                </div>
            `;
            tabPane.appendChild(tableHeader);
            
            // Create scrollable table container
            const tableContainer = document.createElement('div');
            tableContainer.className = 'data-table-container';
            
            const table = createDataTable(records);
            tableContainer.appendChild(table);
            tabPane.appendChild(tableContainer);
        } else {
            tabPane.innerHTML = `
                <div class="alert alert-warning">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    No data available for table "${tableName}"
                </div>
            `;
        }
        
        tabContent.appendChild(tabPane);
        firstTab = false;
    });
    
    tabContainer.appendChild(tabList);
    tabContainer.appendChild(tabContent);
    container.appendChild(tabContainer);
}



function createDataTable(records) {
    console.log('createDataTable called with records:', records);
    console.log('Records length:', records.length);
    console.log('Using single-line format for table display');
    
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover fade-in mb-0';
    
    if (records.length === 0) {
        console.log('No records to display');
        return table;
    }
    
    // Create header - handle both old format (record.data) and new format (direct record)
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    const firstRecord = records[0];
    console.log('First record:', firstRecord);
    console.log('First record.data:', firstRecord.data);
    console.log('First record direct keys:', Object.keys(firstRecord));
    
    const headers = Object.keys(firstRecord.data || firstRecord);
    console.log('Headers extracted:', headers);
    
    // Create single header column for compact view
    const th = document.createElement('th');
    th.className = 'text-nowrap';
    th.textContent = 'Record Data';
    headerRow.appendChild(th);
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // Create body with improved record layout
    const tbody = document.createElement('tbody');
    records.forEach((record, index) => {
        const row = document.createElement('tr');
        const recordData = record.data || record; // Handle both formats
        
        // Create single cell with improved layout
        const td = document.createElement('td');
        td.className = 'record-cell';
        
        // Create improved record display with badges and better formatting
        const recordHtml = headers.map(header => {
            const value = recordData[header] || '';
            const displayValue = typeof value === 'string' && value.length > 30 
                ? value.substring(0, 30) + '...' 
                : value;
            
            return `
                <span class="field-badge">
                    <span class="field-name">${header.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</span>
                    <span class="field-value">${displayValue}</span>
                </span>
            `;
        }).join('');
        
        td.innerHTML = recordHtml;
        row.appendChild(td);
        tbody.appendChild(row);
    });
    
    table.appendChild(tbody);
    return table;
}



async function exportData(format) {
    if (!currentResults || !currentResults.generated_records) {
        showAlert('No data to export. Please generate data first.', 'warning');
        return;
    }
    
    try {
        // Check if this is multi-table data
        if (typeof currentResults.generated_records === 'object' && !Array.isArray(currentResults.generated_records)) {
            // Multi-table data - export each table separately
            const tableNames = Object.keys(currentResults.generated_records);
            
            for (const tableName of tableNames) {
                const records = currentResults.generated_records[tableName];
                
                const response = await fetch(`/api/export/${format}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        records: records
                    })
                });
                
                if (response.ok) {
                    // Create download link
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `${tableName}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${format}`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    const data = await response.json();
                    throw new Error(`Export failed for table ${tableName}: ${data.error || 'Unknown error'}`);
                }
            }
            
            showAlert(`Multi-table data exported successfully as ${format.toUpperCase()}! 📁`, 'success');
        } else {
            // Single table data
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
        // Hide results container when starting generation
        hideResultsContainer();
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
    
    container.innerHTML = `
        <div class="table-responsive">
            <table class="table table-hover datasets-table">
                <thead class="table-light">
                    <tr>
                        <th>Dataset Name</th>
                        <th>Description</th>
                        <th>Records</th>
                        <th>Created</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${datasets.map(dataset => `
                        <tr>
                            <td>
                                <div class="d-flex align-items-center">
                                    <i class="fas fa-database me-2 text-primary"></i>
                                    <div>
                                        <div class="fw-bold">${dataset.name}</div>
                                    </div>
                                </div>
                            </td>
                            <td>
                                <div class="text-truncate" style="max-width: 200px;" title="${dataset.description || 'No description'}">
                                    ${dataset.description || 'No description'}
                                </div>
                            </td>
                            <td>
                                <span class="badge bg-primary">${formatNumber(dataset.record_count)} records</span>
                            </td>
                            <td>
                                <span class="dataset-date">${formatDate(dataset.created_at)}</span>
                            </td>
                            <td>
                                <div class="btn-group btn-group-sm">
                                    <button class="btn btn-outline-primary" onclick="viewDataset(${dataset.id})" title="View Dataset">
                                        <i class="fas fa-eye"></i>
                                    </button>
                                    <button class="btn btn-outline-success" onclick="generateSQLFromDataset(${dataset.id}, '${dataset.name}')" title="Generate SQL">
                                        <i class="fas fa-code"></i>
                                    </button>
                                    <button class="btn btn-outline-danger" onclick="deleteDataset(${dataset.id})" title="Delete Dataset">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

async function viewDataset(datasetId) {
    console.log('viewDataset called with datasetId:', datasetId);
    try {
        // Load dataset details
        const datasetResponse = await fetch(`/api/datasets/${datasetId}`);
        const datasetData = await datasetResponse.json();
        
        if (!datasetData.success) {
            showAlert(`Failed to load dataset: ${datasetData.error}`, 'danger');
            return;
        }
        
        // Load dataset records (all records, high limit to get everything)
        const recordsResponse = await fetch(`/api/datasets/${datasetId}/records?limit=10000`);
        const recordsData = await recordsResponse.json();
        
        if (!recordsData.success) {
            showAlert(`Failed to load records: ${recordsData.error}`, 'danger');
            return;
        }
        
        console.log(`Loaded ${recordsData.records.length} records from dataset ${datasetId}`);
        console.log('Dataset record count from API:', datasetData.dataset.record_count);
        
        // Switch to Generated Data tab and display the dataset
        const generatedTab = document.getElementById('generated-tab');
        if (generatedTab) {
            console.log('Switching to Generated Data tab...');
            generatedTab.click();
        } else {
            console.error('Generated Data tab not found!');
        }
        
        // Display dataset as if it was just generated
        console.log('Records loaded successfully:', recordsData.records.length);
        
        // Check if records are already in the correct format or need transformation
        let processedRecords;
        if (recordsData.records.length > 0) {
            const firstRecord = recordsData.records[0];
                    console.log('First record keys:', Object.keys(firstRecord));
        console.log('First record.record_data type:', typeof firstRecord.record_data);
        console.log('First record.record_data value:', firstRecord.record_data);
        console.log('First record.record_data keys:', firstRecord.record_data ? Object.keys(firstRecord.record_data) : 'undefined');
        
        // Check if record_data is a string that needs to be parsed
        let actualRecordData = firstRecord.record_data;
        if (typeof firstRecord.record_data === 'string') {
            try {
                actualRecordData = JSON.parse(firstRecord.record_data);
                console.log('Parsed record_data from string:', actualRecordData);
            } catch (e) {
                console.log('Failed to parse record_data string:', e);
                actualRecordData = {};
            }
        }
        
        if (actualRecordData && Object.keys(actualRecordData).length > 0) {
            // Records are in the saved format, need to extract record_data
            console.log('Using parsed record_data field');
            processedRecords = recordsData.records.map(record => {
                let recordData = record.record_data;
                if (typeof record.record_data === 'string') {
                    try {
                        recordData = JSON.parse(record.record_data);
                    } catch (e) {
                        recordData = {};
                    }
                }
                return {
                    data: recordData,
                    is_valid: record.is_valid,
                    validation_errors: record.validation_errors,
                    generation_metadata: record.generation_metadata
                };
            });
        } else if (firstRecord.data && Object.keys(firstRecord.data).length > 0) {
            // Records already have data field with content
            console.log('Using existing data field');
            processedRecords = recordsData.records;
        } else {
            // Try to find the actual data in the record
            console.log('Looking for data in record structure');
            const recordKeys = Object.keys(firstRecord);
            const dataKeys = recordKeys.filter(key => 
                key !== 'id' && 
                key !== 'dataset_id' && 
                key !== 'is_valid' && 
                key !== 'validation_errors' && 
                key !== 'generation_metadata' && 
                key !== 'created_at' &&
                key !== 'record_data' &&
                key !== 'data'
            );
            console.log('Potential data keys:', dataKeys);
            
            if (dataKeys.length > 0) {
                // Use the first data key found
                const dataKey = dataKeys[0];
                console.log('Using data key:', dataKey);
                processedRecords = recordsData.records.map(record => ({
                    data: record[dataKey],
                    is_valid: record.is_valid,
                    validation_errors: record.validation_errors,
                    generation_metadata: record.generation_metadata
                }));
            } else {
                console.log('No data found in record');
                processedRecords = [];
            }
        }
        } else {
            processedRecords = [];
        }
        
        const fakeResults = {
            generated_records: processedRecords,
            generation_metadata: datasetData.dataset.generation_metadata,
            total_records: recordsData.records.length
        };
        
        console.log('Processed records:', processedRecords);
        console.log('Displaying dataset results:', fakeResults);
        console.log('About to call displayResults with single-line format');
        console.log('Sample processed record:', processedRecords[0]);
        console.log('Sample record data structure:', processedRecords[0]?.data);
        displayResults(fakeResults);
        showAlert(`Loaded dataset: ${datasetData.dataset.name}`, 'success');
        
    } catch (error) {
        console.error('Failed to view dataset:', error);
        showAlert('Failed to view dataset', 'danger');
    }
}

async function generateSQLFromDataset(datasetId, datasetName) {
    // Show SQL generation modal
    showSQLGenerationModal(datasetId, datasetName);
}

async function generateSQLFromCurrentData() {
    // Check if we have current results
    if (!currentResults || !currentResults.generated_records) {
        showAlert('No data to generate SQL from. Please generate data first.', 'warning');
        return;
    }
    
    // Create a temporary dataset name for the current data
    const tempDatasetName = `generated_data_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`;
    
    // Show SQL generation modal with current data
    showSQLGenerationModalFromCurrentData(tempDatasetName);
}

function showSQLGenerationModal(datasetId, datasetName) {
    console.log('showSQLGenerationModal called with:', { datasetId, datasetName });
    
    const modalHtml = `
        <div class="modal fade" id="sqlGenerationModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-magic me-2"></i>
                            Generate SQL for ${datasetName}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-4">
                            <label class="form-label fw-bold">Select Database Dialect</label>
                            <select class="form-select form-select-lg" id="sqlDialectSelect">
                                <option value="">Choose a database dialect...</option>
                                <option value="mysql">🐬 MySQL</option>
                                <option value="postgresql">🐘 PostgreSQL</option>
                                <option value="sqlserver">🪟 SQL Server</option>
                                <option value="oracle">🔶 Oracle</option>
                                <option value="db2">🔵 IBM DB2</option>
                            </select>
                            <div class="form-text">
                                <small>Select your target database system to generate appropriate SQL statements</small>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label fw-bold">SQL Name</label>
                            <input type="text" class="form-control" id="sqlNameInput" 
                                   value="${datasetName}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label fw-bold">Description (Optional)</label>
                            <textarea class="form-control" id="sqlDescriptionInput" rows="2" 
                                      placeholder="Enter a description for this SQL..."></textarea>
                        </div>
                        
                        <div id="sqlResultsContainer" style="display: none;">
                            <div class="mb-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0">
                                        <i class="fas fa-code me-2"></i>
                                        Generated SQL
                                    </h6>
                                    <div>
                                        <button class="btn btn-sm btn-outline-primary me-2" onclick="copySQLToClipboard()">
                                            <i class="fas fa-copy me-1"></i>
                                            Copy
                                        </button>
                                        <button class="btn btn-sm btn-success" onclick="saveGeneratedSQL()">
                                            <i class="fas fa-save me-1"></i>
                                            Save SQL
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div id="sqlResults" class="bg-light p-3 rounded" style="max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.9em;">
                                <!-- SQL will be displayed here -->
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" id="generateSQLBtn" disabled>
                            <i class="fas fa-magic me-1"></i>
                            Generate SQL
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('sqlGenerationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('sqlGenerationModal'));
    modal.show();
    
    // Wait for modal to be fully rendered before setting up event listeners
    setTimeout(() => {
        // Add event listener for dialect selection
        const dialectSelect = document.getElementById('sqlDialectSelect');
        const generateBtn = document.getElementById('generateSQLBtn');
        
        console.log('Setting up event listeners for modal:', { dialectSelect: !!dialectSelect, generateBtn: !!generateBtn });
        
        if (dialectSelect && generateBtn) {
            // Remove any existing event listeners
            dialectSelect.removeEventListener('change', dialectSelect._changeHandler);
            generateBtn.removeEventListener('click', generateBtn._clickHandler);
            
            // Create new event handlers
            dialectSelect._changeHandler = function() {
                const hasValue = this.value && this.value.trim() !== '';
                generateBtn.disabled = !hasValue;
                console.log('Dialect selected:', this.value, 'Button disabled:', generateBtn.disabled, 'Has value:', hasValue);
            };
            
            generateBtn._clickHandler = function() {
                console.log('Generate button clicked');
                generateSQLWithLLM(datasetId);
            };
            
            // Add event listeners
            dialectSelect.addEventListener('change', dialectSelect._changeHandler);
            generateBtn.addEventListener('click', generateBtn._clickHandler);
            
            // Initial state
            dialectSelect._changeHandler.call(dialectSelect);
            console.log('Initial button state - disabled:', generateBtn.disabled);
        } else {
            console.error('Could not find modal elements:', { dialectSelect: !!dialectSelect, generateBtn: !!generateBtn });
        }
    }, 200);
}

function showSQLGenerationModalFromCurrentData(datasetName) {
    console.log('showSQLGenerationModalFromCurrentData called with:', { datasetName });
    
    const modalHtml = `
        <div class="modal fade" id="sqlGenerationModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-magic me-2"></i>
                            Generate SQL for Current Data
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-4">
                            <label class="form-label fw-bold">Select Database Dialect</label>
                            <select class="form-select form-select-lg" id="sqlDialectSelect">
                                <option value="">Choose a database dialect...</option>
                                <option value="mysql">🐬 MySQL</option>
                                <option value="postgresql">🐘 PostgreSQL</option>
                                <option value="sqlserver">🪟 SQL Server</option>
                                <option value="oracle">🔶 Oracle</option>
                                <option value="db2">🔵 IBM DB2</option>
                            </select>
                            <div class="form-text">
                                <small>Select your target database system to generate appropriate SQL statements</small>
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label fw-bold">SQL Name</label>
                            <input type="text" class="form-control" id="sqlNameInput" 
                                   value="${datasetName}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}">
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label fw-bold">Description (Optional)</label>
                            <textarea class="form-control" id="sqlDescriptionInput" rows="2" 
                                      placeholder="Enter a description for this SQL..."></textarea>
                        </div>
                        
                        <div id="sqlResultsContainer" style="display: none;">
                            <div class="mb-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0">
                                        <i class="fas fa-code me-2"></i>
                                        Generated SQL
                                    </h6>
                                    <div>
                                        <button class="btn btn-sm btn-outline-primary me-2" onclick="copySQLToClipboard()">
                                            <i class="fas fa-copy me-1"></i>
                                            Copy
                                        </button>
                                        <button class="btn btn-sm btn-success" onclick="saveGeneratedSQL()">
                                            <i class="fas fa-save me-1"></i>
                                            Save SQL
                                        </button>
                                    </div>
                                </div>
                            </div>
                            <div id="sqlResults" class="bg-light p-3 rounded" style="max-height: 400px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.9em;">
                                <!-- SQL will be displayed here -->
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" id="generateSQLBtn" disabled>
                            <i class="fas fa-magic me-1"></i>
                            Generate SQL
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('sqlGenerationModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('sqlGenerationModal'));
    modal.show();
    
    // Wait for modal to be fully rendered before setting up event listeners
    setTimeout(() => {
        // Add event listener for dialect selection
        const dialectSelect = document.getElementById('sqlDialectSelect');
        const generateBtn = document.getElementById('generateSQLBtn');
        
        console.log('Setting up event listeners for current data modal:', { dialectSelect: !!dialectSelect, generateBtn: !!generateBtn });
        
        if (dialectSelect && generateBtn) {
            // Remove any existing event listeners
            dialectSelect.removeEventListener('change', dialectSelect._changeHandler);
            generateBtn.removeEventListener('click', generateBtn._clickHandler);
            
            // Create new event handlers
            dialectSelect._changeHandler = function() {
                const hasValue = this.value && this.value.trim() !== '';
                generateBtn.disabled = !hasValue;
                console.log('Dialect selected:', this.value, 'Button disabled:', generateBtn.disabled, 'Has value:', hasValue);
            };
            
            generateBtn._clickHandler = function() {
                console.log('Generate button clicked for current data');
                generateSQLWithLLMFromCurrentData();
            };
            
            // Add event listeners
            dialectSelect.addEventListener('change', dialectSelect._changeHandler);
            generateBtn.addEventListener('click', generateBtn._clickHandler);
            
            // Initial state
            dialectSelect._changeHandler.call(dialectSelect);
            console.log('Initial button state - disabled:', generateBtn.disabled);
        } else {
            console.error('Could not find modal elements:', { dialectSelect: !!dialectSelect, generateBtn: !!generateBtn });
        }
    }, 200);
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



// Setup event listeners for schema admin tab
// Update the main setup function
const originalSetupEventListeners = setupEventListeners;
setupEventListeners = function() {
    originalSetupEventListeners();
    setupDatasetsEventListeners();
    setupSchemaAdminEventListeners();
    setupGeneratedSQLEventListeners();
};

function setupSchemaAdminEventListeners() {
    const schemaAdminTab = document.getElementById('schema-admin-tab');
    if (schemaAdminTab) {
        schemaAdminTab.addEventListener('shown.bs.tab', function() {
            refreshSchemasInTab();
        });
    }
}

// Schema Administration Functions for Tab
let currentSchemasInTab = [];
let editingSchemaIdInTab = null;

async function refreshSchemasInTab() {
    try {
        const response = await fetch('/api/schema-templates');
        const data = await response.json();
        
        if (data.success) {
            currentSchemasInTab = data.templates;
            displaySchemasInTab(data.templates);
        } else {
            showAlert('Failed to load schemas: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Failed to load schemas: ' + error.message, 'danger');
    }
}

function displaySchemasInTab(schemas) {
    const container = document.getElementById('schemasTableBody');
    
    if (!schemas || schemas.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-5">
                    <i class="fas fa-cogs fa-2x mb-3 d-block"></i>
                    <h5>No Schema Templates Yet</h5>
                    <p class="mb-0">Create your first schema template to get started.</p>
                </td>
            </tr>
        `;
        return;
    }

    container.innerHTML = schemas.map(schema => {
        // Count tables and fields
        const tables = schema.schema_definition?.tables || [];
        const totalFields = tables.reduce((sum, table) => sum + (table.fields?.length || 0), 0);
        
        return `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <i class="fas fa-database me-2 text-primary"></i>
                        <div>
                            <div class="fw-bold">${schema.name}</div>
                            <small class="text-muted">Created: ${new Date(schema.created_at).toLocaleDateString()}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="text-truncate" style="max-width: 300px;" title="${schema.description || 'No description'}">
                        ${schema.description || 'No description'}
                    </div>
                </td>
                <td>
                    <span class="badge bg-info">${tables.length} table${tables.length !== 1 ? 's' : ''}</span>
                </td>
                <td>
                    <span class="badge bg-success">${totalFields} field${totalFields !== 1 ? 's' : ''}</span>
                </td>
                <td>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editSchemaInTab(${schema.id})" title="Edit Schema">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-info" onclick="viewSchemaDetailsInTab(${schema.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-outline-success" onclick="copySchemaInTab(${schema.id})" title="Copy Schema">
                            <i class="fas fa-copy"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteSchemaInTab(${schema.id})" title="Delete Schema">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function showCreateSchemaModalInTab() {
    editingSchemaIdInTab = null;
    document.getElementById('modalTitleInTab').textContent = 'Create New Schema';
    document.getElementById('schemaFormInTab').reset();
    document.getElementById('tablesContainerInTab').innerHTML = '';
    addTableInTab();
    new bootstrap.Modal(document.getElementById('schemaModalInTab')).show();
}

function addTableInTab() {
    const container = document.getElementById('tablesContainerInTab');
    const tableCount = container.children.length + 1;
    
    const tableHtml = `
        <div class="table-item p-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">Table ${tableCount}</h6>
                <button type="button" class="btn btn-outline-danger btn-sm" onclick="removeTableInTab(this)">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-6">
                    <label class="form-label">Table Name *</label>
                    <input type="text" class="form-control table-name" placeholder="table_name" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label">Display Name</label>
                    <input type="text" class="form-control table-display-name" placeholder="Table Display Name">
                </div>
            </div>
            
            <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <label class="form-label mb-0">Fields</label>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="addFieldInTab(this)">
                        <i class="fas fa-plus me-1"></i>Add Field
                    </button>
                </div>
                <div class="fields-container">
                    <!-- Fields will be added here -->
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', tableHtml);
    
    // Automatically add a default field to the new table
    const newTable = container.lastElementChild;
    const addFieldBtn = newTable.querySelector('.btn-outline-secondary');
    if (addFieldBtn) {
        addFieldBtn.click();
    }
}

function removeTableInTab(button) {
    button.closest('.table-item').remove();
}

function addFieldInTab(button) {
    const fieldsContainer = button.parentElement.nextElementSibling;
    
    const fieldHtml = `
        <div class="field-item p-3">
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Field Name *</label>
                    <input type="text" class="form-control field-name" placeholder="field_name" required>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Data Type</label>
                    <select class="form-select field-type">
                        <option value="STRING">String</option>
                        <option value="INTEGER">Integer</option>
                        <option value="FLOAT">Float</option>
                        <option value="BOOLEAN">Boolean</option>
                        <option value="DATE">Date</option>
                        <option value="DATETIME">DateTime</option>
                        <option value="EMAIL">Email</option>
                        <option value="PHONE">Phone</option>
                        <option value="ADDRESS">Address</option>
                        <option value="NAME">Name</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Required</label>
                    <div class="form-check mt-2">
                        <input class="form-check-input field-required" type="checkbox" checked>
                        <label class="form-check-label">Required</label>
                    </div>
                </div>
                <div class="col-md-2">
                    <label class="form-label">&nbsp;</label>
                    <button class="btn btn-outline-danger btn-sm w-100" onclick="removeFieldInTab(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    fieldsContainer.insertAdjacentHTML('beforeend', fieldHtml);
}

function removeFieldInTab(button) {
    button.closest('.field-item').remove();
}

async function saveSchemaInTab() {
    try {
        const name = document.getElementById('schemaNameInTab').value.trim();
        if (!name) {
            showAlert('Schema name is required', 'danger');
            return;
        }

        const tables = [];
        const tableItems = document.querySelectorAll('#tablesContainerInTab .table-item');
        
        for (let tableItem of tableItems) {
            const tableName = tableItem.querySelector('.table-name').value.trim();
            if (!tableName) {
                showAlert('All tables must have a name', 'danger');
                return;
            }

            const fields = [];
            const fieldItems = tableItem.querySelectorAll('.field-item');
            
            for (let fieldItem of fieldItems) {
                const fieldName = fieldItem.querySelector('.field-name').value.trim();
                if (!fieldName) {
                    showAlert('All fields must have a name', 'danger');
                    return;
                }

                fields.push({
                    name: fieldName,
                    type: fieldItem.querySelector('.field-type').value,
                    required: fieldItem.querySelector('.field-required').checked
                });
            }

            if (fields.length === 0) {
                showAlert('All tables must have at least one field', 'danger');
                return;
            }

            tables.push({
                name: tableName,
                display_name: tableItem.querySelector('.table-display-name').value.trim() || tableName,
                fields: fields
            });
        }

        if (tables.length === 0) {
            showAlert('Schema must have at least one table', 'danger');
            return;
        }

        const schemaData = {
            name: name,
            description: document.getElementById('schemaDescriptionInTab').value.trim(),
            schema_definition: {
                name: name,
                description: document.getElementById('schemaDescriptionInTab').value.trim(),
                tables: tables
            }
        };

        const url = editingSchemaIdInTab ? `/api/schema-templates/${editingSchemaIdInTab}` : '/api/schema-templates';
        const method = editingSchemaIdInTab ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(schemaData)
        });

        const data = await response.json();
        
        if (data.success) {
            showAlert(`Schema ${editingSchemaIdInTab ? 'updated' : 'created'} successfully!`, 'success');
            bootstrap.Modal.getInstance(document.getElementById('schemaModalInTab')).hide();
            refreshSchemasInTab();
            loadSchemaTemplates(); // Refresh main dropdown
        } else {
            showAlert('Failed to save schema: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Failed to save schema: ' + error.message, 'danger');
    }
}

async function editSchemaInTab(schemaId) {
    try {
        const response = await fetch(`/api/schema-templates/${schemaId}`);
        const data = await response.json();
        
        if (data.success) {
            const schema = data.template;
            editingSchemaIdInTab = schemaId;
            
            document.getElementById('modalTitleInTab').textContent = 'Edit Schema';
            document.getElementById('schemaIdInTab').value = schemaId;
            document.getElementById('schemaNameInTab').value = schema.name;
            document.getElementById('schemaDescriptionInTab').value = schema.description || '';
            
            // Clear and populate tables
            document.getElementById('tablesContainerInTab').innerHTML = '';
            
            if (schema.schema_definition.tables) {
                schema.schema_definition.tables.forEach(tableDef => {
                    addTableWithDataInTab(tableDef);
                });
            } else {
                addTableInTab(); // Add empty table if no tables
            }
            
            new bootstrap.Modal(document.getElementById('schemaModalInTab')).show();
        } else {
            showAlert('Failed to load schema: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Failed to load schema: ' + error.message, 'danger');
    }
}

async function copySchemaInTab(schemaId) {
    try {
        const response = await fetch(`/api/schema-templates/${schemaId}`);
        const data = await response.json();
        
        if (data.success) {
            const schema = data.template;
            editingSchemaIdInTab = null; // Not editing, creating a copy
            
            document.getElementById('modalTitleInTab').textContent = 'Copy Schema';
            document.getElementById('schemaIdInTab').value = '';
            document.getElementById('schemaNameInTab').value = `${schema.name}_copy`;
            document.getElementById('schemaDescriptionInTab').value = `${schema.description || ''} (Copy)`;
            
            // Clear and populate tables with the original data
            document.getElementById('tablesContainerInTab').innerHTML = '';
            
            if (schema.schema_definition.tables) {
                schema.schema_definition.tables.forEach(tableDef => {
                    addTableWithDataInTab(tableDef);
                });
            } else {
                addTableInTab(); // Add empty table if no tables
            }
            
            new bootstrap.Modal(document.getElementById('schemaModalInTab')).show();
        } else {
            showAlert('Failed to load schema for copying: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Failed to load schema for copying: ' + error.message, 'danger');
    }
}

function addTableWithDataInTab(tableDef) {
    addTableInTab();
    const lastTable = document.querySelector('#tablesContainerInTab .table-item:last-child');
    
    lastTable.querySelector('.table-name').value = tableDef.name;
    lastTable.querySelector('.table-display-name').value = tableDef.display_name || tableDef.name;
    
    const fieldsContainer = lastTable.querySelector('.fields-container');
    fieldsContainer.innerHTML = '';
    
    tableDef.fields.forEach(fieldDef => {
        addFieldToContainerInTab(fieldsContainer, fieldDef);
    });
}

function addFieldToContainerInTab(container, fieldDef) {
    const fieldHtml = `
        <div class="field-item p-3">
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label">Field Name *</label>
                    <input type="text" class="form-control field-name" value="${fieldDef.name}" required>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Data Type</label>
                    <select class="form-select field-type">
                        <option value="STRING" ${fieldDef.type === 'STRING' ? 'selected' : ''}>String</option>
                        <option value="INTEGER" ${fieldDef.type === 'INTEGER' ? 'selected' : ''}>Integer</option>
                        <option value="FLOAT" ${fieldDef.type === 'FLOAT' ? 'selected' : ''}>Float</option>
                        <option value="BOOLEAN" ${fieldDef.type === 'BOOLEAN' ? 'selected' : ''}>Boolean</option>
                        <option value="DATE" ${fieldDef.type === 'DATE' ? 'selected' : ''}>Date</option>
                        <option value="DATETIME" ${fieldDef.type === 'DATETIME' ? 'selected' : ''}>DateTime</option>
                        <option value="EMAIL" ${fieldDef.type === 'EMAIL' ? 'selected' : ''}>Email</option>
                        <option value="PHONE" ${fieldDef.type === 'PHONE' ? 'selected' : ''}>Phone</option>
                        <option value="ADDRESS" ${fieldDef.type === 'ADDRESS' ? 'selected' : ''}>Address</option>
                        <option value="NAME" ${fieldDef.type === 'NAME' ? 'selected' : ''}>Name</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label">Required</label>
                    <div class="form-check mt-2">
                        <input class="form-check-input field-required" type="checkbox" ${fieldDef.required !== false ? 'checked' : ''}>
                        <label class="form-check-label">Required</label>
                    </div>
                </div>
                <div class="col-md-2">
                    <label class="form-label">&nbsp;</label>
                    <button class="btn btn-outline-danger btn-sm w-100" onclick="removeFieldInTab(this)">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', fieldHtml);
}

function viewSchemaDetailsInTab(schemaId) {
    const schema = currentSchemasInTab.find(s => s.id === schemaId);
    if (!schema) {
        showAlert('Schema not found', 'error');
        return;
    }
    
    const tables = schema.schema_definition?.tables || [];
    let detailsHtml = `
        <div class="modal fade" id="schemaDetailsModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-database me-2"></i>
                            Schema Details: ${schema.name}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-4">
                            <div class="col-md-12">
                                <strong>Name:</strong> ${schema.name}
                            </div>
                        </div>
                        <div class="mb-4">
                            <strong>Description:</strong><br>
                            ${schema.description || 'No description provided'}
                        </div>
                        <div class="mb-3">
                            <h6><i class="fas fa-table me-2"></i>Tables (${tables.length})</h6>
                        </div>
    `;
    
    if (tables.length === 0) {
        detailsHtml += `
            <div class="alert alert-info">
                <i class="fas fa-info-circle me-2"></i>
                No tables defined in this schema.
            </div>
        `;
    } else {
        tables.forEach((table, tableIndex) => {
            const fields = table.fields || [];
            detailsHtml += `
                <div class="card mb-3">
                    <div class="card-header">
                        <h6 class="mb-0">
                            <i class="fas fa-table me-2"></i>
                            Table ${tableIndex + 1}: ${table.name || 'Unnamed Table'}
                            ${table.display_name ? `(${table.display_name})` : ''}
                        </h6>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead class="table-light">
                                    <tr>
                                        <th>Field Name</th>
                                        <th>Data Type</th>
                                        <th>Required</th>
                                        <th>Unique</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
            `;
            
            if (fields.length === 0) {
                detailsHtml += `
                    <tr>
                        <td colspan="5" class="text-center text-muted">No fields defined</td>
                    </tr>
                `;
            } else {
                console.log('Processing fields for table:', table.name);
                fields.forEach(field => {
                    console.log('Field structure:', field);
                    // Handle different possible field structures
                    const dataType = field.data_type || field.type || field.dataType || 'Unknown';
                    const isRequired = field.required !== undefined ? field.required : field.required_field || false;
                    const isUnique = field.unique !== undefined ? field.unique : field.unique_field || false;
                    
                    detailsHtml += `
                        <tr>
                            <td><code>${field.name}</code></td>
                            <td><span class="badge bg-primary">${dataType}</span></td>
                            <td>${isRequired ? '<span class="badge bg-success">Yes</span>' : '<span class="badge bg-secondary">No</span>'}</td>
                            <td>${isUnique ? '<span class="badge bg-warning">Yes</span>' : '<span class="badge bg-secondary">No</span>'}</td>
                            <td>${field.description || '-'}</td>
                        </tr>
                    `;
                });
            }
            
            detailsHtml += `
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        });
    }
    
    detailsHtml += `
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-primary" onclick="editSchemaInTab(${schema.id}); bootstrap.Modal.getInstance(document.getElementById('schemaDetailsModal')).hide();">
                            <i class="fas fa-edit me-1"></i>Edit Schema
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('schemaDetailsModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to document and show
    document.body.insertAdjacentHTML('beforeend', detailsHtml);
    new bootstrap.Modal(document.getElementById('schemaDetailsModal')).show();
}

async function deleteSchemaInTab(schemaId) {
    if (!confirm('Are you sure you want to delete this schema template?')) {
        return;
    }

    try {
        const response = await fetch(`/api/schema-templates/${schemaId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Schema deleted successfully!', 'success');
            refreshSchemasInTab();
            loadSchemaTemplates(); // Refresh main dropdown
        } else {
            showAlert('Failed to delete schema: ' + data.error, 'danger');
        }
    } catch (error) {
        showAlert('Failed to delete schema: ' + error.message, 'danger');
    }
}

function showCreateSchemaModal() {
    document.getElementById('schemaModalTitle').textContent = 'Create Schema Template';
    document.getElementById('schemaId').value = '';
    document.getElementById('modalSchemaName').value = '';
    document.getElementById('modalSchemaDescription').value = '';
    document.getElementById('modalSchemaCategory').value = 'custom';
    document.getElementById('schemaTablesContainer').innerHTML = '';
    
    // Add initial table
    addTableToSchema();
    
    const modal = new bootstrap.Modal(document.getElementById('schemaModal'));
    modal.show();
}

async function saveSchemaTemplate() {
    const schemaId = document.getElementById('schemaId').value;
    const name = document.getElementById('modalSchemaName').value;
    const description = document.getElementById('modalSchemaDescription').value;
    const category = document.getElementById('modalSchemaCategory').value;
    
    if (!name.trim()) {
        showAlert('Schema name is required', 'danger');
        return;
    }
    
    // Build schema definition from form
    const schemaDefinition = buildSchemaDefinition();
    
    if (!schemaDefinition) {
        showAlert('Schema definition is invalid', 'danger');
        return;
    }
    
    const schemaData = {
        name: name.trim(),
        description: description.trim(),
        category: category,
        schema_definition: schemaDefinition
    };
    
    try {
        const url = schemaId ? `/api/schema-templates/${schemaId}` : '/api/schema-templates';
        const method = schemaId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(schemaData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Schema template ${schemaId ? 'updated' : 'created'} successfully!`, 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('schemaModal'));
            modal.hide();
            
            // Refresh templates list and schema dropdown
            await loadSchemaTemplatesForAdmin();
            await loadSchemaTemplates();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to save schema template:', error);
        showAlert('Failed to save schema template: ' + error.message, 'danger');
    }
}

function buildSchemaDefinition() {
    const tableItems = document.querySelectorAll('#schemaTablesContainer .table-item');
    
    if (tableItems.length === 0) {
        return null;
    }
    
    if (tableItems.length === 1) {
        // Single table schema
        const tableItem = tableItems[0];
        return buildTableDefinition(tableItem);
    } else {
        // Multi-table schema
        const tables = [];
        tableItems.forEach(tableItem => {
            const tableDef = buildTableDefinition(tableItem);
            if (tableDef) {
                tables.push(tableDef);
            }
        });
        
        return {
            name: 'multi_table_schema',
            description: 'Multi-table schema',
            tables: tables
        };
    }
}

function buildTableDefinition(tableItem) {
    const tableName = tableItem.querySelector('.table-name').value.trim();
    const displayName = tableItem.querySelector('.table-display-name').value.trim();
    
    if (!tableName) {
        return null;
    }
    
    const fields = [];
    const fieldItems = tableItem.querySelectorAll('.field-item');
    
    fieldItems.forEach(fieldItem => {
        const fieldName = fieldItem.querySelector('.field-name').value.trim();
        const fieldType = fieldItem.querySelector('.field-type').value;
        const fieldRequired = fieldItem.querySelector('.field-required').checked;
        
        if (fieldName) {
            fields.push({
                name: fieldName,
                type: fieldType,
                required: fieldRequired
            });
        }
    });
    
    return {
        name: tableName,
        display_name: displayName || tableName,
        fields: fields
    };
}

async function editSchemaTemplate(templateId) {
    try {
        const response = await fetch(`/api/schema-templates/${templateId}`);
        const data = await response.json();
        
        if (data.success) {
            const template = data.template;
            
            // Populate modal
            document.getElementById('schemaModalTitle').textContent = 'Edit Schema Template';
            document.getElementById('schemaId').value = template.id;
            document.getElementById('modalSchemaName').value = template.name;
            document.getElementById('modalSchemaDescription').value = template.description || '';
            document.getElementById('modalSchemaCategory').value = template.category;
            
            // Clear and populate tables
            document.getElementById('schemaTablesContainer').innerHTML = '';
            
            if (template.schema_definition.tables) {
                // Multi-table schema
                template.schema_definition.tables.forEach(tableDef => {
                    addTableToSchemaWithData(tableDef);
                });
            } else {
                // Single table schema - convert to multi-table format
                const singleTable = {
                    name: template.schema_definition.name || 'table_1',
                    display_name: template.schema_definition.name || 'Table 1',
                    fields: template.schema_definition.fields || []
                };
                addTableToSchemaWithData(singleTable);
            }
            
            const modal = new bootstrap.Modal(document.getElementById('schemaModal'));
            modal.show();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load schema template:', error);
        showAlert('Failed to load schema template: ' + error.message, 'danger');
    }
}

async function deleteSchemaTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this schema template?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/schema-templates/${templateId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Schema template deleted successfully!', 'success');
            await loadSchemaTemplatesForAdmin();
            await loadSchemaTemplates();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to delete schema template:', error);
        showAlert('Failed to delete schema template: ' + error.message, 'danger');
    }
}

// Test Database Functions
async function saveToDataset() {
    if (!currentResults || !currentResults.generated_records) {
        showAlert('No data to save. Please generate data first.', 'warning');
        return;
    }
    
    if (!currentSchema) {
        showAlert('Schema information not available. Please regenerate data.', 'warning');
        return;
    }
    
    // Check if this is multi-table data
    const isMultiTable = typeof currentResults.generated_records === 'object' && !Array.isArray(currentResults.generated_records);
    
    if (isMultiTable && Object.keys(currentResults.generated_records).length === 0) {
        showAlert('No data to save. Please generate data first.', 'warning');
        return;
    } else if (!isMultiTable && currentResults.generated_records.length === 0) {
        showAlert('No data to save. Please generate data first.', 'warning');
        return;
    }
    
    // Prompt for dataset name
    const datasetName = prompt('Enter a name for the dataset:', `${currentSchema.name || 'generated_data'}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}`);
    
    if (!datasetName) {
        return; // User cancelled
    }
    
    // Prompt for description
    const datasetDescription = prompt('Enter a description for the dataset (optional):', '');
    
    // Show progress indicator
    let recordCount = 0;
    if (isMultiTable) {
        Object.values(currentResults.generated_records).forEach(records => {
            recordCount += records.length;
        });
    } else {
        recordCount = currentResults.generated_records.length;
    }
    
    showAlert(`🔄 Saving dataset "${datasetName}" with ${recordCount} records...`, 'info');
    
    try {
        // Prepare the data for saving
        let recordsToSave = [];
        let schemaToSave = currentSchema;
        
        if (isMultiTable) {
            // For multi-table data, we need to save each table as a separate dataset
            const tableNames = Object.keys(currentResults.generated_records);
            
            for (const tableName of tableNames) {
                const records = currentResults.generated_records[tableName];
                const tableSchema = {
                    name: tableName,
                    description: `${datasetDescription} - ${tableName}`,
                    fields: currentSchema.tables.find(t => t.name === tableName)?.fields || []
                };
                
                // Save each table as a separate dataset
                const response = await fetch('/api/datasets', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: `${datasetName}_${tableName}`,
                        description: `${datasetDescription} - ${tableName}`,
                        schema_definition: tableSchema,
                        records: records,
                        generation_metadata: currentResults.generation_metadata || {},
            
                    })
                });
                
                const data = await response.json();
                
                if (!data.success) {
                    throw new Error(`Failed to save table ${tableName}: ${data.error}`);
                }
            }
            
            showAlert(`✅ Successfully saved multi-table dataset "${datasetName}" with ${tableNames.length} tables!`, 'success');
        } else {
            // Single table data
            
            
            const response = await fetch('/api/datasets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: datasetName,
                    description: datasetDescription,
                    schema_definition: schemaToSave,
                    records: currentResults.generated_records,
                    generation_metadata: currentResults.generation_metadata || {},
        
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showAlert(`✅ Successfully saved dataset "${datasetName}" with ${recordCount} records!`, 'success');
            } else {
                throw new Error(data.error);
            }
        }
        
        // Refresh the datasets list
        await refreshDatasets();
        
    } catch (error) {
        console.error('Failed to save dataset:', error);
        showAlert('Failed to save dataset: ' + error.message, 'danger');
    }
}





async function loadTestDatabases() {
    const container = document.getElementById('testDatabasesList');
    
    // Show loading state
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2">Loading test databases...</p>
        </div>
    `;
    
    try {
        console.log('Loading test databases...');
        const response = await fetch('/api/test-databases');
        const data = await response.json();
        
        console.log('Test databases response:', data);
        
        if (data.success) {
            console.log('Found databases:', data.databases);
            displayTestDatabases(data.databases);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load test databases:', error);
        showAlert('Failed to load test databases: ' + error.message, 'danger');
        
        // Show error state
        container.innerHTML = `
            <div class="text-center text-danger py-5">
                <i class="fas fa-exclamation-triangle fa-3x mb-3"></i>
                <h4>Failed to Load Test Databases</h4>
                <p>${error.message}</p>
                <button class="btn btn-outline-primary" onclick="loadTestDatabases()">
                    <i class="fas fa-sync-alt me-1"></i>Retry
                </button>
            </div>
        `;
    }
}

function displayTestDatabases(databases) {
    const container = document.getElementById('testDatabasesList');
    
    console.log('Displaying test databases:', databases);
    console.log('Container element:', container);
    
    if (!databases || databases.length === 0) {
        console.log('No databases to display');
        container.innerHTML = `
            <div class="text-center text-muted py-5">
                <i class="fas fa-flask fa-3x mb-3"></i>
                <h4>No Test Databases Yet</h4>
                <p>Generate data and apply it to a test database to get started.</p>
            </div>
        `;
        return;
    }
    
    console.log(`Displaying ${databases.length} databases`);
    
    const html = databases.map(db => {
        console.log('Processing database:', db);
        return `
        <div class="card mb-3">
            <div class="card-header d-flex justify-content-between align-items-center">
                <h6 class="mb-0">
                    <i class="fas fa-database me-2"></i>
                    ${db.name}
                </h6>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="queryTestDatabase('${db.name}')">
                        <i class="fas fa-eye me-1"></i>View Data
                    </button>
                    <button class="btn btn-outline-success" onclick="exportTestDatabase('${db.name}')">
                        <i class="fas fa-download me-1"></i>Export
                    </button>
                    <button class="btn btn-outline-warning" onclick="saveTestDatabase('${db.name}')">
                        <i class="fas fa-save me-1"></i>Save
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteTestDatabase('${db.name}')">
                        <i class="fas fa-trash me-1"></i>Delete
                    </button>
                </div>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-2">
                        <small class="text-muted">Tables:</small><br>
                        <strong>${db.tables.join(', ') || 'None'}</strong>
                    </div>
                    <div class="col-md-2">
                        <small class="text-muted">Total Records:</small><br>
                        <strong>${db.total_records}</strong>
                    </div>
                    <div class="col-md-2">
                        <small class="text-muted">Created:</small><br>
                        <strong>${new Date(db.created_at).toLocaleDateString()}</strong>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Time:</small><br>
                        <strong>${new Date(db.created_at).toLocaleTimeString()}</strong>
                    </div>
                    <div class="col-md-3">
                        <small class="text-muted">Status:</small><br>
                        <span class="badge bg-success">Ready</span>
                    </div>
                </div>
            </div>
        </div>
    `}).join('');
    
    console.log('Generated HTML length:', html.length);
    container.innerHTML = html;
    console.log('HTML set to container');
}

async function queryTestDatabase(dbName) {
    try {
        const response = await fetch(`/api/test-database/${dbName}/query?limit=50`);
        const data = await response.json();
        
        if (data.success) {
            // Create a modal to display the data
            const modalHtml = `
                <div class="modal fade" id="testDbModal" tabindex="-1">
                    <div class="modal-dialog modal-xl">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Test Database: ${dbName}</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <strong>Table Info:</strong> ${data.table_info.record_count} records, ${data.table_info.columns.length} columns
                                </div>
                                <div class="table-responsive">
                                    <table class="table table-striped table-sm">
                                        <thead>
                                            <tr>
                                                ${Object.keys(data.data[0] || {}).map(key => `<th>${key}</th>`).join('')}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${data.data.map(record => `
                                                <tr>
                                                    ${Object.values(record).map(value => `<td>${value}</td>`).join('')}
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Remove existing modal if any
            const existingModal = document.getElementById('testDbModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Add new modal to body
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            
            // Show modal
            const modal = new bootstrap.Modal(document.getElementById('testDbModal'));
            modal.show();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to query test database:', error);
        showAlert('Failed to query test database: ' + error.message, 'danger');
    }
}

async function exportTestDatabase(dbName) {
    try {
        // Create a temporary link to trigger download
        const link = document.createElement('a');
        link.href = `/api/test-database/${dbName}/export`;
        link.download = `${dbName}_export.csv`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showAlert(`Exporting test database ${dbName}...`, 'success');
    } catch (error) {
        console.error('Failed to export test database:', error);
        showAlert('Failed to export test database: ' + error.message, 'danger');
    }
}

async function saveTestDatabase(dbName) {
    // Show SQL dialect selection modal for saving
    const modalHtml = `
        <div class="modal fade" id="saveTestDbModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Save Test Database</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">New Database Name</label>
                            <input type="text" class="form-control" id="newDbNameInput" 
                                   value="${dbName}_copy_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label"><strong>Select Database Type:</strong></label>
                            <select class="form-select form-select-lg" id="saveDialectSelect">
                                <option value="sqlite">🗄️ SQLite - Create New Database File</option>
                                <option value="mysql">🐬 MySQL - Generate SQL Script</option>
                                <option value="postgresql">🐘 PostgreSQL - Generate SQL Script</option>
                                <option value="sqlserver">💾 SQL Server - Generate SQL Script</option>
                                <option value="oracle">🔶 Oracle - Generate SQL Script</option>
                                <option value="db2">🔵 IBM DB2 - Generate SQL Script</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Table Name</label>
                            <input type="text" class="form-control" id="tableNameInput" value="test_data">
                            <small class="form-text text-muted">Name of the table to save data from</small>
                        </div>
                        <div class="alert alert-info">
                            <small>
                                <strong>🗄️ SQLite:</strong> Creates a new database file (.db) that you can open with SQLite tools<br>
                                <strong>🐬 MySQL/🐘 PostgreSQL/💾 SQL Server/🔶 Oracle/🔵 DB2:</strong> Downloads a SQL script (.sql) with INSERT statements that you can run on your target database
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="executeSaveTestDatabase('${dbName}')">Save</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('saveTestDbModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('saveTestDbModal'));
    modal.show();
}

async function executeSaveTestDatabase(sourceDbName) {
    const newDbName = document.getElementById('newDbNameInput').value.trim();
    const sqlDialect = document.getElementById('saveDialectSelect').value;
    const tableName = document.getElementById('tableNameInput').value.trim();
    
    if (!newDbName) {
        showAlert('Please enter a new database name', 'warning');
        return;
    }
    
    if (!tableName) {
        showAlert('Please enter a table name', 'warning');
        return;
    }
    
    // Close modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('saveTestDbModal'));
    modal.hide();
    
    // Show progress indicator
    if (sqlDialect === 'sqlite') {
        showAlert(`🔄 Creating new database "${newDbName}" from "${sourceDbName}"...`, 'info');
    } else {
        showAlert(`🔄 Generating ${sqlDialect.toUpperCase()} SQL script from "${sourceDbName}"...`, 'info');
    }
    
    try {
        const response = await fetch(`/api/test-database/${sourceDbName}/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                new_db_name: newDbName,
                sql_dialect: sqlDialect,
                table_name: tableName
            })
        });
        
        // Handle file download for non-SQLite dialects
        if (sqlDialect !== 'sqlite') {
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${newDbName}_${sqlDialect}_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.sql`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                showAlert(`✅ ${sqlDialect.toUpperCase()} SQL script downloaded successfully!`, 'success');
            } else {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to generate SQL script');
            }
            return;
        }
        
        // Handle SQLite database creation
        const data = await response.json();
        
        if (data.success) {
            showAlert(`✅ ${data.message}`, 'success');
            
            // Refresh test databases list to show the new database
            await loadTestDatabases();
            
            // Show completion details
            setTimeout(() => {
                showAlert(`📊 New database created successfully! Records: ${data.new_database.record_count}, Table: ${data.new_database.table_name}`, 'success');
            }, 1000);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to save test database:', error);
        showAlert('Failed to save test database: ' + error.message, 'danger');
    }
}

async function deleteTestDatabase(dbName) {
    if (!confirm(`Are you sure you want to delete the test database "${dbName}"? This action cannot be undone.`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/test-database/${dbName}/delete`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`Test database "${dbName}" deleted successfully!`, 'success');
            
            // Refresh the test databases list
            await loadTestDatabases();
        } else {
            throw new Error(data.error || 'Delete failed');
        }
    } catch (error) {
        console.error('Failed to delete test database:', error);
        showAlert('Failed to delete test database: ' + error.message, 'danger');
    }
}

// Export functions for global access
window.addField = addField;
window.removeField = removeField;
window.generateData = generateData;
window.exportData = exportData;
window.saveToDataset = saveToDataset;
window.refreshDatasets = refreshDatasets;
window.viewDataset = viewDataset;
window.generateSQLFromDataset = generateSQLFromDataset;
window.generateSQLFromCurrentData = generateSQLFromCurrentData;
window.generateSQLWithLLM = generateSQLWithLLM;
window.saveGeneratedSQL = saveGeneratedSQL;
window.copySQLToClipboard = copySQLToClipboard;
window.deleteDataset = deleteDataset;
window.navigateToSchemaAdmin = navigateToSchemaAdmin;





function getTableCount(schemaDefinition) {
    if (schemaDefinition.tables) {
        return schemaDefinition.tables.length;
    }
    return 1; // Single table schema
}

function getFieldCount(schemaDefinition) {
    if (schemaDefinition.tables) {
        return schemaDefinition.tables.reduce((total, table) => total + (table.fields?.length || 0), 0);
    }
    return schemaDefinition.fields?.length || 0;
}



// Function addTableToSchema is defined earlier in the file - removing duplicate

// Function removeTableFromSchema is defined earlier in the file - removing duplicate

// Function addFieldToTable is defined earlier in the file - removing duplicate

// Function addFieldToTableElement is defined earlier in the file - removing duplicate









function addFieldToTableElementWithData(fieldsContainer, fieldDef) {
    const template = document.getElementById('fieldTemplate');
    const fieldElement = template.content.cloneNode(true);
    
    // Set field data
    const fieldNameInput = fieldElement.querySelector('.field-name');
    const fieldTypeSelect = fieldElement.querySelector('.field-type');
    const fieldRequiredCheckbox = fieldElement.querySelector('.field-required');
    
    fieldNameInput.value = fieldDef.name || '';
    fieldTypeSelect.value = fieldDef.type || 'STRING';
    fieldRequiredCheckbox.checked = fieldDef.required !== false;
    
    fieldsContainer.appendChild(fieldElement);
}

async function deleteSchemaTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this schema template?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/schema-templates/${templateId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('Schema template deleted successfully!', 'success');
            await loadSchemaTemplates();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to delete schema template:', error);
        showAlert('Failed to delete schema template: ' + error.message, 'danger');
    }
}

async function useSchemaTemplate(templateId) {
    try {
        const response = await fetch(`/api/schema-templates/${templateId}`);
        const data = await response.json();
        
        if (data.success) {
            const template = data.template;
            
            // Switch to generated data tab
            const generatedTab = document.getElementById('generated-tab');
            const tab = new bootstrap.Tab(generatedTab);
            tab.show();
            
            // Apply schema to the form
            applySchemaToForm(template.schema_definition);
            
            showAlert(`Schema template "${template.name}" loaded successfully!`, 'success');
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load schema template:', error);
        showAlert('Failed to load schema template: ' + error.message, 'danger');
    }
}

function applySchemaToForm(schemaDefinition) {
    // Clear existing tables
    document.getElementById('schemaTablesContainer').innerHTML = '';
    
    if (schemaDefinition.tables && schemaDefinition.tables.length > 0) {
        // Multi-table schema
        schemaDefinition.tables.forEach(tableDef => {
            addTableToSchemaWithData(tableDef);
        });
        
        // Set schema name from first table
        const firstTable = schemaDefinition.tables[0];
        document.getElementById('schemaName').value = firstTable.display_name || firstTable.name;
    } else {
        // Single table schema - convert to multi-table format
        const singleTable = {
            name: schemaDefinition.name || 'table_1',
            display_name: schemaDefinition.name || 'Table 1',
            fields: schemaDefinition.fields || []
        };
        
        addTableToSchemaWithData(singleTable);
        document.getElementById('schemaName').value = schemaDefinition.name || '';
    }
}

// Navigation function to Schema Admin tab
function navigateToSchemaAdmin() {
    const schemaAdminTab = document.getElementById('schema-admin-tab');
    if (schemaAdminTab) {
        const tab = new bootstrap.Tab(schemaAdminTab);
        tab.show();
    } else {
        console.error('Schema Admin tab not found');
        showAlert('Schema Admin tab not found', 'error');
    }
}

// Export functions for global access
window.loadSchemaTemplates = loadSchemaTemplates;
window.refreshSchemaTemplates = refreshSchemaTemplates;
window.addTableToSchema = addTableToSchema;
window.addFieldToTable = addFieldToTable;
// Table removal function removed - read-only display
window.updateTableName = updateTableName;
window.addQuickTestTable = addQuickTestTable;
window.useSchemaTemplate = useSchemaTemplate;

window.showTablesSection = showTablesSection;
window.hideTablesSection = hideTablesSection;
window.addTableToSchemaWithData = addTableToSchemaWithData;
// Field removal function removed - read-only display
window.showDatabaseDialectModal = showDatabaseDialectModal;
window.generateSQLStatements = generateSQLStatements;

// Test function for debugging
window.testFieldTemplate = function() {
    console.log('=== FIELD TEMPLATE TEST ===');
    
    // Check if field template exists
    const fieldTemplate = document.getElementById('fieldTemplate');
    console.log('Field template found:', !!fieldTemplate);
    
    if (fieldTemplate) {
        console.log('Field template content:', fieldTemplate.innerHTML);
        
        // Test creating a field element
        const fieldElement = fieldTemplate.content.cloneNode(true);
        console.log('Field element created:', fieldElement);
        
        // Check if field element has the right class
        const fieldItem = fieldElement.querySelector('.field-item');
        console.log('Field item found:', !!fieldItem);
        
        if (fieldItem) {
            console.log('Field item class:', fieldItem.className);
            console.log('Field item HTML:', fieldItem.outerHTML);
        }
    }
    
    // Check schema tables container
    const container = document.getElementById('schemaTablesContainer');
    console.log('Schema tables container found:', !!container);
    console.log('Container HTML:', container?.innerHTML);
    
    // Check if schema configuration is visible
    const schemaConfig = document.querySelector('.schema-configuration');
    console.log('Schema configuration visible:', schemaConfig?.style.display !== 'none');
};





// Auto-fix function for schema issues
window.autoFixSchema = function() {
    console.log('=== AUTO FIX SCHEMA ===');
    
    // Test current state
    testFieldTemplate();
    
    // Try to create a basic schema automatically
    console.log('Attempting to create basic schema...');
    
    // Show schema configuration
    showSchemaConfiguration();
    
    // Set default schema name if empty
    const schemaNameInput = document.getElementById('schemaName');
    if (!schemaNameInput.value.trim()) {
        schemaNameInput.value = 'Auto Test Schema';
    }
    
    // Set default description if empty - removed since we simplified the interface
    // const schemaDescriptionInput = document.getElementById('schemaDescription');
    // if (!schemaDescriptionInput.value.trim()) {
    //     schemaDescriptionInput.value = 'Automatically created test schema';
    // }
    
    // Add a table
    addTableToSchema();
    
    // Wait a moment and test schema collection
    setTimeout(() => {
        console.log('Testing schema collection after auto-fix...');
        const testSchema = collectSchemaData();
        console.log('Auto-fix result:', testSchema);
        
        if (testSchema.fields && testSchema.fields.length > 0) {
            showAlert('Auto-fix successful! Schema created with fields.', 'success');
        } else {
            showAlert('Auto-fix completed but no fields found. Please check console for details.', 'warning');
        }
    }, 200);
};
window.showSchemaConfiguration = showSchemaConfiguration;
window.hideSchemaConfiguration = hideSchemaConfiguration;
window.clearSchemaConfiguration = clearSchemaConfiguration;
window.hideResultsContainer = hideResultsContainer;
window.showResultsContainer = showResultsContainer;

// Schema Admin Tab functions
window.refreshSchemasInTab = refreshSchemasInTab;
window.showCreateSchemaModalInTab = showCreateSchemaModalInTab;
window.addTableInTab = addTableInTab;
window.removeTableInTab = removeTableInTab;
window.addFieldInTab = addFieldInTab;
window.removeFieldInTab = removeFieldInTab;
window.saveSchemaInTab = saveSchemaInTab;
window.editSchemaInTab = editSchemaInTab;
window.copySchemaInTab = copySchemaInTab;
window.viewSchemaDetailsInTab = viewSchemaDetailsInTab;
window.deleteSchemaInTab = deleteSchemaInTab;

// Comprehensive Schema Admin Test Function
window.testSchemaAdmin = function() {
    console.log('=== SCHEMA ADMIN COMPREHENSIVE TEST ===');
    
    // Test 1: Check if all functions exist
    console.log('\n1. Checking function availability:');
    const functions = [
        'refreshSchemasInTab',
        'displaySchemasInTab', 
        'showCreateSchemaModalInTab',
        'addTableInTab',
        'removeTableInTab',
        'addFieldInTab',
        'removeFieldInTab',
        'saveSchemaInTab',
        'editSchemaInTab',
        'copySchemaInTab',
        'viewSchemaDetailsInTab',
        'deleteSchemaInTab'
    ];
    
    functions.forEach(func => {
        const exists = typeof window[func] === 'function';
        console.log(`  ${exists ? '✅' : '❌'} ${func}: ${exists ? 'Available' : 'Missing'}`);
    });
    
    // Test 2: Check if UI elements exist
    console.log('\n2. Checking UI elements:');
    const elements = [
        'schemasTableBody',
        'schemaModalInTab',
        'schemaFormInTab',
        'tablesContainerInTab',
        'schemaNameInTab',
        'schemaDescriptionInTab'
    ];
    
    elements.forEach(elementId => {
        const element = document.getElementById(elementId);
        console.log(`  ${element ? '✅' : '❌'} ${elementId}: ${element ? 'Found' : 'Missing'}`);
    });
    
    // Test 3: Check API connectivity
    console.log('\n3. Testing API connectivity:');
    fetch('/api/schema-templates')
        .then(response => {
            console.log(`  ✅ API Response Status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log(`  ✅ API Response:`, data);
            console.log(`  ✅ Schemas count: ${data.templates ? data.templates.length : 0}`);
        })
        .catch(error => {
            console.log(`  ❌ API Error: ${error.message}`);
        });
    
    // Test 4: Check if Schema Admin tab is accessible
    console.log('\n4. Checking Schema Admin tab:');
    const schemaAdminTab = document.querySelector('[data-bs-target="#schema-admin-pane"]');
    const schemaAdminPane = document.getElementById('schema-admin-pane');
    console.log(`  ${schemaAdminTab ? '✅' : '❌'} Schema Admin tab button: ${schemaAdminTab ? 'Found' : 'Missing'}`);
    console.log(`  ${schemaAdminPane ? '✅' : '❌'} Schema Admin pane: ${schemaAdminPane ? 'Found' : 'Missing'}`);
    
    // Test 5: Test modal functionality
    console.log('\n5. Testing modal functionality:');
    try {
        const modal = new bootstrap.Modal(document.getElementById('schemaModalInTab'));
        console.log('  ✅ Modal can be instantiated');
    } catch (error) {
        console.log(`  ❌ Modal error: ${error.message}`);
    }
    
    console.log('\n=== TEST COMPLETE ===');
    console.log('Check the results above. All ✅ items should work properly.');
};

// Test complete Schema Admin workflow
window.testSchemaAdminWorkflow = function() {
    console.log('=== SCHEMA ADMIN WORKFLOW TEST ===');
    
    // Step 1: Open Schema Admin tab
    console.log('\n1. Opening Schema Admin tab...');
    const schemaAdminTab = document.querySelector('[data-bs-target="#schema-admin-pane"]');
    if (schemaAdminTab) {
        schemaAdminTab.click();
        console.log('  ✅ Schema Admin tab opened');
    } else {
        console.log('  ❌ Could not find Schema Admin tab');
        return;
    }
    
    // Step 2: Refresh schemas
    console.log('\n2. Refreshing schemas...');
    setTimeout(() => {
        if (typeof refreshSchemasInTab === 'function') {
            refreshSchemasInTab();
            console.log('  ✅ Schemas refreshed');
        } else {
            console.log('  ❌ refreshSchemasInTab function not available');
        }
    }, 500);
    
    // Step 3: Test create schema modal
    console.log('\n3. Testing create schema modal...');
    setTimeout(() => {
        if (typeof showCreateSchemaModalInTab === 'function') {
            showCreateSchemaModalInTab();
            console.log('  ✅ Create schema modal opened');
            
            // Step 4: Test adding table
            setTimeout(() => {
                console.log('\n4. Testing add table functionality...');
                const addTableBtn = document.querySelector('#tablesContainerInTab .btn-outline-secondary');
                if (addTableBtn) {
                    addTableBtn.click();
                    console.log('  ✅ Table added successfully');
                } else {
                    console.log('  ❌ Could not find add table button');
                }
            }, 1000);
            
        } else {
            console.log('  ❌ showCreateSchemaModalInTab function not available');
        }
    }, 1000);
    
    console.log('\n=== WORKFLOW TEST INITIATED ===');
    console.log('Check the browser for modal and UI interactions.');
};

// Test schema data collection and generation
window.testSchemaGeneration = function() {
    console.log('=== SCHEMA GENERATION TEST ===');
    
    // Step 1: Test schema data collection
    console.log('\n1. Testing schema data collection...');
    const schemaData = collectSchemaData();
    console.log('Collected schema data:', schemaData);
    
    // Step 2: Check if we have tables or fields
    const hasTables = schemaData.tables && schemaData.tables.length > 0;
    const hasFields = schemaData.fields && schemaData.fields.length > 0;
    console.log('Has tables:', hasTables, 'Has fields:', hasFields);
    
    if (!hasTables && !hasFields) {
        console.log('❌ No schema data found!');
        console.log('Creating a test schema...');
        
        // Show schema configuration
        showSchemaConfiguration();
        showTablesSection();
        
        // Set default values
        document.getElementById('schemaName').value = 'Test Schema';
        document.getElementById('schemaDescription').value = 'Test schema for generation';
        
        // Add a table
        addTableToSchema();
        
        // Wait and test again
        setTimeout(() => {
            console.log('\n2. Testing schema data collection after adding table...');
            const newSchemaData = collectSchemaData();
            console.log('New collected schema data:', newSchemaData);
            
            const newHasTables = newSchemaData.tables && newSchemaData.tables.length > 0;
            const newHasFields = newSchemaData.fields && newSchemaData.fields.length > 0;
            console.log('New has tables:', newHasTables, 'New has fields:', newHasFields);
            
            if (newHasTables || newHasFields) {
                console.log('✅ Schema data collection is working!');
                
                // Step 3: Test generation parameters
                console.log('\n3. Testing generation parameters...');
                const genParams = collectGenerationParams();
                console.log('Generation parameters:', genParams);
                console.log('✅ Generation parameters collection is working!');
                
                // Step 4: Test actual generation
                console.log('\n4. Testing data generation...');
                console.log('Calling generateData()...');
                generateData();
                
            } else {
                console.log('❌ Schema data collection still not working!');
            }
        }, 500);
        
    } else {
        console.log('✅ Schema data collection is working!');
        
        // Test generation parameters
        console.log('\n2. Testing generation parameters...');
        const genParams = collectGenerationParams();
        console.log('Generation parameters:', genParams);
        console.log('✅ Generation parameters collection is working!');
        
        // Test actual generation
        console.log('\n3. Testing data generation...');
        console.log('Calling generateData()...');
        generateData();
    }
};

// Database Dialect Modal Functions
function showDatabaseDialectModal() {
    if (!currentResults || !currentResults.generated_records) {
        showAlert('No data available. Please generate data first.', 'warning');
        return;
    }
    
    // Reset modal state
    document.getElementById('databaseDialect').value = '';
    document.getElementById('sqlResultsContainer').style.display = 'none';
    document.getElementById('generateSQLBtn').disabled = true;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('databaseDialectModal'));
    modal.show();
}

function generateSQLStatements() {
    const dialect = document.getElementById('databaseDialect').value;
    if (!dialect) {
        showAlert('Please select a database dialect.', 'warning');
        return;
    }
    
    if (!currentResults || !currentResults.generated_records) {
        showAlert('No data available to generate SQL.', 'warning');
        return;
    }
    
    // Show loading state
    const generateBtn = document.getElementById('generateSQLBtn');
    const originalText = generateBtn.innerHTML;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating...';
    generateBtn.disabled = true;
    
    // Prepare data for SQL generation
    const data = {
        dialect: dialect,
        data: currentResults.generated_records,
        schema: currentSchema
    };
    
    // Call API to generate SQL
    fetch('/api/generate-sql', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            displaySQLResults(result.sql_statements, dialect);
        } else {
            throw new Error(result.error || 'Failed to generate SQL');
        }
    })
    .catch(error => {
        console.error('SQL generation failed:', error);
        showAlert('Failed to generate SQL: ' + error.message, 'danger');
    })
    .finally(() => {
        // Restore button state
        generateBtn.innerHTML = originalText;
        generateBtn.disabled = false;
    });
}

function displaySQLResults(sqlStatements, dialect) {
    const container = document.getElementById('sqlResultsContainer');
    const resultsDiv = document.getElementById('sqlResults');
    
    // Format SQL statements
    let formattedSQL = '';
    
    if (typeof sqlStatements === 'object' && !Array.isArray(sqlStatements)) {
        // Multi-table data
        Object.keys(sqlStatements).forEach(tableName => {
            formattedSQL += `-- Table: ${tableName}\n`;
            formattedSQL += `-- Database: ${dialect.toUpperCase()}\n`;
            formattedSQL += `-- Generated: ${new Date().toLocaleString()}\n\n`;
            formattedSQL += sqlStatements[tableName].join('\n');
            formattedSQL += '\n\n';
        });
    } else {
        // Single table data
        formattedSQL += `-- Database: ${dialect.toUpperCase()}\n`;
        formattedSQL += `-- Generated: ${new Date().toLocaleString()}\n\n`;
        formattedSQL += sqlStatements.join('\n');
    }
    
    // Display results
    resultsDiv.textContent = formattedSQL;
    container.style.display = 'block';
    
    // Scroll to results
    container.scrollIntoView({ behavior: 'smooth' });
}

function copySQLToClipboard() {
    const sqlText = document.getElementById('sqlResults').textContent;
    
    navigator.clipboard.writeText(sqlText).then(() => {
        showAlert('SQL statements copied to clipboard! 📋', 'success');
    }).catch(err => {
        console.error('Failed to copy: ', err);
        showAlert('Failed to copy to clipboard', 'danger');
    });
}

// Event listener for dialect selection
document.addEventListener('DOMContentLoaded', function() {
    const dialectSelect = document.getElementById('databaseDialect');
    const generateBtn = document.getElementById('generateSQLBtn');
    
    if (dialectSelect && generateBtn) {
        dialectSelect.addEventListener('change', function() {
            generateBtn.disabled = !this.value;
        });
    }
});

async function generateSQLWithLLM(datasetId) {
    console.log('generateSQLWithLLM called with datasetId:', datasetId);
    
    const dialect = document.getElementById('sqlDialectSelect').value;
    console.log('Selected dialect:', dialect);
    
    if (!dialect) {
        showAlert('Please select a database dialect', 'warning');
        return;
    }
    
    // Show loading state
    const generateBtn = document.getElementById('generateSQLBtn');
    const originalText = generateBtn.innerHTML;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating...';
    generateBtn.disabled = true;
    
    try {
        // First, get the dataset and its records
        const datasetResponse = await fetch(`/api/datasets/${datasetId}`);
        const datasetData = await datasetResponse.json();
        
        if (!datasetData.success) {
            throw new Error(`Failed to load dataset: ${datasetData.error}`);
        }
        
        const recordsResponse = await fetch(`/api/datasets/${datasetId}/records?limit=1000`);
        const recordsData = await recordsResponse.json();
        
        if (!recordsData.success) {
            throw new Error(`Failed to load records: ${recordsData.error}`);
        }
        
        // Prepare data for LLM SQL generation
        const records = recordsData.records.map(record => {
            // Parse record_data if it's a JSON string, otherwise use as is
            let recordData = record.record_data;
            if (typeof record.record_data === 'string') {
                try {
                    recordData = JSON.parse(record.record_data);
                } catch (e) {
                    console.log('Failed to parse record_data:', e);
                    recordData = {};
                }
            }
            return recordData;
        });
        
        const schema = datasetData.dataset.schema_definition;
        const tableName = schema.name || `dataset_${datasetId}`;
        
        console.log('Prepared records for SQL generation:', records);
        console.log('Sample record:', records[0]);
        
        // Call LLM SQL generation API
        const response = await fetch('/api/generate-sql-llm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dialect: dialect,
                data: records,
                schema: schema,
                table_name: tableName,
                description: datasetData.dataset.description || ''
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Display the generated SQL
            const sqlContent = Object.values(data.sql_statements)[0]; // Get first table's SQL
            displayGeneratedSQL(sqlContent, datasetId, dialect, records.length);
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Failed to generate SQL:', error);
        showAlert('Failed to generate SQL: ' + error.message, 'danger');
    } finally {
        // Restore button state
        generateBtn.innerHTML = originalText;
        generateBtn.disabled = false;
    }
}

async function generateSQLWithLLMFromCurrentData() {
    console.log('generateSQLWithLLMFromCurrentData called');
    
    const dialect = document.getElementById('sqlDialectSelect').value;
    console.log('Selected dialect:', dialect);
    
    if (!dialect) {
        showAlert('Please select a database dialect', 'warning');
        return;
    }
    
    if (!currentResults || !currentResults.generated_records) {
        showAlert('No current data available. Please generate data first.', 'warning');
        return;
    }
    
    // Show loading state
    const generateBtn = document.getElementById('generateSQLBtn');
    const originalText = generateBtn.innerHTML;
    generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Generating...';
    generateBtn.disabled = true;
    
    try {
        // Prepare data for LLM SQL generation from current results
        let records, schema, tableName;
        
        if (Array.isArray(currentResults.generated_records)) {
            // Single table data
            records = currentResults.generated_records.map(record => record.data || record);
            schema = currentSchema;
            tableName = currentSchema?.name || 'generated_table';
        } else {
            // Multi-table data - use the first table
            const firstTableName = Object.keys(currentResults.generated_records)[0];
            records = currentResults.generated_records[firstTableName].map(record => record.data || record);
            schema = currentSchema?.tables?.find(t => t.name === firstTableName) || { name: firstTableName };
            tableName = firstTableName;
        }
        
        console.log('Prepared data for SQL generation:', { records: records.length, schema, tableName });
        
        // Call LLM SQL generation API
        const response = await fetch('/api/generate-sql-llm', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                dialect: dialect,
                data: records,
                schema: schema,
                table_name: tableName,
                description: 'Generated from current data'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Display the generated SQL
            const sqlContent = Object.values(data.sql_statements)[0]; // Get first table's SQL
            displayGeneratedSQLFromCurrentData(sqlContent, dialect, records.length);
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Failed to generate SQL from current data:', error);
        showAlert('Failed to generate SQL: ' + error.message, 'danger');
    } finally {
        // Restore button state
        generateBtn.innerHTML = originalText;
        generateBtn.disabled = false;
    }
}

function displayGeneratedSQLFromCurrentData(sqlContent, dialect, recordCount) {
    const resultsContainer = document.getElementById('sqlResultsContainer');
    const sqlResults = document.getElementById('sqlResults');
    
    // Store data for saving (no dataset ID for current data)
    window.currentGeneratedSQL = {
        datasetId: null, // No dataset ID for current data
        dialect: dialect,
        sqlContent: sqlContent,
        recordCount: recordCount
    };
    
    // Display SQL with syntax highlighting
    sqlResults.innerHTML = `<pre class="mb-0">${escapeHtml(sqlContent)}</pre>`;
    resultsContainer.style.display = 'block';
    
    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

function displayGeneratedSQL(sqlContent, datasetId, dialect, recordCount) {
    const resultsContainer = document.getElementById('sqlResultsContainer');
    const sqlResults = document.getElementById('sqlResults');
    
    // Store data for saving
    window.currentGeneratedSQL = {
        datasetId: datasetId,
        dialect: dialect,
        sqlContent: sqlContent,
        recordCount: recordCount
    };
    
    // Display SQL with syntax highlighting
    sqlResults.innerHTML = `<pre class="mb-0">${escapeHtml(sqlContent)}</pre>`;
    resultsContainer.style.display = 'block';
    
    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

async function saveGeneratedSQL() {
    const sqlName = document.getElementById('sqlNameInput').value.trim();
    const sqlDescription = document.getElementById('sqlDescriptionInput').value.trim();
    
    if (!sqlName) {
        showAlert('Please enter a name for the SQL', 'warning');
        return;
    }
    
    if (!window.currentGeneratedSQL) {
        showAlert('No SQL to save. Please generate SQL first.', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/save-generated-sql', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: sqlName,
                description: sqlDescription,
                dataset_id: window.currentGeneratedSQL.datasetId,
                dialect: window.currentGeneratedSQL.dialect,
                sql_content: window.currentGeneratedSQL.sqlContent,
                schema_definition: {}, // Will be filled from dataset
                record_count: window.currentGeneratedSQL.recordCount
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert('SQL saved successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('sqlGenerationModal'));
            modal.hide();
            
            // Refresh datasets to show updated state
            refreshDatasets();
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Failed to save SQL:', error);
        showAlert('Failed to save SQL: ' + error.message, 'danger');
    }
}

// Duplicate copySQLToClipboard function removed

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Generated SQL Management Functions
async function refreshGeneratedSQL() {
    try {
        const response = await fetch('/api/generated-sql');
        const data = await response.json();
        
        if (data.success) {
            displayGeneratedSQLList(data.generated_sql);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load generated SQL:', error);
        showAlert('Failed to load generated SQL: ' + error.message, 'danger');
    }
}

function displayGeneratedSQLList(sqlRecords) {
    const tbody = document.getElementById('generatedSQLTableBody');
    
    if (!sqlRecords || sqlRecords.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted py-5">
                    <i class="fas fa-code fa-2x mb-3 d-block"></i>
                    <h5>No Generated SQL Yet</h5>
                    <p class="mb-0">Generate SQL from your datasets to see them here.</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = sqlRecords.map(sql => `
        <tr>
            <td>
                <strong>${escapeHtml(sql.name)}</strong>
            </td>
            <td>
                <span class="sql-description">${escapeHtml(sql.description || 'No description')}</span>
            </td>
            <td>
                <span class="badge bg-primary">${escapeHtml(sql.dialect.toUpperCase())}</span>
            </td>
            <td>
                <span class="badge bg-secondary">${sql.record_count}</span>
            </td>
            <td>
                <span class="sql-date">${new Date(sql.created_at).toLocaleDateString()}</span>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="viewGeneratedSQL(${sql.id})" title="View SQL">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-outline-success" onclick="downloadGeneratedSQL(${sql.id})" title="Download">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn btn-outline-danger" onclick="deleteGeneratedSQL(${sql.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

async function viewGeneratedSQL(sqlId) {
    try {
        const response = await fetch(`/api/generated-sql/${sqlId}`);
        const data = await response.json();
        
        if (data.success) {
            showGeneratedSQLModal(data.generated_sql);
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to load generated SQL:', error);
        showAlert('Failed to load generated SQL: ' + error.message, 'danger');
    }
}

function showGeneratedSQLModal(sqlRecord) {
    const modalHtml = `
        <div class="modal fade" id="viewSQLModal" tabindex="-1">
            <div class="modal-dialog modal-xl">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-code me-2"></i>
                            ${escapeHtml(sqlRecord.name)}
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <strong>Description:</strong> ${escapeHtml(sqlRecord.description || 'No description')}
                            </div>
                            <div class="col-md-3">
                                <strong>Dialect:</strong> <span class="badge bg-primary">${sqlRecord.dialect.toUpperCase()}</span>
                            </div>
                            <div class="col-md-3">
                                <strong>Records:</strong> <span class="badge bg-secondary">${sqlRecord.record_count}</span>
                            </div>
                        </div>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">SQL Content</h6>
                                <button class="btn btn-sm btn-outline-primary" onclick="copySQLContent()">
                                    <i class="fas fa-copy me-1"></i>Copy
                                </button>
                            </div>
                        </div>
                        <div class="bg-light p-3 rounded" style="max-height: 500px; overflow-y: auto; font-family: 'Courier New', monospace; font-size: 0.9em;">
                            <pre class="mb-0">${escapeHtml(sqlRecord.sql_content)}</pre>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-success" onclick="downloadGeneratedSQL(${sqlRecord.id})">
                            <i class="fas fa-download me-1"></i>Download
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if present
    const existingModal = document.getElementById('viewSQLModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Store SQL content for copying
    window.currentSQLContent = sqlRecord.sql_content;
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('viewSQLModal'));
    modal.show();
}

async function downloadGeneratedSQL(sqlId) {
    try {
        const response = await fetch(`/api/generated-sql/${sqlId}`);
        const data = await response.json();
        
        if (data.success) {
            const sqlRecord = data.generated_sql;
            
            // Create download link
            const blob = new Blob([sqlRecord.sql_content], { type: 'text/plain' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${sqlRecord.name}_${sqlRecord.dialect}.sql`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            showAlert('SQL downloaded successfully!', 'success');
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to download generated SQL:', error);
        showAlert('Failed to download generated SQL: ' + error.message, 'danger');
    }
}

async function deleteGeneratedSQL(sqlId) {
    if (!confirm('Are you sure you want to delete this generated SQL? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/generated-sql/${sqlId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.success) {
            showAlert('Generated SQL deleted successfully', 'success');
            refreshGeneratedSQL();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        console.error('Failed to delete generated SQL:', error);
        showAlert('Failed to delete generated SQL: ' + error.message, 'danger');
    }
}

function copySQLContent() {
    if (!window.currentSQLContent) {
        showAlert('No SQL content to copy', 'warning');
        return;
    }
    
    navigator.clipboard.writeText(window.currentSQLContent).then(() => {
        showAlert('SQL copied to clipboard!', 'success');
    }).catch(() => {
        showAlert('Failed to copy SQL to clipboard', 'danger');
    });
}

// Setup event listeners for generated SQL tab
function setupGeneratedSQLEventListeners() {
    const generatedSQLTab = document.getElementById('generated-sql-tab');
    if (generatedSQLTab) {
        generatedSQLTab.addEventListener('shown.bs.tab', function() {
            refreshGeneratedSQL();
        });
    }
}

// Global exports for Generated SQL functions
window.refreshGeneratedSQL = refreshGeneratedSQL;
window.viewGeneratedSQL = viewGeneratedSQL;
window.downloadGeneratedSQL = downloadGeneratedSQL;
window.deleteGeneratedSQL = deleteGeneratedSQL;
window.copySQLContent = copySQLContent;

// Test function for debugging
window.testGenerateSQL = function() {
    console.log('=== TEST GENERATE SQL ===');
    
    // Test if function exists
    if (typeof generateSQLFromDataset === 'function') {
        console.log('✓ generateSQLFromDataset function exists');
        
        // Test if we have any datasets
        if (currentDatasets && currentDatasets.length > 0) {
            console.log('✓ Found datasets:', currentDatasets.length);
            console.log('Testing with first dataset:', currentDatasets[0]);
            
            // Call the function
            generateSQLFromDataset(currentDatasets[0].id, currentDatasets[0].name);
        } else {
            console.log('✗ No datasets available for testing');
        }
    } else {
        console.error('✗ generateSQLFromDataset function not found!');
    }
};

// Test function to manually enable the button
window.testEnableButton = function() {
    console.log('=== TEST ENABLE BUTTON ===');
    
    const dialectSelect = document.getElementById('sqlDialectSelect');
    const generateBtn = document.getElementById('generateSQLBtn');
    
    console.log('Elements found:', { dialectSelect: !!dialectSelect, generateBtn: !!generateBtn });
    
    if (dialectSelect && generateBtn) {
        // Manually set a value
        dialectSelect.value = 'mysql';
        
        // Manually enable the button
        generateBtn.disabled = false;
        
        console.log('Button manually enabled. Value:', dialectSelect.value, 'Disabled:', generateBtn.disabled);
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        dialectSelect.dispatchEvent(event);
        
        console.log('Change event triggered');
    } else {
        console.error('Modal elements not found');
    }
};
