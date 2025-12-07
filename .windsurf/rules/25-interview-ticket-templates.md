---
trigger: model_decision
description: When creating tickets for specific interview process stages or candidate tracking
---

<hiring_campaign_epic>
## Hiring Campaign Epic Structure 🔵

**Summary Format:**
```
[Epic] Hiring Campaign: {Role} - {Quarter/Year}
```

**Description Template:**

### Overview
{Description of the hiring initiative and its purpose}

### Business Need
{Why this role is needed and how it aligns with strategic goals}

### Success Criteria
{Specific metrics to determine campaign success}

**Required Fields:**
* Epic Name: "{Role} Hiring Campaign"
* Labels: Include values from `$DEFAULT_LABELS` + `"hiring-campaign"`
</hiring_campaign_epic>

<candidate_ticket>
## Candidate Ticket Structure 🔴

**Summary Format:**
```
Candidate: {Last Name, First Name} - {Position}
```

**Description Template:**

### Candidate Information
* Full Name: {First Name Last Name}
* Contact: {Email} | {Phone}
* Position: {Position applied for}
* Source: {Where/how the candidate was sourced}

### Resume Analysis
* Key Qualifications: {Bullet points}
* Experience: {Years and relevant experience}
* Education: {Highest degree, institution}
* Skills Match: {High/Medium/Low assessment}

**Required Fields:**
* Epic Link: {Link to Hiring Campaign Epic}
* Labels: Include values from `$DEFAULT_LABELS` + `"candidate"`
* Issue Type: `Candidate`
</candidate_ticket>

<process_tickets>
## Process Step Tickets 🔴

### 1. Interview Preparation Ticket

**Summary Format:**
```
Interview Preparation: {Last Name, First Name} - {Position}
```

**Description Template:**

### Task Description
{Clear description of the preparation tasks}

### Deliverables
* [ ] Resume processing completed
* [ ] Pre-interview assessment document created
* [ ] Interview questions prepared

**Required Fields:**
* Parent Issue: {Link to Candidate Ticket}
* Issue Type: `Sub-task`

### 2. Interview Execution Ticket

**Summary Format:**
```
Interview Execution: {Last Name, First Name} - {Position}
```

**Description Template:**

### Task Description
Conduct interview with {Candidate Name} following the standardized interview process.

### Deliverables
* [ ] Interview completed
* [ ] Notes documented
* [ ] Assessment submitted

**Required Fields:**
* Parent Issue: {Link to Candidate Ticket}
* Issue Type: `Sub-task`

### 3. Candidate Review Meeting Ticket

**Summary Format:**
```
Review Meeting: {Last Name, First Name} - {Position}
```

**Description Template:**

### Task Description
Hold review meeting to discuss interview outcomes and determine next steps for candidate.

### Deliverables
* [ ] Meeting completed
* [ ] All interviewer assessments reviewed
* [ ] Decision documented

**Required Fields:**
* Parent Issue: {Link to Candidate Ticket}
* Issue Type: `Sub-task`
</process_tickets>

<final_tickets>
## Final Process Tickets 🔵

### 4. Final Determination Ticket

**Summary Format:**
```
Final Determination: {Last Name, First Name} - {Position}
```

**Description Template:**

### Task Description
Document final hiring decision for candidate and communicate outcome.

### Deliverables
* [ ] Decision finalized
* [ ] Confluence assessment documentation completed
* [ ] Candidate notification prepared

**Required Fields:**
* Parent Issue: {Link to Candidate Ticket}
* Issue Type: `Sub-task`

### 5. HR Documentation Ticket

**Summary Format:**
```
HR Documentation: {Last Name, First Name} - {Position}
```

**Description Template:**

### Task Description
Complete all required HR documentation for candidate decision.

### Deliverables
* [ ] HR recommendation report completed
* [ ] All assessments properly stored
* [ ] Required compliance documentation completed

**Required Fields:**
* Parent Issue: {Link to Candidate Ticket}
* Issue Type: `Sub-task`
</final_tickets>
