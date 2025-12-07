---
trigger: model_decision
description: When selecting implementation approaches not covered by higher-priority guidelines
---

<implementation_guidelines>
## Implementation Guidelines 🔵

### Tool Selection Process
* Begin every complex task with `[SequentialThinking]`
* List all tools available in the current environment
* Identify primary tool(s) based on phase, context, and task type
* Combine tools where single-tool resolution is insufficient
* Use `[SearchTool]` early when context is missing or external
* Defer to `[DocTool]` for all library, API, or interface-based work
* Always log selection logic and note when defaults are overridden

### Problem Decomposition
* Break complex tasks into sub-problems before solving
* Assign tools per sub-problem to avoid overuse of general-purpose tools
* Document task-to-tool mapping and revisit if partial failures emerge

### Error Handling Strategy
* When a tool fails or produces ambiguous output:
  - Retry with modified parameters (if supported)
  - Escalate to a more powerful or specific tool
  - Switch to human escalation if failure blocks core logic
* Document failure modes to avoid repeat mistakes
* Explain failure clearly to user when blocking

### Query Refinement Standards
* Start with narrow, specific queries
* Use Boolean operators and domain filters
* When results are noisy, iterate query structure or phrasing
* Document which formulation produced the best result
* Use quote-matching, versioning, and function-specific phrasing

### Tool Combination Rules
* Chain tools in pipelines: e.g., `[SearchTool]` → `[DocTool]` → `[CodeTool]`
* Use `[TimeTool]` early and during long-running sessions
* Validate outputs of one tool using another (e.g., docs ↔ codebase)
* Use memory tools to capture results of tool pipelines for reuse
* Standardize common tool combinations for repeated workflows
</implementation_guidelines>

<workflow_integration>
## Workflow Integration 🔵

### Integration with AI Workflow
* Connect implementation guidelines with the four-phase AI workflow
* Use appropriate tools for each workflow phase (see 04-ai-workflow.md)
* Implement progressive validation throughout the development process
* Follow consistent patterns across similar tasks
* Document decision points and tool selection rationale

### Practical Application
* Start by analyzing existing codebase structure and patterns
* Prioritize documentation and architectural understanding before implementation
* Combine code exploration with documentation review
* Test incrementally during complex implementations
* Validate against requirements at each milestone
* Use appropriate error handling for the current context

### Common Pitfalls to Avoid
* Skipping documentation review before code changes
* Implementing solutions before fully understanding requirements
* Using general-purpose tools when specialized ones are more effective
* Failing to verify outputs from one tool with another
* Not documenting tool selection rationale for complex tasks
* Ignoring context-specific constraints and preferences
</workflow_integration>
