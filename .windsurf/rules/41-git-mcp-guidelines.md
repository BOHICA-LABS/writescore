---
trigger: model_decision
description: When performing version control operations or interacting with git repositories
---

<git_mcp_usage>
## Git MCP Usage Priority 🔴

### WHEN TO USE:
* All standard git operations (status, add, commit, checkout, branch)
* Viewing repository information (log, diff, show)
* Managing branches and staged changes
* Implementing automated git workflows
* Any git operation required for task completion

### PRIORITIZATION RULES:
1. **ALWAYS** use Git MCP tools as the primary method for git operations
2. Git CLI commands should **ONLY** be used when:
   * Troubleshooting Git MCP tool failures
   * Performing advanced operations not supported by Git MCP
   * Executing git operations requiring custom formatting
   * Running git hooks or specialized scripts
   * Implementing complex branching strategies requiring multiple chained commands
</git_mcp_usage>

<git_mcp_tools>
## Git MCP Tool Selection 🔵

### STANDARD OPERATIONS:
* Repository status: `git_status`
* Adding files: `git_add`
* Committing changes: `git_commit`
* Switching branches: `git_checkout`
* Creating branches: `git_create_branch`

### DIFF OPERATIONS:
* View changes between branches/commits: `git_diff`
* View staged changes: `git_diff_staged`
* View unstaged changes: `git_diff_unstaged`

### HISTORY OPERATIONS:
* View commit history: `git_log`
* Show specific commit details: `git_show`

### STATE MANAGEMENT:
* Unstage changes: `git_reset`
</git_mcp_tools>

<git_cli_fallback>
## Git CLI Fallback Protocol 🟠

### FALLBACK TRIGGERS:
* Git MCP returns error or unexpected results
* Operation requires functionality not exposed by Git MCP
* Task requires advanced git features (interactive rebase, cherry-pick, etc.)
* Performance issues with Git MCP for large repositories
* Custom formatting requirements for git output

### FALLBACK PROCEDURE:
1. Document the specific reason for CLI fallback
2. Use precise git CLI command with minimal scope
3. Include clear explanation of command purpose and expected outcome
4. Return to Git MCP for subsequent operations when possible
5. Report persistent Git MCP issues for potential tool enhancement
</git_cli_fallback>

<git_operation_examples>
## Common Usage Examples 🟢

### CORRECT USAGE (Git MCP):
```python
# Check repository status
mcp2_git_status(repo_path="/path/to/repo")

# Stage specific files
mcp2_git_add(repo_path="/path/to/repo", files=["file1.txt", "file2.md"])

# Commit changes with conventional commit message
mcp2_git_commit(repo_path="/path/to/repo", message="feat(component): add new feature")

# View commit history
mcp2_git_log(repo_path="/path/to/repo", max_count=10)
```

### VALID FALLBACK EXAMPLES (Git CLI):
```bash
# Advanced operation: Interactive rebase (not available in Git MCP)
git -C /path/to/repo rebase -i HEAD~3

# Custom formatting: One-line log with graph (for visualization)
git -C /path/to/repo log --oneline --graph --decorate

# Complex operation: Cherry-pick with sign-off
git -C /path/to/repo cherry-pick -s commit_hash
```
</git_operation_examples>

<git_mcp_integration>
## Integration With Other Guidelines 🔵

* Apply Conventional Commits rules (36-conventional-commits.md) when using `git_commit`
* Combine with Sequential Thinking for multi-step git workflows
* Use git operations as atomic steps in workflow standards (40-workflow-standards.md)
* Reference time-based operations with Time Tool when relevant to branching strategies
</git_mcp_integration>