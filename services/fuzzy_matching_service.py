from urllib.parse import urlparse
import re
from difflib import SequenceMatcher
from typing import Optional, Tuple


class FuzzyMatchingService:
    """Service for fuzzy matching operations used in account relationship assessment"""
    
    def __init__(self):
        # Common domain prefixes and suffixes to normalize
        self.domain_prefixes = ['www.', 'app.', 'portal.', 'my.', 'secure.', 'admin.']
        self.domain_suffixes = ['.com', '.org', '.net', '.edu', '.gov', '.co', '.io', '.ai']
        
    def extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract clean domain name from URL"""
        if not url:
            return None
            
        try:
            # Add protocol if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Remove common prefixes
            for prefix in self.domain_prefixes:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
                    break
                    
            return domain
        except Exception:
            return None
    
    def extract_company_name_from_domain(self, domain: str) -> Optional[str]:
        """Extract company name from domain (remove TLD and common patterns)"""
        if not domain:
            return None
            
        # Remove TLD
        for suffix in self.domain_suffixes:
            if domain.endswith(suffix):
                domain = domain[:-len(suffix)]
                break
        
        # Remove common patterns
        domain = re.sub(r'[^a-zA-Z0-9]', '', domain)  # Remove special chars
        return domain.lower() if domain else None
    
    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for comparison"""
        if not name:
            return ""
            
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common business suffixes
        business_suffixes = [
            'inc', 'incorporated', 'corp', 'corporation', 'ltd', 'limited', 
            'llc', 'llp', 'company', 'co', 'group', 'holdings', 'enterprises'
        ]
        
        for suffix in business_suffixes:
            # Remove suffix with various separators
            patterns = [f' {suffix}', f'.{suffix}', f',{suffix}', f'-{suffix}']
            for pattern in patterns:
                if normalized.endswith(pattern):
                    normalized = normalized[:-len(pattern)]
                    break
        
        # Remove special characters and extra spaces
        normalized = re.sub(r'[^a-zA-Z0-9\s]', ' ', normalized)
        normalized = ' '.join(normalized.split())  # Normalize whitespace
        
        return normalized
    
    def compute_fuzzy_similarity(self, str1: str, str2: str) -> float:
        """Compute fuzzy similarity between two strings (0.0 to 1.0)"""
        if not str1 or not str2:
            return 0.0
            
        # Normalize both strings
        norm1 = self.normalize_company_name(str1)
        norm2 = self.normalize_company_name(str2)
        
        if not norm1 or not norm2:
            return 0.0
        
        # Use SequenceMatcher for fuzzy comparison
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity
    
    def compute_name_website_consistency(self, name: str, website: str) -> Tuple[float, str]:
        """
        Compute consistency score between company name and website
        Returns (score_0_to_100, explanation)
        """
        if not name:
            return 0.0, "No company name provided"
            
        if not website:
            return 0.0, "No website provided"
        
        # Extract domain and company name from domain
        domain = self.extract_domain_from_url(website)
        if not domain:
            return 0.0, f"Could not extract valid domain from website: {website}"
        
        domain_company = self.extract_company_name_from_domain(domain)
        if not domain_company:
            return 0.0, f"Could not extract company name from domain: {domain}"
        
        # Compute similarity
        similarity = self.compute_fuzzy_similarity(name, domain_company)
        score = similarity * 100
        
        explanation = f"Comparing '{self.normalize_company_name(name)}' with domain '{domain_company}' from {domain}"
        
        return score, explanation
    
    def compute_name_zi_consistency(self, name: str, zi_company: str, zi_website: str) -> Tuple[float, str]:
        """
        Compute consistency between name and ZoomInfo fields when website is missing
        Returns (score_0_to_100, explanation)
        """
        if not name:
            return 0.0, "No company name provided"
        
        scores = []
        explanations = []
        
        # Compare with ZI Company Name
        if zi_company:
            zi_similarity = self.compute_fuzzy_similarity(name, zi_company)
            scores.append(zi_similarity)
            explanations.append(f"Name vs ZI Company: {zi_similarity:.2f}")
        
        # Compare with ZI Website
        if zi_website:
            zi_website_score, zi_website_explanation = self.compute_name_website_consistency(name, zi_website)
            scores.append(zi_website_score / 100)  # Convert back to 0-1 scale
            explanations.append(f"Name vs ZI Website: {zi_website_score:.1f}")
        
        if not scores:
            return 0.0, "No ZoomInfo data available for comparison"
        
        # Take the maximum score from available comparisons
        best_score = max(scores) * 100
        explanation = f"Best match from ZI fields: {'; '.join(explanations)}"
        
        return best_score, explanation
    
    def compute_customer_consistency_score(self, name: str, website: str, zi_company: str, zi_website: str) -> Tuple[float, str]:
        """
        Main method to compute Customer_Consistency flag
        Returns (score_0_to_100, explanation)
        """
        # First try name vs website
        if website:
            score, explanation = self.compute_name_website_consistency(name, website)
            return score, f"Using Website: {explanation}"
        
        # Fall back to ZI fields if no website
        score, explanation = self.compute_name_zi_consistency(name, zi_company, zi_website)
        return score, f"Using ZI fields: {explanation}"
    
    def get_best_field_value(self, primary_field: str, fallback_field: str, field_type: str) -> str:
        """Get the best available value for a field, using fallback if primary is missing"""
        if primary_field and primary_field.strip():
            return primary_field.strip()
        elif fallback_field and fallback_field.strip():
            return fallback_field.strip()
        else:
            return ""
    
    def compute_customer_shell_coherence_score(self, customer_data: dict, shell_data: dict) -> Tuple[float, str]:
        """
        Compute Customer_Shell_Coherence flag - compare customer account with shell account metadata
        Returns (score_0_to_100, explanation)
        """
        if not shell_data:
            return 0.0, "No shell account data available"
        
        # Get best available values for customer
        customer_name = self.get_best_field_value(
            customer_data.get('Name', ''), 
            customer_data.get('ZI_Company_Name__c', ''), 
            'name'
        )
        customer_website = self.get_best_field_value(
            customer_data.get('Website', ''), 
            customer_data.get('ZI_Website__c', ''), 
            'website'
        )
        
        # Get best available values for shell
        shell_name = self.get_best_field_value(
            shell_data.get('Name', ''), 
            shell_data.get('ZI_Company_Name__c', ''), 
            'name'
        )
        shell_website = self.get_best_field_value(
            shell_data.get('Website', ''), 
            shell_data.get('ZI_Website__c', ''), 
            'website'
        )
        
        scores = []
        explanations = []
        
        # Direct comparisons
        if customer_name and shell_name:
            name_similarity = self.compute_fuzzy_similarity(customer_name, shell_name)
            scores.append(name_similarity)
            explanations.append(f"Name similarity: {name_similarity * 100:.1f}")
        
        if customer_website and shell_website:
            # Compare website domains directly
            customer_domain = self.extract_domain_from_url(customer_website)
            shell_domain = self.extract_domain_from_url(shell_website)
            if customer_domain and shell_domain:
                customer_domain_company = self.extract_company_name_from_domain(customer_domain)
                shell_domain_company = self.extract_company_name_from_domain(shell_domain)
                if customer_domain_company and shell_domain_company:
                    website_similarity = self.compute_fuzzy_similarity(customer_domain_company, shell_domain_company)
                    scores.append(website_similarity)
                    explanations.append(f"Website similarity: {website_similarity * 100:.1f}")
        
        # Cross comparisons
        if customer_name and shell_website:
            cross_score_1, cross_explanation_1 = self.compute_name_website_consistency(customer_name, shell_website)
            if cross_score_1 > 0:
                scores.append(cross_score_1 / 100)  # Convert to 0-1 scale for scoring
                explanations.append(f"Customer name vs Shell website: {cross_score_1:.1f}")
        
        if customer_website and shell_name:
            # Extract domain from customer website and compare with shell name
            customer_domain = self.extract_domain_from_url(customer_website)
            if customer_domain:
                customer_domain_company = self.extract_company_name_from_domain(customer_domain)
                if customer_domain_company:
                    cross_similarity = self.compute_fuzzy_similarity(shell_name, customer_domain_company)
                    scores.append(cross_similarity)
                    explanations.append(f"Customer website vs Shell name: {cross_similarity * 100:.1f}")
        
        if not scores:
            return 0.0, "Insufficient data for shell coherence comparison"
        
        # Comprehensive scoring: take weighted average with higher weight on direct comparisons
        direct_scores = scores[:2] if len(scores) >= 2 else scores
        cross_scores = scores[2:] if len(scores) > 2 else []
        
        if direct_scores and cross_scores:
            # Weight direct comparisons more heavily (70%) than cross comparisons (30%)
            avg_direct = sum(direct_scores) / len(direct_scores)
            avg_cross = sum(cross_scores) / len(cross_scores)
            final_score = (avg_direct * 0.7) + (avg_cross * 0.3)
        elif direct_scores:
            final_score = sum(direct_scores) / len(direct_scores)
        else:
            final_score = sum(cross_scores) / len(cross_scores)
        
        final_score_100 = final_score * 100
        explanation = f"Shell coherence analysis: {'; '.join(explanations)}"
        
        return final_score_100, explanation
    
    def compute_address_consistency(self, customer_data: dict, shell_data: dict) -> Tuple[bool, str]:
        """
        Compute Address_Consistency flag - compare billing addresses
        Returns (boolean, explanation)
        """
        if not shell_data:
            return False, "No shell account data available"
        
        # Define address fields to compare
        address_fields = ['BillingStreet', 'BillingCity', 'BillingState', 'BillingCountry']
        
        matches = []
        differences = []
        
        for field in address_fields:
            customer_value = customer_data.get(field, '').strip() if customer_data.get(field) else ''
            shell_value = shell_data.get(field, '').strip() if shell_data.get(field) else ''
            
            # Normalize for comparison (case-insensitive)
            customer_normalized = customer_value.lower()
            shell_normalized = shell_value.lower()
            
            if customer_normalized == shell_normalized:
                if customer_value:  # Only count as match if there's actual data
                    matches.append(field)
            else:
                if customer_value or shell_value:  # Only count as difference if at least one has data
                    differences.append(f"{field}: '{customer_value}' vs '{shell_value}'")
        
        # Address is consistent if all populated fields match
        is_consistent = len(differences) == 0 and len(matches) > 0
        
        if len(matches) == 0 and len(differences) == 0:
            explanation = "No address data available for comparison"
        elif is_consistent:
            explanation = f"Address match: {', '.join(matches)}"
        else:
            explanation = f"Address differences: {'; '.join(differences)}"
        
        return is_consistent, explanation 