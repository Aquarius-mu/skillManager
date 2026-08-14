---
name: architect
description: Find deepening opportunities in the codebase — refactors that reduce coupling, simplify interfaces, and improve AI-navigability. Use when improving architecture, finding refactoring opportunities, or making a codebase easier to work with.
---

# Architect

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is AI-navigability, clear ownership, and reduced coupling.

## Glossary

Use these terms exactly. Consistent language prevents drift.

- **Module** — anything with an interface and an implementation (function, class, Manager, service)
- **Interface** — everything a caller must know to use the module: types, error modes, ordering
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place
- **Locality** — complexity, bugs, and knowledge concentrated in one place
- **Deletion test** — imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.

## Process

### 1. Explore

Read `CONTEXT.md` and any ADRs first if they exist.

Walk the codebase organically. Note where you experience friction:
- Where does understanding one concept require bouncing between many small files?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where do tightly-coupled modules leak responsibilities across their seams?
- Which areas have repeated `if (p == nullptr) { return ERR_X; }` scattered across many callers instead of being centralised?
- Where does the same data structure get modified in multiple places without a clear owner?

Apply the **deletion test** to anything suspect.

### 2. Present Candidates

Present a numbered list of deepening opportunities. For each:

- **Files** — which files are involved
- **Problem** — why the current architecture causes friction
- **Solution** — plain English description of what would change
- **Benefits** — explained in terms of locality, leverage, and reduced coupling

Use the project's domain vocabulary (Manager names, sdp struct names) — not generic terms like "service" or "component".

**Do NOT propose new interfaces yet.** Ask: "Which of these would you like to explore?"

### 3. Design Loop

Once the user picks a candidate:
- Walk the design tree — constraints, dependencies, the shape of the deepened module
- Resolve one decision at a time (invoke `/grill` if needed)
- Side effects during the conversation:
  - **New concept not in `CONTEXT.md`?** Add it
  - **User rejects with a load-bearing reason?** Offer to record as an ADR
  - **Design crystallises?** Transition to `/plan` to create the implementation plan

### 4. C++ Game Server Specifics

When looking for deepening opportunities in this codebase, focus on:
- Manager classes doing too much — split by domain responsibility
- CmdParser handlers with embedded business logic — push logic into the Manager
- Duplicated data-loading patterns across multiple Managers — centralise
- Direct cross-Manager access — introduce a clean interface at the seam
- Deeply nested `if/else` chains — extract to named functions with clear semantics
