// Global variables to store analysis results for export
let previewData = null;
let analysisResults = null;
let singleAccountResults = null;

// Global variables for Excel upload functionality
let excelFileData = null;
let excelPreviewData = null;
let excelAnalysisResults = null;

// Initialize event handlers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventHandlers();
});

function initializeEventHandlers() {
    // SOQL Query Form Handler (Get Account IDs)
    document.getElementById('queryForm').addEventListener('submit', handleQueryFormSubmit);
    
    // Get Account Data Button Handler (inline button)
    document.getElementById('getAccountDataBtn').addEventListener('click', handleGetAccountData);
    
    // Export Button Handler for Analyze Query
    document.getElementById('exportBtn').addEventListener('click', handleExportAnalysis);
    
    // Account Form Handler
    document.getElementById('accountForm').addEventListener('submit', handleAccountFormSubmit);
    
    // Export Button Handler for Account
    document.getElementById('exportAccountBtn').addEventListener('click', handleExportAccount);
    
    // Clear stored results when inputs change
    document.getElementById('accountId').addEventListener('input', function() {
        singleAccountResults = null;
        document.getElementById('exportAccountBtn').disabled = true;
    });
    
    document.getElementById('soqlQuery').addEventListener('input', function() {
        analysisResults = null;
        // Reset button states
        document.getElementById('getAccountDataBtn').disabled = true;
        document.getElementById('exportBtn').disabled = true;
    });
    
    document.getElementById('maxAnalyze').addEventListener('input', function() {
        analysisResults = null;
        // Reset button states  
        document.getElementById('getAccountDataBtn').disabled = true;
        document.getElementById('exportBtn').disabled = true;
    });
    
    // Excel upload event handlers
    document.getElementById('excelFile').addEventListener('change', handleExcelFileChange);
    document.getElementById('parseExcelBtn').addEventListener('click', handleParseExcel);
    document.getElementById('validateAccountIdsBtn').addEventListener('click', handleValidateAccountIds);
    document.getElementById('exportExcelBtn').addEventListener('click', handleExportExcel);
}

