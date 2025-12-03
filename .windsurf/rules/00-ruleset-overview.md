---
trigger: always_on
---

# Ruleset Overview

This document provides an overview of the structure, conventions, and guiding principles for the entire ruleset.

## Symbol Legend

The rules in this collection use the following symbols to indicate the nature and importance of each guideline. Understanding these conventions is essential for correct interpretation.

*   🔴 **Mandatory**: A critical rule that MUST be followed without exception. Deviations require explicit approval and documentation.
*   🔵 **Best Practice**: A recommended guideline that represents the preferred approach. While not strictly mandatory, deviations should be rare and well-justified.
*   ⚪ **Informational**: A helpful note, piece of context, or clarification that does not enforce a specific action but provides useful background.
*   🟢 **Example**: A correct or recommended implementation pattern or usage example.
*   🟠 **Warning**: A common pitfall, incorrect usage pattern, or an action to be explicitly avoided.

## Core Documentation Strategy

This ruleset is designed to work in tandem with the project's primary documentation, located in the `/docs` directory. The overall strategy is as follows:

1.  **`/docs` as the Source of Truth**: The root `/docs` folder contains the canonical documentation for the project, including product requirements, technical architecture, and process guidelines.
2.  **Ruleset as the Implementation Layer**: This ruleset operationalizes the principles defined in the `/docs`. It provides the specific, actionable instructions that the AI assistant must follow to comply with the high-level documentation.
3.  **Cross-Referencing**: The ruleset will frequently reference documents within the `/docs` folder. These links should be treated as direct extensions of the rule itself.

The documentation is organized into four primary categories, as detailed in [05-documentation-review.md](cci:7://file:///Users/zious/Documents/GITHUB/mss_business/.windsurf/rules/05-documentation-review.md:0:0-0:0):
*   `/docs/product/`
*   `/docs/technical/`
*   `/docs/code/`
*   `/docs/process/`

## Guiding Principles

1.  **Clarity over Brevity**: Rules should be explicit and unambiguous, even if it requires more text.
2.  **Consistency**: The ruleset aims to enforce consistent patterns across all development, documentation, and workflow processes.
3.  **Maintainability**: The rules themselves should be easy to maintain, with clear separation of concerns and minimal redundancy.
