// Global variables to store analysis results for export
let previewData = null;
let analysisResults = null;
let singleLeadResults = null;

// Global variables for Excel upload functionality
let excelFileData = null;
let excelPreviewData = null;
let excelAnalysisResults = null;

// Initialize event handlers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventHandlers();
});

function initializeEventHandlers() {
    // Preview Query Button Handler
    document.getElementById('previewBtn').addEventListener('click', handlePreviewQuery);
    
    // SOQL Query Form Handler (Full Analysis)
    document.getElementById('queryForm').addEventListener('submit', handleQueryFormSubmit);
    
    // Export Button Handler for Analyze Query
    document.getElementById('exportBtn').addEventListener('click', handleExportAnalysis);
    
    // Lead Confidence Form Handler
    document.getElementById('confidenceForm').addEventListener('submit', handleConfidenceFormSubmit);
    
    // Export Button Handler for Lead Confidence
    document.getElementById('exportConfidenceBtn').addEventListener('click', handleExportConfidence);
    
    // Clear stored results when inputs change
    document.getElementById('leadId').addEventListener('input', function() {
        singleLeadResults = null;
        document.getElementById('exportConfidenceBtn').disabled = true;
    });
    
    document.getElementById('soqlQuery').addEventListener('input', function() {
        analysisResults = null;
        document.getElementById('exportBtn').disabled = true;
    });
    
    document.getElementById('maxAnalyze').addEventListener('input', function() {
        analysisResults = null;
        document.getElementById('exportBtn').disabled = true;
    });
    
    // Excel upload event handlers
    document.getElementById('excelFile').addEventListener('change', handleExcelFileChange);
    document.getElementById('parseExcelBtn').addEventListener('click', handleParseExcel);
    document.getElementById('validateLeadIdsBtn').addEventListener('click', handleValidateLeadIds);
    document.getElementById('analyzeExcelBtn').addEventListener('click', handleAnalyzeExcel);
    document.getElementById('exportExcelBtn').addEventListener('click', handleExportExcel);
}

async function handlePreviewQuery(e) {
    e.preventDefault();
    
    const responseDiv = document.getElementById('queryResponse');
    const button = e.target;
    const analyzeBtn = document.getElementById('analyzeBtn');
    
    // Get form values
    const whereClause = document.getElementById('soqlQuery').value.trim();
    const previewLimit = parseInt(document.getElementById('previewLimit').value);
    
    // Validate inputs
    if (isNaN(previewLimit) || previewLimit < 1 || previewLimit > 1000) {
        responseDiv.innerHTML = 'Preview limit must be a number between 1 and 1000.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    // Build SOQL query - let backend handle empty queries
    const fullQuery = whereClause;
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Previewing...';
    analyzeBtn.disabled = true;
    document.getElementById('exportBtn').disabled = true;
    responseDiv.innerHTML = 'Previewing query results...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const response = await fetch('/leads/preview-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                soql_query: fullQuery,
                preview_limit: previewLimit
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            previewData = data.data;
            responseDiv.innerHTML = `✅ Preview Results:\n\n${JSON.stringify(data, null, 2)}\n\n✅ Query successful! You can now proceed to analyze the leads.`;
            responseDiv.className = 'response success';
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = `Get Confidence Assessment (${Math.min(previewData.total_found, parseInt(document.getElementById('maxAnalyze').value))} leads)`;
        } else {
            responseDiv.innerHTML = JSON.stringify(data, null, 2);
            responseDiv.className = 'response error';
            analyzeBtn.disabled = true;
            document.getElementById('exportBtn').disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `Error: ${error.message}`;
        responseDiv.className = 'response error';
        analyzeBtn.disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = '1. Preview Query';
    }
}

