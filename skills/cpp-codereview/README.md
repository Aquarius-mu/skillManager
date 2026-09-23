# cpp-codereview

**游戏服务器 C++ 代码审查的唯一入口。** 本项目所有 review / 代码复审请求都走这里。

---

## 整体流程

```
/cpp-codereview  或  "帮我 review"
  │
  ├─ Step 1  脚本工程准备（scripts/review_setup.py）
  │            · ssh 到 Linux 端跑 svn（本机工作副本格式过旧，跑不了）
  │            · diff 加真实行号标注
  │            · 解析 hunk 行号范围 → line_ranges
  │            · 按 ≤5 文件 / ≤300 变更行自动分组
  │            · 扫描 .ai_review/rules/*.md
  │
  ├─ Step 2  读 index.json，收集上下文（相邻文件 / 被调用实现 / svn log）
  │
  ├─ Step 3  每组 × 六个专项 subagent 并行
  │            🔒 security      安全与防刷
  │            🔗 pairing       配对操作完整性
  │            🧠 logic         逻辑正确性
  │            📐 convention    规范与项目约定
  │            ✍️ readability   可读性与设计质量
  │            📋 requirements  需求符合性
  │
  ├─ Step 4  去重合并（五规则）
  ├─ Step 5  对抗性验证（+ 独立 skeptic 复核 P0/P1）
  ├─ Step 6  双门过滤（置信度 ≥75 且 严重度 P0/P1）
  ├─ Step 7  报告（漏斗数 + 覆盖核对表 + 已排除清单）
  └─ Step 8  修复后复验（含批量替换的零残留检查）
```

---

## 目录结构

```
cpp-codereview/
├── SKILL.md                       # /cpp-codereview 入口，编排逻辑
├── README.md
├── scripts/
│   └── review_setup.py            # 工程准备：diff 收集 / 行号锚定 / 分组 / 规则扫描
├── reference/
│   └── review-method.md           # 公共裁决方法论（注入每个 subagent）
└── agents/                        # 六个专项 subagent（镜像，实际加载的是 ~/.claude/agents/）
    ├── code-review-security.md
    ├── code-review-pairing.md
    ├── code-review-logic.md
    ├── code-review-convention.md
    ├── code-review-readability.md
    └── code-review-requirements.md
```

主 agent 定义在 `~/.claude/agents/code-review.md`（不在本目录内），与 `SKILL.md` 内容一致。

**改规则时两处都要改**，或改完用：
```bash
cp ~/.claude/agents/code-review*.md ~/.claude/skills/cpp-codereview/agents/
```

---

## 用法

```bash
# 本项目（svn 必须走远端）
python "~/.claude/skills/cpp-codereview/scripts/review_setup.py" \
  --ssh user@<your-host> --remote-dir '~/<your-branch>' \
  --dir "Z:/<your-branch>"

# 本地 svn 可用的环境（不加 --ssh）
python review_setup.py --dir /path/to/code

# Git 项目
python review_setup.py --vcs git

# 调整分组粒度（默认 5 文件 / 300 行）
python review_setup.py --max-files 3 --max-lines 200
```

也可用环境变量：`REVIEW_SSH=user@host`、`REVIEW_REMOTE_DIR=~/path`。

---

## 项目自定义规则

在代码仓库任意层级放 `.ai_review/rules/*.md`，审查时自动加载（仓库根优先，再按文件祖先目录浅到深，最多 10 个文件 / 200KB）。

写项目专属的检查点、踩坑清单放这里，不用改 skill。

---

## 版本演进

| 版本 | 变化 |
|---|---|
| v6 | 单 agent 四维度检查清单 |
| v7 | 拆成编排器 + 4 个专项 subagent |
| v8 | 加需求符合性、可读性两个维度；加证据五要素、双分数、对抗性验证、双门过滤、漏斗报告 |
| **v9** | **加工程保证层**：行号锚定与校验、自动分组并行、`.ai_review/rules` 扫描；加 C++ 陷阱检查（基类字段覆盖 / 主循环阻塞 / 循环内状态污染 / 并列分支数值）；修复后复验 |

### v9 的蒸馏来源

| 来源 | 吸收了什么 |
|---|---|
| `local-review`（本地备份） | 三段式流程（发现→关键事实核验→自我反证）、**候选卡片五字段**（写不出 failure_path 直接过滤）、**假设验证闭环**（assumptions / counter-evidence / 概率分级）、**高误报类别强制同类代码搜索 + 裁决规则**、evidence_strength 三级、**强制降级三约束**、行号范围校验、自动分组并行、`.ai_review/rules` |
| `analyzer_cpp_prompt`（同上） | C++ 专项：指针四步裁决（触发点→安全证明→失败路径→patch 增量）、**虚初始化函数中成员赋值被继承链覆盖**（CHECK-CPP-VINIT）、并列分支数值一致性 |
| `review` v6（本地备份） | 循环内状态污染检查项 |
| `issue-code-repairer`（本地备份） | 最小改动原则、修复前自检 |
| `verify-batch`（本地备份） | 批量替换后的零残留 + 全覆盖 + 关联文件检查（并入 Step 8） |
| `requesting-code-review`（本地备份） | 只喂精炼上下文、不喂会话历史 |
| `alibaba/open-code-review` | 纯语言驱动的审查缺硬约束；覆盖完整性 / 位置漂移 / 质量波动三大根因 |
| `feiskyer/claude-code-settings` | 证据五要素、双分数、证伪式验证、双门过滤、漏斗报告 |
| `wshobson/agents` | 多审查者合并五规则、严重性硬性下限 |
| Google eng-practices | 审查关注点分布（功能 40% / 可读性 25% / 性能 15% / 安全 12%） |

**未吸收（有意舍弃）**：`local-review` 的多语言 analyzer（go/rust/vue/java/python…）、Git MR 的 `context_dir` / `walkthrough` / wiki 上下文、JSON orchestrator 协议——本项目只用 C++ + SVN。

---

## 不做什么

- 不审 diff 范围外的存量代码
- 不报运行时不可能触发的边界（游戏数值有配置上限约束）
- 不报纯格式 / 空行 / linter 能处理的内容
- 不凑 finding——没问题就输出"审查通过，未发现问题" + 完整覆盖核对表
