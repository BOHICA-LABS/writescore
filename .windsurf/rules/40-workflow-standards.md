---
trigger: model_decision
description: When creating Windsurf workflows, modifying workflow definitions, or implementing automation scripts
---

<workflow_organization>
## Workflow Organization 🔴

* Store all workflows in `.windsurf/workflows/` directory
* Use kebab-case for workflow filenames (e.g., `review-pr-comments.md`)
* Group related workflows with consistent prefixes
* Include version and last-updated metadata in each workflow
* Follow similar structure to AI rules with proper YAML frontmatter
</workflow_organization>

<workflow_structure>
## Workflow Structure 🔴

* Begin with clear title and description of workflow purpose
* Number steps sequentially and use hierarchical sub-steps (1, 1a, 1b)
* Include specific CLI commands with proper formatting
* Provide clear transition statements between major steps
* End with verification or summary steps

### Recommended Format

```markdown
# [Workflow Name]

## Description
Brief description of what this workflow accomplishes.

## Usage
Instructions for invoking the workflow: `/[workflow-name]`

1. First step instruction
   ```
   Example command or action
   ```

   a. Sub-step instruction
   b. Sub-step instruction

2. Second step instruction
   a. Sub-step instruction
   b. Sub-step instruction

3. Verification step
   ```
   Verification command
   ```

## Version
1.0 (Last updated: YYYY-MM-DD)
```
</workflow_structure>

<workflow_invocation>
## Workflow Invocation 🔵

* Invoke workflows using `/[workflow-name]` command format in Cascade
* Document required parameters in workflow description
* Include examples of proper invocation
* Consider workflow dependencies and chaining
* Workflows can call other workflows using the same invocation format
</workflow_invocation>

<character_limits>
## Character Limits & Optimization 🔴

Windsurf workflows have strict character limits that must be followed:

* **Description**: Limited to 250 characters maximum
* **Workflow Content**: Limited to 6,000 characters maximum
* When a workflow exceeds these limits, break it into multiple workflows
* Workflows can call other workflows using the `/[workflow-name]` syntax
* Use workflow chaining for complex processes that exceed character limits
* Prioritize logical separation when breaking workflows into smaller components
* Consider the single responsibility principle when designing workflows
* Use comments (prefixed with `#`) for additional context without affecting execution
</character_limits>

<workflow_rule_integration>
## Workflow and Rule Integration 🔴

Workflows and rules serve complementary purposes:

* **Rules** provide persistent context at the prompt level
* **Workflows** guide sequential tasks at the trajectory level

### Integration Strategies

1. **Reference workflows in rules**: Include workflow invocation examples in relevant rules
2. **Maintain consistency**: Ensure workflows follow the same standards defined in rules
3. **Workflow-rule pairs**: Create dedicated rule-workflow pairs for complex processes
4. **Documentation alignment**: Keep workflow documentation in sync with rule documentation

### Example Integration

For interview processes:
* Rules define ticket structures, field requirements, and documentation standards
* Workflows guide the sequential execution of interview steps from candidate creation to final determination
</workflow_rule_integration>

<common_workflow_types>
## Common Workflow Types 🔵

### Development Workflows

* **PR Review** - Standardized process for reviewing pull requests
* **Dependency Management** - Installing or updating project dependencies
* **Code Formatting** - Running formatters and linters on files
* **Test Execution** - Running tests and fixing errors

### Project Management Workflows

* **Ticket Creation** - Creating standardized Jira tickets
* **Status Updates** - Updating ticket status with appropriate transitions
* **Release Planning** - Planning and documenting releases

### Deployment Workflows

* **Application Deployment** - Deploying applications to various environments
* **Security Scanning** - Running security scans during deployment
* **Verification Testing** - Executing verification tests post-deployment
</common_workflow_types>

<best_practices>
## Best Practices 🔵

* **Test thoroughly**: Verify workflows work as expected before sharing
* **Document clearly**: Include purpose, usage, and examples
* **Version control**: Track workflow changes in version control
* **Modularize**: Break complex workflows into smaller, reusable components
* **Follow standards**: Adhere to organizational naming and documentation standards
* **Include examples**: Provide clear examples of workflow usage
* **Limit scope**: Each workflow should have a single, clear purpose
* **Add error handling**: Include guidance for common error scenarios
</best_practices>
