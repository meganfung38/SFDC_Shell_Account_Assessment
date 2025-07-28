# Project Structure Guide

## 📁 **Overview**

This document provides a comprehensive guide to the SFDC Shell Account Assessment project structure. It's designed for developers who need to understand, maintain, or extend the codebase.

## 🏗️ **Root Directory Structure**

```
SFDC_Shell_Account_Assessment/
├── app.py                          # Main Flask application entry point
├── README.md                       # Project overview and setup guide
├── config/                         # Configuration and dependencies
├── docs/                          # Project documentation
├── ml_account_matching/           # Separate ML analysis system
├── routes/                        # API route definitions
├── services/                      # Core business logic services
├── static/                        # Frontend assets (CSS, JS)
├── templates/                     # HTML templates
└── venv/                         # Python virtual environment
```

---

## 📄 **Core Application Files**

### **`app.py`** - Main Application Entry Point
**Purpose**: Flask application initialization and configuration

**Key Responsibilities**:
- Initialize Flask app with configuration
- Register API blueprints
- Serve the main web interface
- Handle application startup

**Key Components**:
```python
# Main Flask app initialization
app = Flask(__name__)

# Blueprint registration
app.register_blueprint(api_bp, url_prefix='/api')

# Main route serving the web interface
@app.route('/')
def index():
    return render_template('ui.html')
```

**Dependencies**: `routes/api_routes`, `templates/ui.html`

---

## ⚙️ **Configuration (`config/`)**

### **`config/__init__.py`**
**Purpose**: Configuration module initialization

### **`config/config.py`**
**Purpose**: Centralized configuration management

**Key Features**:
- Environment variable loading via `python-dotenv`
- Salesforce API configuration
- OpenAI API configuration
- Application settings

**Configuration Variables**:
```python
# Salesforce Configuration
SF_USERNAME = os.getenv('SF_USERNAME')
SF_PASSWORD = os.getenv('SF_PASSWORD')
SF_SECURITY_TOKEN = os.getenv('SF_SECURITY_TOKEN')
SF_DOMAIN = os.getenv('SF_DOMAIN', 'login')

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', '1000'))
```

### **`config/env.example`**
**Purpose**: Template for environment variables

**Usage**: Copy to `.env` and fill in actual credentials

### **`config/requirements.txt`**
**Purpose**: Python package dependencies

**Key Dependencies**:
- `flask` - Web framework
- `simple-salesforce` - Salesforce API integration
- `openai` - OpenAI API integration
- `pandas` - Data processing
- `openpyxl` - Excel file handling
- `python-dotenv` - Environment management

---

## 🛣️ **API Routes (`routes/`)**

### **`routes/__init__.py`**
**Purpose**: Routes module initialization

### **`routes/api_routes.py`**
**Purpose**: All RESTful API endpoint definitions

**Key Endpoints**:

#### **Account Analysis Endpoints**
```python
@api_bp.route('/account/<account_id>', methods=['GET', 'POST'])
def get_account(account_id):
    """Single account analysis endpoint"""
```

```python
@api_bp.route('/accounts/analyze-query', methods=['POST'])
def analyze_soql_query():
    """SOQL query validation and account ID extraction"""
```

```python
@api_bp.route('/accounts/get-data', methods=['POST'])
def get_accounts_data():
    """Batch account data retrieval with full assessment"""
```

#### **Excel Processing Endpoints**
```python
@api_bp.route('/excel/parse', methods=['POST'])
def parse_excel_file():
    """Excel file parsing and structure extraction"""
```

```python
@api_bp.route('/excel/validate-account-ids', methods=['POST'])
def validate_excel_account_ids():
    """Validate Account IDs from Excel against Salesforce"""
```

#### **Connection Testing Endpoints**
```python
@api_bp.route('/test-salesforce-connection', methods=['GET'])
def test_salesforce_connection():
    """Test Salesforce API connectivity"""
```

```python
@api_bp.route('/test-openai-connection', methods=['GET'])
def test_openai_connection():
    """Test OpenAI API connectivity"""
```

**Dependencies**: All services in `services/` directory

---

## 🔧 **Core Services (`services/`)**

### **`services/__init__.py`**
**Purpose**: Services module initialization

### **`services/salesforce_service.py`** - Core Business Logic
**Purpose**: Salesforce API integration and relationship assessment

**Key Responsibilities**:
- Salesforce connection management
- Account data retrieval (12 fields)
- Flag computation (4 assessment flags)
- AI assessment integration
- SOQL query validation and execution

**Key Classes and Methods**:

#### **SalesforceService Class**
```python
class SalesforceService:
    def __init__(self):
        self.sf = None
        self.fuzzy_matcher = FuzzyMatchingService()
        self.connection_timeout = 3600  # 1 hour
```

