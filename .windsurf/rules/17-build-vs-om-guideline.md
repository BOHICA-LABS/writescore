---
trigger: model_decision
description: Guideline for distinguishing between Build and O&M work.
---

# Guideline: Differentiating Build vs. Operations & Maintenance (O&M)

## 1. Purpose
This document establishes a clear framework for classifying work as either "Build" (new development, significant enhancements) or "Operations & Maintenance" (O&M) (sustaining, fixing, minor updates). Consistent classification is critical for accurate project tracking, resource allocation, and financial reporting (e.g., CapEx vs. OpEx).

## 2. Definitions

### Build (Capitalizable Work)
"Build" refers to activities that create **new capabilities**, **significant enhancements** to existing systems, or develop new assets. This work is typically project-based, has a defined scope, and results in a net-new or materially improved product or service.

**Key Characteristics:**
- Creates a new product, service, or feature.
- Adds significant new functionality to an existing system.
- Involves a major redesign or re-architecture.
- The result provides substantial new value to the business or users.
- Often requires a dedicated project team and budget.

**Examples:**
- Developing a new software application from scratch.
- Adding a new major module (e.g., a reporting dashboard) to an existing platform.
- **Provisioning new cloud infrastructure (e.g., VPCs, Kubernetes clusters) using IaC.**
- **Deploying a new microservice or serverless function to the cloud.**
- **Setting up a new CI/CD pipeline for a new application.**
- Integrating a new third-party service that provides new functionality.
- Re-architecting an application from a monolith to microservices.

### Operations & Maintenance (O&M) (Non-Capitalizable Work)
"O&M" refers to the ongoing activities required to **sustain** and **support** existing systems and services. This work does not create new capabilities but ensures that current systems operate efficiently, reliably, and securely.

**Key Characteristics:**
- Keeps the system running ("keeping the lights on").
- Involves bug fixes, security patching, and performance tuning.
- Includes minor enhancements or small-scale feature improvements that do not add significant new functionality.
- Addresses user support requests and incident resolution.
- Is often continuous or recurring.

**Examples:**
- Fixing a bug that causes incorrect data to be displayed.
- Applying a security patch to a server or application dependency.
- **Updating existing IaC scripts (e.g., changing an instance size, modifying a security group).**
- **Applying patches or updating dependencies for existing serverless functions.**
- **Rotating credentials, API keys, or SSL certificates.**
- Optimizing a database query to improve page load times.
- Minor UI/UX tweaks (e.g., changing button colors, updating labels).
- Investigating and resolving production incidents.

## 3. Decision Framework

Use the following questions to classify a work item. If the answer to any of the "Build" questions is "Yes," the work should likely be classified as Build.

| Question                                                  | If Yes, likely... | If No, likely... |
| --------------------------------------------------------- | ----------------- | ---------------- |
| Does this work create a brand-new product or service?     | **Build**         | O&M              |
| Does it introduce significant, new functionality?         | **Build**         | O&M              |
| Does it require a major architectural change?             | **Build**         | O&M              |
| Is this a bug fix for existing functionality?             | O&M               | Build            |
| Is this work to maintain security or compliance?          | O&M               | Build            |
| Is this a minor tweak or small enhancement?               | O&M               | Build            |
| Is this work to "keep the lights on"?                     | O&M               | Build            |

## 4. Edge Cases

- **Large-Scale Refactoring**: If refactoring is done to enable future new features, it can be considered **Build**. If it's done purely to improve maintainability or reduce technical debt with no new functionality, it's **O&M**.
- **Upgrades**: A version upgrade of a library or framework is typically **O&M**. However, if the upgrade is substantial and unlocks significant new capabilities that will be immediately implemented, it could be part of a **Build** project.

## 5. Ticketing and Labeling
- **Jira Epics**: New development should be captured in "Build" Epics.
- **Jira Labels**: Use the labels `build` and `o&m` on individual stories and tasks to clearly distinguish the work type.
