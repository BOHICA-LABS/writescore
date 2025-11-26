---
trigger: model_decision
description: When creating or updating risk register items or documenting project risk factors
---

<risk_creation>
## When to Create Risk Items 🔵

Create a *Risk* ticket when:
* Identifying potential threats to project delivery
* Documenting compliance or security concerns
* Capturing external dependencies that may impact timelines
* Noting potential budget or resource constraints
* Identifying technical limitations or challenges
* Documenting hiring process challenges or compliance risks
</risk_creation>

<risk_structure>
## Risk Ticket Structure 🔴

**Summary Format:**
```
[Risk] {risk description} - {affected area}
```

**Description Template:**

### Risk Description
{Clear statement of the risk}

### Impact Assessment
* Likelihood: {Low/Medium/High}
* Impact: {Low/Medium/High}
* Overall Risk Rating: {Low/Medium/High}

### Mitigation Strategy
{How this risk will be addressed or mitigated}

### Contingency Plan
{What to do if the risk materializes}

**Required Fields:**
* Project: `$RISK_REGISTER_PROJECT`
* Priority (based on Risk Rating)
* Components: relevant components from `$DEFAULT_COMPONENTS`
* Labels: Include values from `$DEFAULT_LABELS` + `"risk-register"`
* Epic Link (if risk is related to specific initiative)
* Issue Type: `Idea`
</risk_structure>

<risk_workflow>
## Risk Status Workflow ⚪

* **Identified**: Initial state when risk is documented
* **Analyzed**: Impact and mitigation plans have been defined
* **Monitored**: Risk is being actively tracked
* **Mitigated**: Actions have been taken to reduce the risk
* **Closed**: Risk is no longer relevant or has been fully addressed
* **Occurred**: Risk has materialized and contingency plan is in effect
</workflow>
