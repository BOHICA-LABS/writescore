---
trigger: model_decision
description: When writing new code, reviewing existing code, or refactoring code for improved maintainability
---

<coding_standards>
## Coding Standards 🔵

### General Principles
* Follow the project's established style guide and patterns
* Maintain consistency with existing codebase conventions
* Prioritize readability and maintainability over brevity
* Document code thoroughly with comments and docstrings
* Use descriptive variable and function names

### Language-Specific Standards
* **Python**: Follow PEP 8 style guide, use type hints
* **JavaScript/TypeScript**: Use ESLint/TSLint configurations, prefer modern ES features
* **Java**: Follow Google Java Style Guide, use appropriate design patterns
* **C#**: Follow Microsoft's .NET coding conventions
* **Go**: Follow Go's official style guide and idiomatic patterns

### Quality Metrics
* Maintain high test coverage (minimum 80% for critical paths)
* Keep cyclomatic complexity low (< 10 per function)
* Limit function/method length (< 50 lines preferred)
* Enforce appropriate coupling and cohesion
* Follow SOLID principles for object-oriented code

### Code Organization
* Group related functionality into logical modules
* Separate concerns appropriately (business logic, data access, presentation)
* Use consistent file and directory structure
* Implement clear error handling and logging strategies
* Maintain clean interfaces between components
</coding_standards>

<testing_protocols>
## Testing Protocols 🔵

### Test Coverage Requirements
* Unit tests for all business logic functions
* Integration tests for component interactions
* End-to-end tests for critical user flows
* Performance tests for performance-sensitive operations
* Security tests for authentication and authorization

### Testing Best Practices
* Write tests before or alongside implementation (TDD where appropriate)
* Focus on behavior rather than implementation details
* Test both happy paths and edge cases
* Use appropriate mocking and test doubles
* Maintain test independence and repeatability

### Automated Testing
* Implement continuous integration pipelines
* Run tests automatically on code changes
* Use code coverage tools to identify gaps
* Enforce minimum coverage thresholds
* Prioritize test stability and reliability

### Manual Testing Scenarios
* User experience validation
* Exploratory testing for edge cases
* Accessibility testing
* Cross-browser/device compatibility
* Usability testing with representative users

### Test Documentation
* Document test strategy and approach
* Maintain clear test cases with expected results
* Link tests to requirements or user stories
* Document test data and environment requirements
* Report and track test results and metrics
</testing_protocols>

<enforcement_mechanisms>
## Enforcement Mechanisms 🔴

### Automated Enforcement
* Implement pre-commit hooks for basic validations
* Use linters and formatters integrated with CI/CD
* Apply static analysis tools for deeper code quality checks
* Enforce branch protection and review requirements
* Automate dependency vulnerability scanning

### Review Processes
* Require code reviews for all changes
* Follow a defined pull request template
* Use pair programming for complex implementations
* Conduct periodic architecture reviews
* Implement security and performance-focused reviews

### Quality Gates
* Define clear criteria for passing quality gates
* Block deployments that fail critical checks
* Track technical debt and quality metrics
* Implement graduated quality thresholds based on risk
* Require test coverage reports for critical components
</enforcement_mechanisms>