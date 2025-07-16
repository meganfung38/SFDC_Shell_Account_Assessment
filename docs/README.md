# ZoomInfo Enrichment Quality Assessment API Documentation

A Flask API for assessing the quality and reliability of ZoomInfo-enriched lead data with OpenAI-powered confidence scoring and professional Excel export capabilities.

## Setup

### 1. Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r config/requirements.txt

# Configure environment
cp config/env.example .env
# Edit .env with your credentials
```

### 2. Required Environment Variables
```bash
# Salesforce
SF_USERNAME=your_username
SF_PASSWORD=your_password  
SF_SECURITY_TOKEN=your_token
SF_DOMAIN=login  # or 'test' for sandbox

# OpenAI
OPENAI_API_KEY=sk-your-key-here
```

### 3. Run Application
```bash
python app.py
```

Access the web interface at `http://localhost:5000/ui`

## Demo

📹 **[Watch the Complete Demo](https://drive.google.com/file/d/1G5kbyXztMqzkW44-von2Jbu0ZlHpYQ92/view?usp=sharing)** - See the API in action with step-by-step usage examples

## Architecture

### Core Services

**SalesforceService** (`services/salesforce_service.py`)
- Lead data retrieval with 11+ enrichment fields
- Complex SOQL query support with security validation
- Quality flag computation (`not_in_TAM`, `suspicious_enrichment`)
- Optimized batch processing with robust Lead ID handling (15 ↔ 18 character conversion)

**OpenAIService** (`services/openai_service.py`)
- AI-powered confidence scoring (0-100) with detailed explanations
- Intelligent corrections and inferences based on contextual analysis
- Advanced redundancy validation to prevent duplicate suggestions
- Contextual prompt engineering for accurate assessments
- Free email domain filtering and website accessibility validation

**ExcelService** (`services/excel_service.py`)
- Professional report generation with RingCentral branding and color-coding
- Multiple export formats (single lead, bulk analysis, Excel upload)
- Robust Lead ID matching with automatic format conversion
- Summary statistics and individual lead details with AI explanations

### Project Structure
```
ZI_Enrichment_Assessment/
├── app.py                    # Main Flask application (MVC pattern)
├── templates/ui.html         # Interactive web interface
├── static/                   # Frontend assets with RingCentral theming
├── config/                   # Configuration and environment management
├── services/                 # Core business logic services
├── routes/                   # RESTful API endpoints with export functionality
└── docs/                     # Technical documentation and samples
```

## API Reference

### Connection Testing
- `GET /test-salesforce-connection` - Test Salesforce connectivity
- `GET /test-openai-connection` - Test OpenAI API connectivity
- `GET /health` - Service health check

### Lead Analysis
- `GET /lead/<lead_id>` - Get basic lead data with quality flags
- `GET /lead/<lead_id>/confidence` - **AI-powered confidence assessment**

### Bulk Analysis
- `POST /leads/preview-query` - Preview SOQL query results
- `POST /leads/analyze-query` - **Bulk analysis with AI scoring**

### Excel Upload Workflow
- `POST /excel/parse` - Parse uploaded Excel file and extract headers
- `POST /excel/validate-lead-ids` - Validate Lead IDs with Salesforce
- `POST /excel/analyze` - **Analyze leads from Excel upload with AI assessment**

### Export Endpoints (Cached Results)
- `POST /leads/export-analysis-data` - Export bulk analysis results to Excel
- `POST /leads/export-single-lead-data` - Export single lead assessment to Excel
- `POST /excel/export-analysis-with-file` - **Export Excel analysis with original data**

### Web Interface
- `GET /ui` - **Interactive web interface with step-by-step workflows**

## Lead Data Fields

The system analyzes 11+ core fields for comprehensive cross-validation:

### Core Lead Data
- `Id` - Salesforce Lead ID (15 or 18 character format)
- `Email` - Lead email address with domain extraction
- `First_Channel__c` - Lead source channel
- `SegmentName` - Sales segment (SMB, Mid-Market, Enterprise)
- `LS_Company_Size_Range__c` - Internal company size estimate

### Cross-Validation Sources
- `Website` vs `ZI_Website__c` - Lead-provided vs ZoomInfo website
- `Company` vs `ZI_Company_Name__c` - Lead-provided vs ZoomInfo company name
- `ZI_Employees__c` - ZoomInfo employee count for segment validation

### Computed Analysis
- `email_domain` - Extracted email domain for validation
- `not_in_TAM` - Quality flag for missing enrichment on large companies
- `suspicious_enrichment` - Quality flag for potentially incorrect data

### AI Assessment Output
- `confidence_score` - Overall reliability rating (0-100)
- `explanation_bullets` - Clear explanations with emoji indicators
- `corrections` - High-confidence fixes (≥80% confidence) with website validation
- `inferences` - Lower-confidence suggestions (≥40% confidence) with accessibility checks

## Analysis Methods

### 1. Single Lead Assessment
Direct confidence scoring for individual leads with detailed AI explanations.

### 2. SOQL Query Analysis  
Bulk processing supporting complex queries:
- Simple filters: `WHERE Email LIKE '%@gmail.com'`
- JOINs: `SELECT Lead.Id FROM Lead JOIN Account ON...`
- UNIONs: `SELECT Id FROM Lead WHERE... UNION ALL...`
- Subqueries: `WHERE AccountId IN (SELECT...)`

### 3. Excel File Upload
Step-by-step workflow:
1. **Parse** - Extract sheet names and column headers
2. **Select** - Choose sheet and Lead ID column
3. **Validate** - Verify Lead IDs exist in Salesforce
4. **Analyze** - Run AI assessment on all valid leads
5. **Export** - Generate combined Excel report

## Excel Export Features

Professional reports with RingCentral branding include:
- **Color-coded confidence scores** (Red: 0-59, Orange: 60-79, Blue: 80-100)
- **Original data preservation** with AI analysis appended as new columns
- **Summary statistics** (total leads, issue percentages, average confidence)
- **Individual lead breakdowns** with detailed AI explanations
- **Consistent results** (cached analysis prevents AI response variability)

**Export Columns Added:**
- `AI_Confidence_Score` - Numerical confidence rating
- `AI_Explanation` - Bullet-point explanations with emoji indicators
- `AI_Corrections` - High-confidence data fixes (JSON format)
- `AI_Inferences` - Lower-confidence suggestions (JSON format)
- `AI_Not_in_TAM` - Quality flag for missing enrichment
- `AI_Suspicious_Enrichment` - Quality flag for suspicious data
- `AI_Status` - Analysis completion status

## Usage Examples

### Web Interface (Recommended)
The interactive interface at `/ui` provides:
- **Single Lead**: Enter Lead ID for instant confidence assessment
- **Bulk Analysis**: Write SOQL queries with preview before full analysis
- **Excel Upload**: Drag-and-drop workflow with validation at each step
- **Professional Export**: Download branded Excel reports with cached results

### API Examples

**Single Lead Assessment**
```bash
curl http://localhost:5000/lead/00Q5e00000ABC123/confidence
```

**Bulk Analysis with Export**
```bash
# 1. Run analysis
curl -X POST http://localhost:5000/leads/analyze-query \
  -H "Content-Type: application/json" \
  -d '{"soql_query": "WHERE Email LIKE '\''%@gmail.com'\''", "max_analyze": 10}'

# 2. Export results (using cached data)
curl -X POST http://localhost:5000/leads/export-analysis-data \
  -H "Content-Type: application/json" \
  -d '{"analysis_results": [...], "summary_data": {...}}'
```

## Response Format

All endpoints return standardized JSON:

**Success Response**
```json
{
  "status": "success", 
  "message": "Operation completed successfully",
  "data": { /* response data */ }
}
```

**Error Response**
```json
{
  "status": "error",
  "message": "Descriptive error message"
}
```

## Key Enhancements

### Advanced AI Assessment
- **Redundancy Validation**: Prevents duplicate corrections and inferences
- **Context-Aware Scoring**: Uses segment and channel data for accurate assessment
- **Smart Company Matching**: Detects when ZoomInfo and lead company names are equivalent
- **Data Quality Filtering**: Blocks free email domains and validates website accessibility
- **Enhanced Data Types**: Rejects vague employee counts and enforces proper formatting

### Robust Data Handling
- **Lead ID Conversion**: Automatic 15 ↔ 18 character Salesforce ID handling
- **Batch Optimization**: Efficient processing for large datasets
- **Error Recovery**: Graceful handling of missing or invalid data

### Professional Export
- **Cached Results**: Export endpoints use stored analysis data for consistency
- **Brand Compliance**: RingCentral colors and professional formatting
- **Data Integrity**: Original Excel data preserved with AI analysis appended

### Enhanced UX
- **Step-by-Step Workflows**: Clear validation at each stage
- **Real-Time Feedback**: Progress indicators and detailed error messages
- **Responsive Design**: Modern interface with intuitive navigation

---

**Additional Resources:**
- **[API Demo Video](https://drive.google.com/file/d/1G5kbyXztMqzkW44-von2Jbu0ZlHpYQ92/view?usp=sharing)** - Complete walkthrough and usage examples
- **[Project Overview](project_breakdown.md)** - Requirements and specifications
- **[AI Methodology](lead_data_interpretation.md)** - Scoring and assessment details 