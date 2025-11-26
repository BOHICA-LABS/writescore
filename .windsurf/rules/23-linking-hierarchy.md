---
trigger: model_decision
description: When establishing relationships between Jira tickets or creating hierarchical work structures
---

<purpose>
## Purpose

This rule defines the standard relationship types and hierarchy patterns for Jira tickets and their associated documentation. It ensures consistent linking practices across all projects and provides the foundation for process-specific linking patterns.
</purpose>

<rule_definition>
## Core Relationship Principles

All work item relationships must adhere to these standard patterns:

### Ticket Hierarchies

*   Epics must contain at least one Story.
*   Stories should be linked to their Epic using the **Epic Link** field (`customfield_10014`).
*   Tasks may be standalone or subtasks of Stories.
*   Bugs should be linked to affected Stories when applicable.

### Link Types

*   **Epic Link**: Connect Stories to Epics via the Epic Link field.
*   **Relates to**: General relationships between related items.
*   **Blocks**: Dependency relationships (blocks/is blocked by).
*   **Parent-Child**: Hierarchical parent-child relationships.
*   **Implements**: Implementation relationships for product discovery.
*   **Risk mitigation**: Risk management relationships.
</rule_definition>

<implementation_examples>
## Implementation Examples

### Epic-Story Linking 🔴

To link a Story to an Epic in Jira, use the `mcp0_editJiraIssue` tool with the `customfield_10014` (Epic Link) field:

```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",       // Your Atlassian Cloud ID
    issueIdOrKey: "STORY-123",      // The key of the story to link
    fields: {
        "customfield_10014": "EPIC-456"  // The epic link field with the epic key
    }
});
```

### Creating Subtasks with Parent References 🔵

When creating a Subtask with a parent reference, use the `mcp0_createJiraIssue` tool with the `parent` field:

```javascript
await mcp0_createJiraIssue({
    cloudId: "YOUR_CLOUD_ID",       // Your Atlassian Cloud ID
    projectKey: "PROJ",
    summary: "Subtask Title",
    issueTypeName: "Sub-task",
    description: "Subtask description",
    additional_fields: {
        "parent": {"key": "STORY-123"}
    }
});
```

### General Issue Linking (e.g., Relates, Blocks) 🔵

For all other link types, use `mcp0_editJiraIssue` to add a link. This is an **additive** operation.

**Relates Example:**
```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "ISSUE-123", // The issue to add the link to
    fields: {
        "update": {
            "issuelinks": [
                {
                    "add": {
                        "type": {
                            "name": "Relates"
                        },
                        "outwardIssue": {
                            "key": "ISSUE-456"
                        }
                    }
                }
            ]
        }
    }
});
```

**Blocks Example:**
```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "BLOCKED-123", // The issue that is blocked
    fields: {
        "update": {
            "issuelinks": [
                {
                    "add": {
                        "type": {
                            "name": "Blocks"
                        },
                        "outwardIssue": {
                            "key": "BLOCKER-456" // The issue that is blocking
                        }
                    }
                }
            ]
        }
    }
});
```
</implementation_examples>

<documentation_integration>
## Documentation Integration

### Confluence Integration Requirements

*   Create Confluence pages for all Epics in `$PRIMARY_SPACE`.
*   Link Jira issues to their related documentation pages using remote issue links.
*   Document technical designs in the secondary space from `$CONFLUENCE_SPACES`.
*   Always include issue keys in Confluence page titles for traceability.
*   Link all documentation to relevant tickets using bidirectional relationships.
</documentation_integration>

<specialized_patterns>
## Specialized Relationship Patterns

### Process-Based Relationships

For multi-step processes (e.g., interview workflows, incident response), use these patterns:

1.  **Initiative Epic** (top level)
2.  **Process Instance Ticket** (e.g., Candidate Ticket)
3.  **Process Step Subtasks** (e.g., Interview Execution)

### Product Discovery Linking 🔵

This pattern governs the relationship between feature requests, product discovery, and implementation tickets.

1.  **ISD Feature Request to TOPM Idea**: When a feature request from the `ISD` project is promoted to product discovery, it must be linked to a new `Idea` ticket in the `${PRODUCT_DISCOVERY_PROJECT}` project.
    *   **Link Type**: `Relates to`
    *   **Direction**: The `ISD` ticket "Relates to" the `${PRODUCT_DISCOVERY_PROJECT}` ticket.

2.  **TOPM Idea to Implementation Epic**: When an `Idea` is approved for implementation, it must be linked to a new `Epic` in an implementation project (e.g., `${PRIMARY_PROJECT}`).
    *   **Link Type**: `Implements`
    *   **Direction**: The `Epic` "Implements" the `${PRODUCT_DISCOVERY_PROJECT}` `Idea`.

**Example: Linking ISD to TOPM**
```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "ISD-123", // The source feature request
    fields: {
        "update": {
            "issuelinks": [
                {
                    "add": {
                        "type": {
                            "name": "Relates"
                        },
                        "outwardIssue": {
                            "key": "${PRODUCT_DISCOVERY_PROJECT}-456" // The new Idea ticket
                        }
                    }
                }
            ]
        }
    }
});
```

**Example: Linking Epic to TOPM**
```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "${PRIMARY_PROJECT}-789", // The new implementation Epic
    fields: {
        "update": {
            "issuelinks": [
                {
                    "add": {
                        "type": {
                            "name": "Implements"
                        },
                        "inwardIssue": { // Note: 'inwardIssue' because the Epic implements the Idea
                            "key": "${PRODUCT_DISCOVERY_PROJECT}-456"
                        }
                    }
                }
            ]
        }
    }
});
```
</specialized_patterns>
