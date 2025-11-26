---
trigger: model_decision
description: When creating Idea tickets or transitioning product discovery items to implementation work
---

<purpose>
## Purpose

This rule defines the process for managing product discovery, from creating `Idea` tickets in the `${PRODUCT_DISCOVERY_PROJECT}` project to transitioning them into actionable `Epic` tickets in implementation projects like `${PRIMARY_PROJECT}`.
</purpose>

<rule_definition>
## Product Discovery Workflow 🔴

1.  **Create Idea**: All new concepts must be created as an `Idea` issue type in the `${PRODUCT_DISCOVERY_PROJECT}` project.
2.  **Transition to Implementation**: Once an `Idea` is approved, an `Epic` must be created in the relevant implementation project (e.g., `${PRIMARY_PROJECT}`).
3.  **Link Tickets**: The `Epic` must be linked back to the original `Idea` ticket using the **Implements** link type.

### Linking `Idea` to `Epic`

This is the most critical step. The implementation `Epic` (e.g., `${PRIMARY_PROJECT}-123`) **implements** the product `Idea` (e.g., `${PRODUCT_DISCOVERY_PROJECT}-456`). The link should be added to the `Epic` and point to the `Idea`.
</rule_definition>

<implementation_example>
## Implementation Example 🟢

Use `mcp0_editJiraIssue` to add the `Implements` link to the implementation Epic.

```javascript
// Link an implementation Epic back to the source Idea ticket
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "${PRIMARY_PROJECT}-123", // The implementation Epic
    fields: {
        "update": {
            "issuelinks": [
                {
                    "add": {
                        "type": {
                            "name": "Implements"
                        },
                        "inwardIssue": {
                            "key": "${PRODUCT_DISCOVERY_PROJECT}-456" // The product discovery Idea ticket
                        }
                    }
                }
            ]
        }
    }
});
```

### Implementation Notes

*   The `inwardIssue` field establishes that `${PRIMARY_PROJECT}-123` implements `${PRODUCT_DISCOVERY_PROJECT}-456`.
*   This link provides clear traceability from development work back to the original product concept.
</implementation_example>

<related_rules>
## Related Rules

*   [23-linking-hierarchy.md](./23-linking-hierarchy.md) - General issue linking standards.
*   [/isd-to-topm-conversion](/isd-to-topm-conversion) - Workflow for converting support tickets to product ideas.
</related_rules>
