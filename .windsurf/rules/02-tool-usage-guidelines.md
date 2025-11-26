---
trigger: model_decision
description: When selecting tools for tasks, solving complex problems, or planning implementations
---

# Tool Usage Guidelines

This document provides a comprehensive guide for selecting and using tools effectively.

<time_tool>
## Time Tool Usage 🔴

### WHEN TO USE:
* Every user interaction (start of conversation)
* Date/time formatting or timestamp generation
* Timezone conversions, DST-sensitive schedules
* Recurring events or time-based alerts
* Temporal comparisons or deadline validation

### HOW TO USE:
* Always fetch current time first; prefer UTC for storage, local time for display
* Format dates/times per user locale unless directed otherwise
* Use ISO 8601 format for any stored or transmitted time values
* Show both source and target timezones during conversions
* Clearly indicate recurrence windows and DST behavior
</time_tool>

<sequential_thinking>
## Sequential Thinking Usage 🔴

### WHEN TO USE:
* Multi-step problem-solving and planning
* Architecture design or trade-off decisions
* Tasks involving prioritization or dependencies
* Decision-making trees or branching logic
* Problem decomposition and milestone tracking

### HOW TO USE:
* Break the problem into numbered logical steps
* Re-evaluate previous steps if new context is introduced
* Clearly flag when revising or overwriting prior thoughts
* Maintain a traceable list of planned vs. executed actions
* Require a final verification step: confirm all actions were executed or explain omissions
</sequential_thinking>

<problem_decomposition>
## Problem Decomposition 🔵

### HOW TO USE:
* Break complex tasks into sub-problems before solving.
* Assign tools per sub-problem to avoid overuse of general-purpose tools.
* Document task-to-tool mapping and revisit if partial failures emerge.
* Use checklists to track progress on each sub-problem.
</problem_decomposition>

<error_handling>
## Tool Error Handling Strategy 🟠

### HOW TO HANDLE:
* When a tool fails or produces ambiguous output:
  - Retry with modified parameters (if supported).
  - Escalate to a more powerful or specific tool.
  - Switch to human escalation if failure blocks core logic.
* Document failure modes to avoid repeat mistakes.
* Explain the failure clearly to the user when it is blocking.
</error_handling>

<documentation_tools>
## Documentation Tools Usage 🔵

### INCLUDES:
* `Context7`
* `Documentation Review Tool`
* `atlassian` (Confluence)

### WHEN TO USE:
* Reviewing APIs, interfaces, and library usage
* Understanding system architecture before code changes
* Onboarding to a new project or feature
* Verifying third-party tool usage
* Locating requirements, constraints, and decisions

### HOW TO USE:
* Review documentation strategically according to [05-documentation-review.md](cci:7://file:///Users/zious/Documents/GITHUB/mss_business/.windsurf/rules/05-documentation-review.md:0:0-0:0).
* Prioritize requirements, architecture, and configuration documentation.
* Explicitly acknowledge when following specific documentation instructions.
* Flag discrepancies between documentation and code.
</documentation_tools>

<search_tools>
## Search Tools Usage 🔵

### INCLUDES:
* DuckDuckGo
* Web Search
* Perplexity
* URL Content Reader

### WHEN TO USE:
* Retrieving up-to-date external knowledge
* Researching technical best practices or recent changes
* Verifying claims or resolving conflicting info
* Locating documentation not found in the codebase or `/docs`

### HOW TO USE:
* Formulate precise queries: include versions, error strings, or function names.
* Prioritize official documentation, academic papers, and vendor pages.
* When a useful URL is found, use the URL Content Reader to extract key content.
* Synthesize findings—don't dump raw output.
</search_tools>

<tag_reference>
## Tag Reference Glossary ⚪

* `[TimeTool]` = Time Tool
* `[SequentialThinking]` = Structured logical reasoning
* `[SearchTool]` = DuckDuckGo, Web Search, Perplexity, URL Fetch
* `[DocTool]` = Context7, Documentation Review Tool, atlassian (Confluence)
* `[CodeTool]` = Codebase Search, Grep, View Code Item, View File, Find by Name, List Directory
* `[CodeEditTool]` = Propose Code
* `[ModelingTool]` = Knowledge Graph, Entity/Relation/Observation Mgmt, Graph Query
* `[TestingTool]` = Any tool or workflow validating functional, edge, or integration correctness
</tag_reference>