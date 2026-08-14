---
name: guide
description: Use at the start of any session to understand which skill to invoke. Maps the full workflow — feature development, bug fixing, architecture, and utilities — for a C++ game server project with SVN.
---

# Gameserver Agent Skills — Guide

This package provides a complete agent workflow for C++ game server development.

## The Golden Rule

**Invoke the relevant skill BEFORE any response or action.** Even a 1% chance a skill might apply means you should invoke it. Skills tell you HOW to approach work; don't skip them.

---

## Workflow Map

### Feature Development

```
idea → /brainstorm → /to-prd → /plan → /to-issues → /implement loop → svn commit
```

1. `/brainstorm` — Explore intent, ask clarifying questions, produce a design spec
2. `/to-prd` — Turn the design into a formal PRD and publish to the issue tracker
3. `/plan` — Break the PRD into a step-by-step implementation plan
4. `/to-issues` — Slice the plan into independently-grabbable SVN-ready issues
5. `/implement` — Execute: implement slice → `./qmake.sh` → `/review` → `svn commit`

### Bug Fixing

```
bug report → /debug → implement fix → /review → svn commit
```

1. `/debug` — Build a feedback loop, reproduce, hypothesise, fix
2. `/implement` — Apply the fix with the implement→build→review loop
3. `/review` — Code review before committing

### Architecture Work

```
/zoom-out → /architect → /plan → /implement loop
```

1. `/zoom-out` — Get a map of relevant modules and callers
2. `/architect` — Find deepening opportunities, reduce coupling
3. `/plan` + `/implement` — Execute the refactor

### Prototyping

```
/prototype → capture decision → /plan → /implement
```

---

## Skill Reference

| Skill | When to use |
|-------|-------------|
| `/brainstorm` | Before any feature work — explore requirements, produce a design doc |
| `/to-prd` | Turn conversation context into a formal PRD on the issue tracker |
| `/plan` | Before touching code — write a step-by-step implementation plan |
| `/to-issues` | Break a plan into independently-grabbable issues |
| `/implement` | Execute: implement → build → review → commit (repeat per slice) |
| `/review` | Code review before any SVN commit |
| `/debug` | Disciplined bug diagnosis with feedback loop |
| `/architect` | Find and fix architectural friction in the codebase |
| `/zoom-out` | Get a broader map of modules and callers in an unfamiliar area |
| `/prototype` | Build throwaway C++ code to answer a design question |
| `/grill` | Interview the user or design relentlessly until shared understanding |
| `/triage` | Move issues through the triage state machine |
| `/handoff` | Compact the session into a document for the next agent to pick up |
| `/caveman` | Ultra-compressed output mode (~75% fewer tokens) |

---

## Project Context

- **Language:** C++17
- **Framework:** Custom in-house C++ game server framework
- **Build:** `./qmake.sh` (Unity Build + distcc)
- **Deploy:** `cpgame <server_id>`
- **VCS:** SVN — all commits use `svn commit -m "..."`, all history via `svn log`
- **Protocol:** `.sdp` files in `Common/` (CS/SC) and `Inter/` (server-to-server)
- **Naming:** PascalCase classes, m_ prefix for members, i/b/s/v/st/p prefixes for locals

## Quality Gate

**No code is committed without passing:** `./qmake.sh` compiles clean → `/review` subagent approves → `svn commit`.
