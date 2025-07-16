## **Project 1– ZoomInfo Quality Assessment**

### **What is ZoomInfo?** 

* B2B data provider. They collect and maintain a large database of:   
  * Companies   
  * Contacts  
  * Technographic data (what tools a company uses)   
  * Buying intent signals   
  * Etc.  
* Used by sales, marketing, and recruiting teams to support:   
  * Outreach \+ targeting   
  * Personalization of messaging   
  * Lead prioritization  
* Streamlines data enrichment– process of taking a basic record (company name or email) → supplementing it with detailed information to make it more useful; ultimately helping sales reps reach the right people with the right context 

### **Problem Statement**

* The RC Marketing and Sales Department is uncertain about the reliability/ accuracy of data   
* Outdated, incomplete, incorrect information → low quality records potentially leading sales reps to waste time or make poor outreach decisions 

### **Solution**

* Conduct a quality assessment of ZoomInfo’s output by developing an AI driven confidence rating system for enriched records– paired with explanations to ensure transparency and actionability   
* Steps:    
1. Collect ZoomInfo-Enriched Records  
* Columns to query: 

| SFDC Column | Query ID  |
| :---- | :---- |
| *Demand Funnel : Lead : Lead ID* | Id |
| *Demand Funnel : Lead : Email (input information for enrichment)*  | Email |
| *RTLM Channel* | FIrst\_Channel\_\_c  |
| *Segment Name* | SegmentName\_\_r.Name |
| *Demand Funnel : Lead : Website*  | Website |
| *Demand Funnel : Lead : Company* | Company  |
| *Demand Funnel : Lead : No. of Employees*  | LS\_Company\_Size\_Range\_\_c |
| *Demand Funnel : Lead : ZI Website (enriched)* | ZI\_Website\_\_c |
| *Demand Funnel : Lead : Account Name (enriched)*  | ZI\_Company\_Name\_\_c |
| *Demand Funnel : Lead : ZI Employees (enriched)*  | ZI\_Employees\_\_c |

* Flags to look out for: 

| Flags | Meaning  |
| :---- | :---- |
| not\_in\_TAM ZI\_Employees\_\_c \> 100 but ZI\_Company\_Name\_\_c NOT Populated | Accounts in the RC TAM (total addressable market) base include all accounts with 100+ employees This account should be enriched with an account name or is being incorrectly enriched for employee number |
| suspicious\_enrichment Email has free email domain and Website NOT POPULATED and ZI\_Company\_Name\_\_c POPULATED and ZI\_Employees\_\_c \> 100 | Why are accounts with ambiguous email domains and no websites being enriched with an Account name (company) and other ZI data?  |

2. Verify Data Accuracy \+ Information Discovery    
* Inspect Website and ZI\_Employees\_\_c  
  * Try to populate ZI\_Company\_Name\_\_c for RC TAM base  
* Inspect Email  
  * If there is additional information (company name) in email domain → use to infer Website and ZI\_Company\_Name\_\_c  
  * Try to populate other fields using inferred information   
* Cross check each record with sources  
  * Public databases (LinkedIn, etc.), internal CRM or sales data  
  * Does the Email match the enriched data? 

    

3. Build a Confidence Model   
* Design either a rule based system, ML model, or prompt to LLM to:   
  * Assess freshness of data  
  * Compared against other trusted sources   
  * Evaluate internal consistency   
  * Incorporate outcome history, if applicable  
* Output a confidence score (%) for each record or data point   
4. Explainability   
* Provide clear and concise explanations for why a particular confidence level was assigned  
* Explanation layer should help build trust in the system and enable sales or operation teams to take actions accordingly  
* A correction for incorrect fields