---
trigger: model_decision
description: When formatting content specifically for Jira comment fields or descriptions
---

<atlassian_mcp_jira_markdown>
## Atlassian MCP Jira Markdown 🔵

When creating or updating Jira tickets using the Atlassian MCP, use GitHub-flavored Markdown (GFM). Jira will automatically convert this Markdown to ADF (Atlassian Document Format) on save.

Important constraints:

* Do not use Jira wiki markup (e.g., `h1.`, `[text|URL]`, `{code}`, `{noformat}`, `{panel}`, `{expand}`, `{color}`) in API updates—these will not render reliably.
* The MCP Jira edit tool does not accept raw ADF payloads; it converts Markdown to ADF internally. If you must set ADF directly, use the Jira REST API outside MCP.
* Rendering can differ between the list preview and full issue view. Verify in the full issue view.

### User Mentions 🔴

To mention a user in a comment or description, you **MUST** use their `accountId` in the following format. You can retrieve the `accountId` using the `mcp0_lookupJiraAccountId` tool.

```markdown
[~557058:...]
[~accountId]
```
*   **Note**: Other formats like `@username` are **not supported** via the API.

### Headers

```markdown
# Heading Level 1
## Heading Level 2
### Heading Level 3
```

### Text Formatting

```markdown
**Bold text**
_Italic text_
~~Strikethrough text~~
`Inline code`
```

### Lists

#### Bulleted Lists
```markdown
* Item 1
* Item 2
  * Nested item 2.1
  * Nested item 2.2
* Item 3
```

#### Numbered Lists
```markdown
1. First item
2. Second item
   1. Nested item 2.1
   2. Nested item 2.2
3. Third item
```

### Code Blocks

````markdown
```java
public class Example {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
```
````

### Blockquotes

```markdown
> This is a blockquote
> 
> It can span multiple paragraphs
```

### Links

```markdown
[Link text](https://example.com)
```

### Tables

```markdown
| Header 1 | Header 2 |
|----------|----------|
| Cell 1   | Cell 2   |
| Cell 3   | Cell 4   |
```

### Task Lists

```markdown
- [ ] Unchecked task
- [x] Checked task
```

### Images

```markdown
![Alt text](https://example.com/image.jpg)
```

### Line Breaks and Spacing

```markdown
Paragraph 1

Paragraph 2 (blank line between blocks)

Line with manual break  
continues on next line (two spaces before newline)
```

Notes:

* Put a blank line between headings, lists, paragraphs, and code blocks.
* For multi-line blockquotes, prefix every line with `>`; use `>` on an empty line to separate paragraphs inside a quote.

### Verification (API)

After updating, fetch the issue with `expand=renderedFields` to confirm the UI rendering matches expectations. Prioritize checking:

* Headers (H1/H2/H3) appear as headings
* Links render as anchors
* Lists and code blocks are properly formatted

## Not Supported

These elements from traditional Jira wiki markup do not work with the Atlassian MCP Markdown-to-ADF flow (or are inconsistent). Use the listed alternatives.

* Headings like `h1.`, `h2.`, `h3.` → Use `#`, `##`, `###`
* Links like `[text|URL]` → Use `[text](URL)`
* Code macros `{code}`, `{noformat}` → Use fenced code blocks ```
* Quote macro `bq. ` → Use `>` blockquotes
* Panels `{info}`, `{note}`, `{warning}` → Use blockquotes with bolded lead-in
  * Example: `> **Info**: Important note`
* Expand `{expand}` → Not supported; simulate with a normal section
* Color `{color:red}text{color}` → Not supported; use emphasis instead
* Wiki tables `|| header ||` syntax → Use Markdown tables
* Raw HTML → Avoid; may be sanitized or ignored

Task list caveat:

* `- [ ]` and `- [x]` render as checkboxes, but are not interactive checklist items. Treat them as visual markers only unless edited in Jira’s rich editor.

ADF note:

* The MCP tool cannot set raw ADF. If pure ADF is required, use Jira REST API with an authenticated request to send a `fields.description` ADF JSON document. Maintain a Markdown backup for rollback.

### Best Practices

* Prefer simple bullets over deeply nested lists for consistent rendering.
* Use fenced code blocks for audit footers and technical snippets.
* Avoid trailing spaces inside backticks; keep code fences tight.
* Always include “Last Updated: YYYY-MM-DDThh:mm:ss-05:00 (America/Chicago)” in status docs.
* For mentions, use `[~accountId]`. Plain `@username` does not work via API.
* Verify in the full issue view, not only the list/preview pane.

</atlassian_mcp_jira_markdown>
