<p align="center">
  <a href="./README.md"><img src="https://img.shields.io/badge/lang-English-blue" alt="English"></a>
  <a href="./README_zh.md"><img src="https://img.shields.io/badge/lang-中文-red" alt="中文"></a>
</p>

<p align="center">
  <a href="https://github.com/Aquarius-mu/gameserver-agent-skills/stargazers"><img src="https://img.shields.io/github/stars/Aquarius-mu/gameserver-agent-skills" alt="Stars"></a>
  <a href="https://github.com/Aquarius-mu/gameserver-agent-skills/blob/master/LICENSE"><img src="https://img.shields.io/github/license/Aquarius-mu/gameserver-agent-skills" alt="License"></a>
  <img src="https://img.shields.io/badge/skills-15-blue" alt="Skills">
</p>

# gameserver-agent-skills

A unified AI agent skill pack for C++ game server development.

Merges the best of [obra/superpowers](https://github.com/obra/superpowers) and [mattpocock/skills](https://github.com/mattpocock/skills), stripped of all test-framework assumptions, and adapted for:

- **Language:** C++17
- **Build:** `./qmake.sh` (Unity Build + distcc)
- **VCS:** SVN (not git)
- **Quality gate:** compile clean → code review → `svn commit`

---

## Quick Start

```bash
# Install all skills
npx skills add Aquarius-mu/gameserver-agent-skills -g

# Restart Claude Code, then use any skill
/brainstorm   # Explore a feature idea
/debug        # Diagnose a bug
/plan         # Write an implementation plan
```

---

## Workflow

### Feature Development

```
idea → /brainstorm → /to-prd → /plan → /to-issues → /implement loop → svn commit
```

### Bug Fixing

```
bug report → /debug → /implement → /review → svn commit
```

### Architecture

```
/zoom-out → /architect → /plan → /implement loop
```

---

## Skills

| Skill | Description |
|-------|-------------|
| `/guide` | Overview of all skills and when to invoke them |
| `/brainstorm` | Explore requirements, produce a design doc before any code |
| `/to-prd` | Turn a conversation into a formal PRD |
| `/plan` | Write a step-by-step implementation plan with exact code |
| `/to-issues` | Slice a plan into independently-committable vertical slices |
| `/implement` | Execute: implement → `./qmake.sh` → `/review` → `svn commit` |
| `/review` | Dispatch a code reviewer subagent before any commit |
| `/debug` | Disciplined bug diagnosis: feedback loop → hypothesise → fix |
| `/architect` | Find and fix architectural friction, reduce coupling |
| `/zoom-out` | Map all relevant modules and callers in an unfamiliar area |
| `/prototype` | Build throwaway C++ code to answer a design question |
| `/grill` | Interview a plan or design relentlessly until shared understanding |
| `/triage` | Move issues through the triage state machine |
| `/handoff` | Compact the session into a document for the next agent |
| `/caveman` | Ultra-compressed output mode (~75% fewer tokens) |

---

## Installation

### Via npx skills (recommended)

```bash
npx skills add Aquarius-mu/gameserver-agent-skills -g
```

### Manual (symlink each skill)

```bash
SKILLS_DIR="$HOME/.agents/skills"
PACK_DIR="/path/to/gameserver-agent-skills"

for skill in guide brainstorm plan implement review debug grill architect prototype to-prd to-issues triage zoom-out handoff caveman; do
  ln -sf "$PACK_DIR/$skill" "$SKILLS_DIR/$skill"
done
```

---

## Origin

This pack merges and adapts two open-source skill collections:

- [obra/superpowers](https://github.com/obra/superpowers) — brainstorming, writing-plans, requesting-code-review
- [mattpocock/skills](https://github.com/mattpocock/skills) — diagnose, improve-codebase-architecture, to-prd, to-issues, triage, and more

All test-framework-specific content has been removed. Quality is enforced through code review, not automated tests.

---

## License

MIT