async function handleQueryFormSubmit(e) {
    e.preventDefault();
    
    if (!previewData) {
        const responseDiv = document.getElementById('queryResponse');
        responseDiv.innerHTML = 'Please run the preview first to see which leads will be analyzed.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    const responseDiv = document.getElementById('queryResponse');
    const button = document.getElementById('analyzeBtn');
    
    // Get form values
    const whereClause = document.getElementById('soqlQuery').value.trim();
    const maxAnalyze = parseInt(document.getElementById('maxAnalyze').value);
    
    // Validate inputs
    if (isNaN(maxAnalyze) || maxAnalyze < 1 || maxAnalyze > 500) {
        responseDiv.innerHTML = 'Max leads to analyze must be a number between 1 and 500.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    // Build SOQL query - let backend handle empty queries
    const fullQuery = whereClause;
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Analyzing...';
    document.getElementById('exportBtn').disabled = true;
    responseDiv.innerHTML = `Analyzing first ${maxAnalyze} leads from ${previewData.total_found} total leads found (with AI confidence scoring)...`;
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const response = await fetch('/leads/analyze-query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                soql_query: fullQuery,
                max_analyze: maxAnalyze,
                include_ai_assessment: true
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            analysisResults = data;
            const summary = data.data.summary;
            const leads = data.data.leads;
            const queryInfo = data.data.query_info;
            
            // Display summary and individual lead results
            let output = `✅ SOQL Query Analysis Complete!\n\n📊 Summary:\n- Total query results: ${summary.total_query_results}\n- Leads analyzed: ${summary.leads_analyzed}\n- Leads with issues: ${summary.leads_with_issues} (${summary.issue_percentage}%)\n- Average confidence score: ${summary.avg_confidence_score}\n- AI assessments successful: ${summary.ai_assessments_successful}\n- AI assessments failed: ${summary.ai_assessments_failed}\n\n`;
            
            if (queryInfo) {
                output += `🔍 Query Info:\n- Execution time: ${queryInfo.execution_time}\n- Total found: ${queryInfo.total_found}\n- Analyzed count: ${queryInfo.analyzed_count}\n`;
                if (queryInfo.skipped_count > 0) {
                    output += `- Skipped count: ${queryInfo.skipped_count}\n`;
                }
                output += `\n`;
            }
            
            output += `Ready to export results!\n\n`;
            output += `🔍 Individual Lead Results:\n${'='.repeat(50)}\n\n`;
            
            leads.forEach((lead, index) => {
                output += `Lead ${index + 1}: ${lead.Id}\n`;
                output += `Email: ${lead.Email || 'N/A'}\n`;
                output += `First Channel: ${lead.First_Channel__c || 'N/A'}\n`;
                output += `Segment: ${lead.SegmentName || 'N/A'}\n`;
                output += `Company Size Range: ${lead.LS_Company_Size_Range__c || 'N/A'}\n`;
                output += `Website: ${lead.Website || 'N/A'}\n`;
                output += `Company: ${lead.Company || 'N/A'}\n`;
                output += `ZI Company: ${lead.ZI_Company_Name__c || 'N/A'}\n`;
                output += `ZI Employees: ${lead.ZI_Employees__c || 'N/A'}\n`;
                output += `ZI Website: ${lead.ZI_Website__c || 'N/A'}\n`;
                output += `Email Domain: ${lead.email_domain || 'N/A'}\n`;
                output += `Not in TAM: ${lead.not_in_TAM ? 'Yes' : 'No'}\n`;
                output += `Suspicious Enrichment: ${lead.suspicious_enrichment ? 'Yes' : 'No'}\n`;
                
                if (lead.confidence_assessment) {
                    const assessment = lead.confidence_assessment;
                    output += `Confidence Score: ${assessment.confidence_score || 'N/A'}\n`;
                    
                    if (assessment.explanation_bullets && assessment.explanation_bullets.length > 0) {
                        output += `Explanation:\n`;
                        assessment.explanation_bullets.forEach(bullet => {
                            output += `  • ${bullet}\n`;
                        });
                    }
                    
                    if (assessment.corrections && Object.keys(assessment.corrections).length > 0) {
                        output += `Corrections:\n`;
                        Object.entries(assessment.corrections).forEach(([field, value]) => {
                            output += `  • ${field}: ${value}\n`;
                        });
                    }
                    
                    if (assessment.inferences && Object.keys(assessment.inferences).length > 0) {
                        output += `Inferences:\n`;
                        Object.entries(assessment.inferences).forEach(([field, value]) => {
                            output += `  • ${field}: ${value}\n`;
                        });
                    }
                } else {
                    output += `AI Assessment: ${lead.ai_assessment_status || 'Failed'}\n`;
                }
                
                output += `\n${'-'.repeat(40)}\n\n`;
            });
            
            responseDiv.innerHTML = output;
            responseDiv.className = 'response success';
            document.getElementById('exportBtn').disabled = false;
        } else {
            analysisResults = null;
            responseDiv.innerHTML = JSON.stringify(data, null, 2);
            responseDiv.className = 'response error';
            document.getElementById('exportBtn').disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `Error: ${error.message}`;
        responseDiv.className = 'response error';
        document.getElementById('exportBtn').disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = `Get Confidence Assessment (${Math.min(previewData.total_found, maxAnalyze)} leads)`;
    }
}

async function handleExportAnalysis(e) {
    e.preventDefault();
    
    if (!analysisResults) {
        alert('Please run the analysis first before exporting.');
        return;
    }
    
    const button = e.target;
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Exporting...';
    
    try {
        const response = await fetch('/leads/export-analysis-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                analysis_data: analysisResults.data
            })
        });
        
        if (response.ok) {
            await downloadFile(response, 'lead_query_analysis.xlsx');
            alert('Excel file downloaded successfully!');
        } else {
            const errorData = await response.json();
            alert(`Export failed: ${errorData.message}`);
        }
    } catch (error) {
        alert(`Export error: ${error.message}`);
    } finally {
        button.disabled = false;
        button.textContent = '📊 Export to Excel';
    }
}

