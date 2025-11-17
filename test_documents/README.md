# Test Documents for Compliance Checker

This directory contains sample policy documents with intentional compliance issues for testing the Policy Compliance Checker system.

## Sample Documents

### 1. `sample_privacy_policy.txt`
**Type:** Data Privacy Policy  
**Regulations to Check:** GDPR  
**Expected Issues:**
- Missing explicit consent mechanisms
- Data stored outside EU without adequate safeguards
- Insufficient data subject rights (long response times, no deletion process)
- Inadequate data breach notification timing (60 days instead of 72 hours)
- Indefinite data retention
- No data protection officer mentioned
- Sharing data with third parties without proper basis

**Key GDPR Violations:**
- Article 6: Lawful basis for processing not clearly established
- Article 13/14: Inadequate privacy notices
- Article 15: Access rights not properly implemented
- Article 17: Right to erasure not provided
- Article 32: Insufficient security measures
- Article 33: Data breach notification timing non-compliant
- Article 44-49: International transfers without safeguards

### 2. `sample_ai_usage_policy.txt`
**Type:** AI Usage Policy  
**Regulations to Check:** AI Act, GDPR  
**Expected Issues:**
- High-risk AI systems without conformity assessments
- Fully automated decision-making without human oversight
- No transparency requirements for AI decisions
- No bias audits or discrimination monitoring
- Use of prohibited AI practices (social scoring)
- Missing documentation and logging requirements
- No human oversight for high-risk systems

**Key AI Act Violations:**
- Article 6: High-risk AI systems not properly classified
- Article 8: No conformity assessment for high-risk systems
- Article 13: Transparency requirements not met
- Article 14: Human oversight missing for automated decisions
- Article 29: Prohibited practices (social scoring in employment context)
- Article 71: Registration requirements not fulfilled

**GDPR Violations:**
- Article 22: Automated decision-making without safeguards
- Article 13: Lack of information about automated processing

### 3. `sample_cybersecurity_policy.txt`
**Type:** Cybersecurity Policy  
**Regulations to Check:** NIS2, GDPR  
**Expected Issues:**
- Insufficient incident detection and response capabilities
- Inadequate incident notification procedures
- Weak security measures (short passwords, no MFA)
- No supply chain security assessments
- Missing business continuity planning
- Inadequate vulnerability management
- No penetration testing
- Insufficient security training

**Key NIS2 Violations:**
- Article 7: Risk management measures insufficient
- Article 14: Incident notification requirements not met (timing, content)
- Article 21: Supply chain security not addressed
- Article 23: Security measures for network and information systems inadequate
- Article 24: Incident handling requirements not fulfilled
- Article 25: Business continuity management missing

**GDPR Violations:**
- Article 32: Technical and organizational security measures insufficient
- Article 33/34: Data breach notification procedures non-compliant

## Usage

### Via Streamlit Interface
1. Open Streamlit app: `streamlit run streamlit_app.py`
2. Upload any of these documents
3. Select relevant regulations (GDPR, AI Act, NIS2) for comparison
4. Run compliance analysis
5. Review identified discrepancies and citations
6. Download the generated compliance report

### Via API
1. Start API: `python api/main.py`
2. Upload document: `POST /api/documents/upload`
3. Run analysis: `POST /api/comparison/analyze`
4. Get results: `GET /api/comparison/{id}`
5. Download report: `GET /api/reports/{id}/pdf`

### Via Test Runner Script
Run all tests automatically:
```bash
python test_documents/test_runner.py
```
This will test all sample documents and generate a summary report.

## Expected Test Results

Each document should generate:
- Compliance scores below 60/100 (indicating significant issues)
- Multiple discrepancies with cited regulation articles
- Specific article citations (e.g., "GDPR Article 6", "AI Act Article 8")
- Severity classifications (critical, high, medium, low)
- Actionable recommendations in the report

## Creating Additional Test Documents

To create new test documents:
1. Model after these samples
2. Include intentional compliance gaps
3. Reference specific regulation articles in comments (for validation)
4. Save as `.txt`, `.pdf`, or `.docx` format
5. Test with the compliance checker

## Notes

- These documents are intentionally non-compliant for testing purposes
- In production, policies should comply with all relevant regulations
- Use these documents to validate the compliance checker's ability to identify issues
