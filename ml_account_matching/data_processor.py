import pandas as pd
import numpy as np

class AccountDataProcessor:
    """
    Process account hierarchy data for machine learning analysis.
    Separates shell accounts from customer accounts and prepares data for feature engineering.
    """
    
    def __init__(self, excel_file_path):
        self.excel_file_path = excel_file_path
        self.raw_data = None
        self.shell_account = None
        self.customer_accounts = None
        self.labeled_customers = None
        
    def load_data(self):
        """Load data from Excel file and perform initial processing."""
        print("Loading data from Excel file...")
        self.raw_data = pd.read_excel(self.excel_file_path)
        print(f"Loaded {len(self.raw_data)} total accounts with {len(self.raw_data.columns)} fields")
        
        # Separate shell and customer accounts
        self.shell_account = self.raw_data[
            self.raw_data['RecordType.Name'] == 'ZI Customer Shell Account'
        ].iloc[0] if len(self.raw_data[self.raw_data['RecordType.Name'] == 'ZI Customer Shell Account']) > 0 else None
        
        self.customer_accounts = self.raw_data[
            self.raw_data['RecordType.Name'] == 'Customer Account'
        ].copy()
        
        # Filter to only labeled customer accounts (remove NaN labels)
        self.labeled_customers = self.customer_accounts[
            pd.notna(self.customer_accounts['Correctly Matched'])
        ].copy()
        
        print(f"Found 1 shell account")
        print(f"Found {len(self.customer_accounts)} customer accounts")
        print(f"Found {len(self.labeled_customers)} labeled customer accounts")
        
        # Print label distribution
        if len(self.labeled_customers) > 0:
            label_counts = self.labeled_customers['Correctly Matched'].value_counts()
            print(f"Label distribution:")
            print(f"  Correctly matched: {label_counts.get(1.0, 0)}")
            print(f"  Incorrectly matched: {label_counts.get(0.0, 0)}")
        else:
            print("No labeled customers found")
        
        return self
    
    def get_shell_account(self):
        """Get the shell account data."""
        if self.shell_account is None:
            raise ValueError("No shell account found. Call load_data() first.")
        return self.shell_account
    
    def get_customer_accounts(self):
        """Get all customer accounts."""
        if self.customer_accounts is None:
            raise ValueError("No customer accounts found. Call load_data() first.")
        return self.customer_accounts
    
    def get_labeled_customers(self):
        """Get only customer accounts with labels (for training)."""
        if self.labeled_customers is None:
            raise ValueError("No labeled customers found. Call load_data() first.")
        return self.labeled_customers
    
    def get_field_list(self):
        """Get list of all available fields."""
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        return list(self.raw_data.columns)
    
    def print_data_summary(self):
        """Print a comprehensive summary of the loaded data."""
        if self.raw_data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        print("\n" + "="*60)
        print("DATA SUMMARY")
        print("="*60)
        
        print(f"\nTotal accounts: {len(self.raw_data)}")
        print(f"Total fields: {len(self.raw_data.columns)}")
        
        print(f"\nRecord Type Distribution:")
        record_type_counts = self.raw_data['RecordType.Name'].value_counts()
        for record_type, count in record_type_counts.items():
            print(f"  {record_type}: {count}")
        
        print(f"\nLabel Distribution:")
        label_counts = self.raw_data['Correctly Matched'].value_counts(dropna=False)
        for label, count in label_counts.items():
            if pd.isna(label):
                print(f"  No label (shell account): {count}")
            else:
                label_text = "Correctly matched" if label == 1.0 else "Incorrectly matched"
                print(f"  {label_text}: {count}")
        
        print(f"\nKey Fields Available:")
        key_fields = [
            'Id', 'Name', 'Website', 'ZI_Company_Name__c', 'ZI_Website__c',
            'BillingCity', 'BillingState', 'BillingCountry', 'Parent_Account_ID__c',
            'Ultimate_Parent_Account_ID__c', 'RecordType.Name', 'Correctly Matched'
        ]
        
        for field in key_fields:
            if field in self.raw_data.columns:
                non_null_count = self.raw_data[field].notna().sum()
                print(f"  {field}: {non_null_count}/{len(self.raw_data)} non-null values")
        
        # Show sample shell account data
        if self.shell_account is not None:
            print(f"\nShell Account Info:")
            print(f"  ID: {self.shell_account['Id']}")
            print(f"  Name: {self.shell_account['Name']}")
            print(f"  Website: {self.shell_account.get('Website', 'N/A')}")
            print(f"  ZI Company: {self.shell_account.get('ZI_Company_Name__c', 'N/A')}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    # Test the data processor
    processor = AccountDataProcessor('Sample_ RC Account Hierarchy.xlsx')
    processor.load_data()
    processor.print_data_summary() 