async function handleConfidenceFormSubmit(e) {
    e.preventDefault();
    
    const responseDiv = document.getElementById('confidenceResponse');
    const button = e.target.querySelector('button');
    const leadId = document.getElementById('leadId').value.trim();
    
    // Clear previous results when analyzing a new lead
    singleLeadResults = null;
    document.getElementById('exportConfidenceBtn').disabled = true;
    
    // Validate Lead ID
    if (!leadId) {
        responseDiv.innerHTML = 'Please enter a Salesforce Lead ID.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    if (leadId.length < 15 || leadId.length > 18) {
        responseDiv.innerHTML = 'Lead ID must be 15-18 characters long.';
        responseDiv.className = 'response error';
        responseDiv.style.display = 'block';
        return;
    }
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Analyzing...';
    responseDiv.innerHTML = 'Getting lead data and generating confidence assessment...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const response = await fetch(`/lead/${leadId}/confidence`);
        const data = await response.json();
        
        if (response.ok) {
            singleLeadResults = data;
            const lead = data.lead_data;  // Fixed: use lead_data instead of data
            const assessment = data.confidence_assessment;  // Get assessment from top level
            
            // Display single lead analysis results
            let output = `✅ Single Lead Analysis Complete!\n\n`;
            output += `🔍 Lead Details:\n${'='.repeat(30)}\n`;
            output += `Lead ID: ${lead.Id}\n`;
            output += `Email: ${lead.Email || 'N/A'}\n`;
            output += `First Channel: ${lead.First_Channel__c || 'N/A'}\n`;
            output += `Segment: ${lead.SegmentName || 'N/A'}\n`;
            output += `Company Size Range: ${lead.LS_Company_Size_Range__c || 'N/A'}\n`;
            output += `Website: ${lead.Website || 'N/A'}\n`;
            output += `Company: ${lead.Company || 'N/A'}\n`;
            output += `ZI Company: ${lead.ZI_Company_Name__c || 'N/A'}\n`;
            output += `ZI Employees: ${lead.ZI_Employees__c || 'N/A'}\n`;
            output += `ZI Website: ${lead.ZI_Website__c || 'N/A'}\n`;
            output += `Email Domain: ${lead.email_domain || 'N/A'}\n\n`;
            
            output += `🚩 Quality Flags:\n`;
            output += `Not in TAM: ${lead.not_in_TAM ? 'Yes' : 'No'}\n`;
            output += `Suspicious Enrichment: ${lead.suspicious_enrichment ? 'Yes' : 'No'}\n\n`;
            
            if (assessment) {
                output += `🤖 AI Assessment:\n${'='.repeat(30)}\n`;
                output += `Confidence Score: ${assessment.confidence_score || 'N/A'}\n\n`;
                
                if (assessment.explanation_bullets && assessment.explanation_bullets.length > 0) {
                    output += `📝 Explanation:\n`;
                    assessment.explanation_bullets.forEach(bullet => {
                        output += `  • ${bullet}\n`;
                    });
                    output += `\n`;
                }
                
                if (assessment.corrections && Object.keys(assessment.corrections).length > 0) {
                    output += `🔧 Corrections:\n`;
                    Object.entries(assessment.corrections).forEach(([field, value]) => {
                        output += `  • ${field}: ${value}\n`;
                    });
                    output += `\n`;
                }
                
                if (assessment.inferences && Object.keys(assessment.inferences).length > 0) {
                    output += `💡 Inferences:\n`;
                    Object.entries(assessment.inferences).forEach(([field, value]) => {
                        output += `  • ${field}: ${value}\n`;
                    });
                    output += `\n`;
                }
            } else {
                output += `🤖 AI Assessment: Failed\n\n`;
            }
            
            output += `Ready to export results!`;
            
            responseDiv.innerHTML = output;
            responseDiv.className = 'response success';
            document.getElementById('exportConfidenceBtn').disabled = false;
        } else {
            singleLeadResults = null;
            responseDiv.innerHTML = JSON.stringify(data, null, 2);
            responseDiv.className = 'response error';
            document.getElementById('exportConfidenceBtn').disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `Error: ${error.message}`;
        responseDiv.className = 'response error';
    } finally {
        button.disabled = false;
        button.textContent = 'Get Confidence Assessment';
    }
}

