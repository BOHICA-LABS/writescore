---
trigger: always_on
---

<core_principles>
## Core Principle 🔴

As a Windsurf Assistant, I MUST always select and use the most appropriate tools for every user task. This includes prioritizing **structured thinking tools** for multi-step problems and **retrieval tools** for knowledge-intensive or fast-changing topics. Tools must be selected intentionally, not reflexively, with reasoning explicitly traceable to the problem's structure and user intent.
</core_principles>

<mandatory_protocol>
## Mandatory Protocol 🔴

For ALL complex tasks (multi-step logic, open-ended design, deep research), Windsurf Assistants MUST:

1. List all available tools before proceeding.
2. Identify which tools are best-suited and why.
3. Prioritize sequential thinking when task involves multiple dependent decisions.
4. Use the **Time Tool** at the start of all interactions to anchor temporal context.
5. Use a [SearchTool] whenever:
   - Information may be outdated, incomplete, or external to the codebase.
   - Cross-referencing multiple sources improves accuracy or confidence.
6. Combine tools intentionally. Example: search → doc retrieval → code inspection → implementation.
7. Never skip tool usage when it would improve precision, safety, speed, or user value.
8. Rely on **Time Tool**, **Context7**, and **Documentation Review** for all tasks involving coding, APIs, time-sensitive logic, or dependency checks.
9. Record which tools were used and whether alternative tools were considered.
10. Clearly mark when default toolsets are overridden by user constraints or edge-case needs.
11. Review documentation according to the guidelines in [05-documentation-review.md](cci:7://file:///Users/zious/Documents/GITHUB/mss_business/.windsurf/rules/05-documentation-review.md:0:0-0:0), prioritizing relevant files based on query context rather than scanning all docs indiscriminately.
</mandatory_protocol>

<tool_selection>
## Tool Selection Decision Tree 🔵

IF task requires multi-step reasoning THEN
  USE Sequential Thinking
ELSE IF task involves time-sensitive data THEN
  USE Time Tool first
END IF
</tool_selection>

<context_awareness>
## Context-Aware Tool Activation 🔵

IF task_type = "ticket_creation" THEN
  ACTIVATE rules: [21-ticket-creation.md, 22-ticket-structure.md, 23-linking-hierarchy.md]
ELSE IF task_type = "code_commit" THEN
  ACTIVATE rules: [36-conventional-commits.md]
END IF
</context_awareness>

<enforcement_scope>
## Enforcement Scope 🔴

This rulebook governs all behavior of Windsurf Assistants operating across development, design, research, and support domains. No directive may be skipped, bypassed, or partially applied unless:

- A user explicitly requests a deviation
- The system lacks tool access (log this)
- An override is authorized by downstream workflows or automation policies

Assistants must treat this document as *authoritative*. New capabilities or tools must map into these rule categories or trigger an update.

Tool usage must be explainable post-hoc via logs, memory, or assistant reasoning history.
</enforcement_scope>