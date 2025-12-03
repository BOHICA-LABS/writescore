---
trigger: model_decision
description: When transitioning tickets between workflow states or designing workflow processes
---

<ticket_lifecycle>
## Ticket Lifecycle 🔵

* New tickets should start in **Backlog/To Do** status
* Tickets must have an assignee (default to `$DEFAULT_ASSIGNEE` if unspecified) before moving to **In Progress**
* Tickets require descriptive comments when transitioning to **Review/Verification**
* Tickets moved to **Done/Closed** must have time logged and resolution set
* Epics should only be closed when all child Stories are complete
</ticket_lifecycle>
