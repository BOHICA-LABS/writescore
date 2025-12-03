---
trigger: model_decision
description: When defining AI workflows, implementing sequential thinking, or solving multi-step problems
---

<workflow_overview>
## Windsurf AI Workflow Overview 🔴

The Windsurf AI workflow consists of four distinct phases that must be followed for all complex tasks. Each phase has specific tools, outputs, and validation criteria.

### Phase 1: Requirements & Context
* **Primary Tools**: `[TimeTool]`, `[DocTool]`, `[SearchTool]`, `[ModelingTool]`
* **Key Activities**: Requirement elicitation, context gathering, constraint mapping
* **Critical Outputs**: Problem statement, scope boundaries, success criteria
* **Validation**: User confirmation of understanding and requirements

### Phase 2: Design Planning
* **Primary Tools**: `[SequentialThinking]`, `[SearchTool]`, `[CodeTool]`
* **Key Activities**: Architecture planning, pattern selection, component design
* **Critical Outputs**: Component diagram, interface definitions, data models
* **Validation**: Alignment with requirements and quality attributes

### Phase 3: Implementation with Milestones
* **Primary Tools**: `[SequentialThinking]`, `[CodeTool]`, `[CodeEditTool]`
* **Key Activities**: Incremental implementation, milestone tracking, user updates
* **Critical Outputs**: Working code modules, integration points, progress markers
* **Validation**: Functional testing, milestone completion

### Phase 4: Validation & QA
* **Primary Tools**: `[TestingTool]`, `[CodeTool]`, `[ModelingTool]`
* **Key Activities**: Testing, edge case validation, requirements verification
* **Critical Outputs**: Test results, verification matrix, quality metrics
* **Validation**: User acceptance, requirements satisfaction
</workflow_overview>

<requirements_phase>
## Phase 1: Requirements & Context 🔴

### Initial Context Acquisition
* Start EVERY interaction with current time using `[TimeTool]`
* Check `/docs` directory for relevant standards, templates, or constraints
* Scan for `.env` file and extract environment variables

### Core Requirements Process
* Identify key objectives and success criteria
* Document constraints and dependencies
* Define acceptance criteria for each requirement
* Validate understanding with the user

### Scope Definition Standards
* Clear statement of in-scope vs. out-of-scope features
* Defined acceptance criteria for each requirement
* Explicit documentation of assumptions
* Identification of potential extension points

See [04a-ai-workflow-examples.md](./04a-ai-workflow-examples.md) for detailed requirement elicitation techniques and knowledge building protocols.
</requirements_phase>

<design_phase>
## Phase 2: Design Planning 🔴

### Architecture Selection
* Use `[SequentialThinking]` to evaluate architectural patterns
* Consider scalability, maintainability, and performance requirements
* Select domain-appropriate patterns based on requirements
* Document trade-offs and alternative approaches considered

### Implementation Planning
* Break down work into logical milestones
* Estimate complexity and dependencies between components
* Identify critical path components for early implementation

### Design Documentation
* Document key design decisions and their rationales
* Link design elements to specific requirements
* Outline testing approach for design verification

See [04a-ai-workflow-examples.md](./04a-ai-workflow-examples.md) for detailed component design techniques and validation approaches.
</design_phase>

<implementation_phase>
## Phase 3: Implementation with Milestones 🔵

### Core Implementation Principles
* Implement critical path components first
* Use iterative approach with functional milestones
* Follow project-specific coding standards
* Maintain traceability to requirements

### Progress Communication
* Provide updates at logical checkpoints
* Document milestone completion
* Explain technical decisions clearly
* Flag issues requiring design reconsideration

See [04a-ai-workflow-examples.md](./04a-ai-workflow-examples.md) for detailed implementation techniques, code quality standards, and examples.
</implementation_phase>

<validation_phase>
## Phase 4: Validation & QA 🔵

### Core Validation Principles
* Test critical components and integration points
* Verify implementation against original requirements
* Review for security and maintainability
* Confirm with user that requirements are satisfied

### Validation Documentation
* Document test results and coverage
* Record any unsatisfied requirements
* Identify open issues and future work items
* Provide summary of implemented functionality

See [04a-ai-workflow-examples.md](./04a-ai-workflow-examples.md) for detailed validation techniques and examples.
</validation_phase>

<related_rules>
## Related Rules

* **[01-core-principles.md](./01-core-principles.md)**: Core principles, mandatory protocols, and tool selection guidelines.
* **[02-tool-usage-guidelines.md](./02-tool-usage-guidelines.md)**: Detailed usage for Sequential Thinking and other primary tools.
* **[04a-ai-workflow-examples.md](./04a-ai-workflow-examples.md)**: Detailed implementation and validation examples.
* **[05-documentation-review.md](./05-documentation-review.md)**: Guidelines for reviewing and using project documentation.
</related_rules>
