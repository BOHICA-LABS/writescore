---
trigger: model_decision
description: When creating assessment documents, documenting evaluations, or generating interview summaries
---

<purpose>
## Purpose

This rule establishes standards for creating and maintaining candidate assessment documentation in Confluence to ensure consistency, compliance, and proper integration with the interview process workflow in Jira.
</purpose>

<compliance_requirements>
## Compliance Requirements 🔴

### Equal Employment Opportunity

*   Focus assessments on job-relevant competencies only.
*   Avoid comments on protected characteristics.
*   Document objective evidence for all ratings.

### Documentation Standards

*   Maintain a consistent rating system across all candidates.
*   Document all assessment criteria used.
*   Store assessments in approved, access-controlled locations only.
</compliance_requirements>

<document_structure>
## Required Document Structure 🔴

### Assessment Page Structure

All candidate assessment documents must include:

1.  **Title & Header**: "Candidate Assessment: [Name] - [Position] ([Ticket-ID])"
2.  **Campaign Reference**: Link to the hiring campaign Epic.
3.  **Candidate Information Table**: Position, date, interviewer, ticket.
4.  **Executive Summary**: Brief overview with a clear recommendation.
5.  **Evaluation Breakdown**: Strengths and gaps with specific examples.
6.  **Role Fit Table**: Competency areas with standardized ratings.
7.  **Final Verdict**: Clear recommendation with justification.

### Standard Rating Symbols

*   ✅ - Meets or exceeds requirements
*   ⚠️ - Partially meets requirements / Concerns exist
*   ❌ - Does not meet requirements / Critical gap
</document_structure>

<implementation>
## Implementation Guidelines 🔵

### Creating and Linking Assessment Pages

```javascript
// Step 1: Create the assessment page in Confluence
const pageResult = await mcp0_createConfluencePage({
    cloudId: "YOUR_CLOUD_ID",
    spaceId: "$PRIMARY_SPACE", // Use environment variable for the space
    title: "Candidate Assessment: Smith, John - Senior Developer (${PRIMARY_PROJECT}-1234)",
    body: "# Candidate Assessment: Smith, John...", // Full markdown content
    parentId: "PARENT_PAGE_ID" // ID of the hiring campaign documentation page
});

// Step 2: Link the new Confluence page back to the Jira ticket
const confluencePageUrl = pageResult.url; // Assuming the tool returns the URL
await mcp0_addCommentToJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "${PRIMARY_PROJECT}-1234", // The candidate's Jira ticket
    commentBody: `Assessment documentation for this candidate can be found here: ${confluencePageUrl}`
});
```

Place assessment pages in the `$PRIMARY_SPACE` with the hiring campaign documentation as the parent page. Use standardized page restrictions to limit visibility to the hiring team.
</implementation>

<best_practices>
## Best Practices 🟢

1.  **Objective Assessment**: Use specific, measurable examples for all ratings.
2.  **Consistent Evaluation**: Apply a standardized rating system uniformly.
3.  **Privacy Protection**: Restrict page access to the hiring team only.
4.  **Documentation Integrity**: Link all related Jira tickets for traceability.
</best_practices>

<related_rules>
## Related Rules

*   [24-interview-process-overview.md](./24-interview-process-overview.md) - Interview process workflow
*   [25-interview-ticket-templates.md](./25-interview-ticket-templates.md) - Jira ticket templates
*   [26-interview-assessment-structure.md](./26-interview-assessment-structure.md) - Assessment criteria
*   [23-linking-hierarchy.md](./23-linking-hierarchy.md) - Ticket relationship patterns
*   [34-atlassian-mcp-guidelines.md](./34-atlassian-mcp-guidelines.md) - MCP integration guidelines
</related_rules>