async function handleExportConfidence(e) {
    e.preventDefault();
    
    if (!singleLeadResults) {
        alert('Please run the confidence analysis first before exporting.');
        return;
    }
    
    const button = e.target;
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Exporting...';
    
    try {
        const response = await fetch('/leads/export-single-lead-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                lead_data: singleLeadResults
            })
        });
        
        if (response.ok) {
            const leadId = singleLeadResults.lead_data?.Id || 'unknown';
            await downloadFile(response, `lead_confidence_${leadId}.xlsx`);
            alert('Excel file downloaded successfully!');
        } else {
            const errorData = await response.json();
            alert(`Export failed: ${errorData.message}`);
        }
    } catch (error) {
        alert(`Export error: ${error.message}`);
    } finally {
        button.disabled = false;
        button.textContent = '📊 Export to Excel';
    }
}

async function downloadFile(response, defaultFilename) {
    // Handle file download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    
    // Extract filename from response headers or use default
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = defaultFilename;
    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
            filename = filenameMatch[1];
        }
    }
    
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
}

// Excel Upload Handlers

function handleExcelFileChange(e) {
    const file = e.target.files[0];
    const parseBtn = document.getElementById('parseExcelBtn');
    const configDiv = document.getElementById('excelConfig');
    const responseDiv = document.getElementById('excelResponse');
    
    if (file) {
        excelFileData = file;
        parseBtn.disabled = false;
        configDiv.style.display = 'none';
        responseDiv.style.display = 'none';
        
        // Reset all subsequent buttons
        document.getElementById('validateLeadIdsBtn').disabled = true;
        document.getElementById('analyzeExcelBtn').disabled = true;
        document.getElementById('exportExcelBtn').disabled = true;
        
        // Clear previous data
        excelPreviewData = null;
        excelAnalysisResults = null;
    } else {
        excelFileData = null;
        parseBtn.disabled = true;
        configDiv.style.display = 'none';
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
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Parsing...';
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
            responseDiv.innerHTML = `✅ File parsed successfully! Found ${data.data.total_rows} rows in ${data.data.sheet_names.length} sheet(s).\n\nSelect the sheet and Lead ID column, then validate the Lead IDs.`;
            responseDiv.className = 'response success';
            document.getElementById('excelConfig').style.display = 'block';
            document.getElementById('validateLeadIdsBtn').disabled = false;
        } else {
            responseDiv.innerHTML = JSON.stringify(data, null, 2);
            responseDiv.className = 'response error';
            document.getElementById('excelConfig').style.display = 'none';
        }
    } catch (error) {
        responseDiv.innerHTML = `Error: ${error.message}`;
        responseDiv.className = 'response error';
        document.getElementById('excelConfig').style.display = 'none';
    } finally {
        button.disabled = false;
        button.textContent = '1. Parse File';
    }
}

