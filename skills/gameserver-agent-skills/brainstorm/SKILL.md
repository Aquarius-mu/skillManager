---
name: brainstorm
description: Use before any feature work — explores intent, asks clarifying questions one at a time, produces a design doc. Invoke before writing any code or plan.
---

# Brainstorm

Turn ideas into fully-formed designs through collaborative dialogue. Start by understanding the current project context, then ask questions one at a time. Once the design is clear, write a spec and transition to `/plan`.

<HARD-GATE>
Do NOT write any code, scaffold anything, or invoke `/plan` until you have presented a design and the user has approved it.
</HARD-GATE>

## Checklist

Create a task for each item and complete in order:

1. **Explore project context** — read relevant files, check recent SVN history (`svn log -l 5`)
2. **Ask clarifying questions** — one at a time, understand purpose / constraints / success criteria
3. **Propose 2-3 approaches** — with trade-offs and a clear recommendation
4. **Present design** — section by section, get user approval on each
5. **Write design doc** — save to `docs/specs/YYYY-MM-DD-<topic>.md`, then `svn add` + `svn commit -m "docs: add design spec"`
6. **Spec self-review** — scan for placeholders, contradictions, ambiguity
7. **User reviews spec** — ask user to confirm before proceeding
8. **Transition** — invoke `/plan` to create the implementation plan

## Process

**Exploring the idea:**
- Check the current project state first (files, relevant sdp, recent SVN history)
- For large requests spanning multiple subsystems, flag it and help the user decompose before diving into details
- Ask one question at a time — prefer multiple-choice when possible
- Focus on: purpose, constraints, success criteria

**Proposing approaches:**
- Always propose 2-3 options with trade-offs
- Lead with your recommendation and explain why
- Keep options realistic for a C++ game server (no greenfield architectural shifts)

**Working in existing codebases:**
- Follow existing patterns (CmdParser layer, Logic layer, Manager singleton, sdp definitions)
- Where existing code has problems that affect the work, include targeted improvements — don't propose unrelated refactoring

**Writing the design doc:**
- Save to `docs/specs/YYYY-MM-DD-<topic>.md`
- Cover: modules touched, protocol changes (sdp), data flow, error handling
- After writing: `svn add docs/specs/YYYY-MM-DD-<topic>.md && svn commit -m "docs: add design spec"`
- Ask user to review before proceeding: *"Spec committed. Please review and let me know if you want changes before I write the implementation plan."*

## Key Principles

- **One question at a time** — don't overwhelm
- **YAGNI ruthlessly** — remove unnecessary features from all designs
- **Explore alternatives** — always propose 2-3 approaches
- **Incremental validation** — present design, get approval, then move on
