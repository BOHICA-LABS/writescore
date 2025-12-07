---
trigger: model_decision
description: When implementing complex Atlassian API patterns not covered in the main guidelines
---

<purpose>
## Purpose

This rule provides guidelines for advanced Atlassian MCP tool usage, including bulk operations, complex data manipulation, and sophisticated error handling. It builds upon the foundational knowledge in `34-atlassian-mcp-guidelines.md`.
</purpose>

<advanced_patterns>
## Advanced Patterns 🔵

### Bulk Issue Creation

To create multiple issues efficiently, loop through a data array and call `mcp0_createJiraIssue` for each item. Use `Promise.all` to run operations in parallel for better performance.

```javascript
const issuesToCreate = [
    { summary: "Task 1", description: "First task" },
    { summary: "Task 2", description: "Second task" }
];

const creationPromises = issuesToCreate.map(issue => {
    return mcp0_createJiraIssue({
        cloudId: "YOUR_CLOUD_ID",
        projectKey: "${PRIMARY_PROJECT}",
        issueTypeName: "Task",
        summary: issue.summary,
        description: issue.description
    });
});

try {
    const results = await Promise.all(creationPromises);
    console.log("Successfully created issues:", results.map(r => r.key));
} catch (error) {
    console.error("One or more issue creations failed:", error);
}
```

### Chaining API Calls

Chain API calls when one operation depends on the result of another. Always use `await` to ensure sequential execution.

```javascript
// Example: Create an issue, then immediately add a comment
async function createAndComment(cloudId, accountId) {
    try {
        const newIssue = await mcp0_createJiraIssue({
            cloudId: cloudId,
            projectKey: "PROJ",
            summary: "A new issue that needs a comment",
            issueTypeName: "Task"
        });

        await mcp0_addCommentToJiraIssue({
            cloudId: cloudId,
            issueIdOrKey: newIssue.key,
            commentBody: `This is the first comment, FYI [~${accountId}]`
        });

        console.log(`Successfully created ${newIssue.key} and added a comment.`);
    } catch (error) {
        console.error("Chained operation failed:", error);
    }
}
```

### Updating Custom Fields
Note: For Epic-Story linking, set fields: {"customfield_10014": "EPIC-KEY"}. In this Jira instance, the Epic Link field is `customfield_10014`.


Use `mcp0_editJiraIssue` to update any custom field by its ID.

```javascript
// Example: Update a custom text field and a select list
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "${PRIMARY_PROJECT}-456",
    fields: {
        "customfield_10020": "New text value", // A text field
        "customfield_10021": { "value": "Option B" } // A select list field
    }
});
```
</advanced_patterns>

<error_handling>
## Advanced Error Handling 🔴

When performing bulk operations, it's critical to handle partial failures where some API calls succeed and others fail.

```javascript
// Using Promise.allSettled to handle partial failures in bulk linking
const linkPromises = issueKeys.map(key =>
  mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: key,
    update: {
      issuelinks: [{
        add: {
          type: { name: "Relates" },
          inwardIssue:  { key },
          outwardIssue: { key: "TARGET-123" }
        }
      }]
    }
  })
);

const results = await Promise.allSettled(linkPromises);
const successes = results.filter(r => r.status === "fulfilled");
const failures  = results.filter(r => r.status === "rejected");
console.log(`Linked: ${successes.length}, Failed: ${failures.length}`);
```