function populateExcelSelectors(data) {
    const sheetSelect = document.getElementById('sheetSelect');
    const columnSelect = document.getElementById('leadIdColumn');
    
    // Populate sheet selector
    sheetSelect.innerHTML = '';
    data.sheet_names.forEach(sheetName => {
        const option = document.createElement('option');
        option.value = sheetName;
        option.textContent = sheetName;
        sheetSelect.appendChild(option);
    });
    
    // Populate column selector
    columnSelect.innerHTML = '<option value="">-- Select Lead ID Column --</option>';
    data.headers.forEach(header => {
        const option = document.createElement('option');
        option.value = header;
        option.textContent = header;
        columnSelect.appendChild(option);
    });
}

async function handleValidateLeadIds(e) {
    e.preventDefault();
    
    if (!excelFileData || !excelPreviewData) {
        alert('Please parse the Excel file first.');
        return;
    }
    
    const button = e.target;
    const responseDiv = document.getElementById('excelResponse');
    const sheetName = document.getElementById('sheetSelect').value;
    const leadIdColumn = document.getElementById('leadIdColumn').value;
    
    if (!sheetName || !leadIdColumn) {
        alert('Please select both sheet and Lead ID column.');
        return;
    }
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Validating...';
    responseDiv.innerHTML = 'Validating Lead IDs with Salesforce...';
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', excelFileData);
        formData.append('sheet_name', sheetName);
        formData.append('lead_id_column', leadIdColumn);
        
        const response = await fetch('/excel/validate-lead-ids', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const validationData = data.data;
            let output = `✅ Validation Complete!\n\n`;
            output += `📋 Validation Summary:\n`;
            output += `- Total Lead IDs found: ${validationData.total_lead_ids}\n`;
            output += `- Valid Lead IDs: ${validationData.valid_lead_ids}\n`;
            output += `- Invalid Lead IDs: ${validationData.invalid_lead_ids}\n`;
            
            if (validationData.invalid_ids && validationData.invalid_ids.length > 0) {
                output += `\n❌ Invalid Lead IDs found:\n`;
                validationData.invalid_ids.forEach(id => {
                    output += `  • ${id}\n`;
                });
                output += `\n❌ Please fix the invalid Lead IDs before proceeding.`;
                responseDiv.className = 'response error';
                document.getElementById('analyzeExcelBtn').disabled = true;
            } else {
                output += `\n✅ All Lead IDs are valid! You can now proceed to analyze.`;
                responseDiv.className = 'response success';
                document.getElementById('analyzeExcelBtn').disabled = false;
            }
            
            responseDiv.innerHTML = output;
        } else {
            responseDiv.innerHTML = `❌ Validation failed!\n\n${JSON.stringify(data, null, 2)}`;
            responseDiv.className = 'response error';
            document.getElementById('analyzeExcelBtn').disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `Error: ${error.message}`;
        responseDiv.className = 'response error';
        document.getElementById('analyzeExcelBtn').disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = '2. Validate Lead IDs';
    }
}

