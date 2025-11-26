---
trigger: model_decision
description: When creating or editing Confluence pages requiring specific formatting standards
---

<general_principles>
## General Principles 🔵

1. Use **traditional markdown** for creating Confluence pages via API
2. Format content for maximum readability and consistent structure
3. Include proper links to related Jira tickets and other documentation
4. Follow 1898 & Co. branding and style guidelines
</general_principles>

<required_elements>
## Required Page Elements 🔴

### Metadata

Every Confluence page MUST include:

* Clear descriptive title including relevant Jira ticket numbers
* Author information
* Creation and last updated dates
* Space classification (e.g., MSS, DEV, DOCS)
* Related content links (Jira tickets, other Confluence pages)

### Structure

All Confluence pages MUST follow this structure:

1. **Title/Header** (Level 1 Heading)
2. **Context Statement** (Brief introduction linking to parent project/epic)
3. **Information Table** (For key attributes - dates, owners, statuses)
4. **Content Sections** (Using hierarchical headings - H2, H3, etc.)
5. **Next Steps** (When applicable)
6. **Document Information** (Creation date, author, etc.)
</required_elements>

<formatting_guidelines>
## Formatting Guidelines 🔵

### Headings

```markdown
# Page Title (H1)
## Major Section (H2)
### Subsection (H3)
#### Minor Subsection (H4)
```

### Lists

```markdown
* Unordered list item
  * Nested unordered item
    * Further nested item

1. Ordered list item
   1. Nested ordered item
   2. Another nested item
2. Second ordered item
```

### Tables

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

### Links

```markdown
[Link Text](URL)
```
</formatting_guidelines>

<space_organization>
## Space Organization ⚪

Organize Confluence content according to these spaces:

* **MSS** - Primary space for Managed Security Services documentation
* **DEV** - Development resources and technical designs
* **TEAM** - Team processes and internal documentation
* **TRAINING** - Onboarding and training materials

Use parent/child page relationships to maintain proper hierarchical structure.
</space_organization>