---
trigger: model_decision
description: When structuring candidate assessment documents or formatting evaluation content
---

<assessment_structure>
## Assessment Structure 🔵

### Confluence Page Requirements

**Page Title Format:**
```
Candidate Assessment: {Last Name, First Name} - {Position} ({Jira-Ticket-ID})
```

**Required Sections:**

1. **Candidate Information Table**
   * Position
   * Interview Date
   * Interviewer(s)
   * Jira Ticket Link

2. **Executive Summary**
   * Brief overview of candidate qualifications and fit
   * Clear recommendation highlighted in panel format

3. **Evaluation Breakdown**
   * Strengths with detailed explanations
   * Gaps & Concerns with impact analysis

4. **Role Fit Summary Table**
   * Assessment by competency area
   * Standard rating symbols
   * Supporting notes

5. **Final Verdict**
   * Overall assessment and recommendation
   * Next steps with links to related tickets
   * Document metadata (creation date, author)
</assessment_structure>

<rating_standards>
## Rating Standards 🔴

### Standard Assessment Symbols

For role fit and competency assessments, use these standardized symbols:

* ✅ - Meets or exceeds requirements
* ⚠️ - Partially meets requirements / Concerns exist
* ❌ - Does not meet requirements / Critical gap

### Rating Definitions

**Technical Competencies:**
* **✅ Strong** - Demonstrates mastery and can lead others
* **⚠️ Acceptable** - Meets minimum requirements but needs development
* **❌ Insufficient** - Does not meet minimum requirements

**Behavioral Competencies:**
* **✅ Strong** - Consistently demonstrates desired behaviors
* **⚠️ Acceptable** - Shows some evidence but inconsistent
* **❌ Insufficient** - Shows contrary behaviors or significant gaps

### Required Competency Areas

All assessments must include ratings for these core competencies:
* Technical Knowledge
* Problem-Solving
* Communication
* Team Collaboration
* Adaptability
* Leadership (if applicable to role)
</rating_standards>

<privacy_requirements>
## Privacy Requirements 🟢

### Sensitive Information Handling

1. **Personally Identifiable Information (PII)**
   * Limit personal contact information in assessment documents
   * Redact sensitive details from interview transcripts
   * Use candidate ID rather than full name in shared assessments

2. **Access Controls**
   * Restrict Confluence page access to the hiring team
   * Set appropriate permissions on all assessment documentation
   * Apply the "hiring-confidential" label to all assessment pages

3. **Retention Policy**
   * Archive assessments after 1 year
   * Follow company data retention policy for documentation
   * Ensure proper document disposal procedures
</privacy_requirements>