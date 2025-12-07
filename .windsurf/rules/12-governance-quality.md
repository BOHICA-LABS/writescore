---
trigger: model_decision
description: When ensuring code quality, implementing security controls, or maintaining technical standards
---

# Governance, Quality, and Security Standards

This document provides a unified set of standards for coding, security, performance, and testing.

<coding_standards>
## Coding Standards 🔵

### General Principles
* Follow the project's established style guide and patterns.
* Maintain consistency with existing codebase conventions.
* Prioritize readability and maintainability over brevity.
* Document code thoroughly with comments and docstrings.
* Use descriptive variable and function names.

### Language-Specific Standards
* **Python**: Follow PEP 8 style guide, use type hints.
* **JavaScript/TypeScript**: Use ESLint/TSLint configurations, prefer modern ES features.
* **Java**: Follow Google Java Style Guide, use appropriate design patterns.
* **C#**: Follow Microsoft's .NET coding conventions.
* **Go**: Follow Go's official style guide and idiomatic patterns.

### Quality Metrics
* Maintain high test coverage (minimum 80% for critical paths).
* Keep cyclomatic complexity low (< 10 per function).
* Limit function/method length (< 50 lines preferred).
* Enforce appropriate coupling and cohesion.
* Follow SOLID principles for object-oriented code.

### Code Organization
* Group related functionality into logical modules.
* Separate concerns appropriately (business logic, data access, presentation).
* Use consistent file and directory structure.
* Implement clear error handling and logging strategies.
* Maintain clean interfaces between components.
</coding_standards>

<security_guidelines>
## Security & Privacy Guidelines 🔴

### Data Protection
* Never hardcode credentials or secrets.
* Use environment variables, secret managers, or secure vaults.
* Implement proper data encryption at rest and in transit.
* Follow the principle of least privilege for data access.
* Apply proper input sanitization and validation.

### Authentication & Authorization
* Implement robust authentication mechanisms.
* Use proper session management.
* Apply role-based access control where appropriate.
* Consider multi-factor authentication for sensitive operations.
* Validate permissions on both client and server sides.

### Common Vulnerabilities Prevention
* Protect against injection attacks (SQL, NoSQL, OS command).
* Prevent cross-site scripting (XSS).
* Defend against cross-site request forgery (CSRF).
* Avoid security misconfigurations.
* Implement proper error handling without leaking sensitive information.
</security_guidelines>

<performance_optimization>
## Performance Optimization 🔵

### Resource Efficiency
* Optimize CPU usage in critical paths.
* Manage memory allocation and prevent leaks.
* Reduce network calls and payload sizes.
* Implement appropriate caching strategies.
* Optimize database queries and indexing.

### Scalability Considerations
* Design for horizontal scalability when appropriate.
* Implement proper load balancing.
* Use asynchronous processing for time-consuming operations.
* Consider stateless architectures for better scaling.
* Plan for graceful degradation under load.

### Performance Monitoring
* Implement application performance monitoring (APM).
* Track key performance indicators (KPIs).
* Set up alerting for performance degradation.
* Use profiling tools to identify bottlenecks.
* Conduct regular performance reviews.
</performance_optimization>

<testing_protocols>
## Testing Protocols 🔵

### Test Coverage Requirements
* Unit tests for all business logic functions.
* Integration tests for component interactions.
* End-to-end tests for critical user flows.
* Performance tests for performance-sensitive operations.
* Security tests for authentication and authorization.

### Testing Best Practices
* Write tests before or alongside implementation (TDD where appropriate).
* Focus on behavior rather than implementation details.
* Test both happy paths and edge cases.
* Use appropriate mocking and test doubles.
* Maintain test independence and repeatability.
</testing_protocols>

<enforcement_mechanisms>
## Governance and Enforcement 🔴

### Automated Enforcement
* Implement pre-commit hooks for basic validations.
* Use linters and formatters integrated with CI/CD.
* Apply static analysis tools for deeper code quality checks.
* Enforce branch protection and review requirements.
* Automate dependency vulnerability scanning.

### Review Processes
* Require code reviews for all changes.
* Follow a defined pull request template.
* Use pair programming for complex implementations.
* Conduct periodic architecture reviews.
* Implement security and performance-focused reviews.

### Exception Process
* Document any exceptions to standards.
* Provide justification for exceptions.
* Include risk assessment and mitigation plan.
* Obtain appropriate approvals for exceptions.
* Set expiration dates for temporary exceptions.
</enforcement_mechanisms>
