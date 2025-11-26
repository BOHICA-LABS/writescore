---
trigger: model_decision
description: When defining content structure for Jira tickets or completing required fields
---

<epic_structure>
## Epic Structure 🔴

**Summary Format:**
```
[Epic] {descriptive title}
```

**Description Template:**

### Overview

{High-level description of the epic's purpose}

### Business Value

{Why this work is important}

### Success Metrics

{How we'll measure success}

### Stories

{List of related stories – to be updated as they're created}

**Required Fields:**
* Fix Version/s
* Epic Name (short name for the roadmap)
* Components
* Labels: Include values from `$DEFAULT_LABELS`
</epic_structure>

<story_structure>
## Story Structure 🔴

**Summary Format:**
```
{action verb} {what} {for whom/why}
```

**Description Template:**

### Objective

{Clear statement of what needs to be accomplished}

### Requirements

* {Specific, measurable requirement 1}
* {Specific, measurable requirement 2}

### Acceptance Criteria

* [ ] {Testable criterion 1}
* [ ] {Testable criterion 2}

### Notes

{Additional context, design decisions, technical details}

**Required Fields:**
* Epic Link (all stories must belong to an epic)
* Components from `$DEFAULT_COMPONENTS`
* Story Points
* Labels: Include values from `$DEFAULT_LABELS`
</story_structure>

<bug_structure>
## Bug Structure 🔴

**Summary Format:**
```
{affected feature} {issue description}
```

**Description Template:**

### Bug Description

{Clear description of the issue}

### Steps to Reproduce

1. {Step 1}
2. {Step 2}

### Expected Behavior

{What should happen}

### Actual Behavior

{What actually happens}

**Required Fields:**
* Priority (default to `$DEFAULT_PRIORITY`)
* Components from `$DEFAULT_COMPONENTS`
* Affects Version/s
* Epic Link (if part of feature work)
* Labels: Include values from `$DEFAULT_LABELS` + `"bug"`
</bug_structure>

<task_structure>
## Task Structure 🔵

**Summary Format:**
```
{action verb} {specific task}
```

**Description Template:**

### Task Description

{Clear description of what needs to be done}

### Deliverables

* {Specific deliverable 1}
* {Specific deliverable 2}

**Required Fields:**
* Components from `$DEFAULT_COMPONENTS`
* Epic Link or Parent Link (if subtask)
* Labels: Include values from `$DEFAULT_LABELS`
</task_structure>