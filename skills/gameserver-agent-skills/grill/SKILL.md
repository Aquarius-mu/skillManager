---
name: grill
description: Interview the user or a design relentlessly until reaching shared understanding. Walk down every branch of the decision tree, resolving dependencies one by one. Use when stress-testing a plan, clarifying design, or the user says "grill me".
---

# Grill

Interview relentlessly about every aspect of a plan or design until reaching shared understanding. Walk down each branch of the decision tree, resolving dependencies between decisions one by one.

For each question, provide your recommended answer so the user can agree, correct, or redirect.

## Process

1. Read the plan, design doc, or feature description provided
2. Identify the open decision tree — what is undecided, ambiguous, or potentially wrong?
3. Ask the most important unresolved question first, with your recommended answer
4. When the user answers, update your understanding and ask the next question
5. Continue until all branches are resolved or the user is satisfied

## Rules

- **One question at a time** — never ask multiple questions in one message
- **Always provide your recommendation** — don't ask open-ended questions without a suggested answer
- **Walk dependencies first** — resolve foundational decisions before detail decisions
- **Be relentless** — don't stop because an answer "seems fine"

## C++ Game Server Focus

When grilling a game server design, specifically probe:

- **Protocol layer**: Is the CmdId range available? Are CS/SC structs clearly defined?
- **Logic layer**: Which Manager owns this feature? Are the data structures in SdpData clearly defined?
- **Persistence**: What data needs `setChanged()`? When is it saved to DB?
- **Error codes**: Are new ERR_ codes needed? Are they in `ErrorDefine.sdp`?
- **Registration**: Does this need `ADD_NORMAL_COMMAND` in `CmdRegister.h`?
- **Concurrency**: Is there any cross-module state access that needs care?
- **Edge cases**: What happens when the player is offline? When the data doesn't exist yet?

## Example

```
User: "I want to add a daily reward system"

Grill: "Should the daily reward reset at midnight server time or at a rolling 24h window
from the player's last claim? I'd recommend midnight server time — it's simpler to reason
about and consistent with most other daily systems in the codebase."

User: "Midnight server time"

Grill: "Should claiming the daily reward be possible while the player is offline (e.g. via
an automated system) or only when they actively log in? I'd recommend login-only — it keeps
the flow simple and doesn't require a background job."

... and so on
```
