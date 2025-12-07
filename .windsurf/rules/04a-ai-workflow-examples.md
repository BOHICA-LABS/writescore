---
trigger: model_decision
description: When implementing specific AI workflow patterns described in the main workflow documentation
---

# AI Workflow Implementation Examples

This companion file provides detailed implementation examples and techniques for the core AI workflow phases defined in [04-ai-workflow.md](./04-ai-workflow.md).

## Implementation Phase Examples

### Progressive Implementation

* Implement critical path components first
* Use iterative approach with functional milestones
* Provide updates to user at logical checkpoints
* Refine approach based on discoveries during implementation

### Code Quality Standards

* Follow project-specific style guides and patterns
* Add appropriate documentation and comments
* Implement error handling and validation
* Use consistent naming conventions
* Ensure secure coding practices

### Milestone Tracking

* Document when each milestone is completed
* Track changes to the original design or plan
* Flag issues that require design reconsideration
* Maintain traceability from code to requirements

### Communication

* Provide clear status updates on milestone completion
* Explain technical decisions in user-appropriate terms
* Highlight deviations from original design with justification

## Validation Phase Examples

### Testing Approach

* Implement unit tests for critical components
* Verify edge cases and boundary conditions
* Test integration points between components
* Validate error handling and recovery

### Requirements Verification

* Check implementation against each original requirement
* Test specific acceptance criteria
* Document any requirements not fully satisfied

### Quality Assurance

* Review code for security vulnerabilities
* Check for maintainability and readability
* Test with varied inputs and environments

### Final Validation

* Request user confirmation of requirements satisfaction
* Document open issues or future work items
* Provide summary of implemented functionality
* Confirm task completion or next steps

## Detailed Requirements Techniques

### Requirement Elicitation Techniques

* Parse initial user request and identify core objectives
* Use reflective questioning to clarify ambiguous requirements
* Decompose complex requirements into atomic components
* Document constraints, dependencies, and quality attributes

### Knowledge Building Protocol

* Create entities for key concepts in the knowledge graph
* Document discovered interfaces, modules, and patterns
* Extract version constraints and compatibility requirements

## Component Design Details

* Define clear module boundaries and responsibilities
* Specify interfaces and contracts between components
* Identify data models and state management approach
* Map error handling and exception flows

## Examples of AI Workflow Application

### Example 1: Web Application Development

**Phase 1: Requirements & Context**
* Identify user needs and project scope using `[TimeTool]` and `[DocTool]`
* Document functional requirements and technical constraints
* Define success criteria and acceptance tests

**Phase 2: Design Planning**
* Select architecture patterns (e.g., microservices vs monolith)
* Define component structure and API contracts
* Document data models and state management

**Phase 3: Implementation**
* Build core authentication and data services first
* Implement UI components with progressive enhancement
* Provide milestone updates at logical checkpoints

**Phase 4: Validation**
* Test against requirements matrix
* Perform security and performance testing
* Validate with user acceptance testing

### Example 2: Data Analysis Pipeline

**Phase 1: Requirements & Context**
* Define analysis objectives and available data sources
* Document data quality constraints and output requirements
* Establish success metrics and validation criteria

**Phase 2: Design Planning**
* Select appropriate algorithms and validation methods
* Design data transformation and cleaning pipeline
* Plan visualization and reporting components

**Phase 3: Implementation**
* Implement data ingestion and cleaning modules first
* Build analysis and modeling components
* Create visualization and reporting outputs

**Phase 4: Validation**
* Validate against benchmark datasets
* Test with edge cases and anomalous data
* Verify accuracy and performance metrics
