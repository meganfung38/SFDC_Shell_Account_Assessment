# ML Account Matching Analysis

This system uses machine learning (scikit-learn decision trees) to analyze which field comparisons are most predictive of correct vs incorrect customer-to-shell account matches in Salesforce.

## 🎯 **What This System Does**

1. **Loads your account data** from Excel file
2. **Creates dozens of comparison features** between customer and shell accounts (name similarity, domain matching, address comparisons, etc.)
3. **Trains a decision tree** to identify which comparisons matter most
4. **Provides insights** on which field patterns predict correct matches
5. **Generates actionable recommendations** for improving your matching logic

## 📁 **File Structure**

```
ml_account_matching/
├── requirements.txt         # Python dependencies
├── data_processor.py       # Load and prepare account data
├── feature_engineer.py     # Create comparison features
├── decision_tree_model.py  # Train model and analyze results
├── README.md              # This file
└── Sample_ RC Account Hierarchy.xlsx  # Your data file
```

## 🚀 **Quick Start**

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Complete Analysis
```bash
python decision_tree_model.py
```

This will:
- Load your Excel data
- Create ~100+ comparison features
- Train the decision tree
- Show you which field comparisons are most important
- Generate feature importance plot

## 📊 **Expected Output**

### Feature Importance Analysis
```
MOST IMPORTANT FEATURES:
1. name_vs_shell_zi_company_ratio       0.245
2. zi_company_vs_shell_name_ratio       0.183  
3. website_domain_exact_match           0.156
4. best_name_match                      0.142
...
```

### Key Insights
- **Most predictive feature**: Which single comparison is most important
- **Feature categories**: Name vs Website vs Address importance
- **Decision rules**: "If name_similarity > 0.8 AND domain_match = True, then CORRECT"
- **Recommendations**: Focus areas for improving matching logic

## 🔧 **How It Works**

### 1. Data Processing (`data_processor.py`)
- Loads Excel file with account hierarchy data
- Separates shell account (RecordType = "ZI Customer Shell Account") 
- Identifies customer accounts with labels (RecordType = "Customer Account")
- Prepares data for feature engineering

### 2. Feature Engineering (`feature_engineer.py`)
Creates **comparison features** between each customer account and the shell account:

#### Name Comparisons (15+ features)
- `name_vs_shell_name_ratio`: Fuzzy similarity between customer name and shell name
- `zi_company_vs_shell_ultimate_ratio`: ZI company name vs shell ultimate parent
- `best_name_match`: Maximum similarity across all name fields
- etc.

#### Website Comparisons (10+ features)  
- `website_domain_exact_match`: Do domains match exactly?
- `zi_website_vs_shell_website_ratio`: ZI website similarity
- `any_domain_match`: Any domain match across all website fields
- etc.

#### Address Comparisons (15+ features)
- `city_exact_match`: Billing cities match exactly?
- `address_exact_match_count`: How many address fields match?
- `customer_zi_city_vs_shell_billing`: ZI city vs shell billing city
- etc.

#### ZoomInfo Comparisons (10+ features)
- `zi_name_exact_match`: ZI company names match?
- `zi_exact_match_count`: Count of exact ZI field matches
- etc.

#### Other Features (20+ features)
- Company size, revenue, industry comparisons
- Null data patterns
- Exact field matches

### 3. Machine Learning (`decision_tree_model.py`)
- Trains scikit-learn DecisionTreeClassifier
- Uses all comparison features to predict correct/incorrect labels
- Analyzes feature importance to show which comparisons matter most
- Generates human-readable decision rules

## 📈 **Sample Results**

With your data (9 correct + 3 incorrect matches), you might see results like:

```
KEY INSIGHTS:
• Most predictive feature: zi_company_vs_shell_name_ratio
• Name similarity features are 60% of importance  
• Website domain matching is 25% of importance
• Address matching is only 15% of importance

RECOMMENDATIONS:
• Focus on ZI company name vs shell name comparison
• Implement fuzzy string matching with >85% threshold
• Domain matching is secondary but still valuable
• Address matching is less reliable for your data
```

## 🎛️ **Customization Options**

### Adjust Decision Tree Parameters
```python
# In decision_tree_model.py
model = AccountMatchingModel(
    max_depth=5,           # Tree depth (3-10 recommended)
    min_samples_split=2,   # Min samples to split (2-5 recommended)
    random_state=42        # For reproducible results
)
```

### Focus on Specific Feature Types
```python
# In feature_engineer.py - comment out feature groups you don't want
features.update(self._create_name_features(customer, shell))        # Keep
features.update(self._create_website_features(customer, shell))     # Keep  
# features.update(self._create_address_features(customer, shell))   # Skip
```

### Add Custom Features
```python
# In feature_engineer.py - add your own comparison logic
def _create_custom_features(self, customer, shell):
    features = {}
    # Your custom comparison logic here
    features['my_custom_metric'] = your_calculation()
    return features
```

## 🔍 **Understanding Your Results**

### Feature Importance Scores
- **0.0 - 0.1**: Low importance, might not be useful
- **0.1 - 0.3**: Moderate importance, worth considering  
- **0.3+**: High importance, critical for matching decisions

### Decision Tree Rules
The system generates rules like:
```
|--- zi_company_vs_shell_name_ratio <= 0.85
|   |--- website_domain_exact_match <= 0.5  
|   |   |--- class: Incorrect (confidence: 0.75)
|   |--- website_domain_exact_match >  0.5
|   |   |--- class: Correct (confidence: 0.67)
|--- zi_company_vs_shell_name_ratio >  0.85
|   |--- class: Correct (confidence: 0.90)
```

Translation: "If ZI company name similarity is >85%, it's probably correct. If <85%, check domain matching."

## 📝 **Data Requirements**

### Excel File Format
Your Excel file should have:
- **One row per account** (shell + all customers)
- **RecordType.Name column**: "ZI Customer Shell Account" or "Customer Account"  
- **Correctly Matched column**: Boolean (1.0/0.0) for customer accounts, NaN for shell
- **All Salesforce fields**: Name, Website, ZI fields, billing address, etc.

### Minimum Data Size
- **At least 5 labeled accounts** for meaningful analysis
- **Mix of correct/incorrect** examples (ideally 70/30 or 60/40 split)
- **Rich field data** - more populated fields = better feature engineering

## 🚨 **Troubleshooting**

### "No labeled customers found"
- Check that 'Correctly Matched' column has 1.0 and 0.0 values
- Ensure customer accounts have RecordType.Name = "Customer Account"

### "Feature importance all zeros"  
- Check that you have variation in your labels (not all correct or all incorrect)
- Ensure field data has meaningful differences between correct/incorrect cases

### Low accuracy scores
- Normal with small datasets (12 accounts)
- Focus on feature importance rankings rather than accuracy
- Add more labeled examples if possible

## 🎯 **Next Steps**

1. **Run the analysis** on your current data
2. **Review feature importance** to understand what matters most
3. **Implement insights** in your production matching logic  
4. **Collect more labeled data** to improve model reliability
5. **Re-run analysis** with larger datasets for production use

## 💡 **Tips for Success**

- **Start with obvious patterns**: The model will confirm/refute your intuitions
- **Focus on top 5-10 features**: Don't get overwhelmed by all features
- **Use insights for business rules**: "If name_similarity > 0.8, auto-approve"
- **Combine with human review**: Use model to flag uncertain cases
- **Iterate and improve**: Re-run as you get more labeled data 