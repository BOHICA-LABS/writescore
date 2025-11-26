---
trigger: model_decision
description: When reading documentation, analyzing requirements, or extracting information from specifications
---

# Documentation Review Guidelines

## Purpose

Establish clear protocols for when, how, and which documentation to review during different stages of interaction, ensuring targeted information retrieval without exhausting context window.

<when_to_review>
## When to Review Documentation 🔴

**Review documentation when**:
- First interacting with project/repository
- Understanding architecture or system design
- Implementing features with established patterns
- Analyzing business or technical requirements
- Before suggesting significant code changes
- Working with project-specific tools or frameworks
- Verifying process compliance
- Working with APIs or interfaces

**Skip documentation review for**:
- Simple syntax questions
- Generic programming concepts
- Basic bug fixes
- Standard tool operations
</when_to_review>

<documentation_structure>
## MSS Business Documentation Structure 🔵

Our documentation follows a six-layer structure:

1.  **Product Documentation** - `/docs/product/`
    -   Requirements, user guides, feature specifications, product discovery

2.  **Technical Documentation** - `/docs/technical/`
    -   Architecture, system design, API documentation, financial analysis

3.  **Code Documentation** - `/docs/code/`
    -   Coding standards and conventions

4.  **Process Documentation** - `/docs/process/`
    -   Workflows, standards, Jira/Confluence integration, risk management

5.  **Architecture Documentation** - `/docs/adr/`
    -   Architecture Decision Records (ADRs) providing rationale for technical decisions.

6.  **Training Documentation** - `/docs/training/`
    -   Materials and guides for onboarding and skill development.

Always respect this hierarchy when navigating documentation.
</documentation_structure>

<documentation_prioritization>
## Documentation Prioritization 🔵

### High Priority (Always Check)
1.  **Project README.md** - Main `/docs/index.md` contains critical project overview
2.  **Technical Architecture** - `/docs/technical/architecture/index.md` for system design
3.  **Process Documentation** - `/docs/process/index.md` for process-related queries
4.  **Domain-Specific Docs** - Documents directly related to the query's domain

### Medium Priority (Check When Relevant)
1.  **API Documentation** - `/docs/technical/api/` when working with interfaces
2.  **Standards Documentation** - `/docs/process/standards/` for coding or design standards
3.  **Workflow Documentation** - `/docs/process/workflows/` for process compliance
4.  **Product Documentation** - `/docs/product/` for feature and requirements queries

### Low Priority (Check If Referenced)
1.  **Standards Governance** - `/docs/process/standards/standards-governance/` for detailed standards
2.  **Historical Discussions** - Only when understanding past decisions is necessary
3.  **AI Standards** - `/docs/process/standards/standards-governance/ai-standards/` for AI rule creation
</documentation_prioritization>

<implementation_techniques>
## Implementation Techniques 🟢

### Efficient Document Processing
1.  **Selective Reading**: Target only relevant documentation sections
