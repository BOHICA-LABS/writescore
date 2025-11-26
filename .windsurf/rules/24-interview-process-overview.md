---
trigger: model_decision
description: When managing candidate interviews, planning interview cycles, or creating interview-related tickets
---

<purpose>
## Purpose

This rule defines the standard hierarchy, relationship structure, and implementation patterns for managing the interview process in Jira. It ensures consistent ticket organization and proper linking between interview artifacts across the workflow.
</purpose>

<process_hierarchy>
## Interview Process Hierarchy 🔵

### Three-Tier Structure

* **Hiring Campaign Epic** (top level)
  * Contains all candidate tickets for a specific role or hiring initiative.
  * Must include success criteria and hiring timeline.

* **Candidate Ticket** (middle level)
  * Parent ticket for all process steps for a specific candidate.
  * Must be linked to the Hiring Campaign Epic using the **Epic Link** field.

* **Process Step Tickets** (bottom level)
  * Child tickets of the Candidate Ticket using a Parent-Child relationship.
  * Include: Interview Preparation, Interview Execution, Review Meeting, Final Determination, HR Documentation.
</process_hierarchy>

<ticket_relationships>
## Interview Process Relationships 🔴

### Required Link Types

*   **Epic Link**: Field for connecting Candidate Tickets to the Hiring Campaign Epic.
*   **Parent-Child**: For connecting Process Step Tickets to the Candidate Ticket.
*   **Relates**: For connecting related documentation in Confluence.
*   **Blocks**: For connecting sequential process steps.

### Implementation

1.  Create the Hiring Campaign Epic.
2.  Create the Candidate Ticket and link it to the Epic using the `customfield_10014` (Epic Link) field via `mcp0_editJiraIssue`.
3.  Create Process Step Tickets as children of the Candidate Ticket using the `parent` field in `mcp0_createJiraIssue`.
4.  Link Process Step Tickets to Confluence documentation by adding a remote link in a comment with `mcp0_addCommentToJiraIssue`.
5.  Create dependencies between sequential Process Step Tickets using the `Blocks` link type via `mcp0_editJiraIssue`.
</ticket_relationships>

<implementation_basics>
## Implementation Basics 🟢

### API Integration Examples

All interview process tickets should be created and linked via the API for consistency:

```javascript
// Link a candidate ticket to a hiring campaign epic
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "CAND-456",      // The Candidate Ticket
    fields: {
        "customfield_10014": "HCMP-123"  // The Epic Link field with the Hiring Campaign Epic
    }
});

// Create a process step as a child of the candidate ticket
await mcp0_createJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    projectKey: "PROJ",
    summary: "Interview Preparation",
    issueTypeName: "Sub-task",
    description: "Prepare materials for the candidate interview.",
    additional_fields: {
        "parent": {"key": "CAND-456"}
    }
});

// Create a dependency between process steps (Execution blocks Review)
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "REVIEW-790", // The ticket that is blocked (Review Meeting)
    fields: {
        "update": {
            "issuelinks": [
                {
                    "add": {
                        "type": {
                            "name": "Blocks"
                        },
                        "inwardIssue": {
                            "key": "EXEC-789" // The ticket that is blocking (Interview Execution)
                        }
                    }
                }
            ]
        }
    }
});

// Link to Confluence documentation
await mcp0_addCommentToJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "CAND-456", // The Candidate Ticket
    commentBody: "Candidate Assessment Documentation: [https://your-confluence-instance.atlassian.net/wiki/spaces/SPACE/pages/12345]"
});
```

### Jira Markdown Format

When using the API, use standard Markdown syntax:
*   Headings: `# H1`, `## H2`, `### H3`
*   Bullet points: `*` or `-`
*   Checkboxes: `- [ ]` for unchecked, `- [x]` for checked
</implementation_basics>

<related_rules>
## Related Rules

*   [23-linking-hierarchy.md](./23-linking-hierarchy.md) - Provides detailed hierarchy and linking guidelines.
*   [25-interview-ticket-templates.md](./25-interview-ticket-templates.md) - Offers templates for each ticket type in the process.
*   [27-interview-documentation-standards.md](./27-interview-documentation-standards.md) - Outlines documentation requirements in Confluence.
*   [34-atlassian-mcp-guidelines.md](./34-atlassian-mcp-guidelines.md) - Contains MCP function guidelines used in this process.
</related_rules>
