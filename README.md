# SFDC Account to Shell Account Relationship Assessment

## 🎯 **Project Overview**

This project builds an automated system to evaluate the validity of Salesforce account-to-shell-account relationships using field comparison, pattern analysis, and AI-powered confidence scoring. The goal is to identify misaligned parent-child relationships that cause poor data hygiene, misleading sales attribution, and operational inefficiencies.

### **Account Hierarchy Background**
RingCentral's Salesforce system uses a structured hierarchy:
- **Shell Accounts** (RecordType: "ZI Customer Shell Account"): ZoomInfo-enriched master entities representing business identities
- **Customer Accounts** (RecordType: "Customer Account"): Individual or departmental accounts that should roll up to appropriate shell accounts

### **Problem Statement**
Inconsistencies in data and incorrect associations have led to misaligned parent-child relationships, introducing:
- Poor data hygiene
- Misleading sales attribution  
- Fragmented customer insights
- Operational inefficiencies

---

## 🚀 **Current Implementation Status**

### ✅ **Completed: Core API Infrastructure**

#### **Web Interface & API Endpoints**
- **Full-featured web UI** at `/` for account analysis
- **RESTful API** with comprehensive account data retrieval
- **Excel upload processing** with validation and analysis
- **Salesforce & OpenAI integration** with connection testing

#### **Account Data Retrieval (12 Fields)**
The system currently queries these fields for comprehensive account analysis:

**Standard Fields:**
- `Id` - Account's unique Salesforce ID
- `Name` - Account name
- `Website` - Account's website URL
- `RecordType.Name` - Account type (Shell vs Customer)
- `BillingStreet`, `BillingCity`, `BillingState`, `BillingCountry` - Billing address

**Custom ZoomInfo Fields:**
- `Ultimate_Parent_Account_Name__c` - Ultimate parent account name
- `ZI_Company_Name__c` - ZoomInfo company name
- `ZI_Website__c` - ZoomInfo website
- `Parent_Account_ID__c` - Parent account ID reference

#### **Current API Endpoints**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/account/{id}` | GET | Single account analysis |
| `/accounts/analyze-query` | POST | Validate SOQL queries, return Account IDs |
| `/accounts/get-data` | POST | Batch account data retrieval |
| `/excel/parse` | POST | Parse Excel files, return structure |
| `/excel/validate-account-ids` | POST | Validate Account IDs from Excel |
| `/test-salesforce-connection` | GET | Test Salesforce connectivity |
| `/test-openai-connection` | GET | Test OpenAI API connectivity |

#### **Supported Input Methods**
1. **SOQL Queries**: Complete SELECT statements returning Account IDs
2. **Single Account ID**: Direct 15/18-character Salesforce ID lookup
3. **Excel Upload**: Batch processing with column selection and validation

---

### ✅ **Completed: ML Account Matching System**

#### **Purpose**
A separate machine learning system (`ml_account_matching/`) that analyzes field comparison patterns to identify which factors are most predictive of correct vs incorrect account relationships.

#### **System Components**
```
ml_account_matching/
├── requirements.txt         # ML dependencies (scikit-learn, pandas, etc.)
├── data_processor.py       # Excel data loading and preparation
├── feature_engineer.py     # 77 comparison feature creation
├── decision_tree_model.py  # ML training and analysis
├── README.md              # Complete ML system documentation
└── Sample_*.xlsx          # Training data (13 accounts: 1 shell + 12 customers)
```

#### **Technical Implementation Success**
- **✅ Data Processing**: Successfully loaded Excel data with 53 Salesforce fields including RecordType.Name
- **✅ Feature Engineering**: Created 77 comparison features across all field types:
  - Name similarity (15+ features): fuzzy matching between customer and shell names
  - Website comparisons (10+ features): domain matching and URL analysis  
  - Address comparisons (15+ features): billing address field matching
  - ZoomInfo fields (10+ features): ZI company name and website analysis
  - Other patterns (20+ features): exact matches, null patterns, ratios
- **✅ Model Training**: Decision tree achieved 100% training accuracy, 67% cross-validation
- **✅ Feature Ranking**: Generated importance scores for all comparison features

#### **Critical Analysis Results**