#### **Connection Management**
```python
def ensure_connection(self):
    """Establish and maintain Salesforce connection with timeout"""
```

#### **Account Data Retrieval**
```python
def get_account_by_id(self, account_id):
    """Retrieve single account with full assessment"""
```

```python
def get_accounts_data_by_ids(self, account_ids):
    """Batch retrieve accounts with full assessment"""
```

#### **Flag Computation**
```python
def compute_has_shell_flag(self, account):
    """Compute Has_Shell flag (Boolean)"""
```

```python
def compute_customer_consistency_flag(self, account):
    """Compute Customer_Consistency flag (0-100 score)"""
```

```python
def compute_customer_shell_coherence_flag(self, account, shell_data):
    """Compute Customer_Shell_Coherence flag (0-100 score)"""
```

```python
def compute_address_consistency_flag(self, account, shell_data):
    """Compute Address_Consistency flag (Boolean)"""
```

#### **SOQL Query Processing**
```python
def get_account_ids_from_query(self, soql_query):
    """Execute SOQL query and extract Account IDs"""
```

```python
def _validate_account_soql_query(self, query, return_error=False):
    """Validate SOQL query syntax and security"""
```

**Dependencies**: `fuzzy_matching_service`, `openai_service`

### **`services/openai_service.py`** - AI Integration
**Purpose**: OpenAI API integration and prompt management

**Key Responsibilities**:
- OpenAI API communication
- System prompt management
- JSON response parsing and validation
- Error handling and fallback

**Key Functions**:
```python
def get_system_prompt():
    """Return the comprehensive system prompt for relationship assessment"""
```

```python
def ask_openai(data_for_openai):
    """Send data to OpenAI and parse response"""
```

**Features**:
- Robust JSON extraction from AI responses
- Comprehensive error handling
- Fallback when AI service unavailable
- GPT-4o model integration

### **`services/fuzzy_matching_service.py`** - String Analysis
**Purpose**: Fuzzy string matching and domain analysis

**Key Responsibilities**:
- String similarity computation
- Domain extraction from URLs
- Company name normalization
- Multi-dimensional comparison scoring

**Key Functions**:
```python
def extract_domain_from_url(url):
    """Extract domain from website URL"""
```

```python
def normalize_company_name(name):
    """Normalize company names for comparison"""
```

```python
def compute_fuzzy_similarity(str1, str2):
    """Compute similarity score between two strings"""
```

```python
def compute_customer_consistency_score(account):
    """Compute customer name/website consistency score"""
```

```python
def compute_customer_shell_coherence_score(customer_account, shell_account):
    """Compute customer-shell coherence score"""
```

```python
def compute_address_consistency(customer_account, shell_account):
    """Compute address consistency between accounts"""
```

### **`services/excel_service.py`** - File Processing
**Purpose**: Excel file parsing and data extraction

**Key Responsibilities**:
- Excel file validation and parsing
- Sheet and column detection
- Account ID extraction
- Data structure validation

**Key Functions**:
```python
def parse_excel_file(file_content):
    """Parse Excel file and return structure information"""
```

```python
def extract_account_ids_from_excel(file_content, sheet_name, column_name):
    """Extract Account IDs from specified Excel column"""
```

---

## 🎨 **Frontend (`static/` and `templates/`)**

### **`templates/ui.html`** - Main Web Interface
**Purpose**: Single-page web application interface

**Key Features**:
- Three input method sections (SOQL, Single Account, Excel)
- Real-time validation feedback
- Collapsible output sections
- Responsive design

**Structure**:
```html
<!-- SOQL Query Analysis Section -->
<div class="input-section">
    <h3>1. SOQL Query Analysis</h3>
    <!-- Query input and validation -->
</div>

<!-- Single Account Analysis Section -->
<div class="input-section">
    <h3>2. Single Account Analysis</h3>
    <!-- Account ID input -->
</div>

<!-- Excel Upload Analysis Section -->
<div class="input-section">
    <h3>3. Excel Upload Analysis</h3>
    <!-- File upload and processing -->
</div>
```

### **`static/css/ringcentral-theme.css`** - Styling
**Purpose**: Application styling and theme

**Key Features**:
- RingCentral brand colors and styling
- Collapsible section styling
- Responsive design
- Interactive elements

**Key CSS Classes**:
```css
/* Collapsible sections */
details {
    margin: 8px 0;
    padding: 2px;
    border-radius: 4px;
    background-color: transparent;
}

/* Account headers */
pre strong {
    font-weight: bold;
}

/* Color-coded section borders */
details[data-section="account-details"] {
    border-left: 3px solid #2c5aa0;
}
```

### **`static/js/ui-handlers.js`** - Frontend Logic
**Purpose**: Client-side JavaScript for user interaction

**Key Responsibilities**:
- Form submission handling
- API communication
- Dynamic UI updates
- Error handling and display

