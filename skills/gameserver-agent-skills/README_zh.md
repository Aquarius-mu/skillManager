> 📦 **此技能包已合并进 [Aquarius-mu/skillManager](https://github.com/Aquarius-mu/skillManager)（`skills/gameserver-agent-skills/`），本目录为唯一维护源。原独立仓库 `Aquarius-mu/gameserver-agent-skills` 已归档只读。**

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

专为 C++ 游戏服务器开发设计的统一 AI Agent Skill 包。

融合了 [obra/superpowers](https://github.com/obra/superpowers) 与 [mattpocock/skills](https://github.com/mattpocock/skills) 两个开源 Skill 包的精华，去除所有自动化测试依赖，适配以下项目特点：

- **语言：** C++17
- **版本控制：** SVN（非 git）
- **质量门禁：** 编译通过 → 代码复审 → `svn commit`

---

## 快速开始

```bash
# 安装所有 skills
npx skills add Aquarius-mu/gameserver-agent-skills -g

# 重启 Claude Code，然后使用任意 skill
/brainstorm   # 探索功能需求
/debug        # 诊断 Bug
/plan         # 编写实现计划
```

---

## 工作流

### 功能开发

```
想法 → /brainstorm → /to-prd → /plan → /to-issues → /implement 循环 → svn commit
```

### Bug 修复

```
Bug 报告 → /debug → /implement → /review → svn commit
```

### 架构优化

```
/zoom-out → /architect → /plan → /implement 循环
```

---

## Skill 一览

| Skill | 说明 |
|-------|------|
| `/guide` | 所有 skill 的使用指南和调用时机 |
| `/brainstorm` | 写代码前先探索需求、产出设计文档 |
| `/to-prd` | 将对话内容转化为正式 PRD |
| `/plan` | 编写包含精确代码和命令的分步实现计划 |
| `/to-issues` | 将计划拆分为可独立提交的垂直切片 Issue |
| `/implement` | 执行循环：实现 → `./build.sh` → `/review` → `svn commit` |
| `/review` | 提交前派发代码复审 Subagent |
| `/debug` | 纪律性 Bug 诊断：构建反馈循环 → 假设验证 → 修复 |
| `/architect` | 发现并修复架构问题，降低耦合 |
| `/zoom-out` | 在不熟悉的代码区域获取模块和调用关系全图 |
| `/prototype` | 构建一次性 C++ 原型来验证设计思路 |
| `/grill` | 对计划或设计进行彻底追问，直到达成共识 |
| `/triage` | 将 Issue 通过状态机流转 |
| `/handoff` | 将当前会话压缩为交接文档供下一个 Agent 接力 |
| `/caveman` | 超压缩输出模式（减少约 75% Token）|

---

## 安装

### 通过 npx skills 安装（推荐）

```bash
npx skills add Aquarius-mu/gameserver-agent-skills -g
```

### 手动安装（创建软链接）

```bash
SKILLS_DIR="$HOME/.agents/skills"
PACK_DIR="/path/to/gameserver-agent-skills"

for skill in guide brainstorm plan implement review debug grill architect prototype to-prd to-issues triage zoom-out handoff caveman; do
  ln -sf "$PACK_DIR/$skill" "$SKILLS_DIR/$skill"
done
```

---

## 来源说明

本包融合并改编自两个开源 Skill 集合：

- [obra/superpowers](https://github.com/obra/superpowers) — brainstorming、writing-plans、requesting-code-review
- [mattpocock/skills](https://github.com/mattpocock/skills) — diagnose、improve-codebase-architecture、to-prd、to-issues、triage 等

所有自动化测试相关内容已移除。代码质量通过代码复审而非自动化测试来保障。

---

## 许可证

MIT
