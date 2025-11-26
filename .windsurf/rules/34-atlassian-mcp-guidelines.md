---
trigger: model_decision
description: When programmatically creating/updating Jira tickets, managing fields, or modifying Confluence
---

<purpose>
## Purpose

This rule provides the standard guidelines and best practices for using the Atlassian MCP toolset (`mcp0`). It covers authentication, common operations, error handling, and advanced patterns to ensure consistent and reliable integration with Jira and Confluence.
</purpose>

<core_concepts>
## Core Concepts 🔴

### Authentication and Cloud ID

Every Atlassian MCP tool call requires a `cloudId`. This ID is specific to the user's Atlassian instance and must be retrieved before making other API calls.

**Correct Usage:**
```javascript
// Get Cloud ID (zero-argument)
const resources = await mcp0_getAccessibleAtlassianResources();
const cloudId = resources[0].id;
```
*   🟠 **Warning**: Calling `mcp0_getAccessibleAtlassianResources({})` with an empty object will fail. You must provide a dummy parameter.

### User Account ID

For operations involving users (e.g., assigning tickets, mentioning users), you must use the `accountId`.

**Correct Usage:**
```javascript
// Get a user's account ID
const userSearch = await mcp0_lookupJiraAccountId({
  cloudId: "YOUR_CLOUD_ID",
  searchString: "Jared Richards" // Can be name or email
});
const accountId = userSearch.users.users[0].accountId;
```
</core_concepts>

<common_operations>
## Common Operations 🟢

### Creating a Jira Issue

Use `mcp0_createJiraIssue` for creating new tickets.

```javascript
await mcp0_createJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    projectKey: "${PRIMARY_PROJECT}",
    issueTypeName: "Story",
    summary: "New feature summary",
    description: "Detailed description of the new feature.",
    assignee_account_id: "USER_ACCOUNT_ID" // Optional: Assign the ticket
});
```

### Editing a Jira Issue (and Linking)
Note: In this Jira instance, the Epic Link field is `customfield_10014`. To link a Story to an Epic, set fields: {"customfield_10014": "EPIC-KEY"} using mcp0_editJiraIssue.


Use `mcp0_editJiraIssue` for all modifications, including creating issue links. The `update` field is additive and will not overwrite existing links.

**Example: Linking two issues**
```javascript
await mcp0_editJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "ISSUE-2", // The issue that is being blocked
    update: {
        issuelinks: [{
            add: {
                type: { name: "Blocks" },
                inwardIssue:  { key: "ISSUE-2" }, // blocked
                outwardIssue: { key: "ISSUE-1" }  // blocking
            }
        }]
    }
});
```
*   🟠 **Deprecated**: The `mcp0_createJiraIssueLink` tool is deprecated and **MUST NOT** be used.

### Adding a Comment

Use `mcp0_addCommentToJiraIssue`. For user mentions, use the `[~accountId]` format.

```javascript
// Add a comment and mention a user
await mcp0_addCommentToJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "${PRIMARY_PROJECT}-123",
    commentBody: "FYI [~557058:...] this has been updated."
});
```
*   See [34-jira-markdown-reference.md](./34-jira-markdown-reference.md) for more formatting details.

### Transitioning an Issue

First, get available transitions, then perform the transition.

```javascript
// Step 1: Get available transitions
const transitions = await mcp0_getTransitionsForJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "${PRIMARY_PROJECT}-123"
});
const doneTransitionId = transitions.transitions.find(t => t.name === "Done").id;

// Step 2: Perform the transition
await mcp0_transitionJiraIssue({
    cloudId: "YOUR_CLOUD_ID",
    issueIdOrKey: "${PRIMARY_PROJECT}-123",
    transition: {
        id: doneTransitionId
    }
});
```
</common_operations>

<error_handling>
## Error Handling 🔵

Always wrap MCP calls in `try...catch` blocks to handle potential API errors gracefully.

```javascript
try {
    const result = await mcp0_createJiraIssue({ /* ...params */ });
    console.log("Issue created:", result.key);
} catch (error) {
    console.error("Failed to create Jira issue:", error);
    // Implement retry logic or user notification
}
```
</error_handling>

<related_rules>
## Related Rules
*   [34a-atlassian-mcp-advanced.md](./34a-atlassian-mcp-advanced.md) - Advanced patterns and bulk operations.
*   [34b-atlassian-integration-patterns.md](./34b-atlassian-integration-patterns.md) - Cross-system workflow examples.
*   [34-jira-markdown-reference.md](./34-jira-markdown-reference.md) - Guide to Jira's markdown syntax.
</related_rules>
