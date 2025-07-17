import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
import tldextract
import re
from typing import Dict, Any, Optional

class AccountFeatureEngineer:
    """
    Create comparison features between customer accounts and their shell account.
    This generates dozens of comparison metrics that the decision tree can analyze.
    """
    
    def __init__(self):
        self.feature_names = []
        
    def create_all_features(self, customer_accounts: pd.DataFrame, shell_account: pd.Series) -> pd.DataFrame:
        """
        Create comprehensive comparison features for all customer accounts.
        
        Args:
            customer_accounts: DataFrame of customer accounts
            shell_account: Series containing shell account data
            
        Returns:
            DataFrame with comparison features for each customer account
        """
        print(f"Creating features for {len(customer_accounts)} customer accounts...")
        
        features_list = []
        feature_names = []
        
        for idx, customer in customer_accounts.iterrows():
            customer_features = self._create_customer_features(customer, shell_account)
            features_list.append(customer_features)
            
            # Store feature names from first iteration
            if not feature_names:
                feature_names = list(customer_features.keys())
                
        # Create DataFrame
        features_df = pd.DataFrame(features_list)
        
        # Add account ID and label for reference
        features_df['account_id'] = customer_accounts['Id'].values
        if 'Correctly Matched' in customer_accounts.columns:
            features_df['correctly_matched'] = customer_accounts['Correctly Matched'].values
        
        self.feature_names = feature_names
        print(f"Created {len(feature_names)} comparison features")
        
        return features_df
    
    def _create_customer_features(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create all comparison features for a single customer account."""
        features = {}
        
        # Name comparison features
        features.update(self._create_name_features(customer, shell))
        
        # Website comparison features  
        features.update(self._create_website_features(customer, shell))
        
        # Address comparison features
        features.update(self._create_address_features(customer, shell))
        
        # ZoomInfo field comparisons
        features.update(self._create_zi_features(customer, shell))
        
        # Company details comparisons
        features.update(self._create_company_features(customer, shell))
        
        # Exact field matches
        features.update(self._create_exact_matches(customer, shell))
        
        # Null/missing data patterns
        features.update(self._create_null_patterns(customer, shell))
        
        return features
    
    def _create_name_features(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create name-based comparison features."""
        features = {}
        
        # Get name fields
        customer_name = self._clean_text(customer.get('Name', ''))
        shell_name = self._clean_text(shell.get('Name', ''))
        shell_ultimate = self._clean_text(shell.get('Ultimate_Parent_Account_Name__c', ''))
        shell_zi_company = self._clean_text(shell.get('ZI_Company_Name__c', ''))
        customer_zi_company = self._clean_text(customer.get('ZI_Company_Name__c', ''))
        
        # Direct name comparisons
        features['name_vs_shell_name_ratio'] = fuzz.ratio(customer_name, shell_name) / 100.0
        features['name_vs_shell_name_partial'] = fuzz.partial_ratio(customer_name, shell_name) / 100.0
        features['name_vs_shell_ultimate_ratio'] = fuzz.ratio(customer_name, shell_ultimate) / 100.0
        features['name_vs_shell_zi_company_ratio'] = fuzz.ratio(customer_name, shell_zi_company) / 100.0
        
        # ZI Company name comparisons
        features['zi_company_vs_shell_name_ratio'] = fuzz.ratio(customer_zi_company, shell_name) / 100.0
        features['zi_company_vs_shell_zi_company_ratio'] = fuzz.ratio(customer_zi_company, shell_zi_company) / 100.0
        features['zi_company_vs_shell_ultimate_ratio'] = fuzz.ratio(customer_zi_company, shell_ultimate) / 100.0
        
        # Token-based comparisons (good for reordered words)
        features['name_vs_shell_name_token_ratio'] = fuzz.token_sort_ratio(customer_name, shell_name) / 100.0
        features['name_vs_shell_ultimate_token_ratio'] = fuzz.token_sort_ratio(customer_name, shell_ultimate) / 100.0
        
        # Best name match (maximum similarity across all name fields)
        name_similarities = [
            features['name_vs_shell_name_ratio'],
            features['name_vs_shell_ultimate_ratio'], 
            features['name_vs_shell_zi_company_ratio'],
            features['zi_company_vs_shell_name_ratio'],
            features['zi_company_vs_shell_zi_company_ratio']
        ]
        features['best_name_match'] = max(name_similarities)
        features['name_match_above_80'] = features['best_name_match'] > 0.8
        features['name_match_above_90'] = features['best_name_match'] > 0.9
        
        return features
    
    def _create_website_features(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create website-based comparison features."""
        features = {}
        
        # Get website fields
        customer_website = self._clean_text(customer.get('Website', ''))
        customer_zi_website = self._clean_text(customer.get('ZI_Website__c', ''))
        shell_website = self._clean_text(shell.get('Website', ''))
        shell_zi_website = self._clean_text(shell.get('ZI_Website__c', ''))
        
        # Domain extraction and comparison
        customer_domain = self._extract_domain(customer_website)
        customer_zi_domain = self._extract_domain(customer_zi_website)
        shell_domain = self._extract_domain(shell_website)
        shell_zi_domain = self._extract_domain(shell_zi_website)
        
        # Domain matches
        features['website_domain_exact_match'] = customer_domain == shell_domain if customer_domain and shell_domain else False
        features['zi_website_domain_exact_match'] = customer_zi_domain == shell_zi_domain if customer_zi_domain and shell_zi_domain else False
        features['customer_website_vs_shell_zi_domain'] = customer_domain == shell_zi_domain if customer_domain and shell_zi_domain else False
        features['customer_zi_website_vs_shell_domain'] = customer_zi_domain == shell_domain if customer_zi_domain and shell_domain else False
        
        # Any domain match
        domain_matches = [
            features['website_domain_exact_match'],
            features['zi_website_domain_exact_match'],
            features['customer_website_vs_shell_zi_domain'],
            features['customer_zi_website_vs_shell_domain']
        ]
        features['any_domain_match'] = any(domain_matches)
        
        # Website similarity (full URL)
        features['website_vs_shell_website_ratio'] = fuzz.ratio(customer_website, shell_website) / 100.0
        features['zi_website_vs_shell_zi_website_ratio'] = fuzz.ratio(customer_zi_website, shell_zi_website) / 100.0
        
        # Cross-website comparisons
        features['website_vs_shell_zi_website_ratio'] = fuzz.ratio(customer_website, shell_zi_website) / 100.0
        features['zi_website_vs_shell_website_ratio'] = fuzz.ratio(customer_zi_website, shell_website) / 100.0
        
        return features
    
    def _create_address_features(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create address-based comparison features."""
        features = {}
        
        # Billing address comparisons
        address_fields = ['BillingCity', 'BillingState', 'BillingCountry', 'BillingPostalCode']
        
        for field in address_fields:
            customer_val = self._clean_text(customer.get(field, ''))
            shell_val = self._clean_text(shell.get(field, ''))
            
            field_name = field.lower().replace('billing', '')
            features[f'{field_name}_exact_match'] = customer_val == shell_val if customer_val and shell_val else False
            features[f'{field_name}_similarity'] = fuzz.ratio(customer_val, shell_val) / 100.0
        
        # ZI location vs billing address
        zi_fields = ['ZI_Company_City__c', 'ZI_Company_State__c', 'ZI_Company_Country__c', 'ZI_Company_Postal_Code__c']
        billing_map = {
            'ZI_Company_City__c': 'BillingCity',
            'ZI_Company_State__c': 'BillingState', 
            'ZI_Company_Country__c': 'BillingCountry',
            'ZI_Company_Postal_Code__c': 'BillingPostalCode'
        }
        
        for zi_field, billing_field in billing_map.items():
            customer_zi = self._clean_text(customer.get(zi_field, ''))
            shell_billing = self._clean_text(shell.get(billing_field, ''))
            
            field_name = zi_field.lower().replace('zi_company_', '').replace('__c', '')
            features[f'customer_zi_{field_name}_vs_shell_billing'] = customer_zi == shell_billing if customer_zi and shell_billing else False
        
        # Count of exact address matches
        exact_matches = [features[f'{field.lower().replace("billing", "")}_exact_match'] for field in address_fields]
        features['address_exact_match_count'] = sum(exact_matches)
        features['address_full_match'] = features['address_exact_match_count'] >= 3
        
        return features
    
    def _create_zi_features(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create ZoomInfo-specific comparison features.""" 
        features = {}
        
        # ZI field comparisons
        zi_fields = [
            'ZI_Company_Name__c', 'ZI_Website__c', 'ZI_Company_Phone__c',
            'ZI_Employees__c', 'ZI_Company_Revenue__c', 'ZI_Company_City__c',
            'ZI_Company_State__c', 'ZI_Company_Country__c'
        ]
        
        for field in zi_fields:
            customer_val = customer.get(field, '')
            shell_val = shell.get(field, '')
            
            # Convert to string and clean
            customer_str = self._clean_text(str(customer_val) if customer_val is not None else '')
            shell_str = self._clean_text(str(shell_val) if shell_val is not None else '')
            
            field_name = field.lower().replace('zi_company_', '').replace('zi_', '').replace('__c', '')
            
            # Exact match
            features[f'zi_{field_name}_exact_match'] = customer_str == shell_str if customer_str and shell_str else False
            
            # Similarity for text fields
            if field in ['ZI_Company_Name__c', 'ZI_Website__c', 'ZI_Company_Phone__c']:
                features[f'zi_{field_name}_similarity'] = fuzz.ratio(customer_str, shell_str) / 100.0
        
        # Count ZI exact matches
        zi_exact_matches = [v for k, v in features.items() if 'zi_' in k and 'exact_match' in k]
        features['zi_exact_match_count'] = sum(zi_exact_matches)
        
        return features
    
    def _create_company_features(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create company-specific comparison features."""
        features = {}
        
        # Revenue comparison
        customer_revenue = self._safe_float(customer.get('AnnualRevenue', 0))
        shell_revenue = self._safe_float(shell.get('AnnualRevenue', 0))
        
        if customer_revenue and shell_revenue:
            features['revenue_ratio'] = min(customer_revenue, shell_revenue) / max(customer_revenue, shell_revenue)
            features['revenue_similar'] = features['revenue_ratio'] > 0.5
        else:
            features['revenue_ratio'] = 0.0
            features['revenue_similar'] = False
        
        # Employee count comparison
        customer_employees = self._safe_float(customer.get('NumberOfEmployees', 0))
        shell_employees = self._safe_float(shell.get('NumberOfEmployees', 0))
        
        if customer_employees and shell_employees:
            features['employees_ratio'] = min(customer_employees, shell_employees) / max(customer_employees, shell_employees)
            features['employees_similar'] = features['employees_ratio'] > 0.5
        else:
            features['employees_ratio'] = 0.0
            features['employees_similar'] = False
        
        # Industry comparison
        customer_industry = self._clean_text(customer.get('Industry', ''))
        shell_industry = self._clean_text(shell.get('Industry', ''))
        features['industry_exact_match'] = customer_industry == shell_industry if customer_industry and shell_industry else False
        features['industry_similarity'] = fuzz.ratio(customer_industry, shell_industry) / 100.0
        
        return features
    
    def _create_exact_matches(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create exact field match features."""
        features = {}
        
        # Key fields for exact comparison
        exact_fields = [
            'Website', 'Phone', 'Industry', 'AccountSource',
            'BillingPostalCode', 'BillingCountry'
        ]
        
        for field in exact_fields:
            customer_val = self._clean_text(customer.get(field, ''))
            shell_val = self._clean_text(shell.get(field, ''))
            
            field_name = field.lower().replace('billing', '')
            features[f'{field_name}_exact_match'] = customer_val == shell_val if customer_val and shell_val else False
        
        return features
    
    def _create_null_patterns(self, customer: pd.Series, shell: pd.Series) -> Dict[str, Any]:
        """Create features based on null/missing data patterns."""
        features = {}
        
        # Key fields to check for null patterns
        key_fields = [
            'Website', 'ZI_Company_Name__c', 'ZI_Website__c', 'BillingCity',
            'BillingState', 'Industry', 'Phone'
        ]
        
        for field in key_fields:
            customer_null = pd.isna(customer.get(field)) or customer.get(field) == '' or customer.get(field) is None
            shell_null = pd.isna(shell.get(field)) or shell.get(field) == '' or shell.get(field) is None
            
            field_name = field.lower().replace('zi_', '').replace('__c', '').replace('billing', '')
            features[f'{field_name}_both_null'] = customer_null and shell_null
            features[f'{field_name}_customer_null'] = customer_null
            features[f'{field_name}_shell_null'] = shell_null
        
        # Count nulls
        customer_nulls = sum(features[k] for k in features.keys() if 'customer_null' in k)
        shell_nulls = sum(features[k] for k in features.keys() if 'shell_null' in k)
        
        features['customer_null_count'] = customer_nulls
        features['shell_null_count'] = shell_nulls
        features['total_null_count'] = customer_nulls + shell_nulls
        
        return features
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for comparison."""
        if pd.isna(text) or text is None:
            return ''
        
        text = str(text).lower().strip()
        # Remove common business suffixes
        suffixes = [' inc', ' llc', ' corp', ' corporation', ' company', ' co', ' ltd']
        for suffix in suffixes:
            if text.endswith(suffix):
                text = text[:-len(suffix)].strip()
        
        return text
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if pd.isna(url) or not url:
            return ''
        
        try:
            extracted = tldextract.extract(str(url))
            return f"{extracted.domain}.{extracted.suffix}" if extracted.domain and extracted.suffix else ''
        except:
            return ''
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float."""
        if pd.isna(value) or value is None or value == '':
            return 0.0
        try:
            return float(value)
        except:
            return 0.0
    
    def get_feature_names(self) -> list:
        """Get list of all feature names."""
        return self.feature_names
    
    def print_feature_summary(self, features_df: pd.DataFrame):
        """Print summary of created features."""
        print("\n" + "="*60)
        print("FEATURE ENGINEERING SUMMARY")
        print("="*60)
        
        print(f"\nTotal features created: {len(self.feature_names)}")
        
        # Group features by type
        feature_groups = {
            'Name comparisons': [f for f in self.feature_names if 'name' in f.lower()],
            'Website comparisons': [f for f in self.feature_names if 'website' in f.lower() or 'domain' in f.lower()],
            'Address comparisons': [f for f in self.feature_names if any(addr in f.lower() for addr in ['city', 'state', 'country', 'postal', 'address'])],
            'ZoomInfo comparisons': [f for f in self.feature_names if 'zi_' in f.lower()],
            'Company comparisons': [f for f in self.feature_names if any(comp in f.lower() for comp in ['revenue', 'employee', 'industry'])],
            'Exact matches': [f for f in self.feature_names if 'exact_match' in f.lower() and 'zi_' not in f.lower() and 'address' not in f.lower()],
            'Null patterns': [f for f in self.feature_names if 'null' in f.lower()]
        }
        
        for group_name, feature_list in feature_groups.items():
            if feature_list:
                print(f"\n{group_name}: {len(feature_list)} features")
                for feature in feature_list[:5]:  # Show first 5
                    print(f"  • {feature}")
                if len(feature_list) > 5:
                    print(f"  ... and {len(feature_list) - 5} more")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    # Test feature engineering
    from data_processor import AccountDataProcessor
    
    processor = AccountDataProcessor('Sample_ RC Account Hierarchy.xlsx')
    processor.load_data()
    
    engineer = AccountFeatureEngineer()
    features_df = engineer.create_all_features(
        processor.get_labeled_customers(),
        processor.get_shell_account()
    )
    
    engineer.print_feature_summary(features_df)
    print(f"\nFeatures shape: {features_df.shape}")
    print(f"Sample features:\n{features_df.head()}") 