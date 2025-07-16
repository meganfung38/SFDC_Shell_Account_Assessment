from simple_salesforce.api import Salesforce
from config.config import Config, BAD_EMAIL_DOMAINS
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
            
            # Simple test - query 5 Lead IDs
            assert self.sf is not None  # Type hint for linter
            query_result = self.sf.query("SELECT Id FROM Lead LIMIT 5")
            
            # If we get here, connection is working and we can query data
            record_count = len(query_result['records'])
            return True, f"Connection successful - Retrieved {record_count} Lead records"
            
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
    
    def _is_free_email_domain(self, email):
        """Check if email uses a free email domain"""
        if not email:
            return False
        try:
            domain = email.split('@')[1].lower()
            return bool(domain in BAD_EMAIL_DOMAINS)
        except (IndexError, AttributeError):
            return False
    
    def _extract_email_domain(self, email):
        """Extract domain from email address"""
        if not email:
            return None
        try:
            domain = email.split('@')[1].lower().strip()
            return domain if domain else None
        except (IndexError, AttributeError):
            return None
    
    def _normalize_lead_record(self, lead_record):
        """Normalize lead record by extracting relationship fields and cleaning up structure"""
        # Handle SegmentName__r.Name relationship field
        if 'SegmentName__r' in lead_record:
            segment_obj = lead_record.get('SegmentName__r')
            if segment_obj and isinstance(segment_obj, dict):
                lead_record['SegmentName'] = segment_obj.get('Name')
            else:
                lead_record['SegmentName'] = None
            # Remove the relationship object
            del lead_record['SegmentName__r']
        
        # Remove Salesforce metadata if present
        if 'attributes' in lead_record:
            del lead_record['attributes']
        
        return lead_record
    
    def _analyze_lead_flags(self, lead_record):
        """Analyze lead data and return business logic flags and email domain"""
        # Extract values with explicit None handling
        zi_employees = lead_record.get('ZI_Employees__c')
        zi_company_name = lead_record.get('ZI_Company_Name__c')
        email = lead_record.get('Email')
        website = lead_record.get('Website')
        
        # Convert employee count to int if it exists, default to 0
        try:
            employee_count = int(zi_employees) if zi_employees is not None else 0
        except (ValueError, TypeError):
            employee_count = 0
        
        # Normalize string values - treat empty strings as None
        zi_company_name = zi_company_name.strip() if zi_company_name else None
        email = email.strip() if email else None
        website = website.strip() if website else None
        
        # Extract email domain
        email_domain = self._extract_email_domain(email)
        
        # Flag 1: not_in_TAM
        # True when ZI_Employees__c > 100 AND ZI_Company_Name__c is null/empty
        not_in_tam = bool(employee_count > 100 and not zi_company_name)
        
        # Flag 2: suspicious_enrichment  
        # True when: free email domain AND no website AND has company name AND > 100 employees
        has_free_email = self._is_free_email_domain(email)
        has_no_website = not website  # website is null/empty
        has_company_name = bool(zi_company_name)  # company name is populated
        has_many_employees = employee_count > 100
        
        suspicious_enrichment = bool(
            has_free_email and 
            has_no_website and 
            has_company_name and 
            has_many_employees
        )
        
        return {
            'not_in_TAM': not_in_tam,
            'suspicious_enrichment': suspicious_enrichment,
            'email_domain': email_domain
        }
    
    def get_lead_by_id(self, lead_id):
        """Get specific Lead fields by Lead ID with business logic flags"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Query for specific ZoomInfo fields and additional enrichment data
            query = """
            SELECT Id, Email, First_Channel__c, 
                   SegmentName__r.Name, LS_Company_Size_Range__c, Website, Company,
                   ZI_Website__c, ZI_Company_Name__c, ZI_Employees__c
            FROM Lead 
            WHERE Id = '{}'
            """.format(lead_id)
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(query)
            
            if result['totalSize'] == 0:
                return None, f"No Lead found with ID: {lead_id}"
            
            # Get the lead record
            lead_record = result['records'][0]
            
            # Normalize the lead record (handle relationship fields and cleanup)
            lead_record = self._normalize_lead_record(lead_record)
            
            # Add business logic flags
            flags = self._analyze_lead_flags(lead_record)
            lead_record.update(flags)
                
            return lead_record, "Lead retrieved successfully with analysis"
            
        except Exception as e:
            return None, f"Error retrieving Lead: {str(e)}"
    
    def query_leads(self, query_conditions=None, limit=100):
        """Query leads with optional conditions"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Base query with ZoomInfo fields and additional enrichment data
            base_query = """
            SELECT Id, Email, First_Channel__c, 
                   SegmentName__r.Name, LS_Company_Size_Range__c, Website, Company,
                   ZI_Website__c, ZI_Company_Name__c, ZI_Employees__c
            FROM Lead
            """
            
            # Add conditions if provided
            if query_conditions:
                base_query += f" WHERE {query_conditions}"
            
            # Add limit
            base_query += f" LIMIT {limit}"
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(base_query)
            
            # Clean up records by normalizing and adding flags
            clean_records = []
            for record in result['records']:
                # Normalize the lead record (handle relationship fields and cleanup)
                record = self._normalize_lead_record(record)
                
                # Add business logic flags
                flags = self._analyze_lead_flags(record)
                record.update(flags)
                clean_records.append(record)
            
            return {
                'records': clean_records,
                'totalSize': result['totalSize'],
                'done': result['done']
            }, "Query executed successfully"
            
        except Exception as e:
            return None, f"Error executing query: {str(e)}"

    def preview_soql_query(self, soql_query, limit=100):
        """Preview SOQL query results - just return Lead IDs and count"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Validate SOQL query 
            if not self._validate_soql_query(soql_query):
                return None, "Invalid SOQL query. Must return Lead IDs only (e.g., SELECT Id FROM Lead, SELECT Lead.Id FROM Lead, or WHERE/LIMIT clauses). JOINs and UNIONs allowed if they return Lead IDs."
            
            # Build the proper query using the new helper method
            preview_query = self._build_soql_query(soql_query, limit)
            
            # Execute the SOQL query to get lead IDs only
            assert self.sf is not None  # Type hint for linter
            query_result = self.sf.query(preview_query)
            
            execution_time = time.time() - start_time
            
            # Extract just the Lead IDs
            lead_ids = [record['Id'] for record in query_result['records']]
            
            result = {
                'total_found': query_result['totalSize'],
                'preview_count': len(lead_ids),
                'lead_ids': lead_ids,
                'query_info': {
                    'original_query': soql_query,
                    'preview_query': preview_query,
                    'execution_time': f"{execution_time:.2f}s",
                    'has_more': not query_result['done']
                }
            }
            
            return result, f"Found {query_result['totalSize']} total leads, showing first {len(lead_ids)}"
            
        except Exception as e:
            return None, f"Error previewing SOQL query: {str(e)}"

    def analyze_leads_from_query(self, soql_query, max_analyze=100, include_ai_assessment=True):
        """Analyze leads from a custom SOQL query with quality assessment and AI confidence scoring"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            # Validate SOQL query
            if not self._validate_soql_query(soql_query):
                return None, "Invalid SOQL query. Must return Lead IDs only (e.g., SELECT Id FROM Lead, SELECT Lead.Id FROM Lead, or WHERE/LIMIT clauses). JOINs and UNIONs allowed if they return Lead IDs."
            
            # Execute the SOQL query to get lead IDs only (much faster than query_all)
            assert self.sf is not None  # Type hint for linter
            
            # Build the proper query using the new helper method
            final_query = self._build_soql_query(soql_query, max_analyze)
            id_result = self.sf.query(final_query)
            lead_ids_to_analyze = [record['Id'] for record in id_result['records']]
            actual_analyze_count = len(lead_ids_to_analyze)
            
            # If no leads found, return early
            if actual_analyze_count == 0:
                return {
                    'summary': {
                        'total_query_results': 0,
                        'leads_analyzed': 0,
                        'leads_with_issues': 0,
                        'not_in_tam_count': 0,
                        'suspicious_enrichment_count': 0,
                        'avg_confidence_score': 0
                    },
                    'leads': [],
                    'query_info': {
                        'original_query': soql_query,
                        'execution_time': f"{time.time() - start_time:.2f}s",
                        'total_found': 0,
                        'analyzed_count': 0
                    }
                }, "No leads found matching the query"
            
            # For total count, we can estimate or get it if needed
            # For now, we'll use the actual count we got (could be less than total if limited)
            total_found = id_result['totalSize'] if not id_result.get('done', True) else actual_analyze_count
            
            # Process leads with AI confidence assessment
            analyzed_leads = []
            leads_with_issues = 0
            not_in_tam_count = 0
            suspicious_enrichment_count = 0
            total_confidence_score = 0
            successful_ai_assessments = 0
            
            # Import here to avoid circular imports
            from services.openai_service import generate_lead_confidence_assessment
            
            # Get all lead data in one batch query (much faster!)
            batch_leads = self._analyze_lead_batch(lead_ids_to_analyze, include_details=True)
            
            # Process each lead for AI assessment
            for lead_data in batch_leads:
                try:
                    # Count basic quality issues
                    if lead_data.get('not_in_TAM') or lead_data.get('suspicious_enrichment'):
                        leads_with_issues += 1
                    if lead_data.get('not_in_TAM'):
                        not_in_tam_count += 1
                    if lead_data.get('suspicious_enrichment'):
                        suspicious_enrichment_count += 1
                    
                    # Generate AI confidence assessment if requested
                    if include_ai_assessment:
                        assessment, ai_message = generate_lead_confidence_assessment(lead_data)
                        if assessment and assessment.get('confidence_score') is not None:
                            lead_data['confidence_assessment'] = assessment
                            lead_data['ai_assessment_status'] = 'success'
                            total_confidence_score += assessment.get('confidence_score', 0)
                            successful_ai_assessments += 1
                        else:
                            lead_data['confidence_assessment'] = None
                            lead_data['ai_assessment_status'] = f'failed: {ai_message}'
                    
                    # Always include full lead data
                    analyzed_leads.append(lead_data)
                        
                except Exception as e:
                    print(f"Error processing lead {lead_data.get('Id', 'unknown')}: {str(e)}")
                    continue
            
            execution_time = time.time() - start_time
            avg_confidence_score = (total_confidence_score / successful_ai_assessments) if successful_ai_assessments > 0 else 0
            
            result = {
                'summary': {
                    'total_query_results': total_found,
                    'leads_analyzed': actual_analyze_count,
                    'leads_with_issues': leads_with_issues,
                    'not_in_tam_count': not_in_tam_count,
                    'suspicious_enrichment_count': suspicious_enrichment_count,
                    'issue_percentage': round((leads_with_issues / actual_analyze_count) * 100, 2) if actual_analyze_count > 0 else 0,
                    'avg_confidence_score': round(avg_confidence_score, 1),
                    'ai_assessments_successful': successful_ai_assessments,
                    'ai_assessments_failed': actual_analyze_count - successful_ai_assessments
                },
                'leads': analyzed_leads,
                'query_info': {
                    'original_query': soql_query,
                    'final_query': final_query,
                    'execution_time': f"{execution_time:.2f}s",
                    'total_found': total_found,
                    'analyzed_count': actual_analyze_count,
                    'skipped_count': total_found - actual_analyze_count,
                    'include_ai_assessment': include_ai_assessment
                }
            }
            
            return result, f"Successfully analyzed {actual_analyze_count} of {total_found} leads from query with AI confidence scoring"
            
        except Exception as e:
            return None, f"Error analyzing leads from query: {str(e)}"
    
    def _validate_soql_query(self, soql_query):
        """Validate SOQL query for safety - must return Lead IDs only"""
        # Empty query is valid (will default to random leads)
        if not soql_query or not soql_query.strip():
            return True
        
        # Convert to uppercase for checking
        query_upper = soql_query.upper().strip()
        
        # If it's not a full SELECT query, it's a WHERE/LIMIT clause - validate it
        if not query_upper.startswith('SELECT'):
            # Check for dangerous operations in WHERE/LIMIT clauses
            dangerous_keywords = ['DELETE', 'UPDATE', 'INSERT', 'UPSERT', 'MERGE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    return False
            return True
        
        # For full SELECT queries, validate for security and Lead ID requirement
        import re
        
        # Check for dangerous operations (most important security check)
        dangerous_keywords = ['DELETE', 'UPDATE', 'INSERT', 'UPSERT', 'MERGE', 'DROP', 'ALTER', 'CREATE', 'TRUNCATE']
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False
        
        # Must be a SELECT query
        if not query_upper.startswith('SELECT'):
            return False
        
        # Extract the main SELECT clause (first occurrence)
        select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.DOTALL)
        if not select_match:
            return False
        
        select_fields = select_match.group(1).strip()
        
        # Check if selecting Lead.Id or just Id (both should be allowed)
        # Remove whitespace and normalize
        select_fields_clean = re.sub(r'\s+', '', select_fields)
        
        # Allow: "Id", "Lead.Id", "l.Id" (with alias), etc.
        # The key is that it should end with ".ID" or be exactly "ID"
        valid_id_patterns = [
            r'^ID$',                    # Just "Id"
            r'^LEAD\.ID$',             # "Lead.Id"  
            r'^\w+\.ID$',              # "alias.Id" (like "l.Id")
        ]
        
        is_valid_id_selection = any(re.match(pattern, select_fields_clean) for pattern in valid_id_patterns)
        if not is_valid_id_selection:
            return False
        
        # For the main FROM clause, we need to ensure it involves Lead object
        # This is more flexible - allows JOINs as long as Lead is involved
        if 'LEAD' not in query_upper:
            return False
        
        # Additional validation: if there are UNIONs, each part should be validated
        if 'UNION' in query_upper:
            # Split by UNION and validate each part
            union_parts = re.split(r'UNION\s+(?:ALL\s+)?', query_upper)
            for part in union_parts:
                part = part.strip()
                if not part:
                    continue
                    
                # Each UNION part should also select Lead IDs
                part_select_match = re.search(r'SELECT\s+(.*?)\s+FROM', part, re.DOTALL)
                if not part_select_match:
                    return False
                    
                part_select_fields = part_select_match.group(1).strip()
                part_select_clean = re.sub(r'\s+', '', part_select_fields)
                
                # Each UNION part should also be selecting ID
                part_valid = any(re.match(pattern, part_select_clean) for pattern in valid_id_patterns)
                if not part_valid:
                    return False
                
                # Each UNION part should involve Lead object
                if 'LEAD' not in part:
                    return False
        
        return True
    
    def _build_soql_query(self, user_query, max_analyze):
        """Build the final SOQL query handling empty queries and LIMIT clauses"""
        # Handle empty query - return random leads
        if not user_query or not user_query.strip():
            return f"SELECT Id FROM Lead LIMIT {max_analyze}"
        
        user_query = user_query.strip()
        
        # If query doesn't start with SELECT, assume it's a WHERE/LIMIT clause
        if not user_query.upper().startswith('SELECT'):
            base_query = f"SELECT Id FROM Lead {user_query}"
        else:
            base_query = user_query
        
        # Check if LIMIT already exists
        query_upper = base_query.upper()
        if 'LIMIT' in query_upper:
            # Extract existing LIMIT value
            import re
            limit_match = re.search(r'LIMIT\s+(\d+)', query_upper)
            if limit_match:
                existing_limit = int(limit_match.group(1))
                # Use the smaller of the two limits
                effective_limit = min(existing_limit, max_analyze)
                # Replace the existing LIMIT with the effective limit
                base_query = re.sub(r'LIMIT\s+\d+', f'LIMIT {effective_limit}', base_query, flags=re.IGNORECASE)
            return base_query
        else:
            # No existing LIMIT, add our own
            return f"{base_query} LIMIT {max_analyze}"
    
    def _analyze_lead_batch(self, lead_ids, include_details=True):
        """Analyze a batch of leads by their IDs"""
        try:
            # Convert all Lead IDs to 18-character format for querying
            query_lead_ids = []
            for lid in lead_ids:
                if len(str(lid).strip()) == 15:
                    query_lead_ids.append(self._convert_15_to_18_char_id(str(lid).strip()))
                else:
                    query_lead_ids.append(str(lid).strip())
            
            # Build batch query for all lead IDs
            ids_string = "', '".join(query_lead_ids)
            batch_query = f"""
            SELECT Id, Email, First_Channel__c, 
                   SegmentName__r.Name, LS_Company_Size_Range__c, Website, Company,
                   ZI_Website__c, ZI_Company_Name__c, ZI_Employees__c
            FROM Lead 
            WHERE Id IN ('{ids_string}')
            """
            
            assert self.sf is not None  # Type hint for linter
            result = self.sf.query(batch_query)
            
            analyzed_leads = []
            for record in result['records']:
                # Normalize the lead record (handle relationship fields and cleanup)
                record = self._normalize_lead_record(record)
                
                # Add business logic flags
                flags = self._analyze_lead_flags(record)
                
                if include_details:
                    # Include all lead data
                    record.update(flags)
                    analyzed_leads.append(record)
                else:
                    # Include only ID and flags
                    analyzed_leads.append({
                        'Id': record['Id'],
                        'not_in_TAM': flags['not_in_TAM'],
                        'suspicious_enrichment': flags['suspicious_enrichment']
                    })
            
            return analyzed_leads
            
        except Exception as e:
            # Return empty results for this batch on error
            print(f"Error analyzing batch: {str(e)}")
            return []
    
    def validate_lead_ids(self, lead_ids):
        """Validate that all provided Lead IDs exist in Salesforce"""
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            if not lead_ids:
                return {'valid_lead_ids': [], 'invalid_lead_ids': []}, "No Lead IDs provided"
            

            
            # Clean and validate Lead ID format first
            cleaned_lead_ids = []
            format_invalid_ids = []
            id_mapping = {}  # Maps original ID to cleaned ID for response
            
            for lid in lead_ids:
                lid_str = str(lid).strip()
                # Basic Lead ID format validation (15 or 18 characters, starts with 00Q)
                if len(lid_str) in [15, 18] and lid_str.startswith('00Q'):
                    # Convert 15-char IDs to 18-char for consistent querying
                    if len(lid_str) == 15:
                        converted_id = self._convert_15_to_18_char_id(lid_str)
                        cleaned_lead_ids.append(converted_id)
                        id_mapping[converted_id] = lid_str  # Remember original format
                    else:
                        cleaned_lead_ids.append(lid_str)
                        id_mapping[lid_str] = lid_str
                else:
                    format_invalid_ids.append(lid_str)
            
            # If any Lead IDs have invalid format, return them as invalid
            if format_invalid_ids:
                print(f"🔍 Found {len(format_invalid_ids)} Lead IDs with invalid format: {format_invalid_ids}")
            
            # Query Salesforce to check which Lead IDs exist (only for format-valid IDs)
            valid_lead_ids = []
            sf_invalid_ids = []
            
            if cleaned_lead_ids:
                # Process in batches to avoid SOQL query limits
                batch_size = 200  # Salesforce IN clause limit
                for i in range(0, len(cleaned_lead_ids), batch_size):
                    batch = cleaned_lead_ids[i:i + batch_size]
                    ids_string = "', '".join(batch)
                    validation_query = f"SELECT Id FROM Lead WHERE Id IN ('{ids_string}')"
                    
                    assert self.sf is not None  # Type hint for linter
                    result = self.sf.query(validation_query)
                    
                    # Extract valid Lead IDs from this batch (in 18-char format from Salesforce)
                    batch_valid_18char = [record['Id'] for record in result['records']]
                    
                    # Convert back to original format for response
                    for valid_18char in batch_valid_18char:
                        original_format = id_mapping.get(valid_18char, valid_18char)
                        valid_lead_ids.append(original_format)
                    
                    # Find invalid Lead IDs in this batch (return in original format)
                    for clean_id in batch:
                        if clean_id not in batch_valid_18char:
                            original_format = id_mapping.get(clean_id, clean_id)
                            sf_invalid_ids.append(original_format)
            
            # Combine all invalid Lead IDs (format issues + Salesforce not found)
            all_invalid_ids = format_invalid_ids + sf_invalid_ids
            
            print(f"🔍 Lead ID validation results:")
            print(f"   - Total provided: {len(lead_ids)}")
            print(f"   - Format valid: {len(cleaned_lead_ids)}")
            print(f"   - Format invalid: {len(format_invalid_ids)}")
            print(f"   - Salesforce valid: {len(valid_lead_ids)}")
            print(f"   - Salesforce invalid: {len(sf_invalid_ids)}")
            print(f"   - 15-char conversions: {len([k for k, v in id_mapping.items() if len(v) == 15])}")
            
            return {
                'valid_lead_ids': valid_lead_ids,
                'invalid_lead_ids': all_invalid_ids,
                'format_invalid_count': len(format_invalid_ids),
                'sf_invalid_count': len(sf_invalid_ids)
            }, f"Validated {len(valid_lead_ids)} valid and {len(all_invalid_ids)} invalid Lead IDs"
            
        except Exception as e:
            return None, f"Error validating Lead IDs: {str(e)}"
    
    def analyze_leads_from_ids(self, lead_ids, include_ai_assessment=True):
        """Analyze leads from a list of Lead IDs with quality assessment and AI confidence scoring"""
        import time
        start_time = time.time()
        
        try:
            if not self.ensure_connection():
                return None, "Failed to establish Salesforce connection"
            
            if not lead_ids:
                return {
                    'summary': {
                        'leads_analyzed': 0,
                        'leads_with_issues': 0,
                        'not_in_tam_count': 0,
                        'suspicious_enrichment_count': 0,
                        'avg_confidence_score': 0
                    },
                    'leads': []
                }, "No Lead IDs provided"
            
            actual_analyze_count = len(lead_ids)
            
            # Process leads with AI confidence assessment
            analyzed_leads = []
            leads_with_issues = 0
            not_in_tam_count = 0
            suspicious_enrichment_count = 0
            total_confidence_score = 0
            successful_ai_assessments = 0
            
            # Import here to avoid circular imports
            from services.openai_service import generate_lead_confidence_assessment
            
            # Get all lead data in one batch query (much faster!)
            batch_leads = self._analyze_lead_batch(lead_ids, include_details=True)
            
            # Process each lead for AI assessment
            for lead_data in batch_leads:
                try:
                    # Count basic quality issues
                    if lead_data.get('not_in_TAM') or lead_data.get('suspicious_enrichment'):
                        leads_with_issues += 1
                    if lead_data.get('not_in_TAM'):
                        not_in_tam_count += 1
                    if lead_data.get('suspicious_enrichment'):
                        suspicious_enrichment_count += 1
                    
                    # Generate AI confidence assessment if requested
                    if include_ai_assessment:
                        assessment, ai_message = generate_lead_confidence_assessment(lead_data)
                        if assessment and assessment.get('confidence_score') is not None:
                            lead_data['confidence_assessment'] = assessment
                            lead_data['ai_assessment_status'] = 'success'
                            total_confidence_score += assessment.get('confidence_score', 0)
                            successful_ai_assessments += 1
                        else:
                            lead_data['confidence_assessment'] = None
                            lead_data['ai_assessment_status'] = f'failed: {ai_message}'
                    
                    # Always include full lead data
                    analyzed_leads.append(lead_data)
                        
                except Exception as e:
                    print(f"Error processing lead {lead_data.get('Id', 'unknown')}: {str(e)}")
                    continue
            
            execution_time = time.time() - start_time
            avg_confidence_score = (total_confidence_score / successful_ai_assessments) if successful_ai_assessments > 0 else 0
            
            result = {
                'summary': {
                    'leads_analyzed': actual_analyze_count,
                    'leads_with_issues': leads_with_issues,
                    'not_in_tam_count': not_in_tam_count,
                    'suspicious_enrichment_count': suspicious_enrichment_count,
                    'issue_percentage': round((leads_with_issues / actual_analyze_count) * 100, 2) if actual_analyze_count > 0 else 0,
                    'avg_confidence_score': round(avg_confidence_score, 1),
                    'ai_assessments_successful': successful_ai_assessments,
                    'ai_assessments_failed': actual_analyze_count - successful_ai_assessments
                },
                'leads': analyzed_leads
            }
            
            return result, f"Successfully analyzed {actual_analyze_count} leads with AI confidence scoring"
            
        except Exception as e:
            return None, f"Error analyzing leads from IDs: {str(e)}" 