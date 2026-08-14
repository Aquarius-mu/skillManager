---
name: plan
description: Use when you have a spec or requirements for a multi-step task, before touching code. Writes a step-by-step implementation plan with exact file paths, code, and build commands.
---

# Plan

Write a comprehensive implementation plan. Every step must be self-contained — the implementer may read tasks out of order.

**Announce at start:** "I'm using the plan skill to create the implementation plan."

**Project:** Existing C++ game server. No scaffolding needed. VCS = SVN.

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Scope Check

If the spec covers multiple independent subsystems, suggest breaking into separate plans — one per subsystem. Each plan should produce working, deployable code on its own.

## File Structure

Before defining tasks, map which files will be created or modified:

- Follow existing patterns: one CmdParser cpp per feature area, one Logic Manager per domain
- Prefer smaller focused files; don't unilaterally restructure existing code
- Files that change together should live together

## Plan Document Header

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** Execute task-by-task using the `/implement` skill. Steps use `- [ ]` for tracking.

**Goal:** [One sentence]

**Architecture:** [2-3 sentences]

**Tech Stack:** C++17, SVN, build script

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Modify: `GameServer/CmdParser/CmdParserXxx.cpp:45-80`
- Modify: `GameServer/Logic/RoleXxx.cpp`
- Modify: `Common/ProtoXxx.sdp`

- [ ] **Step 1: [Protocol] Define sdp structs**

```cpp
// in Common/ProtoXxx.sdp
// exact structs to add
```

- [ ] **Step 2: [Logic] Implement business logic**

```cpp
// exact code to add in RoleXxx.cpp
```

- [ ] **Step 3: [Handler] Implement CmdParser handler**

```cpp
// exact handler in CmdParserXxx.cpp
int32_t HandlerManager::handle_Xxx_Yyy(Role &role, const Proto::Req_Xxx_Yyy &stReq)
{
    int32_t iRet = role.xxxMgr->doSomething(stReq.iParam);
    if (iRet != 0)
    {
        return iRet;
    }
    Proto::Rsp_Xxx_Yyy stSend;
    role.xxxMgr->fillState(stSend.stState);
    sendResponse(stSend);
    return 0;
}
```

- [ ] **Step 4: Build**

Run: `cd <workdir> && ./build.sh`
Expected: no errors, binary produced

- [ ] **Step 5: Code review**

Invoke `/review`. Fix all Critical and Important issues before committing.

- [ ] **Step 6: Commit**

```bash
svn commit -m "feat: [description]"
```
````

## No Placeholders

These are plan failures — never write them:
- "TBD", "TODO", "implement later"
- "Add appropriate error handling" / "handle edge cases"
- "Similar to Task N" — always repeat the actual code
- Steps that describe what to do without showing how
- References to types or functions not defined in any task

## Project-Specific Checks

Every plan must verify each new feature:
- [ ] CmdId enum values are unique and non-overlapping
- [ ] New CS/SC commands registered in `CommandRegister.h` via `REGISTER_COMMAND`
- [ ] All subtraction uses `SafeSub()`
- [ ] All map lookups use `FindMapPtr` (no raw `.find()`)
- [ ] `setChanged()` called after every data modification
- [ ] `sendResponse()` only in CmdParser layer, never in Logic layer
- [ ] All control flow bodies have full brace blocks on separate lines

## Self-Review

After writing the complete plan:

1. **Coverage** — can you point to a task for every requirement in the spec?
2. **Placeholders** — search for any of the failure patterns above
3. **Consistency** — do function names used in later tasks match their definitions in earlier tasks?

Fix issues inline, then offer execution:

**"Plan saved to `docs/plans/<filename>.md`. Ready to execute — I'll work through each task with `/implement`, requesting code review after each task. Proceed?"**
