---
name: implement
description: Disciplined implement→build→review→commit loop for C++ game server features. Use when executing a plan task, fixing a bug, or making any code change. One vertical slice at a time.
---

# Implement

Execute one vertical slice at a time: implement → build clean → code review → SVN commit. Never pile up changes across multiple slices before reviewing.

## Core Loop

```
SLICE: implement change
BUILD: ./build.sh  →  must compile with zero new errors/warnings
REVIEW: invoke /review skill  →  fix Critical + Important issues
COMMIT: svn commit -m "feat/fix: <description>"
```

Repeat per slice. **Do not proceed to the next slice until the current one is committed.**

## Anti-Pattern: Big-Bang Implementation

Do NOT implement multiple tasks, then build, then review everything at once.

```
WRONG:
  change1 + change2 + change3 → build → one big review → commit

RIGHT:
  change1 → build → review → commit
  change2 → build → review → commit
  change3 → build → review → commit
```

Big-bang implementations fail review for reasons that cascade. Small slices = small reviews = faster iteration.

## Planning the Slice

Before writing any code for a task:

- [ ] Read the relevant files: sdp definitions, CmdParser handler, Logic Manager
- [ ] Understand what currently exists — don't duplicate or conflict
- [ ] Identify the vertical path: sdp → Logic → CmdParser → response
- [ ] Confirm the slice boundaries with the plan

## C++ Game Server Checklist

Before building, verify:

- [ ] All subtraction uses `SafeSub(value, sub)` — no `--` or `-=`
- [ ] All map lookups use `FindMapPtr` — no raw `.find()` + iterator compare
- [ ] `setChanged()` called after every data modification that needs persistence
- [ ] `sendResponse()` only in CmdParser layer — never inside Logic/Manager
- [ ] All control flow bodies (`if`/`for`/`while`) use full brace blocks, braces on their own lines
- [ ] New CS/SC commands registered in `CommandRegister.h` via `REGISTER_COMMAND`
- [ ] Integer variables use `int32_t` for iRet (not `uint32_t`)
- [ ] Error codes use `ERR_` prefix, propagated via `if (iRet != 0) { return iRet; }`
- [ ] Protocol IDs are unique — check the surrounding CmdId enum range before assigning

## Build

```bash
cd <workdir> && ./build.sh
```

Expected: clean compilation, no new warnings. Fix any warnings before proceeding to review.

## After Build — Request Review

Invoke the `/review` skill. Pass:
- **DESCRIPTION**: what this slice implements
- **BASE_REV**: the SVN revision before your changes
- **HEAD_REV**: current revision (or use `svn diff` for uncommitted changes)

Fix all **Critical** issues immediately. Fix all **Important** issues before committing. Log **Minor** issues for later.

## Commit

```bash
svn commit -m "<type>: <concise description>"
```

Commit types: `feat` (new feature), `fix` (bug fix), `refactor` (no behavior change), `docs` (documentation).

## Refactor (optional, after all slices committed)

After all slices are done:
- [ ] Extract duplicated logic
- [ ] Simplify complex functions
- [ ] Verify naming conventions (m_ prefix, i/b/s/v/st/p prefixes, PascalCase classes)
- [ ] Build clean after each change
- [ ] Request review for the refactor batch
