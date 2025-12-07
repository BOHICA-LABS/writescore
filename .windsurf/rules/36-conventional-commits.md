---
trigger: model_decision
description: when task involves making git commits or version control operations
---

<commit_structure>
## Commit Message Structure 🔴

All commit messages MUST adhere to the Conventional Commits 1.0.0 specification with the following structure:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```
</commit_structure>

<required_elements>
## Required Elements 🔴

### Type

The type MUST be one of the following:

* `feat`: A new feature (correlates with MINOR in Semantic Versioning)
* `fix`: A bug fix (correlates with PATCH in Semantic Versioning)
* `docs`: Documentation only changes
* `style`: Changes that do not affect the meaning of the code
* `refactor`: A code change that neither fixes a bug nor adds a feature
* `perf`: A code change that improves performance
* `test`: Adding missing tests or correcting existing tests
* `build`: Changes that affect the build system or external dependencies
* `ci`: Changes to our CI configuration files and scripts
* `chore`: Other changes that don't modify src or test files

### Description

* MUST be a short summary of the code changes
* MUST be in the imperative, present tense (e.g., "change" not "changed" or "changes")
* MUST NOT capitalize the first letter
* MUST NOT end with a period
</required_elements>

<optional_elements>
## Optional Elements 🔵

### Scope

* MUST be enclosed in parentheses
* SHOULD be a noun describing the section of the codebase affected by the change
* Common scopes for this project include:
  * `jira`
  * `confluence`
  * `rules`
  * `docs`
  * `api`
  * `ui`
  * `backend`

### Body

* MUST use the imperative, present tense
* SHOULD include the motivation for the change and contrast with previous behavior
* SHOULD be separated from the description by a blank line

### Footer

* MUST start with a word token followed by either `:` or ` #`
* Breaking changes MUST be indicated by a `BREAKING CHANGE:` footer
* Other common footers include:
  * `Refs: #123` - Issue references
  * `Closes: #123` - Issues closed by this commit
</optional_elements>

<breaking_changes>
## Breaking Changes 🔴

Breaking changes MUST be indicated in one of two ways:

1. By appending a `!` after the type/scope: `feat(api)!: remove user endpoint`
2. By adding a `BREAKING CHANGE:` footer with description:
   ```
   feat(api): remove user endpoint

   BREAKING CHANGE: The user endpoint has been removed and replaced with accounts
   ```
</breaking_changes>
