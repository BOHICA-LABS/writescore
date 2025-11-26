---
trigger: model_decision
description: When creating programmatic relationships between Jira tickets using API methods
---

<epic_story_linking>
## Epic-Story Linking 🔴

To link a Story to an Epic in Jira, use the `mcp0_editJiraIssue` tool with the epicLink field:

```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",       // Your Atlassian Cloud ID
    issueIdOrKey: "STORY-123",      // The key of the story to link
    fields: {
        "customfield_10014": "EPIC-456"  // The epic link field with the epic key
    }
});
```

This creates a **"belongs to"** relationship between the Story and Epic.
In this Jira instance, the Epic Link custom field is `customfield_10014`.

</epic_story_linking>

<parent_child_linking>
## Creating Issues with Parent References 🔵

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
</parent_child_linking>

<general_issue_linking>
## Creating Issue Links 🔵

Create links using `mcp0_editJiraIssue` with the `update.issuelinks.add` pattern.

Relates:
```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "ISSUE-123",
    update: {
        issuelinks: [
            {
                add: {
                    type: { name: "Relates" },
                    inwardIssue:  { key: "ISSUE-123" },
                    outwardIssue: { key: "ISSUE-456" }
                }
            }
        ]
    }
});
```

Blocks (ISSUE-123 is blocked by ISSUE-456):
```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "ISSUE-123",
    update: {
        issuelinks: [
            {
                add: {
                    type: { name: "Blocks" },
                    inwardIssue:  { key: "ISSUE-123" },   // blocked
                    outwardIssue: { key: "ISSUE-456" }    // blocking
                }
            }
        ]
    }
});
```
</general_issue_linking>


<product_discovery_linking>
## Product Discovery Linking 🔵

For linking **Idea** tickets to implementation work, use the `"Polaris issue link"` type with `update.issuelinks.add`:

```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "TOPM-123",           // The Idea ticket (inward)
    update: {
        issuelinks: [
            {
                add: {
                    type: { name: "Polaris issue link" },
                    inwardIssue:  { key: "TOPM-123" },    // Idea
                    outwardIssue: { key: "MSSCI-456" }    // Implementation Epic
                }
            }
        ]
    }
});
```

This creates an **"is implemented by"/"implements"** relationship.
</product_discovery_linking>


<best_practices>
## Best Practices for Ticket Linking 🔵

1. **Always verify Cloud ID** before making any Jira API calls:
   ```javascript
   const resources = await mcp0_getAccessibleAtlassianResources({});
   const cloudId = resources[0].id;  // Use the appropriate cloud ID
   ```

2. **Store Cloud ID** in a variable to avoid redundant API calls:
   ```javascript
   const cloudId = "934c63a0-0b96-4d46-b906-0f8c1c85c5d7";  // Example ID
   ```

3. **Check available link types** if you're unsure which one to use:
   ```javascript
   const linkTypes = await mcp0_getJiraIssueLinkTypes({
       cloudId: cloudId
   });
   ```

4. **Error handling** for link creation:
   ```javascript
   try {