async function handleQueryFormSubmit(e) {
    e.preventDefault();
    
    const responseDiv = document.getElementById('queryResponse');
    const button = document.getElementById('analyzeBtn');
    const getDataBtn = document.getElementById('getAccountDataBtn');
    const exportBtn = document.getElementById('exportBtn');
    
    // Get form values
    const soqlQuery = document.getElementById('soqlQuery').value.trim();
    const maxAnalyze = parseInt(document.getElementById('maxAnalyze').value);
    
    // Validate inputs
    if (isNaN(maxAnalyze) || maxAnalyze < 1 || maxAnalyze > 500) {
        responseDiv.innerHTML = 'Max accounts to analyze must be a number between 1 and 500.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    // Validate SOQL query - must be a full query, not empty or partial
    if (!soqlQuery) {
        responseDiv.innerHTML = 'Please enter a complete SOQL query that returns Account IDs.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    // Must start with SELECT (full query required)
    if (!soqlQuery.toUpperCase().startsWith('SELECT')) {
        responseDiv.innerHTML = 'Please enter a complete SOQL query starting with SELECT. WHERE/LIMIT clauses alone are not accepted.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    // Show loading state and disable buttons
    button.disabled = true;
    button.textContent = 'Validating...';
    getDataBtn.disabled = true;
    exportBtn.disabled = true;
    responseDiv.innerHTML = 'Validating SOQL query and getting Account IDs...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const response = await fetch('/accounts/analyze-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                soql_query: soqlQuery,
                max_ids: maxAnalyze
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            analysisResults = data;
            const accountIds = data.data.account_ids;
            const queryInfo = data.data.query_info;
            
            // Display results
            let output = `✅ SOQL Query Valid - Account IDs Retrieved!\n\n`;
            output += `📊 Summary:\n`;
            output += `- Account IDs found: ${accountIds.length}\n`;
            output += `- Execution time: ${queryInfo.execution_time}\n`;
            output += `- Effective limit: ${queryInfo.effective_limit}\n\n`;
            
            output += `🔍 Query Info:\n`;
            output += `- Original query: ${queryInfo.original_query}\n`;
            output += `- Final query: ${queryInfo.final_query}\n\n`;
            
            output += `Account IDs:\n${'='.repeat(50)}\n`;
            accountIds.forEach((id, index) => {
                output += `${index + 1}. ${id}\n`;
            });
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
            
            // Enable the next step button
            getDataBtn.disabled = false;
        } else {
            responseDiv.innerHTML = `❌ Error: ${data.message}`;
            responseDiv.className = 'response error';
            getDataBtn.disabled = true;
            exportBtn.disabled = true;
        }
        
    } catch (error) {
        responseDiv.innerHTML = `❌ Network Error: ${error.message}`;
        responseDiv.className = 'response error';
        getDataBtn.disabled = true;
        exportBtn.disabled = true;
    } finally {
        // Restore button state
        button.disabled = false;
        button.textContent = 'Validate Account IDs';
        responseDiv.style.display = 'block';
    }
}

async function handleGetAccountData(e) {
    e.preventDefault();
    
    if (!analysisResults || !analysisResults.data.account_ids) {
        alert('Please validate Account IDs first.');
        return;
    }
    
    const responseDiv = document.getElementById('queryResponse');
    const button = document.getElementById('getAccountDataBtn');
    const exportBtn = document.getElementById('exportBtn');
    const accountIds = analysisResults.data.account_ids;
    
    try {
        // Show loading state
        button.disabled = true;
        button.textContent = 'Analyzing...';
        exportBtn.disabled = true;
        responseDiv.innerHTML = 'Analyzing accounts...';
        responseDiv.className = 'response loading';
        
        const response = await fetch('/accounts/get-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                account_ids: accountIds
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const accounts = data.data.accounts;
            const summary = data.data.summary;
            
            let output = `✅ Account Analysis Complete!\n\n`;
            output += `📊 Summary:\n`;
            output += `- Accounts requested: ${summary.total_requested}\n`;
            output += `- Accounts retrieved: ${summary.accounts_retrieved}\n`;
            output += `- Execution time: ${data.data.execution_time}\n\n`;
            
            output += `Account Details:\n${'='.repeat(50)}\n\n`;
            
            accounts.forEach((account, index) => {
                output += `${index + 1}. Account: ${account.Name} (${account.Id})\n`;
                output += `   Record Type: ${account.RecordType?.Name || 'N/A'}\n`;
                output += `   Website: ${account.Website || 'N/A'}\n`;
                output += `   Ultimate Parent: ${account.Ultimate_Parent_Account_Name__c || 'N/A'}\n`;
                output += `   Billing Address: ${formatBillingAddress(account)}\n`;
                output += `   ZI Company: ${account.ZI_Company_Name__c || 'N/A'}\n`;
                output += `   ZI Website: ${account.ZI_Website__c || 'N/A'}\n`;
                output += `   Parent Account ID: ${account.Parent_Account_ID__c || 'N/A'}\n\n`;
            });
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
            
            // Enable export button (though it's disabled for now)
            // exportBtn.disabled = false;
            
            // Update stored results for future export
            analysisResults.data.accounts = accounts;
        } else {
            responseDiv.innerHTML = `❌ Error getting account data: ${data.message}`;
            responseDiv.className = 'response error';
        }
        
    } catch (error) {
        responseDiv.innerHTML = `❌ Network Error: ${error.message}`;
        responseDiv.className = 'response error';
    } finally {
        // Restore button state
        button.disabled = false;
        button.textContent = 'Analyze Accounts';
    }
}

async function handleAccountFormSubmit(e) {
    e.preventDefault();
    
    const responseDiv = document.getElementById('accountResponse');
    const button = e.target.querySelector('button[type="submit"]');
    const exportBtn = document.getElementById('exportAccountBtn');
    
    // Get form values
    const accountId = document.getElementById('accountId').value.trim();
    
    // Validate inputs
    if (!accountId) {
        responseDiv.innerHTML = 'Please enter an Account ID.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Analyzing...';
    exportBtn.disabled = true;
    responseDiv.innerHTML = 'Analyzing account...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const response = await fetch(`/account/${accountId}`);
        const data = await response.json();
        
        if (response.ok) {
            singleAccountResults = data;
            const account = data.account;
            
            let output = `✅ Account Analysis Complete!\n\n`;
            output += `Account Details:\n${'='.repeat(50)}\n\n`;
            output += `ID: ${account.Id}\n`;
            output += `Name: ${account.Name}\n`;
            output += `Record Type: ${account.RecordType?.Name || 'N/A'}\n`;
            output += `Ultimate Parent: ${account.Ultimate_Parent_Account_Name__c || 'N/A'}\n`;
            output += `Website: ${account.Website || 'N/A'}\n`;
            output += `Billing Address: ${formatBillingAddress(account)}\n`;
            output += `ZI Company: ${account.ZI_Company_Name__c || 'N/A'}\n`;
            output += `ZI Website: ${account.ZI_Website__c || 'N/A'}\n`;
            output += `Parent Account ID: ${account.Parent_Account_ID__c || 'N/A'}\n`;
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
            
            // Enable export button (though it's disabled for now)
            // exportBtn.disabled = false;
        } else {
            responseDiv.innerHTML = `❌ Error: ${data.message}`;
            responseDiv.className = 'response error';
            exportBtn.disabled = true;
        }
        
    } catch (error) {
        responseDiv.innerHTML = `❌ Network Error: ${error.message}`;
        responseDiv.className = 'response error';
        exportBtn.disabled = true;
    } finally {
        // Restore button state
        button.disabled = false;
        button.textContent = 'Analyze Account';
        responseDiv.style.display = 'block';
    }
}

function formatBillingAddress(account) {
    const parts = [
        account.BillingStreet,
        account.BillingCity,
        account.BillingState,
        account.BillingCountry
    ].filter(part => part && part.trim());
    
    return parts.length > 0 ? parts.join(', ') : 'N/A';
}

// Placeholder functions for export functionality
async function handleExportAnalysis(e) {
    e.preventDefault();
    alert('Export functionality to be implemented');
}

async function handleExportAccount(e) {
    e.preventDefault();
    alert('Export functionality to be implemented');
}

async function handleExportExcel(e) {
    e.preventDefault();
    alert('Export functionality to be implemented');
}

// Excel handling functions
async function handleExcelFileChange(e) {
    const file = e.target.files[0];
    const parseBtn = document.getElementById('parseExcelBtn');
    const configDiv = document.getElementById('excelConfig');
    const responseDiv = document.getElementById('excelResponse');
    const validateBtn = document.getElementById('validateAccountIdsBtn');
    const exportBtn = document.getElementById('exportExcelBtn');
    
    if (file) {
        excelFileData = file;
        parseBtn.disabled = false;
        configDiv.style.display = 'none';
        responseDiv.style.display = 'none';
        
        // Reset subsequent buttons
        validateBtn.disabled = true;
        exportBtn.disabled = true;
        
        // Clear previous data
        excelPreviewData = null;
        excelAnalysisResults = null;
    } else {
        excelFileData = null;
        parseBtn.disabled = true;
        configDiv.style.display = 'none';
        validateBtn.disabled = true;
        exportBtn.disabled = true;
    }
}

async function handleParseExcel(e) {
    e.preventDefault();
    
    if (!excelFileData) {
        alert('Please select an Excel file first.');
        return;
    }
    
    const button = e.target;
    const responseDiv = document.getElementById('excelResponse');
    const validateBtn = document.getElementById('validateAccountIdsBtn');
    const exportBtn = document.getElementById('exportExcelBtn');
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Parsing...';
    validateBtn.disabled = true;
    exportBtn.disabled = true;
    responseDiv.innerHTML = 'Parsing Excel file...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', excelFileData);
        
        const response = await fetch('/excel/parse', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            excelPreviewData = data.data;
            populateExcelSelectors(data.data);
            responseDiv.innerHTML = `✅ File parsed successfully! Found ${data.data.total_rows} rows in ${data.data.sheet_names.length} sheet(s).\n\nSelect the sheet and Account ID column, then validate the Account IDs.`;
            responseDiv.className = 'response success';
            document.getElementById('excelConfig').style.display = 'block';
            validateBtn.disabled = false;
        } else {
            responseDiv.innerHTML = `❌ Parse failed: ${data.message}`;
            responseDiv.className = 'response error';
            document.getElementById('excelConfig').style.display = 'none';
            validateBtn.disabled = true;
            exportBtn.disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `❌ Network Error: ${error.message}`;
        responseDiv.className = 'response error';
        document.getElementById('excelConfig').style.display = 'none';
        validateBtn.disabled = true;
        exportBtn.disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = '1. Parse File';
    }
}

