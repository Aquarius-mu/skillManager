---
name: to-issues
description: Break a plan, spec, or PRD into independently-committable issues using vertical slices. Use when converting a plan into trackable work items.
---

# To Issues

Break a plan into independently-committable issues using vertical slices (tracer bullets).

## Process

### 1. Gather Context

Work from the plan or PRD already in context. If an issue reference was provided, fetch it from the issue tracker.

### 2. Explore the Codebase (if needed)

Understand the current code state. Issue titles and descriptions should use the project's domain vocabulary (Manager names, struct names, module names).

### 3. Draft Vertical Slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL layers end-to-end — sdp definition + Logic + CmdParser + response — NOT a horizontal slice of one layer.

Slices may be **HITL** (requires human interaction: design decision, deployment approval) or **AFK** (can be implemented and committed to SVN without human interaction). Prefer AFK over HITL where possible.

**Vertical slice rules:**
- Each slice delivers a narrow but COMPLETE path through every layer
- A completed slice produces a working feature that can be deployed and verified
- Prefer many thin slices over few thick ones

### 4. Quiz the User

Present the proposed breakdown as a numbered list. For each slice:
- **Title**: short descriptive name
- **Type**: HITL / AFK
- **Blocked by**: which other slices must complete first
- **Covers**: what functionality this slice delivers

Ask the user:
- Does the granularity feel right?
- Are the dependency relationships correct?
- Should any slices be merged or split?
- Are HITL/AFK assignments correct?

Iterate until the user approves.

### 5. Publish Issues

For each approved slice, create an issue. Use the template below. Publish in dependency order (blockers first).

## Issue Template

```markdown
## Parent

Reference to the parent plan or PRD (if applicable).

## What to Build

A concise description of this vertical slice. Describe the end-to-end behavior (sdp → logic → response), not layer-by-layer steps.

Avoid specific file paths or code — they go stale. Exception: if a prototype produced a key data structure or state machine snippet, inline it here.

## Acceptance Criteria

- [ ] CmdId enum value added and unique
- [ ] CS/SC structs defined in sdp
- [ ] Logic implemented in Manager
- [ ] CmdParser handler implemented and registered in CmdRegister.h
- [ ] ./qmake.sh compiles clean
- [ ] Code review passed (no Critical/Important issues)
- [ ] svn commit done

## Blocked By

- [issue reference] OR "None — can start immediately"
```
