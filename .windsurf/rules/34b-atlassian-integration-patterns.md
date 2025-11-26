---
trigger: model_decision
description: When integrating Atlassian products or implementing cross-system workflows
---

<purpose>
## Purpose

This rule provides standard patterns for creating automated, multi-step workflows that integrate Jira and Confluence. These patterns serve as blueprints for complex processes like converting support tickets into product ideas or managing incident response.
</purpose>

<integration_pattern>
## Pattern: Support Ticket to Product Idea Workflow 🟢

This pattern outlines the automated process for converting a feature request from an ISD (IT Service Desk) ticket into a `TOPM` (Product Management) `Idea` ticket.

### Workflow Steps

1.  **Trigger**: A user identifies an `ISD` ticket as a feature request.
2.  **Get ISD Ticket Details**: Fetch the content of the `ISD` ticket using `mcp0_getJiraIssue`.
3.  **Create TOPM Idea**: Create a new `Idea` ticket in the `TOPM` project using `mcp0_createJiraIssue`, summarizing the ISD request.
4.  **Add Cross-References**: Use `mcp0_addCommentToJiraIssue` to add comments to both tickets, linking them together.
5.  **Resolve ISD Ticket**: Use `mcp0_transitionJiraIssue` to transition the original `ISD` ticket to a "Resolved" status.

### Implementation Example

This example demonstrates the full, end-to-end workflow.

```javascript
// This function encapsulates the entire workflow
async function convertIsdToTopm(cloudId, isdTicketKey) {
    try {
        // 1. Get original ticket details
        const isdTicket = await mcp0_getJiraIssue({ cloudId, issueIdOrKey: isdTicketKey });
        const isdSummary = isdTicket.fields.summary;
        const isdDescription = isdTicket.fields.description;

        // 2. Create the new TOPM Idea ticket
        const topmIdea = await mcp0_createJiraIssue({
            cloudId: cloudId,
            projectKey: "TOPM",
            issueTypeName: "Idea",
            summary: `[Idea] From ISD: ${isdSummary}`,
            description: `Original request from ${isdTicketKey}:\n\n{quote}${isdDescription}{quote}`,
            additional_fields: {
                "labels": ["product-discovery", "from-isd"]
            }
        });
        console.log(`Created TOPM Idea: ${topmIdea.key}`);

        // 3. Add cross-reference comments
        await Promise.all([
            mcp0_addCommentToJiraIssue({
                cloudId: cloudId,
                issueIdOrKey: topmIdea.key,
                commentBody: `This Idea was generated from ISD ticket: ${isdTicketKey}`
            }),
            mcp0_addCommentToJiraIssue({
                cloudId: cloudId,
                issueIdOrKey: isdTicketKey,
                commentBody: `This feature request has been captured in product discovery ticket: ${topmIdea.key}`
            })
        ]);
        console.log("Added cross-reference comments.");

        // 4. Resolve the original ISD ticket
        const transitions = await mcp0_getTransitionsForJiraIssue({ cloudId, issueIdOrKey: isdTicketKey });
        const resolveTransitionId = transitions.transitions.find(t => t.name === "Resolve").id;

        await mcp0_transitionJiraIssue({
            cloudId: cloudId,
            issueIdOrKey: isdTicketKey,
            transition: { id: resolveTransitionId }
        });
        console.log(`Resolved ISD ticket ${isdTicketKey}.`);

    } catch (error) {
        console.error(`Workflow failed for ${isdTicketKey}:`, error);
    }
}
```
</integration_pattern>

<related_rules>
## Related Rules

*   [34-atlassian-mcp-guidelines.md](./34-atlassian-mcp-guidelines.md) - Core MCP tool usage.
*   [34a-atlassian-mcp-advanced.md](./34a-atlassian-mcp-advanced.md) - Advanced patterns for bulk operations.
*   [/isd-to-topm-conversion](/isd-to-topm-conversion) - The user-facing workflow definition.
</related_rules>