**Key Functions**:

#### **SOQL Query Workflow**
```javascript
async function handleQueryFormSubmit(e) {
    // Handle SOQL query submission
}

async function handleGetAccountData() {
    // Handle account analysis after query validation
}

function displayQueryResults(result) {
    // Display query validation results
}
```

#### **Single Account Workflow**
```javascript
async function handleAccountFormSubmit(e) {
    // Handle single account analysis
}
```

#### **Excel Workflow**
```javascript
async function handleExcelSubmit(e) {
    // Handle Excel file parsing
}

async function handleValidateAccountIds() {
    // Handle account ID validation
}

async function handleAnalyzeExcelAccounts() {
    // Handle account analysis after validation
}
```

#### **Output Formatting**
```javascript
function formatAccountOutput(account) {
    // Format account data for display
}

function formatBillingAddress(account) {
    // Format billing address for display
}
```

---

## 📚 **Documentation (`docs/`)**

### **`docs/project_breakdown.md`**
**Purpose**: Original project requirements and scope definition

**Contents**:
- Project background and problem statement
- Account hierarchy explanation
- Solution approach and steps
- Flag definitions and requirements

### **`docs/data_interpretation.md`**
**Purpose**: AI system prompt and assessment logic

**Contents**:
- Complete OpenAI system prompt
- Assessment criteria and scoring logic
- External knowledge application guidelines
- Output format specifications

### **`docs/project_structure.md`** (This File)
**Purpose**: Codebase organization and architecture guide

---

## 🤖 **ML System (`ml_account_matching/`)**

### **Overview**
A separate machine learning system for analyzing field comparison patterns.

**Status**: ✅ **Completed but Limited by Data**
- Successfully implemented 77 comparison features
- Trained decision tree model
- Found insufficient data variation for production use
- Ready for diverse datasets when available

**Key Files**:
- `requirements.txt` - ML dependencies
- `data_processor.py` - Data loading and preparation
- `feature_engineer.py` - 77 comparison feature creation
- `decision_tree_model.py` - ML training and analysis
- `README.md` - Complete ML documentation

---

## 🔄 **Data Flow Architecture**

### **1. Input Processing**
```
User Input → Frontend Validation → API Endpoint → Service Layer
```

### **2. Account Data Retrieval**
```
Service Layer → Salesforce API → Account Data (12 fields) → Flag Computation
```

### **3. Assessment Processing**
```
Account Data → Flag Computation → AI Assessment → Formatted Output
```

### **4. Response Generation**
```
Assessment Results → Frontend Formatting → Collapsible Display → User
```

---

## 🛠️ **Development Workflow**

### **Adding New Features**
1. **Service Layer**: Add business logic to appropriate service
2. **API Routes**: Add endpoint in `routes/api_routes.py`
3. **Frontend**: Update UI handlers and templates
4. **Documentation**: Update relevant docs

### **Testing Changes**
1. **Backend**: Test API endpoints with curl or Postman
2. **Frontend**: Test UI workflows in browser
3. **Integration**: Test end-to-end workflows

### **Configuration Management**
1. **Environment**: Update `.env` file with new variables
2. **Config**: Add to `config/config.py` if needed
3. **Documentation**: Update setup instructions

---

## 🔍 **Key Design Patterns**

### **Service Layer Pattern**
- Business logic separated from API routes
- Clear separation of concerns
- Easy testing and maintenance

### **Dependency Injection**
- Services initialized with dependencies
- Easy mocking for testing
- Flexible configuration

### **Error Handling**
- Comprehensive try-catch blocks
- User-friendly error messages
- Graceful degradation

### **Configuration Management**
- Environment-based configuration
- Centralized settings
- Secure credential management

---

## 🚀 **Deployment Considerations**

### **Environment Setup**
- Python 3.8+ required
- Virtual environment recommended
- Environment variables for credentials

### **Dependencies**
- All packages in `config/requirements.txt`
- Salesforce API access required
- OpenAI API key required

### **Security**
- Credentials in environment variables
- No hardcoded secrets
- API key rotation recommended

### **Performance**
- Connection reuse for Salesforce API
- Batch processing for multiple accounts
- Timeout handling for long operations

---

## 📞 **Support and Maintenance**

### **Common Issues**
1. **Salesforce Connection**: Check credentials and network
2. **OpenAI Errors**: Verify API key and quota
3. **Excel Processing**: Validate file format and structure
4. **Frontend Issues**: Check browser console for errors

### **Monitoring**
- API response times
- Error rates and types
- User workflow completion rates
- AI assessment quality

### **Updates**
- Regular dependency updates
- Salesforce API version compatibility
- OpenAI model updates
- Security patches

This structure guide provides a comprehensive overview for anyone taking over the project, with clear explanations of each component's purpose and how they work together. 