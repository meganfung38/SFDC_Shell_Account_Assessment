from simple_salesforce.api import Salesforce
from config.config import Config
from typing import Optional


class SalesforceService:
    """Service class for handling Salesforce operations"""
    
    def __init__(self):
        self.sf: Optional[Salesforce] = None
        self._is_connected = False
    
    def _convert_15_to_18_char_id(self, id_15):
        """Convert 15-character Salesforce ID to 18-character format"""
        if len(id_15) != 15:
            return id_15
        
        # Salesforce ID conversion algorithm
        suffix = ""
        for i in range(3):
            chunk = id_15[i*5:(i+1)*5]
            chunk_value = 0
            for j, char in enumerate(chunk):
                if char.isupper():
                    chunk_value += 2 ** j
            
            # Convert to base-32 character
            if chunk_value < 26:
                suffix += chr(ord('A') + chunk_value)
            else:
                suffix += str(chunk_value - 26)
        
        return id_15 + suffix
    
    def connect(self):
        """Establish connection to Salesforce"""
        try:
            # Validate configuration first
            Config.validate_salesforce_config()
            
            # Create Salesforce connection
            self.sf = Salesforce(
                username=Config.SF_USERNAME,
                password=Config.SF_PASSWORD,
                security_token=Config.SF_SECURITY_TOKEN,
                domain=Config.SF_DOMAIN
            )
            
            self._is_connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to Salesforce: {str(e)}")
            self._is_connected = False
            return False
    
    def ensure_connection(self):
        """Ensure we have an active Salesforce connection"""
        if not self._is_connected or not self.sf:
            return self.connect()
        return True
    
    def test_connection(self):
        """Test if connection is working by running a simple query"""
        try:
            if not self.ensure_connection():
                return False, "Failed to establish connection"
            
            # Simple test - query 5 Account IDs
            assert self.sf is not None  # Type hint for linter
            query_result = self.sf.query("SELECT Id FROM Account LIMIT 5")
            
            # If we get here, connection is working and we can query data
            record_count = len(query_result['records'])
            return True, f"Connection successful - Retrieved {record_count} Account records"
            
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
    
    def get_connection_info(self):
        """Get basic connection information"""
        if not self._is_connected or not self.sf:
            return None
        
        return {
            "instance_url": self.sf.sf_instance,
            "session_id": "Connected" if self.sf.session_id else "Not Connected",
            "api_version": self.sf.sf_version
        }

    def get_account_by_id(self, account_id):
        """Get specific Account data by Account ID"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Validate Account ID format
            account_id = str(account_id).strip()
            if not account_id:
                return None, "Account ID cannot be empty"
            
            # Basic Account ID format validation
            if len(account_id) not in [15, 18]:
                return None, f"Invalid Account ID format. Account IDs must be 15 or 18 characters long. Provided: '{account_id}' ({len(account_id)} characters)"
            
            if not account_id.startswith('001'):
                return None, f"Invalid Account ID format. Account IDs must start with '001'. Provided: '{account_id}'"
            
            # Query for Account fields including custom fields and RecordType
            query = """
            SELECT Id, Name, Ultimate_Parent_Account_Name__c, Website, 
                   BillingStreet, BillingCity, BillingState, BillingCountry,
                   ZI_Company_Name__c, ZI_Website__c, Parent_Account_ID__c, RecordType.Name
            FROM Account 
            WHERE Id = '{}'
            """.format(account_id)
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(query)
            
            if result['totalSize'] == 0:
                return None, f"No Account found with ID: {account_id}. Please verify the Account ID exists in your Salesforce org."
            
            # Get the account record
            account_record = result['records'][0]
            
            # Remove Salesforce metadata if present
            if 'attributes' in account_record:
                del account_record['attributes']
                
            return account_record, "Account retrieved successfully"
            
        except Exception as e:
            error_msg = str(e)
            # Provide cleaner error messages for common issues
            if "invalid ID field" in error_msg.lower():
                return None, f"Invalid Account ID: '{account_id}'. Please check the Account ID format and try again."
            elif "malformed request" in error_msg.lower():
                return None, f"Account ID '{account_id}' is not valid. Please provide a valid 15 or 18-character Salesforce Account ID."
            else:
                return None, f"Error retrieving Account: {error_msg}"

    def query_accounts(self, query_conditions=None, limit=100):
        """Query accounts with optional conditions"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Base query with Account fields including custom fields and RecordType
            base_query = """
            SELECT Id, Name, Ultimate_Parent_Account_Name__c, Website, 
                   BillingStreet, BillingCity, BillingState, BillingCountry,
                   ZI_Company_Name__c, ZI_Website__c, Parent_Account_ID__c, RecordType.Name
            FROM Account
            """
            
            # Add conditions if provided
            if query_conditions:
                base_query += f" WHERE {query_conditions}"
            
            # Add limit
            base_query += f" LIMIT {limit}"
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(base_query)
            
            # Clean up records by removing metadata
            clean_records = []
            for record in result['records']:
                if 'attributes' in record:
                    del record['attributes']
                clean_records.append(record)
            
            return {
                'records': clean_records,
                'totalSize': result['totalSize'],
                'done': result['done']
            }, "Query executed successfully"
            
        except Exception as e:
            return None, f"Error executing query: {str(e)}"

    def validate_account_ids(self, account_ids):
        """Validate that all provided Account IDs exist in Salesforce"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            if not account_ids:
                return {'valid_account_ids': [], 'invalid_account_ids': []}, "No Account IDs provided"
            
            # Clean and validate Account ID format first
            cleaned_account_ids = []
            format_invalid_ids = []
            id_mapping = {}  # Maps original ID to cleaned ID for response
            
            for aid in account_ids:
                aid_str = str(aid).strip()
                # Basic Account ID format validation (15 or 18 characters, starts with 001)
                if len(aid_str) in [15, 18] and aid_str.startswith('001'):
                    # Convert 15-char IDs to 18-char for consistent querying
                    if len(aid_str) == 15:
                        converted_id = self._convert_15_to_18_char_id(aid_str)
                        cleaned_account_ids.append(converted_id)
                        id_mapping[converted_id] = aid_str  # Remember original format
                    else:
                        cleaned_account_ids.append(aid_str)
                        id_mapping[aid_str] = aid_str
                else:
                    format_invalid_ids.append(aid_str)
            
            # Query Salesforce to check which Account IDs exist (only for format-valid IDs)
            valid_account_ids = []
            sf_invalid_ids = []
            
            if cleaned_account_ids:
                # Process in batches to avoid SOQL query limits
                batch_size = 200  # Salesforce IN clause limit
                for i in range(0, len(cleaned_account_ids), batch_size):
                    batch = cleaned_account_ids[i:i + batch_size]
                    ids_string = "', '".join(batch)
                    validation_query = f"SELECT Id FROM Account WHERE Id IN ('{ids_string}')"
                    
                    assert self.sf is not None  # Type hint for linter
                    result = self.sf.query(validation_query)
                    
                    # Extract valid Account IDs from this batch (in 18-char format from Salesforce)
                    batch_valid_18char = [record['Id'] for record in result['records']]
                    
                    # Convert back to original format for response
                    for valid_18char in batch_valid_18char:
                        original_format = id_mapping.get(valid_18char, valid_18char)
                        valid_account_ids.append(original_format)
                    
                    # Find invalid Account IDs in this batch (return in original format)
                    for clean_id in batch:
                        if clean_id not in batch_valid_18char:
                            original_format = id_mapping.get(clean_id, clean_id)
                            sf_invalid_ids.append(original_format)
            
            # Combine all invalid Account IDs (format issues + Salesforce not found)
            all_invalid_ids = format_invalid_ids + sf_invalid_ids
            
            return {
                'valid_account_ids': valid_account_ids,
                'invalid_account_ids': all_invalid_ids,
                'format_invalid_count': len(format_invalid_ids),
                'sf_invalid_count': len(sf_invalid_ids)
            }, f"Validated {len(valid_account_ids)} valid and {len(all_invalid_ids)} invalid Account IDs"
            
        except Exception as e:
            return None, f"Error validating Account IDs: {str(e)}"

    def get_account_ids_from_query(self, soql_query, max_ids=100):
        """Get Account IDs from a custom SOQL query that returns Account IDs only"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Validate SOQL query
            if not self._validate_account_soql_query(soql_query):
                return None, "Invalid SOQL query. Must return Account IDs only (e.g., SELECT Id FROM Account, SELECT Account.Id FROM Account). Only complete SELECT queries are accepted."
            
            # Execute the SOQL query to get account IDs only
            assert self.sf is not None  # Type hint for linter
            
            # Build the proper query with smart limit handling
            try:
                final_query = self._build_account_soql_query(soql_query, max_ids)
            except ValueError as ve:
                return None, str(ve)
            
            id_result = self.sf.query(final_query)
            account_ids = [record['Id'] for record in id_result['records']]
            
            execution_time = time.time() - start_time
            total_found = id_result['totalSize'] if not id_result.get('done', True) else len(account_ids)
            
            result = {
                'account_ids': account_ids,
                'query_info': {
                    'original_query': soql_query,
                    'final_query': final_query,
                    'execution_time': f"{execution_time:.2f}s",
                    'total_found': total_found,
                    'returned_count': len(account_ids),
                    'effective_limit': min(self._extract_limit_from_query(soql_query) or float('inf'), max_ids) if soql_query and soql_query.strip() else max_ids
                }
            }
            
            return result, f"Successfully retrieved {len(account_ids)} Account IDs from query"
            
        except Exception as e:
            error_msg = str(e)
            # Provide cleaner error messages for common SOQL issues
            if "malformed request" in error_msg.lower() or "malformed_query" in error_msg.lower():
                return None, "Invalid SOQL syntax. Please check your query and try again. Make sure it follows proper SOQL format."
            elif "unexpected token" in error_msg.lower():
                return None, "SOQL syntax error. Please check for typos, missing keywords, or incorrect field names in your query."
            elif "no such column" in error_msg.lower() or "invalid field" in error_msg.lower():
                return None, "Invalid field name in query. Please check that all field names exist in the Account object."
            elif "invalid object name" in error_msg.lower():
                return None, "Invalid object name in query. This API only supports queries on the Account object."
            else:
                return None, f"Error executing SOQL query: Please check your query syntax and try again."

    def get_accounts_data_by_ids(self, account_ids):
        """Get full Account data for a list of Account IDs"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            if not account_ids:
                return {'accounts': []}, "No Account IDs provided"
            
            # Get account data in batch
            analyzed_accounts = self._analyze_account_batch(account_ids)
            
            execution_time = time.time() - start_time
            
            result = {
                'accounts': analyzed_accounts,
                'summary': {
                    'total_requested': len(account_ids),
                    'accounts_retrieved': len(analyzed_accounts)
                },
                'execution_time': f"{execution_time:.2f}s"
            }
            
            return result, f"Successfully retrieved data for {len(analyzed_accounts)} of {len(account_ids)} accounts"
            
        except Exception as e:
            return None, f"Error retrieving Account data: {str(e)}"

    def analyze_accounts_from_query(self, soql_query, max_analyze=100):
        """Analyze accounts from a custom SOQL query that returns Account IDs only"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Validate SOQL query
            if not self._validate_account_soql_query(soql_query):
                return None, "Invalid SOQL query. Must return Account IDs only (e.g., SELECT Id FROM Account, SELECT Account.Id FROM Account). Only complete SELECT queries are accepted."
            
            # Execute the SOQL query to get account IDs only
            assert self.sf is not None  # Type hint for linter
            
            # Build the proper query with smart limit handling
            try:
                final_query = self._build_account_soql_query(soql_query, max_analyze)
            except ValueError as ve:
                return None, str(ve)
            
            id_result = self.sf.query(final_query)
            account_ids_to_analyze = [record['Id'] for record in id_result['records']]
            actual_analyze_count = len(account_ids_to_analyze)
            
            # If no accounts found, return early
            if actual_analyze_count == 0:
                return {
                    'summary': {
                        'total_query_results': 0,
                        'accounts_analyzed': 0
                    },
                    'accounts': [],
                    'query_info': {
                        'original_query': soql_query,
                        'execution_time': f"{time.time() - start_time:.2f}s",
                        'total_found': 0,
                        'analyzed_count': 0
                    }
                }, "No accounts found matching the query"
            
            # For total count
            total_found = id_result['totalSize'] if not id_result.get('done', True) else actual_analyze_count
            
            # Get account data in batch
            analyzed_accounts = self._analyze_account_batch(account_ids_to_analyze)
            
            execution_time = time.time() - start_time
            
            result = {
                'summary': {
                    'total_query_results': total_found,
                    'accounts_analyzed': actual_analyze_count
                },
                'accounts': analyzed_accounts,
                'query_info': {
                    'original_query': soql_query,
                    'final_query': final_query,
                    'execution_time': f"{execution_time:.2f}s",
                    'total_found': total_found,
                    'analyzed_count': actual_analyze_count,
                    'effective_limit': min(self._extract_limit_from_query(soql_query) or float('inf'), max_analyze) if soql_query and soql_query.strip() else max_analyze
                }
            }
            
            return result, f"Successfully analyzed {actual_analyze_count} accounts from query"
            
        except Exception as e:
            return None, f"Error analyzing accounts from query: {str(e)}"

    def _validate_account_soql_query(self, soql_query):
        """Validate SOQL query for safety - must be complete SELECT query returning Account IDs only"""
        # Empty query is no longer valid - require complete SELECT statement
        if not soql_query or not soql_query.strip():
            return False
        
        # Convert to uppercase for checking
        query_upper = soql_query.upper().strip()
        
        # Must be a complete SELECT query, not a WHERE/LIMIT clause
        if not query_upper.startswith('SELECT'):
            return False
        
        # For full SELECT queries, validate for security and Account ID requirement
        import re
        
        # Check for dangerous operations
        dangerous_keywords = ['DELETE', 'UPDATE', 'INSERT', 'UPSERT', 'MERGE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        # Extract the main SELECT clause
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.DOTALL)
        if not select_match:
            return False
        
        select_fields = select_match.group(1).strip()
        select_fields_clean = re.sub(r'\s+', '', select_fields)
        
        # Allow: "Id", "Account.Id", "a.Id" (with alias), etc.
        valid_id_patterns = [
            r'^ID$',                    # Just "Id"
            r'^ACCOUNT\.ID$',           # "Account.Id"  
            r'^\w+\.ID$',              # "alias.Id" (like "a.Id")
        ]
        
        is_valid_id_selection = any(re.match(pattern, select_fields_clean) for pattern in valid_id_patterns)
        if not is_valid_id_selection:
            return False
        
        # For the main FROM clause, ensure it involves Account object
        if 'ACCOUNT' not in query_upper:
            return False
        
        return True

    def _build_account_soql_query(self, user_query, max_limit):
        """Build the final SOQL query for accounts with smart limit handling"""
        # No longer handle empty queries - require full SELECT query
        if not user_query or not user_query.strip():
            raise ValueError("Empty query not allowed. Please provide a complete SOQL SELECT query.")
        
        user_query = user_query.strip()
        
        # Only accept full SELECT queries, not WHERE/LIMIT clauses
        if not user_query.upper().startswith('SELECT'):
            raise ValueError("Query must be a complete SELECT statement. WHERE/LIMIT clauses alone are not accepted.")
        
        # For full SELECT queries, handle LIMIT clause intelligently
        query_upper = user_query.upper()
        if 'LIMIT' in query_upper:
            # Extract existing LIMIT value and use the smaller of the two
            import re
            limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
            if limit_match:
                existing_limit = int(limit_match.group(1))
                effective_limit = min(existing_limit, max_limit)
                # Replace the existing LIMIT with the effective limit
                final_query = re.sub(r'LIMIT\s+\d+', f'LIMIT {effective_limit}', user_query, flags=re.IGNORECASE)
                return final_query
            return user_query
        else:
            # No existing LIMIT, add our own
            return f"{user_query} LIMIT {max_limit}"

    def _extract_limit_from_query(self, query):
        """Extract the LIMIT value from a SOQL query, returns None if no LIMIT found"""
        if not query:
            return None
        
        import re
        limit_match = re.search(r'LIMIT\s+(\d+)', query.upper())
        return int(limit_match.group(1)) if limit_match else None

    def _analyze_account_batch(self, account_ids):
        """Analyze a batch of accounts by their IDs"""
        try:
            # Convert all Account IDs to 18-character format for querying
            query_account_ids = []
            for aid in account_ids:
                if len(str(aid).strip()) == 15:
                    query_account_ids.append(self._convert_15_to_18_char_id(str(aid).strip()))
                else:
                    query_account_ids.append(str(aid).strip())
            
            # Build batch query for all account IDs including custom fields and RecordType
            ids_string = "', '".join(query_account_ids)
            batch_query = f"""
            SELECT Id, Name, Ultimate_Parent_Account_Name__c, Website, 
                   BillingStreet, BillingCity, BillingState, BillingCountry,
                   ZI_Company_Name__c, ZI_Website__c, Parent_Account_ID__c, RecordType.Name
            FROM Account 
            WHERE Id IN ('{ids_string}')
            """
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(batch_query)
            
            analyzed_accounts = []
            for record in result['records']:
                # Remove Salesforce metadata if present
                if 'attributes' in record:
                    del record['attributes']
                analyzed_accounts.append(record)
            
            return analyzed_accounts
            
        except Exception as e:
            # Return empty results for this batch on error
            print(f"Error analyzing account batch: {str(e)}")
            return [] 