<p align="center">
  <h1 align="center">🧰 skillManager</h1>
  <p align="center">
    个人 AI Agent 技能库 · 收集 · 整理 · 版本管理
  </p>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="#-技能总览"><img src="https://img.shields.io/badge/Skills-9%2B-brightgreen.svg" alt="Skills"></a>
  <a href="#-安装技能"><img src="https://img.shields.io/badge/Platform-Hermes%20%7C%20Claude-purple.svg" alt="Platform"></a>
  <img src="https://img.shields.io/github/last-commit/Aquarius-mu/skillManager" alt="Last Commit">
  <img src="https://img.shields.io/github/stars/Aquarius-mu/skillManager?style=social" alt="Stars">
</p>

---

> 一个开箱即用的个人技能库，把平时用顺手、反复踩坑总结出来的 AI Agent 技能沉淀成可复用、可版本化、可分享的资产。每个技能都是自包含目录，clone 下来登录自己的账号就能直接用。

## ✨ 特性

| | |
|---|---|
| 🧩 **自包含** | 每个技能一个目录，含 `SKILL.md` 主文档 + `references/` 参考规则 + `scripts/` 辅助脚本 + `assets/` 资产 |
| 🔒 **零硬编码** | 用户身份、密钥、路径一律运行时动态获取，任何人 clone 下来即可使用，不泄露隐私 |
| 🚀 **一键安装** | 自带 `install.sh`，一条命令列出 / 安装任意技能到 Hermes 或 Claude |
| 🎨 **多场景覆盖** | 数据分析 · 消息交互 · 可视化 · 开发流程 · 创意指导 · 质量保障 · 网页设计 |
| 📚 **踩坑沉淀** | 正文写清触发条件、使用流程和实测踩过的坑，而不是泛泛的方法论 |
| 🔄 **Git 版本管理** | 每个技能的演进都有完整提交历史，可回滚、可 diff、可协作 |

## 📦 技能总览

| 技能 | 类型 | 说明 | 依赖 |
|---|---|---|---|
| 📊 [daily-weekly-report](skills/daily-weekly-report) | 数据分析 | 日报周报工作分析：把飞书聊天记录自动变成「早间梳理 / 一天总结 / 周报总结」三种产出 | `lark-cli`（im:message 权限即可） |
| 💬 [feishu-card](skills/feishu-card) | 消息交互 | 飞书交互卡片（schema 2.0）：构建和发送卡片消息，含 @提及、流式思考态、原地更新、按钮/选择器交互 | `lark-cli` + `jq` + `python3` |
| 🎨 [beautiful-feishu-whiteboard](skills/beautiful-feishu-whiteboard) | 可视化 | 生成美观、可编辑的飞书画板：35 种配色风格，偏向技术/代码场景（架构图、类图、时序图、状态机等） | `lark-cli` + `@larksuite/whiteboard-cli` + Node 20+ |
| 🎮 [gameserver-agent-skills](skills/gameserver-agent-skills) | 技能包（15 个子技能） | C++ 游戏服务器开发技能包：brainstorm / to-prd / plan / implement / review / debug / architect 等全流程，SVN 工作流，代码复审驱动质量门禁 | C++17 + SVN |
| 🎬 [tig-acting-task](skills/tig-acting-task) | 创意指导 | AI 视频/场景表演指导（Tigran 方法）：为角色写 ACTING TASK 表演任务块，让 AI 生成的角色「眼睛活起来」 | 无（纯方法论） |
| 🛡️ [adversarial-gameplay-acceptance](skills/adversarial-gameplay-acceptance) | 质量保障 | 游戏后端功能的对抗性业务验收：以策划/QA/玩家三视角验证服务端反馈闭环，揪出「玩家操作了却没正确反馈」的 bug | `python3`（scripts 工具） |
| ✨ [silk-design](skills/silk-design) | 网页设计 | 丝绸动效网页设计：默认带高端丝滑动效做网页/落地页，Lenis 平滑滚动 + reveal + 视差 + marquee + 页面转场 + 13 种动态背景 + 10 套风格皮肤 | React + Vite + Tailwind v4 + motion + GSAP + Lenis |
| 📰 [ai-daily-pulse](skills/ai-daily-pulse) | 资讯聚合 | 每日 AI 行业新闻聚合：30+ 白名单源（官方博客/arXiv/GitHub/HuggingFace/国内媒体）采集 → 去重评分 → 飞书 Interactive Card 或 Markdown 推送；内置自我进化引擎（信源自动拓展 + 品质信用分） | python3（标准库）+ 飞书 App 凭证（可选） |
| 🖼️ [xhs-zine-cover](skills/xhs-zine-cover) | 图像生成 | 小红书 Zine 风格封面生成器：纯代码绘制 3:4 极简独立杂志封面（撕纸边缘/Risograph 颗粒/套色偏移），文字拼写 100% 准确、风格统一 | python3 + Pillow |