async function handleAnalyzeExcel(e) {
    e.preventDefault();
    
    if (!excelFileData || !excelPreviewData) {
        alert('Please parse and validate the Excel file first.');
        return;
    }
    
    const button = e.target;
    const responseDiv = document.getElementById('excelResponse');
    const sheetName = document.getElementById('sheetSelect').value;
    const leadIdColumn = document.getElementById('leadIdColumn').value;
    
    // Validate inputs
    if (!sheetName || !leadIdColumn) {
        alert('Please select both sheet and Lead ID column.');
        return;
    }
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Analyzing...';
    document.getElementById('exportExcelBtn').disabled = true;
    responseDiv.innerHTML = `Analyzing all leads from Excel file with AI confidence scoring...`;
    responseDiv.className = 'response loading';
    responseDiv.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('file', excelFileData);
        formData.append('sheet_name', sheetName);
        formData.append('lead_id_column', leadIdColumn);
        formData.append('max_analyze', '10000'); // Set high limit to analyze all
        formData.append('include_ai_assessment', 'true'); // Always include AI assessment
        
        const response = await fetch('/excel/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            excelAnalysisResults = data;
            const summary = data.data.summary;
            const leads = data.data.leads;
            
            // Display summary and individual lead results
            let output = `✅ Analysis complete!\n\n📊 Summary:\n- Total leads analyzed: ${summary.leads_analyzed}\n- Leads with issues: ${summary.leads_with_issues} (${summary.issue_percentage}%)\n- Average confidence score: ${summary.avg_confidence_score}\n- AI assessments successful: ${summary.ai_assessments_successful}\n\nReady to export results!\n\n`;
            
            output += `🔍 Individual Lead Results:\n${'='.repeat(50)}\n\n`;
            
            leads.forEach((lead, index) => {
                output += `Lead ${index + 1}: ${lead.Id}\n`;
                output += `Email: ${lead.Email || 'N/A'}\n`;
                output += `First Channel: ${lead.First_Channel__c || 'N/A'}\n`;
                output += `Segment: ${lead.SegmentName || 'N/A'}\n`;
                output += `Company Size Range: ${lead.LS_Company_Size_Range__c || 'N/A'}\n`;
                output += `Website: ${lead.Website || 'N/A'}\n`;
                output += `Company: ${lead.Company || 'N/A'}\n`;
                output += `ZI Company: ${lead.ZI_Company_Name__c || 'N/A'}\n`;
                output += `ZI Employees: ${lead.ZI_Employees__c || 'N/A'}\n`;
                output += `ZI Website: ${lead.ZI_Website__c || 'N/A'}\n`;
                output += `Email Domain: ${lead.email_domain || 'N/A'}\n`;
                output += `Not in TAM: ${lead.not_in_TAM ? 'Yes' : 'No'}\n`;
                output += `Suspicious Enrichment: ${lead.suspicious_enrichment ? 'Yes' : 'No'}\n`;
                
                if (lead.confidence_assessment) {
                    const assessment = lead.confidence_assessment;
                    output += `Confidence Score: ${assessment.confidence_score || 'N/A'}\n`;
                    
                    if (assessment.explanation_bullets && assessment.explanation_bullets.length > 0) {
                        output += `Explanation:\n`;
                        assessment.explanation_bullets.forEach(bullet => {
                            output += `  • ${bullet}\n`;
                        });
                    }
                    
                    if (assessment.corrections && Object.keys(assessment.corrections).length > 0) {
                        output += `Corrections:\n`;
                        Object.entries(assessment.corrections).forEach(([field, value]) => {
                            output += `  • ${field}: ${value}\n`;
                        });
                    }
                    
                    if (assessment.inferences && Object.keys(assessment.inferences).length > 0) {
                        output += `Inferences:\n`;
                        Object.entries(assessment.inferences).forEach(([field, value]) => {
                            output += `  • ${field}: ${value}\n`;
                        });
                    }
                } else {
                    output += `AI Assessment: ${lead.ai_assessment_status || 'Failed'}\n`;
                }
                
                output += `\n${'-'.repeat(40)}\n\n`;
            });
            
            responseDiv.innerHTML = output;
            responseDiv.className = 'response success';
            document.getElementById('exportExcelBtn').disabled = false;
        } else {
            excelAnalysisResults = null;
            responseDiv.innerHTML = JSON.stringify(data, null, 2);
            responseDiv.className = 'response error';
            document.getElementById('exportExcelBtn').disabled = true;
        }
    } catch (error) {
        responseDiv.innerHTML = `Error: ${error.message}`;
        responseDiv.className = 'response error';
        document.getElementById('exportExcelBtn').disabled = true;
    } finally {
        button.disabled = false;
        button.textContent = '3. Analyze All Leads';
    }
}

async function handleExportExcel(e) {
    e.preventDefault();
    
    if (!excelAnalysisResults) {
        alert('Please run the Excel analysis first before exporting.');
        return;
    }
    
    const button = e.target;
    const leadIdColumn = document.getElementById('leadIdColumn').value;
    const sheetName = document.getElementById('sheetSelect').value;
    
    // Show loading state
    button.disabled = true;
    button.textContent = 'Exporting...';
    
    try {
        // Create FormData to re-send the file for export
        const formData = new FormData();
        formData.append('file', excelFileData);
        formData.append('sheet_name', sheetName);
        formData.append('lead_id_column', leadIdColumn);
        formData.append('analysis_results', JSON.stringify(excelAnalysisResults.data.leads));
        
        const response = await fetch('/excel/export-analysis-with-file', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            await downloadFile(response, 'excel_analysis.xlsx');
            alert('Excel file with analysis results downloaded successfully!');
        } else {
            const errorData = await response.json();
            alert(`Export failed: ${errorData.message}`);
        }
    } catch (error) {
        alert(`Export error: ${error.message}`);
    } finally {
        button.disabled = false;
        button.textContent = '📊 Export Results';
    }
} 