---
name: handoff
description: Compact the current conversation into a handoff document for another agent or session to pick up.
argument-hint: "What will the next session focus on?"
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to a path produced by `mktemp -t handoff-XXXXXX.md` (read the file before writing to it).

Suggest which skills the next session should use.

Do not duplicate content already captured in other artifacts (PRDs, plans, SVN commit messages, diffs). Reference them by path instead.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.

## Structure

```markdown
# Handoff — [Date] [Focus]

## Context
[What we were working on and why]

## Current State
[What is done, what is in progress, what is blocked]

## Key Files
[Exact paths to plans, PRDs, or design docs relevant to the next session]

## Next Steps
[Ordered list of what to do next]

## Suggested Skills
[Which skills to invoke in the next session, in order]

## Open Questions
[Anything unresolved that the next session needs to decide]
```