> 💡 「单个技能」= 一个技能一个目录；「技能包」= 一个目录里含多个子技能（自带 install.sh / package.json / README）。两者并列放在 `skills/` 下。

## 🚀 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Aquarius-mu/skillManager.git
cd skillManager

# 2. 查看库里有哪些技能
./install.sh

# 3. 安装你需要的技能（以 silk-design 为例）
./install.sh silk-design ~/.hermes/skills
```

三步搞定，登录自己的账号即可直接使用。

## 📥 安装技能

### 方式一：安装脚本（推荐）

```bash
# 列出库里的技能
./install.sh

# 安装单个技能到目标技能目录（默认自动识别 ~/.hermes/skills 或 ~/.claude/skills）
./install.sh daily-weekly-report ~/.hermes/skills
./install.sh beautiful-feishu-whiteboard ~/.hermes/skills

# 技能包用自己的安装脚本（见包内 README）
npx skills add Aquarius-mu/gameserver-agent-skills -g
```

### 方式二：手动复制

```bash
cp -r skills/beautiful-feishu-whiteboard ~/.hermes/skills/
```

## 📁 目录结构

```
skillManager/
├── README.md              # 本文件（技能总览 + 安装 + 贡献指南）
├── install.sh             # 技能安装脚本（自动列出 / 一键安装）
├── LICENSE                # MIT 开源协议
└── skills/                # 技能库（单个技能 + 技能包并列）
    ├── daily-weekly-report/               # 📊 单个技能
    ├── feishu-card/                       # 💬 单个技能
    ├── beautiful-feishu-whiteboard/       # 🎨 单个技能（含 35 套风格资产）
    ├── gameserver-agent-skills/           # 🎮 技能包（15 个子技能）
    ├── tig-acting-task/                   # 🎬 单个技能
    ├── adversarial-gameplay-acceptance/   # 🛡️ 单个技能
    └── silk-design/                       # ✨ 单个技能（丝绸动效网页设计）
```

## ➕ 贡献新技能

往这个库里加技能只需三步：

1. **放目录** —— 单个技能在 `skills/` 下建一个以技能名命名的目录；整包技能把整个包目录放进 `skills/`；
2. **写文档** —— 放入 `SKILL.md`（必选，带 YAML frontmatter：`name` + `description`），以及可选的 `references/`、`scripts/`、`assets/`、`templates/`；
3. **更清单** —— 更新上方「技能总览」表格，然后提交 push。

技能规范：frontmatter 里 `description` 要写清触发条件，正文写清步骤和实测踩过的坑。

## 🔒 设计原则

所有技能遵循「**零硬编码**」原则：

- **身份** —— 不写死用户名、open_id、chat_id，运行时动态解析；
- **密钥** —— 不硬编码 token / secret，通过环境变量或登录态获取；
- **路径** —— 不写死绝对路径，用 `~` 或相对路径，保证可移植；
- **隐私** —— 收录前逐文件扫描，清理真实姓名、公司名、具体代码指纹后再公开。

## ❓ 常见问题

**Q：为什么技能要「零硬编码」？**
A：这样任何人 clone 下来、登录自己的账号就能直接用，既方便分享，也不会把作者的真实身份和密钥泄露到公开仓库。

**Q：`install.sh` 和手动复制有什么区别？**
A：`install.sh` 会自动识别目标平台（Hermes / Claude）的 skills 目录、校验技能是否存在，并覆盖式安装；手动复制则完全由你控制。

**Q：如何判断某个技能会不会泄露隐私？**
A：收录前会做隐私扫描（真实姓名 / 公司名 / open_id / 密钥 / 具体路径 / 代码指纹）。你可以放心，公开仓库里的内容都是清理过的。

**Q：技能包里和单个技能能混放吗？**
A：可以。两者并列放在 `skills/` 下，`install.sh` 会自动识别所有含 `SKILL.md` 的目录。

## 📄 License

[MIT](LICENSE) © Aquarius-mu

---

<p align="center">
  Made with ❤️ for personal productivity · 持续沉淀 · 欢迎自取
</p>
