## **Project 3– SFDC Shell Account Assessment**

### **SFDC Account Hierarchy** 

* RC’s internal Salesforce system uses a structured account hierarchy to capture the relationships between company-level shell accounts and individual customer-level accounts.   
* Account Hierarchy Purpose:   
  * Organize and deduplicate data across free trials, leads, and customer accounts   
  * Provide sales teams with a holistic view of all contacts and accounts associated with a company   
  * Enable accurate reporting and account-based marketing by grouping related records under a single umbrella  
  * Consolidate engagement insights and interactions at the company level   
* Parent Account (Record Type: ZI Customer Shell Account)  
  * A ZoomInfo enriched entity representing the master identity for a business or organization. Contains firmographic data like company name, website, and billing address.   
* Child Account (Record Type: Customer Account)  
  * Represents individuals or departments who sign up for a RC trial or service. Each record includes a parent id field referencing the shell account it belongs to

### **Problem Statement**

* ZoomInfo-enriched shell accounts are designed to unify customer-level records under one corporate identity. However, inconsistencies in data and incorrect associations have led to misaligned parent-child relationships within SFDC. This introduces:   
  * Poor data hygiene   
  * Misleading sales attribution   
  * Fragmented customer insights   
  * Operational inefficiencies


### **Solution**

* Build an automated system to evaluate the validity of SFDC account-to-shell-account relationships using field comparison and pattern analysis.   
  * Inputs:   
    * list of SFDC account IDs (via SOQL query or excel upload)   
    * Single SFDC account ID   
    * Single SFDC shell account ID (to trigger batch evaluation of its child accounts)  
  * Output:   
    * Confidence scoring (%) for each account-shell pairing that reflects the likelihood of a correct match   
    * An explanation detailing why the score was assigned  
    * Flags and metadata indicators for further review

    

* Steps:    
1. Salesforce Data Extraction  
* Shell and Customer Account data: 

| Field  | Description | API Name |
| :---- | :---- | :---- |
| *Id*  | 18 Character SFDC Id | id |
| *Account Name*  | Company/ Organization/ Personal Name | Name |
| *Ultimate Parent Account Name*  | Shell Account Company/ Organization | Ultimate\_Parent\_Account\_Name\_\_c |
| *Website*  | Associated Website | Website |
| *Billing Address*  | Location  | BillingStreet, BillingCity, BillingState, BillingCountry |
| *ZI Company Name*  | ZoomInfo Enriched Company Name | ZI\_Company\_Name\_\_c |
| *ZI Website* | ZoomInfo Enriched Company Name | ZI\_Website\_\_c  |
| *Parent Account ID*  | 15 Character SFDC Id | Parent\_Account\_ID\_\_c |
| *Record Type*  | Customer Account or ZI Customer Shell Account | RecordTypeId.Name  |

* Flags: 

| Flags  | Meaning  |
| :---- | :---- |
| *Name\_Mismatch*  Find one match between (using fuzzy matching): shell account: Name, Ultimate\_Parent\_Account\_Name\_\_c, ZI\_Company\_Name\_\_c  customer account: Name, ZI\_Company\_Name\_\_c | Compares company name fields between customer and shell account. Calculates similarity score.  |
| *MetaData\_Mismatch* Find one match between (using fuzzy matching): shell account: Website, ZI\_Website\_\_c  customer account: Website, ZI\_Website\_\_c OR shell account: BillingStreet, BillingCity, BillingState, BillingCountry  customer account: BillingStreet, BillingCity, BillingState, BillingCountry | Evaluates website and billing address fields. Use fuzzy logic to determine semantic similarity.  |

2. Confidence Score Generation  
* Design a hybrid model using fuzzy logic, contextual analysis, and LLM prompts to evaluate relationship validity  
  * Flag verification: leverage Name\_Mismatch and MetaData\_Mismatch similarity scores   
  * Outlier detection: compare a customer account’s attributes to its sibling accounts under the same shell. Identify accounts that deviate from the dominant patterns  
  * Address relevance: semantically compare billing addresses. Identify if the child account is located in a region plausibly connected to the shell entity  
  * Field website: assign different weights to each factor   
    * Company name match \= high priority   
    * Website match \= medium priority   
    * Address match \= low priority   
  * Edge cases: use AI to normalize noisy names, determine domain affliction, evaluate overall relationship coherence across fields  
* Output a confidence score (%) for each customer account


3. Explainability   
* Clear explanation that describes:  
  * Fields matched/ mismatched  
  * Why score was assigned (should include actual calculations, just overall logic and understanding behind assignment)   
  * Signals that influenced the score   
* Transparency should help sales and operations teams trust the assessment and take action with clarity