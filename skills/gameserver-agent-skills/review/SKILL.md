---
name: review
description: Dispatch a code reviewer subagent before any SVN commit. Mandatory after each implement slice, after completing a major feature, and before committing to trunk.
---

# Review

Dispatch a code reviewer subagent to catch issues before they cascade into more work. The reviewer gets focused context — not your session history.

**Core principle:** Review early, review often. Fix Critical and Important issues before committing.

## When to Review

**Mandatory:**
- After each implement slice (before `svn commit`)
- After completing a major feature
- Before committing to trunk

**Optional but valuable:**
- When stuck — fresh perspective often unblocks
- Before a large refactor — establish a baseline

## How to Request

**1. Get SVN revisions:**

```bash
# For committed changes:
HEAD_REV=$(svn info --show-item last-changed-revision)
BASE_REV=$((HEAD_REV - 1))

# For uncommitted local changes — skip rev lookup, just diff:
svn status
svn diff
```

**2. Dispatch a code reviewer subagent** (use Agent tool, `general-purpose` type):

Fill in these placeholders from `code-reviewer-prompt.md`:
- `{DESCRIPTION}` — brief summary of what was built
- `{PLAN_OR_REQUIREMENTS}` — what it should do
- `{BASE_REV}` — starting SVN revision (or `PREV`)
- `{HEAD_REV}` — ending revision (or use `svn diff` for uncommitted)

**3. Act on feedback:**
- **Critical** — fix immediately, never commit with unresolved Critical issues
- **Important** — fix before committing
- **Minor** — note for later, optional

## Reviewer Prompt Template

```
You are a Senior Code Reviewer for a C++ game server.
Review the changes below against the requirements and identify issues before they cascade.

## What Was Implemented
{DESCRIPTION}

## Requirements / Plan
{PLAN_OR_REQUIREMENTS}

## SVN Range to Review
Base revision: {BASE_REV}
Head revision: {HEAD_REV}

```bash
# For committed revisions:
svn diff -r {BASE_REV}:{HEAD_REV} --summarize
svn diff -r {BASE_REV}:{HEAD_REV}

# For uncommitted local changes:
svn status
svn diff
```

## What to Check

**C++ game server conventions:**
- Naming: m_ prefix for members; i/b/s/v/st/p prefixes for locals; PascalCase classes
- Subtraction: must use `SafeSub()` — no direct `--` or `-=`
- Map lookups: must use `FindMapPtr` — no raw `.find()` + iterator compare
- String conversion: `ToString()` not `std::to_string()`
- Control flow: all `if`/`for`/`while` bodies use full brace blocks, braces on their own lines
- `setChanged()` called after all persistent data modifications
- `sendResponse()` only in CmdParser layer, never inside Logic/Manager
- New CS/SC commands registered in `CommandRegister.h`
- Error codes use `ERR_` prefix; `iRet` declared as `int32_t`

**Architecture:**
- CmdParser / Logic layer separation respected?
- `loop()` functions have throttle guards?
- Protocol IDs unique and non-overlapping?

**Logic correctness:**
- Off-by-one errors?
- Integer underflow risks?
- Missing null checks on pointer lookups?

## Output Format

### Strengths
[What's well done — be specific]

### Issues

#### Critical (Must Fix)
[Bugs, data loss risks, broken functionality, convention violations that cause runtime errors]

#### Important (Should Fix Before Commit)
[Architecture problems, missing setChanged(), wrong layer placement, missing registration]

#### Minor (Nice to Have)
[Style, optimization, documentation polish]

For each issue: file:line reference, what's wrong, why it matters, how to fix.

### Assessment

**Ready to commit?** [Yes | No | With fixes]

**Reasoning:** [1-2 sentence technical assessment]
```

## Example

```
[Just implemented Task 2: Add feature query]

BASE_REV=$(svn info --show-item last-changed-revision)  # e.g. 4820
BASE_REV=$((BASE_REV - 1))  # 4819 — before this task

[Dispatch code reviewer subagent]
  DESCRIPTION: Added getXxxRank() in RoleXxx.cpp and handle_Xxx_Yyy handler
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/2026-05-12-feature.md
  BASE_REV: 4819
  HEAD_REV: 4820

[Reviewer returns]:
  Strengths: Clean iRet propagation, correct layer separation
  Issues:
    Important: Missing setChanged() after m_oCache.iScore update
    Minor: Magic number 100 for rank cap — extract to constant
  Assessment: Fix before commit

[Fix setChanged() call]
svn commit -m "feat: add feature query"
```
