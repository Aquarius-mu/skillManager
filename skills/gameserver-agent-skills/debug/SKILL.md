---
name: debug
description: Disciplined diagnosis loop for hard bugs and performance regressions. Reproduce → minimise → hypothesise → instrument → fix → review. Use when something is broken, throwing errors, or regressing.
---

# Debug

A discipline for hard bugs. Skip phases only when explicitly justified. Use the project's domain glossary (module names, struct names) to build a clear mental model before diving in.

## Phase 1 — Build a Feedback Loop

**This is the skill.** If you have a fast, deterministic, agent-runnable pass/fail signal for the bug, you will find the cause. If you don't, no amount of staring at code will save you.

Spend disproportionate effort here. **Be aggressive. Be creative. Refuse to give up.**

### Ways to Build One (try in order)

1. **Reproduce via server log** — find the exact error in the game server log, capture the call stack or error code
2. **CLI invocation / GM command** — trigger the bug via a GM command on the dev server
3. **Reproduce via client** — replicate the exact client sequence that triggers the bug
4. **Throwaway harness** — add a temporary GM command that exercises the broken code path in isolation
5. **Instrument the code path** — add tagged `MLOG` calls: `MLOG_DEBUG("...[DEBUG-a4f2] value=%d", iValue)`, recompile, redeploy
6. **Property loop** — if the bug is "sometimes wrong output", trigger it 100× and look for the failure mode
7. **Differential loop** — compare behavior between two SVN revisions by checking out each and redeploying
8. **Bisection** — if the bug appeared between two known SVN revisions, use `svn log -r N:M --limit 50` to find suspect commits, then `svn update -r <REV>` + redeploy to binary-search for the culprit

### Iterate on the Loop

Once you have a loop:
- Can I make it faster? (Narrow the trigger to fewer steps)
- Can I make the signal sharper? (Assert on the specific symptom, not just "server crashed")
- Can I make it more deterministic? (Eliminate timing or state dependencies)

### When You Cannot Build a Loop

Stop and say so explicitly. List what you tried. Ask the user for: (a) a captured log file or crash dump, (b) exact reproduction steps, or (c) permission to add temporary production instrumentation.

**Do not proceed to Phase 2 without a loop.**

## Phase 2 — Reproduce

Run the loop. Confirm:

- [ ] The failure mode matches what the user described — not a different error nearby
- [ ] Reproducible across multiple attempts (or at a high enough rate)
- [ ] Exact symptom captured (error code, wrong value, crash location)

## Phase 3 — Hypothesise

Generate **3–5 ranked hypotheses** before testing any of them.

Each hypothesis must be falsifiable:
> *"If X is the cause, then changing Y will make the bug disappear / changing Z will make it worse."*

**Show the ranked list to the user before testing.** They often have domain knowledge that re-ranks instantly. Proceed with your ranking if the user is AFK.

## Phase 4 — Instrument

Each probe maps to a specific prediction from Phase 3. **Change one variable at a time.**

Tool preference:
1. **Targeted `MLOG_DEBUG` calls** at the boundaries that distinguish hypotheses
2. **Breakpoint via gdb** if the environment supports it
3. Never "log everything and grep"

**Tag every debug log** with a unique prefix, e.g. `[DEBUG-a4f2]`. Cleanup becomes a single grep. Remove all tagged logs before committing the fix.

**For performance regressions:** Establish a baseline timing measurement first; then bisect to find which revision introduced the slowdown. Measure first, fix second.

## Phase 5 — Fix

Apply the minimal fix for the confirmed root cause. Don't expand scope.

After fixing:
1. Re-run the Phase 1 feedback loop — confirm the bug no longer reproduces
2. Invoke `/review` — get a code review on the fix before committing
3. Remove all `[DEBUG-...]` instrumentation (`grep -r "DEBUG-a4f2" .`)
4. `svn commit -m "fix: <root cause description>"`

## Phase 6 — Post-Mortem

Required before declaring done:

- [ ] Original reproduction no longer works
- [ ] All `[DEBUG-...]` instrumentation removed
- [ ] Throwaway GM commands deleted
- [ ] The root cause is stated in the SVN commit message
- [ ] Ask: what would have prevented this bug? If architectural change is needed, invoke `/architect` with the specifics