function populateExcelSelectors(data) {
    const sheetSelect = document.getElementById('sheetSelect');
    const columnSelect = document.getElementById('accountIdColumn');
    
    // Populate sheet selector
    sheetSelect.innerHTML = '';
    data.sheet_names.forEach(sheetName => {
        const option = document.createElement('option');
        option.value = sheetName;
        option.textContent = sheetName;
        sheetSelect.appendChild(option);
    });
    
    // Populate column selector
    columnSelect.innerHTML = '<option value="">-- Select Account ID Column --</option>';
    data.headers.forEach(header => {
        const option = document.createElement('option');
        option.value = header;
        option.textContent = header;
        columnSelect.appendChild(option);
    });
}

async function handleValidateAccountIds(e) {
    e.preventDefault();
    
    if (!excelFileData || !excelPreviewData) {
        alert('Please parse the Excel file first.');
        return;
    }
    
    const button = e.target;
    const responseDiv = document.getElementById('excelResponse');
    const exportBtn = document.getElementById('exportExcelBtn');
    const sheetName = document.getElementById('sheetSelect').value;
    const accountIdColumn = document.getElementById('accountIdColumn').value;
    
    if (!sheetName || !accountIdColumn) {
        alert('Please select both sheet and Account ID column.');
        return;
    }
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Validating & Analyzing...';
    exportBtn.disabled = true;
    responseDiv.innerHTML = 'Validating Account IDs with Salesforce and retrieving Account data...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', excelFileData);
        formData.append('sheet_name', sheetName);
        formData.append('account_id_column', accountIdColumn);
        
        const response = await fetch('/excel/validate-account-ids', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const summary = data.data.validation_summary;
            const accounts = data.data.accounts;
            const excelInfo = data.data.excel_info;
            
            let output = `✅ Excel Account Analysis Complete!\n\n`;
            output += `📊 Validation Summary:\n`;
            output += `- Total IDs from Excel: ${summary.total_ids_from_excel}\n`;
            output += `- Valid Account IDs: ${summary.valid_account_ids}\n`;
            output += `- Invalid Account IDs: ${summary.invalid_account_ids}\n`;
            output += `- Execution time: ${data.data.execution_time}\n\n`;
            
            output += `📁 Excel File Info:\n`;
            output += `- File: ${excelInfo.file_name}\n`;
            output += `- Sheet: ${excelInfo.sheet_name}\n`;
            output += `- Account ID Column: ${excelInfo.account_id_column}\n\n`;
            
            output += `Account Details:\n${'='.repeat(50)}\n\n`;
            
            accounts.forEach((account, index) => {
                output += `${index + 1}. Account: ${account.Name} (${account.Id})\n`;
                output += `   Record Type: ${account.RecordType?.Name || 'N/A'}\n`;
                output += `   Website: ${account.Website || 'N/A'}\n`;
                output += `   Ultimate Parent: ${account.Ultimate_Parent_Account_Name__c || 'N/A'}\n`;
                output += `   Billing Address: ${formatBillingAddress(account)}\n`;
                output += `   ZI Company: ${account.ZI_Company_Name__c || 'N/A'}\n`;
                output += `   ZI Website: ${account.ZI_Website__c || 'N/A'}\n`;
                output += `   Parent Account ID: ${account.Parent_Account_ID__c || 'N/A'}\n\n`;
            });
            
            responseDiv.innerHTML = `<pre>${output}</pre>`;
            responseDiv.className = 'response success';
            
            // Enable export button (though it's disabled for now)
            // exportBtn.disabled = false;
            
            // Store results for future export
            excelAnalysisResults = data;
        } else {
            if (data.data && data.data.invalid_account_ids && data.data.invalid_account_ids.length > 0) {
                let output = `❌ Validation Failed!\n\n`;
                output += `📋 Validation Summary:\n`;
                output += `- Total IDs from Excel: ${data.data.total_from_excel}\n`;
                output += `- Valid Account IDs: ${data.data.valid_account_ids.length}\n`;
                output += `- Invalid Account IDs: ${data.data.invalid_account_ids.length}\n\n`;
                
                output += `❌ Invalid Account IDs found:\n`;
                data.data.invalid_account_ids.forEach(id => {
                    output += `  • ${id}\n`;
                });
                output += `\n❌ Please fix the invalid Account IDs before proceeding.`;
                
                responseDiv.innerHTML = `<pre>${output}</pre>`;
            } else {
                responseDiv.innerHTML = `❌ Error: ${data.message}`;
            }
            responseDiv.className = 'response error';
            exportBtn.disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `❌ Network Error: ${error.message}`;
        responseDiv.className = 'response error';
        exportBtn.disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = '2. Validate Account IDs';
    }
}