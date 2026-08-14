---
name: to-prd
description: Turn the current conversation context into a PRD and save it. Use when you want a formal product requirements document from the current discussion.
---

# To PRD

Synthesise the current conversation and codebase understanding into a PRD. Do NOT interview the user — just synthesise what you already know.

## Process

1. **Explore the codebase** if you haven't already. Understand the current state of the relevant modules. Use the project's domain vocabulary throughout.

2. **Sketch the major modules** to build or modify. Look for opportunities to extract deep modules with clean interfaces. Check with the user that the module breakdown matches their expectations.

3. **Write the PRD** using the template below and save to `docs/prd/YYYY-MM-DD-<feature>.md`. Then `svn add` + `svn commit -m "docs: add PRD"`.

## PRD Template

```markdown
# [Feature Name] PRD

## Problem Statement

The problem the user is facing, from their perspective.

## Solution

The solution, from the user's perspective.

## User Stories

A numbered list of user stories:

1. As a <actor>, I want <feature>, so that <benefit>

Cover all aspects of the feature. Be thorough.

## Implementation Decisions

- Modules to build or modify (name them by their Manager/class names)
- Interface decisions (what the Manager exposes to CmdParser)
- Protocol changes (new CmdId ranges, CS/SC structs)
- Data structure changes (new fields in SdpData sdp files)
- Error code additions (new ERR_ entries in ErrorDefine.sdp)
- Architectural decisions and constraints

Do NOT include specific file paths or code snippets — they go stale quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose
(e.g. a key state machine or data structure shape), inline it and note it came from a prototype.

## Out of Scope

What is explicitly NOT included in this PRD.

## Further Notes

Any open questions, dependencies, or follow-up items.
```

## After Writing

Transition to `/plan` to create the implementation plan, or `/to-issues` to slice into individually-committable issues.
