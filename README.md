# ZoomInfo Enrichment Quality Assessment API

A Flask API for assessing the quality and reliability of ZoomInfo-enriched lead data with AI-powered confidence scoring and professional Excel export capabilities.

## Quick Start

```bash
# Install dependencies
pip install -r config/requirements.txt

# Set up environment
cp config/env.example .env
# Edit .env with your Salesforce and OpenAI credentials

# Run the application
python app.py
```

Access the web interface at `http://localhost:5000/ui`

## Demo

📹 **[Watch the API Demo](https://drive.google.com/file/d/1G5kbyXztMqzkW44-von2Jbu0ZlHpYQ92/view?usp=sharing)** - Complete walkthrough of the tool's features and workflow

## Key Features

🧠 **AI-Powered Assessment**
- OpenAI-driven confidence scoring (0-100) for ZoomInfo enrichment quality
- Intelligent corrections and inferences with advanced redundancy validation
- Context-aware analysis using sales segment and channel data
- Smart duplicate detection to prevent redundant suggestions
- Free email domain validation (blocks gmail.com, yahoo.com, etc. as company websites)
- Website accessibility verification for corrected/inferred URLs

🔍 **Comprehensive Data Analysis**
- 11+ lead fields including dual website/company sources and employee counts
- Automated quality flags (`not_in_TAM`, `suspicious_enrichment`)
- Cross-validation between ZoomInfo data and internal estimates
- Robust Lead ID handling (15 ↔ 18 character conversion)
- Enhanced data type validation (rejects vague employee counts like "Small", "Large")

📊 **Three Analysis Methods**
- **Single Lead Assessment**: Individual confidence scoring with detailed explanations
- **SOQL Query Analysis**: Bulk processing with complex query support (JOINs, UNIONs)
- **Excel File Upload**: Batch analysis from uploaded Lead ID lists

📈 **Professional Excel Export**
- RingCentral-branded reports with color-coded confidence scores
- Summary statistics and individual lead breakdowns with AI explanations
- Consistent export data (cached analysis results prevent AI variability)
- Multiple export formats for different analysis types

⚡ **Enhanced User Experience**
- Step-by-step workflow with validation at each stage
- Real-time progress feedback and detailed error handling
- Responsive web interface with modern UI/UX design
- Comprehensive debug logging for troubleshooting

## Tech Stack

- **Backend**: Flask 3.1.1, Python 3.8+
- **Salesforce**: simple-salesforce 1.12.6 with optimized batch processing
- **AI**: OpenAI API 1.90.0+ with intelligent prompt engineering
- **Excel**: openpyxl 3.1.5 with advanced formatting and theming
- **Frontend**: Vanilla JavaScript, RingCentral-themed CSS

## Project Structure

```
ZI_Enrichment_Assessment/
├── app.py                           # Main Flask application (MVC pattern)
├── templates/ui.html                # Web interface template
├── static/                          # Frontend assets
│   ├── css/ringcentral-theme.css    # Professional brand styling
│   └── js/ui-handlers.js            # Interactive UI logic
├── config/                          # Configuration and dependencies
│   ├── config.py                    # Environment and settings
│   ├── requirements.txt             # Python dependencies
│   └── env.example                  # Configuration template
├── services/                        # Core business logic
│   ├── salesforce_service.py        # SF API with batch optimization
│   ├── openai_service.py           # AI assessment with validation
│   └── excel_service.py            # Professional report generation
├── routes/                          # API endpoint definitions
│   └── api_routes.py               # RESTful API with export endpoints
└── docs/                           # Documentation and samples
    ├── README.md                   # Detailed technical documentation
    ├── project_breakdown.md        # Requirements and specifications
    ├── lead_data_interpretation.md # AI methodology and scoring
    └── sample_result.xlsx          # Example bulk analysis report
```

## Core Services

### SalesforceService
- Lead data retrieval with 11+ enrichment fields
- Complex SOQL query support with security validation
- Quality flag computation and business logic
- Optimized batch processing for large datasets

### OpenAIService  
- AI-powered confidence scoring with detailed explanations
- Intelligent corrections and inferences based on context
- Advanced redundancy validation to prevent duplicate suggestions
- Contextual prompt engineering for accurate assessments

### ExcelService
- Professional report generation with RingCentral branding
- Color-coded confidence visualization and formatting
- Multiple export formats (single lead, bulk analysis, Excel upload)
- Robust Lead ID matching (15 ↔ 18 character handling)

## API Endpoints

### Analysis Endpoints
- `GET /lead/<id>/confidence` - Single lead AI assessment
- `POST /leads/analyze-query` - Bulk SOQL query analysis  
- `POST /excel/analyze` - Excel file upload analysis

### Export Endpoints (Cached Results)
- `POST /leads/export-analysis-data` - Export bulk analysis results
- `POST /leads/export-single-lead-data` - Export single lead assessment
- `POST /excel/export-analysis-with-file` - Export Excel analysis with original data

### Excel Workflow
- `POST /excel/parse` - Parse uploaded Excel file
- `POST /excel/validate-lead-ids` - Validate Lead IDs with Salesforce
- `POST /excel/export-analysis-with-file` - Export combined results

### Utilities
- `GET /test-salesforce-connection` - Test SF connectivity
- `GET /test-openai-connection` - Test OpenAI API connectivity  
- `GET /ui` - Interactive web interface

## Configuration

Required environment variables in `.env`:

```bash
# Salesforce
SF_USERNAME=your_username
SF_PASSWORD=your_password
SF_SECURITY_TOKEN=your_token
SF_DOMAIN=login  # or 'test' for sandbox

# OpenAI
OPENAI_API_KEY=sk-your-key-here
```

## Lead Data Fields

The system analyzes 11+ core fields with cross-validation:

**Lead Information**: ID, Email, Channel, Segment, Size Range  
**Website Sources**: Lead Website vs ZoomInfo Website  
**Company Sources**: Lead Company vs ZoomInfo Company Name  
**ZoomInfo Data**: Employee Count, Enrichment Quality  
**Computed Fields**: Email domain, Quality flags  
**AI Assessment**: Confidence score, Explanations, Corrections, Inferences

## Usage Examples

### Web Interface (Recommended)
Visit `http://localhost:5000/ui` for interactive analysis with:
- Single lead confidence assessment
- Bulk SOQL query analysis with preview
- Excel file upload with step-by-step workflow
- Professional export with cached results

### API Usage
```bash
# Single lead assessment
curl http://localhost:5000/lead/00Q5e00000ABC123/confidence

# Bulk analysis  
curl -X POST http://localhost:5000/leads/analyze-query \
  -H "Content-Type: application/json" \
  -d '{"soql_query": "WHERE Email LIKE '\''%@gmail.com'\''", "max_analyze": 10}'
```

## Documentation

- **[API Demo Video](https://drive.google.com/file/d/1G5kbyXztMqzkW44-von2Jbu0ZlHpYQ92/view?usp=sharing)** - Complete walkthrough and usage examples
- **[Technical Documentation](docs/README.md)** - Complete API reference and setup
- **[Project Specifications](docs/project_breakdown.md)** - Requirements and architecture
- **[AI Methodology](docs/lead_data_interpretation.md)** - Scoring and assessment details  
- **[Sample Exports](docs/sample_result.xlsx)** - Example Excel reports

---

For detailed API documentation and advanced usage, see [docs/README.md](docs/README.md) 