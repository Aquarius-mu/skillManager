---
name: zoom-out
description: Go up a level of abstraction and map all relevant modules and callers. Use when unfamiliar with a section of code or needing to understand how something fits into the bigger picture.
disable-model-invocation: true
---

# Zoom Out

Get a map of how a piece of code fits into the bigger picture. Use when you're unfamiliar with an area, about to make changes, or need to understand call chains before modifying behaviour.

## When to Invoke

- About to work in an unfamiliar module or subsystem
- Need to understand who calls a function, Manager, or CmdParser handler
- Planning changes that might have side effects elsewhere
- User asks "what touches this?" or "how does this connect?"

## Process

### 1. Identify the Target

Ask or infer what the user wants to understand:
- A specific function, class, Manager, or CmdParser handler
- A subsystem (e.g. "the mail system", "guild logic")
- A data flow (e.g. "how does player login work end to end?")

### 2. Map Upward — Callers

Walk up from the target:
- Who calls this function/handler? (grep for function name, check CommandRegister.h for command routing)
- What triggers this code path? (client CS command? server-to-server Inter command? timer?)
- Which Managers or Logic layers are involved?

### 3. Map Downward — Dependencies

Walk down from the target:
- What does this module depend on? (other Managers, utility classes, data loaders)
- What data does it read/write? (player data, global data, caches)
- What protocols does it send/receive? (SC responses, Inter messages)

### 4. Map Sideways — Peers

Identify related modules at the same level:
- Other handlers in the same CmdParser
- Other methods on the same Manager
- Sibling modules in the same subsystem

### 5. Present the Map

Output a structured overview:

```
## Target: <module/function name>

### Call Chain (upward)
Client → CmdParser::<Handler>::onCmd → <Manager>::<method>

### Dependencies (downward)
- <Manager>::getData() — reads player data
- SafeSub() — balance calculation
- SC_<protocol> — sends response to client

### Peers (sideways)
- CmdParser::<OtherHandler> — related command in same parser
- <Manager>::<otherMethod> — sibling operation

### Key Data Flows
- Reads: PlayerData.stXXX, GlobalData.iXXX
- Writes: PlayerData.stXXX (calls setChanged())
- Protocols: CS_XXX → SC_YYY

### Notes
- <any important context: race conditions, ordering constraints, known issues>
```

Use the project's actual vocabulary — Manager names, struct names, sdp command names — not generic terms.

## C++ Game Server Specifics

- Always check `CommandRegister.h` for command routing (REGISTER_COMMAND entries)
- Look for Manager singletons and their dependencies
- Check `.sdp` files in `Common/` (CS/SC) and `Inter/` (server-to-server) for protocol definitions
- Note `setChanged()` calls — these indicate persistent state modifications
- Identify which layer owns the logic (CmdParser should only parse + delegate, Manager owns business logic)