**Top "Important" Features Identified:**
1. `website_vs_shell_website_ratio` (53% importance)
2. `name_vs_shell_zi_company_ratio` (27% importance) 
3. `postalcode_similarity` (19% importance)

**⚠️ Data Limitations Discovered:**

The ML analysis revealed a fundamental issue with the current dataset that prevents meaningful pattern discovery:

**Insufficient Data Variation:**
- **Sample size**: Only 12 customer accounts (9 correct, 3 incorrect matches)
- **Nearly identical data**: All customer accounts have essentially the same values:
  - **Websites**: All `ringcentral.com` or `test.ringcentral.com`
  - **ZI Company Names**: All `RingCentral Inc`
  - **Most other fields**: Virtually identical across all accounts
- **Noise vs Signal**: Decision tree found patterns in tiny differences (0.86 vs 1.0 similarity ratios) which represent statistical noise, not meaningful business patterns

**Key Finding**: Traditional field comparison approaches are **insufficient** for distinguishing correct vs incorrect account relationships in the current data environment.

#### **Business Implications**

1. **Standard ML Ineffective**: Current account relationships cannot be reliably distinguished using conventional field similarity metrics
2. **Data Homogeneity**: RingCentral customer accounts are too similar to each other to reveal differentiating patterns
3. **Need Alternative Approaches**: Success requires:
   - Access to more diverse account relationship examples
   - Business-specific domain knowledge beyond standard Salesforce fields
   - Alternative data sources or relationship indicators
   - Expert consultation on what actually distinguishes correct vs incorrect relationships

#### **Usage & Results**
```bash
cd ml_account_matching/
pip install -r requirements.txt
python decision_tree_model.py
```

**Current Output**: Demonstrates technically successful ML methodology but reveals that current account data lacks the variation necessary for reliable pattern discovery. The system is proven and ready for diverse datasets when available.

#### **Methodology Validation**
✅ **ML Infrastructure**: Proven system ready for larger, more diverse datasets  
✅ **Feature Engineering**: Comprehensive comparison framework established  
✅ **Analysis Pipeline**: End-to-end workflow validated and documented  
⚠️ **Training Data**: Current dataset insufficient for production ML model

---

## 🔄 **Next Steps: Remaining Implementation**

### **Phase 1: Field Comparison Logic**
**Status**: ⏸️ **Pending Consultation**
- **ML Analysis Complete**: 77 comparison features tested, but current data lacks meaningful patterns
- **Key Finding**: Traditional field matching insufficient for current account relationships
- **Next Step**: Consult with Laurice's team for guidance on:
  - Alternative field comparison approaches beyond traditional fuzzy matching
  - Access to more diverse account relationship examples for training
  - Business-specific patterns not captured in standard Salesforce fields
  - Domain expertise on what distinguishes correct vs incorrect relationships
  - Potential integration with other RingCentral data sources

**Reference**: See `Name_Mismatch` and `MetaData_Mismatch` flags in [project_breakdown.md](docs/project_breakdown.md)

### **Phase 2: AI-Powered Confidence Scoring**
**Status**: 📋 **Planned**

#### **Hybrid Scoring Model**
Combine multiple analysis methods:
1. **Flag Verification**: Leverage Name_Mismatch and MetaData_Mismatch similarity scores
2. **Outlier Detection**: Compare customer account attributes to sibling accounts under same shell
3. **Address Relevance**: Semantic address comparison for geographic plausibility
4. **Weighted Factors**:
   - Company name match = High priority
   - Website match = Medium priority  
   - Address match = Low priority

#### **OpenAI Integration**
- **Edge Case Handling**: Use AI to normalize noisy names and determine domain affiliation
- **Contextual Analysis**: Evaluate overall relationship coherence across fields
- **System Prompt Development**: Create prompts for consistent confidence scoring

**Expected Output**: Confidence score (0-100%) for each customer account relationship

### **Phase 3: Explainability & Reporting**
**Status**: 📋 **Planned**

#### **Explanation Generation**
For each confidence score, provide:
- **Fields matched/mismatched** with specific similarity scores
- **Reasoning logic** behind score assignment
- **Contributing signals** that influenced the assessment
- **Recommended actions** for sales/operations teams

