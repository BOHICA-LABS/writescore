---
trigger: model_decision
description: When encountering output size limits or handling large text generation
---

<error_trigger>
## Cascade Error Trigger 🔴

When encountering the following error:
Cascade error Deadline exceeded: Encountered retryable error from model provider: context deadline exceeded


This indicates the text generation exceeds size limits. The assistant MUST chunk the content.
</error_trigger>

<chunking_protocol>
## Content Chunking Protocol 🔴

1.  Immediately divide the task into smaller, logical chunks.
2.  Generate content incrementally across multiple steps.
3.  Create a clear outline of ALL planned chunks at the beginning.
4.  Number each chunk explicitly (e.g., "Part 1 of 5: Introduction").
5.  Confirm user approval for each chunk before proceeding to the next.
</chunking_protocol>

<implementation_guidelines>
## Implementation Guidelines 🔵

1.  Proactively chunk content that is likely to be large (e.g., long documents, multiple code files).
2.  Use natural segment boundaries (sections, modules, components) for chunking.
3.  Generate documents with multiple sections one section at a time.
4.  Chunk code generation by logical components or files.
5.  Maintain consistency in formatting and style across all chunks.
</implementation_guidelines>

<error_prevention>
## Error Prevention 🔵

1.  Monitor response size during generation.
2.  Prioritize the most critical content for the first chunk.
3.  Begin each new chunk with a brief continuation context.
4.  Provide clear transitions between chunks.
5.  Create a final summary connecting all components after completion.
</error_prevention>
