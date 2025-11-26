---
trigger: model_decision
description: When implementing security features, handling sensitive data, or optimizing performance
---

<security_guidelines>
## Security & Privacy Guidelines 🔴

### Data Protection
* Never hardcode credentials or secrets
* Use environment variables, secret managers, or secure vaults
* Implement proper data encryption at rest and in transit
* Follow the principle of least privilege for data access
* Apply proper input sanitization and validation

### Authentication & Authorization
* Implement robust authentication mechanisms
* Use proper session management
* Apply role-based access control where appropriate
* Consider multi-factor authentication for sensitive operations
* Validate permissions on both client and server sides

### Common Vulnerabilities Prevention
* Protect against injection attacks (SQL, NoSQL, OS command)
* Prevent cross-site scripting (XSS)
* Defend against cross-site request forgery (CSRF)
* Avoid security misconfigurations
* Implement proper error handling without leaking sensitive information

### Security Verification
* Conduct regular code security reviews
* Use static application security testing tools
* Implement runtime protection mechanisms
* Test for known vulnerabilities in dependencies
* Apply security patches promptly

### Privacy Compliance
* Follow data minimization principles
* Implement appropriate data retention policies
* Respect user consent and preferences
* Consider relevant privacy regulations (GDPR, CCPA, etc.)
* Document data flows and processing activities
</security_guidelines>

<performance_optimization>
## Performance Optimization 🔵

### Resource Efficiency
* Optimize CPU usage in critical paths
* Manage memory allocation and prevent leaks
* Reduce network calls and payload sizes
* Implement appropriate caching strategies
* Optimize database queries and indexing

### Scalability Considerations
* Design for horizontal scalability when appropriate
* Implement proper load balancing
* Use asynchronous processing for time-consuming operations
* Consider stateless architectures for better scaling
* Plan for graceful degradation under load

### Performance Monitoring
* Implement application performance monitoring (APM)
* Track key performance indicators (KPIs)
* Set up alerting for performance degradation
* Use profiling tools to identify bottlenecks
* Conduct regular performance reviews

### Optimization Methodology
* Measure before optimizing (establish baselines)
* Focus on high-impact areas first
* Test performance changes with realistic workloads
* Document performance requirements and achievements
* Balance performance with other quality attributes

### User Experience Optimization
* Prioritize perceived performance
* Implement progressive loading techniques
* Optimize critical rendering paths
* Reduce time to first meaningful content
* Consider offline capabilities where appropriate
</performance_optimization>

<governance_application>
## Governance Application 🔴

### Scope of Application
* These governance standards apply to all production code
* Critical systems must meet all mandatory requirements
* Support and tooling code may have adjusted thresholds
* Experimental code must be clearly labeled and isolated
* Legacy code should have migration plans to meet standards

### Exception Process
* Document any exceptions to standards
* Provide justification for exceptions
* Include risk assessment and mitigation plan
* Obtain appropriate approvals for exceptions
* Set expiration dates for temporary exceptions

### Compliance Monitoring
* Regular audits of code quality and security
* Automated reporting on compliance metrics
* Trend analysis of quality over time
* Identification of recurring issues
* Visibility of compliance status to stakeholders
</governance_application>