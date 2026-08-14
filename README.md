# skillManager 🧰

个人技能库（Personal Skill Library）——用来收集、整理和版本管理我平时用到的 AI Agent 技能（Skill）。

每个技能是一个自包含的目录，含 `SKILL.md` 主文档（触发条件 + 使用流程 + 常见坑）、`references/` 参考规则和 `scripts/` 辅助脚本。技能设计遵循「零硬编码」原则：用户身份、密钥等一律运行时动态获取，任何人 clone 下来登录自己的账号即可直接用。

## 技能清单

| 技能 | 说明 | 依赖 |
|---|---|---|
| [daily-weekly-report](skills/daily-weekly-report) | 日报周报工作分析：把飞书聊天记录自动变成「早间梳理 / 一天总结 / 周报总结」三种产出 | `lark-cli`（im:message 权限即可） |

## 目录结构

```
skillManager/
├── README.md              # 本文件
├── install.sh             # 技能安装脚本
├── skills/                # 技能库（每个子目录一个技能）
│   └── daily-weekly-report/
│       ├── SKILL.md       # 技能主文档：触发词、流程、常见坑
│       ├── references/    # 各模式的详细规则
│       └── scripts/       # 数据采集 / 卡片生成脚本
└── LICENSE
```

## 安装技能

### 方式一：安装脚本（推荐）

```bash
# 把某个技能安装到目标技能目录
./install.sh daily-weekly-report ~/.hermes/skills
# 或安装到 Claude Code 技能目录
./install.sh daily-weekly-report ~/.claude/skills
```

不带参数会列出当前库里所有可安装的技能：

```bash
./install.sh
```

### 方式二：手动复制

```bash
cp -r skills/daily-weekly-report ~/.hermes/skills/
```

## 贡献新技能

往这个库里加技能只需三步：

1. 在 `skills/` 下新建一个以技能名命名的目录；
2. 放入 `SKILL.md`（必选，带 YAML frontmatter：`name` + `description`），以及可选的 `references/`、`scripts/`；
3. 更新上面的「技能清单」表格，然后提交 push。

技能规范参考 [SKILL.md 写作约定](#)（frontmatter 里 `description` 要写清触发条件，正文写清步骤和实测踩过的坑）。

## License

[MIT](LICENSE)