#### **Advanced Features**
- **Sibling account comparison** for outlier detection
- **Batch shell account analysis** (process all customers under a shell)
- **Historical trend analysis** and pattern recognition
- **Export capabilities** for action planning

---

## 🏗️ **Technical Architecture**

### **Core Technologies**
- **Backend**: Python Flask API
- **Data Layer**: Salesforce API integration via simple-salesforce
- **AI/ML**: OpenAI GPT integration + scikit-learn decision trees
- **Frontend**: Responsive web interface with JavaScript
- **Data Processing**: pandas, openpyxl for Excel handling

### **Service Layer**
```
services/
├── salesforce_service.py   # SOQL queries, account data retrieval
├── openai_service.py       # AI prompt management and completion
├── excel_service.py        # File processing and validation
```

### **Configuration**
Environment-based configuration supporting:
- Salesforce credentials (username, password, security token, domain)
- OpenAI API key and model settings
- Configurable query limits and batch sizes

---

## 🚀 **Getting Started**

### **Prerequisites**
- Python 3.8+
- Salesforce org access with API enabled
- OpenAI API key
- Required Python packages (see `config/requirements.txt`)

### **Setup**
1. **Clone repository and install dependencies**:
   ```bash
   pip install -r config/requirements.txt
   ```

2. **Configure environment variables**:
   ```bash
   cp config/env.example .env
   # Edit .env with your Salesforce and OpenAI credentials
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access web interface**: http://localhost:5000

### **API Testing**
```bash
# Test Salesforce connection
curl http://localhost:5000/test-salesforce-connection

# Test OpenAI connection  
curl http://localhost:5000/test-openai-connection

# Get single account
curl http://localhost:5000/account/0012H00001cH3WB
```

---

## 📊 **Current Capabilities**

### **Account Analysis**
- ✅ **Field Extraction**: 12 comprehensive account fields
- ✅ **Data Validation**: Account ID format checking and existence verification
- ✅ **Batch Processing**: Handle up to 500 accounts simultaneously
- ✅ **Excel Integration**: Upload, parse, and validate account lists
- ✅ **SOQL Support**: Custom query validation and execution

### **Web Interface**
- ✅ **Multi-input Support**: SOQL queries, single IDs, Excel uploads
- ✅ **Real-time Validation**: Immediate feedback on query syntax and account validity
- ✅ **Comprehensive Display**: Formatted account details with all retrieved fields
- ✅ **Export Ready**: Buttons prepared for future Excel export functionality

### **ML Analysis**
- ✅ **Comprehensive Feature Engineering**: 77 comparison features across all field types
- ✅ **Decision Tree Training**: Successfully trained model and generated feature rankings
- ✅ **Data Analysis**: Identified limitations in current account data for pattern recognition
- ✅ **Methodology Validation**: Proven approach ready for diverse training datasets

---

## 🎯 **Project Goals Alignment**

This implementation directly addresses the project requirements outlined in [project_breakdown.md](docs/project_breakdown.md):

| Requirement | Status | Implementation |
|-------------|--------|---------------|
| **Data Extraction** | ✅ Complete | 12-field comprehensive account retrieval |
| **Input Flexibility** | ✅ Complete | SOQL queries, single IDs, Excel uploads |
| **Field Comparison** | ⏸️ Pending Consultation | ML analysis complete - requires alternative approach |
| **Confidence Scoring** | 📋 Planned | OpenAI integration for hybrid scoring |
| **Explainability** | 📋 Planned | Detailed reasoning and recommendations |
| **Web Interface** | ✅ Complete | Full-featured UI with all input methods |

---

## 📝 **Documentation**

- **[Project Breakdown](docs/project_breakdown.md)**: Complete project scope and requirements
- **[ML System README](ml_account_matching/README.md)**: Detailed ML analysis documentation
- **API Documentation**: Available at `/api` endpoint when running
- **Configuration Guide**: See `config/env.example` for setup details

---

## 🤝 **Contributing**

This project is designed for iterative development with clear separation of concerns:
- **Core API**: Handle data retrieval and basic validation
- **ML Analysis**: Pattern discovery and feature importance
- **AI Integration**: Advanced scoring and explanation generation
- **Web Interface**: User-friendly access to all functionality

Each component can be developed and tested independently while contributing to the overall solution.