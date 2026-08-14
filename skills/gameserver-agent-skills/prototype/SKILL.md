---
name: prototype
description: Build a throwaway prototype to answer a design question before committing to an implementation. Use when sanity-checking a data model, state machine, or design approach.
---

# Prototype

A prototype is **throwaway code that answers a question**. The question decides the shape.

## Pick a Branch

Identify the question being answered:

- **"Does this data model / state machine feel right?"** → Build a minimal C++ harness that exercises the key state transitions or data operations
- **"What should this protocol look like?"** → Sketch the sdp struct definitions and walk through the request/response flow

If genuinely ambiguous, default to whichever branch matches the surrounding code.

## Rules

1. **Throwaway from day one, clearly marked.** Name the file or directory so a reader instantly knows it's a prototype: `proto_xxx.cpp`, `scratch_xxx.sdp`
2. **One command to build.** Use `./qmake.sh`. The result must compile and run without thinking
3. **No persistence by default.** State lives in memory unless persistence is the question being answered
4. **Skip the polish.** No full error handling beyond what makes it runnable. The point is to learn fast and delete
5. **Surface the state.** After every operation, log the full relevant state so the question can be answered
6. **Delete or absorb when done.** Never leave prototype code rotting in the codebase

## Capture the Answer

The answer is the only thing worth keeping. Capture it in a `NOTES.md` next to the prototype, or in an SVN commit message, or as an ADR:

```markdown
## Question
[What were we trying to learn?]

## Answer
[What did we find out?]

## Decision
[What will we do as a result?]
```

Then delete the prototype and invoke `/plan` to begin the real implementation.
