---
trigger: model_decision
description: When working with specialized AI models, code generation, or testing frameworks
---

<codebase_tools>
## Codebase Tools Usage 🔵

### INCLUDES:
* Codebase Search
* Grep Search
* View Code Item
* View File
* List Directory
* Find by Name

### WHEN TO USE:
* Exploring unfamiliar projects or repositories
* Finding functions, methods, or configuration files
* Understanding the structure, logic, and relationships in existing code
* Searching for patterns, log messages, or specific variables
* Locating schema files, resource definitions, and utility functions

### HOW TO USE:
* Start with `List Directory` or `Find by Name` to map the structure
* Use `Codebase Search` for high-level queries on purpose or feature
* Switch to `Grep Search` for exact strings, error messages, or identifiers
* View complete code with `View File` when context is essential (e.g., configs, schemas)
* Use `View Code Item` for specific function, class, or method analysis
* Avoid redundant queries; don't reload already-viewed content
* Prefer scoped searches (e.g., directory or file pattern limits) over broad scans
* Combine `Codebase Search` with `[SearchTool]` to locate similar usage patterns
* Cross-reference viewed code with documentation when verifying implementation
* Document code references used in reasoning for traceability
* Use tool chaining: search → view → analyze → edit (`[CodeEditTool]`)
* Build a mental map of code ownership and module boundaries during exploration
</codebase_tools>

<code_editing_tools>
## Code Editing Tools Usage 🔵

### INCLUDES:
* Propose Code

### WHEN TO USE:
* Suggesting precise edits to existing files
* Adding, modifying, or replacing defined code segments
* Fixing bugs or implementing user-specified features
* Refactoring logic in line with architectural or documentation alignment

### HOW TO USE:
* Only use after code has been explored with `[CodeTool]` and validated with `[DocTool]`
* Target only the necessary lines—avoid broad replacements
* Use placeholders (`[...]`) for unchanged code when proposing inline edits
* Document the purpose and intent of the change (bugfix, new logic, cleanup)
* Suggest meaningful names, patterns, and alignment with existing code style
* Annotate TODOs for anything needing human review or context
* Chain with `[TestingTool]` to propose related tests or validation steps
* Include short reasoning block with every proposal to justify the decision
* Avoid proposing full files unless absolutely necessary
* Never suggest destructive changes without backward compatibility notes
* Flag changes that affect shared libraries or widely used components
</code_editing_tools>

<modeling_tools>
## Modeling Tools Usage ⚪

### INCLUDES:
* Knowledge Graph
* Entity Management
* Relation Management
* Observation Management
* Graph Query Tool

### WHEN TO USE:
* Modeling complex system relationships, component dependencies, or architectures
* Documenting implementation-to-requirement traceability
* Capturing external research or documentation references
* Performing impact analysis, dependency mapping, or knowledge validation
* Tracking evolving concepts across conversations
* Building context models for long-running tasks
* Recording state that needs to persist across sessions

### HOW TO USE:
* Create entities for any concept, component, or external resource
* Use descriptive, unique names and relevant types (Code, Doc, Pattern, etc.)
* Define relationships using clear verbs (e.g., `implements`, `depends on`, `requires validation`)
* Use observations to enrich entities with properties, metadata, and context
* Document publication dates, authorship, and version compatibility for sourced knowledge
* Avoid deleting entities unless verified obsolete
* Use bidirectional relations when applicable (e.g., `is used by`, `calls`)
* Visualize indirect dependencies through graph queries
* Highlight contradictions, alternatives, or incomplete knowledge with tags
* For evolving knowledge (e.g., best practices), add version-specific notes
* Use queries to retrieve chains of logic or uncover missing documentation
* Store research findings in the graph for reuse across sessions
* Link observations directly to code, design choices, or doc citations
</modeling_tools>

<testing_tools>
## Testing Tools Usage ⚪

### WHEN TO USE:
* Verifying that proposed code works as expected
* Validating edge cases and boundary conditions
* Checking behavior under varied inputs and states
* Assessing integration between components
* Confirming bug fixes don't introduce regressions

### HOW TO USE:
* Start with unit tests focused on specific functionality
* Extend to integration tests for component interactions
* Use parameterized tests for edge cases and variations
* Consider performance, security, and reliability testing
* Document test purposes and expected outcomes
</testing_tools>