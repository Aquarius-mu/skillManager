# skillManager 🧰

个人技能库（Personal Skill Library）——用来收集、整理和版本管理我平时用到的 AI Agent 技能（Skill）。

每个技能是一个自包含的目录，含 `SKILL.md` 主文档（触发条件 + 使用流程 + 常见坑）、`references/` 参考规则和 `scripts/` 辅助脚本。技能设计遵循「零硬编码」原则：用户身份、密钥等一律运行时动态获取，任何人 clone 下来登录自己的账号即可直接用。

## 技能清单

| 技能 | 类型 | 说明 | 依赖 |
|---|---|---|---|
| [daily-weekly-report](skills/daily-weekly-report) | 单个技能 | 日报周报工作分析：把飞书聊天记录自动变成「早间梳理 / 一天总结 / 周报总结」三种产出 | `lark-cli`（im:message 权限即可） |
| [gameserver-agent-skills](skills/gameserver-agent-skills) | 技能包（15 个子技能） | C++ 游戏服务器开发技能包：brainstorm / to-prd / plan / implement / review / debug / architect 等全流程，SVN 工作流，代码复审驱动质量门禁 | C++17 + SVN + `./qmake.sh` |

> `gameserver-agent-skills` 是一个**技能包**（一个目录里含多个子技能，自带 install.sh / package.json / README），与 `daily-weekly-report` 这种单个技能并列放在 `skills/` 下。

## 目录结构

```
skillManager/
├── README.md              # 本文件
├── install.sh             # 技能安装脚本
├── skills/                # 技能库（单个技能 + 技能包）
│   ├── daily-weekly-report/           # 单个技能
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/
│   └── gameserver-agent-skills/       # 技能包（15 个子技能）
│       ├── README.md / README_zh.md
│       ├── install.sh / package.json
│       └── {15 个技能目录，各自含 SKILL.md}
└── LICENSE
```

## 安装技能

### 方式一：安装脚本（推荐）

```bash
# 列出库里的技能
./install.sh

# 安装单个技能到目标技能目录
./install.sh daily-weekly-report ~/.hermes/skills

# 技能包用自己的安装脚本（见包内 README）
npx skills add Aquarius-mu/gameserver-agent-skills -g
```

### 方式二：手动复制

```bash
cp -r skills/daily-weekly-report ~/.hermes/skills/
```

## 贡献新技能

往这个库里加技能只需三步：

1. 单个技能放进 `skills/` 下建一个以技能名命名的目录；整包技能则把整个包目录放进 `skills/`；
2. 放入 `SKILL.md`（必选，带 YAML frontmatter：`name` + `description`），以及可选的 `references/`、`scripts/`；
3. 更新上面的「技能清单」表格，然后提交 push。

技能规范：frontmatter 里 `description` 要写清触发条件，正文写清步骤和实测踩过的坑。

## License

[MIT](LICENSE)
