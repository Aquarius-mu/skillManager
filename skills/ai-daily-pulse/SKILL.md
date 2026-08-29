---
name: ai-daily-pulse
description: >
  每日 AI 行业新闻聚合工具。从 30+ 白名单源(RSS/Atom/JSON API/Web)采集 AI 新闻,经主 Agent
  评分筛选后,通过飞书群机器人推送 Interactive Card 卡片;未配置飞书 Bot 时直接在对话窗口
  输出 Markdown 摘要。当用户提到 AI日报、AI每日推送、今日AI新闻、AI Daily Pulse、
  ai-daily-pulse 时使用此 Skill。
license: MIT
metadata:
  version: 1.0.0
  author: Vincent
  owner: Vincent
  capabilities:
    - cap-network
  api_endpoints:
    outbound:
      - host: open.feishu.cn
        purpose: 飞书 Open API (tenant_access_token + 群消息推送)
        scheme: https
      - host: openai.com
        purpose: OpenAI 官方博客 RSS
        scheme: https
      - host: www.anthropic.com
        purpose: Anthropic 新闻页 (Web 抓取)
        scheme: https
      - host: deepmind.google
        purpose: Google DeepMind 博客 RSS
        scheme: https
      - host: ai.meta.com
        purpose: Meta AI 博客 (Web 抓取)
        scheme: https
      - host: github.blog
        purpose: GitHub Blog RSS (含 changelog / security-lab)
        scheme: https
      - host: github.com
        purpose: GitHub Trending + Releases Atom
        scheme: https
      - host: huggingface.co
        purpose: HuggingFace Papers JSON API
        scheme: https
      - host: export.arxiv.org
        purpose: arXiv cs.AI / cs.LG / cs.CL RSS
        scheme: https
      - host: aider.chat
        purpose: Aider 博客 RSS
        scheme: https
      - host: windsurf.com
        purpose: Windsurf 博客 RSS
        scheme: https
      - host: www.cognition.ai
        purpose: Cognition AI 博客 (Web 抓取)
        scheme: https
      - host: www.latent.space
        purpose: Latent Space 博客 RSS
        scheme: https
      - host: feed.infoq.com
        purpose: InfoQ AI/ML/Data Engineering RSS
        scheme: https
      - host: www.microsoft.com
        purpose: Microsoft Research / AI Blog RSS
        scheme: https
      - host: blogs.nvidia.com
        purpose: NVIDIA 博客 RSS
        scheme: https
      - host: aws.amazon.com
        purpose: AWS Machine Learning Blog RSS
        scheme: https
      - host: techcrunch.com
        purpose: TechCrunch AI 分类 RSS
        scheme: https
      - host: owasp.org
        purpose: OWASP 博客 RSS
        scheme: https
      - host: openssf.org
        purpose: OpenSSF 博客 RSS
        scheme: https
      - host: snyk.io
        purpose: Snyk 博客 RSS
        scheme: https
      - host: ossinsight.io
        purpose: OSSInsight 博客 RSS
        scheme: https
      - host: www.qbitai.com
        purpose: 量子位 RSS
        scheme: https
      - host: 36kr.com
        purpose: 36氪 AI 频道 RSS
        scheme: https
      - host: www.jiqizhixin.com
        purpose: 机器之心 (Web 抓取)
        scheme: https
---

# AI Daily Pulse

每日 AI 行业新闻聚合 Skill。设计原则:
- **脚本只采集 + 去重 + 输出**,不主动调用任何 LLM,零 API Key 依赖
- **AI 评分/分类/摘要由主 Claude Agent 在采集后完成**(复用当前会话能力,免配置)
- **飞书推送可选**: 配置了 Bot 走 Interactive Card,未配置则直接 stdout 输出 Markdown

## 触发关键词

- AI日报 / AI每日推送 / 今日AI新闻
- AI Daily Pulse / ai-daily-pulse

## 工作流(主 Agent 编排)

当用户请求 AI 日报时,按以下步骤执行:

### 步骤 1: 采集 + 去重

```bash
python3 <skill-dir>/scripts/main.py collect --tier 2 > /tmp/ai-pulse-raw.json
```

> `<skill-dir>` 替换为本 Skill 的绝对路径(例如 `~/.claude/skills/ai-daily-pulse`)。
> 命令本身不会输出进度到 stdout,所以 `> /tmp/...` 拿到的是干净 JSON。

`collect` 输出去重后的文章 JSON 数组到 stdout,每条含 `title / url / source / category / description / tier` 字段。Tier 1 = RSS/API(快),Tier 2 = 加 Web 抓取(全)。

### 步骤 2: 你(主 Agent)进行评分 + 分类 + 摘要

读取 `/tmp/ai-pulse-raw.json`,对每篇文章给出:
- `score`: 1-10 整数(9-10 重大突破; 7-8 重要进展; 5-6 值得关注; 3-4 一般; 1-2 低价值)
- `category`: 8 个分类之一(见下表)
- `summary`: 50 字以内中文摘要

将评分结果合并写回 `/tmp/ai-pulse-scored.json`(保留原字段并新增 score/category/summary)。

**评分参考**:
- Tier 1 源(官方/权威媒体)优先加分
- 有 upvotes / weekly_stars 等热度信号时加分
- 关键词命中(release/launch/发布/开源/突破)加分

### 步骤 3: 后处理 + 输出

```bash
cat /tmp/ai-pulse-scored.json | \
  python3 <skill-dir>/scripts/main.py deliver --scored --top-n 20
```

`deliver --scored` 表示输入已含 score,跳过兜底评分,只做跨分类去重 + 分类配额选取 + 推送。
- 已配置飞书 Bot → 推送 Interactive Card 到默认群
- 未配置飞书 Bot → 直接打印 Markdown 到 stdout(你将其展示给用户即可)

### 一键纯规则模式(无需 LLM,适合 cron)

```bash
python3 <skill-dir>/scripts/main.py pipeline --tier 2
```

跳过主 Agent 评分,使用脚本内置规则评分。适合定时任务场景。

## 8 大分类

| key | Emoji | 名称 | 典型源 |
|------|-------|------|------|
| official | 🚀 | 官方发布 | OpenAI / Anthropic / Google DeepMind / Meta AI |
| coding_agent | 🛠️ | AI Coding & Agent | GitHub Blog / Aider / OpenHands / Windsurf / Cognition |
| opensource | 🔥 | 开源趋势 | GitHub Trending / OSSInsight |
| research | 📚 | 研究论文 | arXiv (cs.AI/LG/CL) / HuggingFace Papers |
| engineering | ⚙️ | 工程实践 | InfoQ / Latent Space / Microsoft Research |
| security | 🛡️ | 安全 & 质量 | OWASP / Snyk / OpenSSF |
| domestic | 🇨🇳 | 国内实践 | 量子位 / 36氪 / 机器之心 |
| media | 📰 | 行业动态 | TechCrunch AI |

## 子命令一览

| 子命令 | 用途 | 关键参数 |
|--------|------|--------|
| `collect` | 采集 + 去重,输出 JSON | `--tier {1,2}` `--source <key>` `--no-dedup` |
| `deliver` | 读 JSON 后处理 + 输出 | `--input <file>` `--scored` `--top-n N` `--chat-id <id>` `--stdout` `--dry-run` |
| `pipeline` | 完整流程(规则评分,无 LLM) | `--tier {1,2}` `--top-n N` `--chat-id <id>` `--stdout` `--dry-run` |
| `test` | 采集 + 去重统计 | `--tier {1,2}` `--source <key>` |

通用:
- `--source <key>`: 仅采集单个源(如 `openai` / `github_trending` / `huggingface_papers`)
- `--chat-id <id>`: 推送到指定飞书群(覆盖默认)
- `--stdout`: 强制 Markdown 输出(忽略飞书配置)
- `--dry-run`: 只打印选中 JSON,不推送/不输出

## 配置(全部可选)

未配置任何凭证时,Skill 也能完整运行——结果会以 Markdown 输出到 stdout。

### 配置文件路径

```
~/.config/ai-daily-pulse/config.json
```

示例:
```json
{
  "feishu_app_id": "cli_xxxxxxxxxxxx",
  "feishu_app_secret": "xxxxxxxxxxxxxxxxxx",
  "feishu_default_chat_id": "oc_xxxxxxxxxxxxxxxxxxxx"
}
```

### 等价环境变量

| 环境变量 | 等价 config 字段 |
|---------|----------------|
| `FEISHU_APP_ID` | `feishu_app_id` |
| `FEISHU_APP_SECRET` | `feishu_app_secret` |
| `FEISHU_DEFAULT_CHAT_ID` | `feishu_default_chat_id` |
| `FEISHU_SOURCE_CHAT_ID` | (运行时注入,例如由触发指令的群注入) |

**优先级**: 环境变量 > 配置文件 > 默认空值。

### 推送目标群三级路由

| 优先级 | 来源 |
|--------|------|
| 1 | CLI `--chat-id <id>` |
| 2 | 环境变量 `FEISHU_SOURCE_CHAT_ID`(机器人触发时注入"哪里触发推哪里")|
| 3 | `FEISHU_DEFAULT_CHAT_ID` 配置 |

## 飞书自建机器人(Bot)创建与授权指南

### 1. 创建企业自建应用

1. 打开飞书开放平台 <https://open.feishu.cn/app>
2. 点击「创建企业自建应用」,填写名称/简介/图标
3. 进入应用详情,记录 **App ID** 和 **App Secret**(写入 `feishu_app_id` / `feishu_app_secret`)

### 2. 开通必要权限

「权限管理」→ 至少勾选以下:
- `im:message` 或 `im:message:send_as_bot` — 发送消息
- `im:chat` 或 `im:chat:readonly` — 读取群信息(可选)
- `im:resource` — 上传图片(可选)

提交版本审核(企业自建应用通常即时生效)。

### 3. 启用机器人能力

「功能 → 机器人」→ 启用机器人。完成后即可被加进群聊。

### 4. 把机器人加进目标群

1. 在飞书群设置 → 「群机器人」→ 「添加机器人」
2. 搜索你刚创建的应用名,确认添加
3. 群管理员可能需要审批

### 5. 获取目标群 chat_id

**推荐方式(curl 一行命令)**:用机器人凭证拿 token 后查机器人所在群列表:

```bash
APP_ID=cli_xxxxxxxxxxxx
APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# 1. 取 tenant_access_token
TOKEN=$(curl -s -X POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$APP_ID\",\"app_secret\":\"$APP_SECRET\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")

# 2. 列出机器人所在的所有群,每行一个 (chat_id, name)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://open.feishu.cn/open-apis/im/v1/chats?page_size=50" \
  | python3 -c "import sys,json; [print(c['chat_id'], '-', c.get('name','')) for c in json.load(sys.stdin)['data']['items']]"
```

**其它方式**:
- 让机器人发个测试消息后看 webhook 回包
- 文档接口: <https://open.feishu.cn/document/server-docs/group/chat/list>
- 暂时跳过: `pipeline --tier 1 --dry-run` 无需 chat_id 也能跑通,后续再补

将拿到的 `oc_xxxxx` 填入 `feishu_default_chat_id`。

### 6. 验证

```bash
python3 <skill-dir>/scripts/main.py pipeline --tier 1
```

成功会在群里看到一张 Interactive Card。失败请检查:
- App Secret 是否正确
- 机器人是否在目标群
- 权限是否已发布

## 输出回退策略

| 场景 | 行为 |
|------|------|
| 飞书 App ID/Secret 都已配置且推送成功 | 推送 Feishu Interactive Card |
| 飞书 App ID 或 Secret 缺失 | 自动回退打印 Markdown 到 stdout(主 Agent 直接展示给用户) |
| 飞书已配置但推送失败(token 过期/凭证错误/群无机器人) | stderr 打印 WARN + 自动回退 Markdown 到 stdout,内容不丢 |
| `--stdout` 强制开启 | 跳过飞书,直接 Markdown |
| `--dry-run` | 不推送/不输出,只打印选中文章 JSON |

## 数据源

详见 `scripts/config.py` 中的 `TIER1_RSS_SOURCES` / `TIER1_API_SOURCES` / `TIER2_WEB_SOURCES`。
默认包含:
- 25+ Tier 1 RSS/Atom(OpenAI / DeepMind / arXiv / GitHub Blog / 量子位 / OWASP …)
- 1 个 Tier 1 JSON API(HuggingFace Papers)
- 5 个 Tier 2 Web 源(Anthropic / Meta AI / Cognition / GitHub Trending / 机器之心)

源可在 `config.py` 中自由增删,无副作用。

## 数据目录

```
data/
├── log.json              # 运行日志(最近 100 条)
└── cache/
    ├── rss_cache.json    # RSS 缓存 (TTL 48h)
    ├── github_cache.json # GitHub 缓存 (TTL 24h)
    ├── api_cache.json    # API 缓存 (TTL 12h)
    └── sent_hashes.json  # 已推送 hash (TTL 7d)
```

## 依赖

- **Python 3.8+** — 仅用标准库,零第三方依赖
- **Node.js + Puppeteer** — 可选,Tier 2 部分 SPA 站点抓取时用到。未安装时这些站点会自动跳过

## 定时任务示例

```crontab
# 工作日早 9 点纯规则模式推送
0 9 * * 1-5 python3 ~/.claude/skills/ai-daily-pulse/scripts/main.py pipeline --tier 2
```

## 整点速报卡片规范（2026-08-27 定稿，用户确认）

整点速报数据目录：`<项目>/.tmpfiles/ai-hourly-pulse/`
- `pulse.json`：RSS/白名单采集池（含 title/url/source/published）
- `aihot_selected.json`：AI HOT 精选（含 url/source/publishedAt/score）
- `sent.json`：已推送条目索引（URL → 发送时间+标题），**构造卡片链接时的 URL 事实源**

卡片硬性要求（用户 2026-08-27 明确纠错，违反会被打回）：
1. **每条必须带全局连续序号**（1. 2. 3. … 36.），跨板块不重置
2. **每条来源必须是可跳转链接**，格式 `[来源 · 时间 · 类型](url)`（如 `[X：唐杰 · 今天 13:42 · 原帖](https://x.com/...)`）。URL 从 sent.json / aihot_selected.json 里按标题匹配取，**禁止只写灰色文字不带链接**；确实无 URL 的（如线下活动官网）才允许纯文字
3. 卡片结构：schema 2.0，蓝色 header「🤖 AI 整点速报 · 全量汇总」+ 副标题（时间 · 共 N 条）；顶部灰字时间窗+来源说明；6 板块（🤖模型发布 / 🚀产品发布 / 🏢大厂与行业动向 / 📄论文与研究 / 💡技巧与观点 / 🎤活动与发布会）；每板块标题注明条数
4. 每条格式：`**N. 标题** — 一句话事实。` 换行后来源链接（灰色小字风格）
5. 数字与标题事实以速报原文为准，不杜撰；发现原文矛盾（如"首破千亿"vs 实际 962 亿）用数字口径并提醒用户
6. **schema 2.0 不支持 `note` 标签**（报错 `unsupported tag note`），底部落款用 `{"tag":"div","text":{"tag":"lark_md","text_size":"notation","content":"<font color=grey>…</font>"}}`（2026-08-28 踩坑）
7. **卡片汇总版信息量必须全（2026-08-28 用户强调，三轮加码）**：目标 20 条上下（15-25 条），不许只挑热点。每期必须覆盖以下**基础维度**，逐项搜过才能定稿：
   - 模型发布（国内外新模型/版本/开源）
   - 产品发布（AI 应用、工具、工作台升级）
   - 大厂与行业动向（公司战略、人事、辟谣/传闻核查）
   - 官方活动与大会（数博会/AGIC/GTC/DevDay/交通展等，含当日开幕与收官）
   - 相关人士发言（黄仁勋/Altman/扎克伯格/马斯克/唐杰/李彦宏等 CEO 与研究者的新表态）
   - 融资/收购/IPO 与资本市场（隔夜美股 AI 板块、A 股 AI 概念、目标价调整）
   - 具身智能/机器人（发布、量产、展会、出货数据）
   - 智能驾驶/Robotaxi（车企智驾时间表、Robotaxi 运营、展会）
   - AI 内容创作与出圈事件（AI 短剧/AI 音乐/AI 游戏等破圈作品）
   - 论文与研究/安全事件
   - AI 政策监管（国内外新政策、标准发布——注意核实发布日期，旧政策不收）
   - AI 终端硬件（AI 眼镜/AI PC/新硬件发布）
   - 人才流动（高管任命/跳槽/年轻化趋势）
   - 垂直行业应用（医疗/教育/金融/法律等）
   - 开源社区（GitHub Trending/HuggingFace 热门）

   **维度自我发现机制（用户 2026-08-28 最终要求：维度要靠 Agent 自己发现，越滚越长，不是套固定清单）**——每期采集必做，流程：
   1. **扫描归类**：把当期全部搜索结果逐条过一遍，问「这条属于哪个维度？」——凡是**不属于上方任何已有维度**的条目，单独列出
   2. **归纳新维度**：把同类落单条目归纳成新维度名（如 AI 能源电力、AI 存储基础设施、AI 农业气象、AI 科学发现、AI 军事安防、AI 电商零售、AI 法律诉讼）
   3. **当期加搜**：每个新发现的维度立即补 1 组搜索验证是否有货，有货直接进当期卡片
   4. **持久化追加**：本期结束前把验证有效的新维度**追加进上方清单**（只增不减，标注首次发现日期）。SKILL.md 的维度清单是一张**活登记表**——每期只允许变长，严禁缩减或替换
   5. **连带扩展信息源**（呼应「官方信息源优先清单」的自我迭代要求）：新维度里出现的公司/媒体/信源，确认官方渠道后同步补进信息源表

   **已发现维度登记表**（活登记表，随期追加）：
   | 维度 | 首次发现 | 验证结果 |
   |---|---|---|
   | 基础 15 维（上方清单） | 2026-08-27~28 | 稳定 |
   | AI 基础设施（存储/网络/电力/液冷/智算中心） | 2026-08-28 首轮维度发现 | 有效：闪存峰会、光模块出口数据、液冷渗透率、华为源网荷储 AIDC 战略均有稳定产出；当日硬新闻偏少，多为趋势数据，按需收录 |
   | AI 出海与地缘（出口数据/海外订单/管制/国际组织报告） | 2026-08-28 首轮维度发现 | 有效：AI 产品出口高速增长（光模块+22.3%/集成电路+88.7%/激光雷达+58.3%）、零一物等出海订单、穆迪 AI 风险展望均有稳定产出 |
   | AI 法律诉讼与合规（训练数据诉讼/版权判决/合规监管案件） | 2026-08-28 晚报维度发现 | 有效：xAI 被诉使用非法材料训练 Grok（8/28 Ars Technica）当日硬新闻；GEMA 诉 OpenAI、德国法院裁定 Suno 须授权、韩国三大电视台诉 OpenAI 等存量案件持续有进展，每期值得扫一组 |
   | AI 安全与联合治理（网络安全联名信/安全事件复盘/对齐研究/蜜罐攻防） | 2026-08-29 早报维度发现 | 有效：本期 4 条独立条目（百余家机构网络防御联名信、Wiz 90 天蜜罐证据、OpenAI 发布 HF 入侵复盘、Anthropic 对齐失败自动缓解研究），密集且持续产出，从「论文与研究/安全事件」中独立成维度 |
   | AI 电商零售（AI 购物助手/商家 AI 工具/电商报告与补贴政策） | 2026-08-29 晚报维度发现 | 有效：第六届中国新电商大会（吉林市）发布《中国新电商发展报告（2026）》——AI 购物覆盖约 2.5 亿用户、超九成商家用 AI、商务部补贴试点扩至 20 省；千问 App 等入口规模化落地，每期可扫一组 |
   | （下一行由未来各期追加，只增不减） | | |

   搜到但已入选晚报的条目剔除；确定性不足的传闻标注「传闻/待确认」或写明辟谣状态。

发送（Windows/AIMana 环境）：PowerShell 直调 lark-cli 会静默失败，必须走 node spawn 包装脚本（见记忆 `larkcli-card-send-node-wrapper`），`--as bot`。

## 小红书双产物规范（2026-08-27 定稿；2026-08-28 两轮修订：1000→500 字 + 风格定稿）

每次速报产出两份：**① 全量卡片汇总**（上述规范）+ **② 小红书风格推文**（发用户私聊）。

**字数铁律 v3（2026-08-29 用户定稿，替代 v2 的净字数口径）**：以**小红书编辑器计数为准——正文连空格、换行、话题标签一起算 ≤500 字**（即文本原始长度 ≤500），净字数目标 420-460（给排版空白留余量）。结构压缩为：标题 + 今日头条（3-4 行）+ **4 条**值得看（每条 2 行内）+ 收尾悬念 + 6-8 个话题标签。同源条目合并、头条对照事件不重复展开。

**文风定稿（2026-08-28 用户确认 8.27 版为基准，严格仿照）**：
- 头条 3-4 行短句叙事，每行一个信息点，叙事里带口语（"要换个活法了"）
- 每条 = 时间点标题 + 事实 1-2 句 + **点评一句含蓄带梗**（对照式收尾是招牌：「卖铲人的自信，和买铲人的账单，是同一天的两种现实」「是圈养还是放养」）
- 点评风格：对仗但克制，留半句让读者自己品；不喊口号、不解释梗
- 收尾固定「今天我最想看的还是…见分晓」
- 蹭热点优先：当日全网刷屏的 AI 相关社会事件（如孙宇晨-Claude）优先上头条，比行业新闻更出圈

```
标题：M月D日AI速报｜头条事件钩子，副事件钩子（全角｜分隔）

今日头条：
（3-5 行短句事实，每行一个信息点，不用长段落）
（+ 1-2 句个人观点，敢下判断、口语化、可以带损）

今天另外N条值得看：
N️⃣时间点｜标题
事实 1-2 句。
点评一句（带立场）。

今天我最想测/好奇的还是XXX。
（悬念式收尾一句）

#AI[话题]# #大模型[话题]# …（话题标签带[话题]#）
```

要点：时间精确到分钟且用「昨晚23:32 / 今天04:25」格式；每条几乎都带主观点评；结尾固定"最想测/最好奇"+悬念；去 AI 味叠加 humanizer-zh + sound-human skill 规则。

## 封面图片风格规范（2026-08-29 定稿：小红书与公众号统一 Zine 规范）

**所有封面（小红书 3:4 / 公众号 16:9）统一采用极简独立杂志 Zine 风格**，与 `xhs-zine-cover` skill（`~/.claude/skills/xhs-zine-cover/`）的定稿规范完全一致——用户 2026-08-29 明确要求"公众号图片生成参考小红书发来的格式"。风格规范（改任何一条都会破坏系列统一性）：

- 背景：浅灰蓝旧纸 `#D1DCE2`，保留**纸张纤维、扫描颗粒、复印柔化、撕纸边缘、Risograph 印刷颗粒、轻微套色偏移**；画面平面、克制、有人工排版和旧杂志印刷质感
- 大标题：左上大号深海军蓝黑 `#182A3A` 凸版字，带轻微套色偏移（如「AI 速报」「AI 晚报」+「M月D日」）
- 纸条元素：竖向撕边纸条列示本期要点（日报封面用 4-6 张纸条写当日头条关键词/模型名/公司名）；**头条纸条深灰蓝 `#214E78`，面积比其他纸条大约 20%，向前、向上错位**；其余纸条暖灰白与浅灰蓝交替
- **名称拼写 100% 准确、清晰可读**：公司名/模型名/人名逐字核对（模型名如 GLM-5.3、Claude、GPT-5、Gemini 3.5 必须拼写准确）——AI 生图文字易错，生成后必须逐字检查，拼错即重生成
- **留白 58%~65%**，但标题和本期头条在缩略图（小红书信息流/公众号分享卡片）里必须一眼可见
- 信息层级（重点阅读顺序）：大标题 → 本期头条（M月D日 + 头条事件）→ 纸条要点
- 配色固定：只许用 `#D1DCE2`（背景）/ `#182A3A`（标题）/ `#214E78`（头条纸条）/ 暖灰白 / 浅灰蓝，禁止引入其他色相
- **禁止**：人物、机器人、风景、任何 Logo、AI 科技图标、卡通、3D、霓虹、渐变、玻璃质感、商业光泽、复杂图表、额外文案、水印
- 尺寸：小红书封面 3:4（1620×2160，可走 xhs-zine-cover 的 make_cover.py 纯代码绘制，文字最准）；公众号封面 16:9（mcp__image__generate，profile gemini-3-pro-image-preview，生成后逐字验收）

## AI 晚报 · 公众号版规范（2026-08-27 定稿 v2，每天 21:00 自动生成）

用途：用户每天 21 点收到一份可直接发微信公众号的 AI 晚报（自动化任务生成，飞书 bot 会话私发预览）。

**时间窗铁律（用户 2026-08-27 强调）**：
- **公众号晚报：只选当天（北京时间）发布的新闻**，一条前天/昨天的都不行。时间从采集数据的 publishedAt 换算（数据源是 UTC，北京时间 = UTC+8，如 20:25Z 8/26 = 北京 8/27 04:25，算"今天"）。当天条目不足 8 条时，用全网实时检索补当天新闻，宁可换条目也不放宽时间窗
- **小红书 AI 速报：可放宽到最近 3 天**

结构模板（**固定 8 条，编号 1-8，不设板块分组，不含安全/研究类负面条目**——用户 2026-08-27 明确要求去掉安全与研究板块）：
```
标题：AI 晚报 · M月D日｜头条事件钩子，副事件钩子
导语：一句开场（"各位晚上好，这里是 AI 晚报。今天一天的事，8 条，全是今天的。"）

**1. 头条事件（当天最大新闻，篇幅最长，关键数字逐个加粗）**
---
**2-8. 其余 7 条**：每条格式为
**N. 时间｜小标题（带一句钩子）**（时间格式同小红书版：「今天 13:42 / 昨晚 23:32 / 8/25」，精确到分钟，从采集数据的 publishedAt 取）
事实 1-3 短段（关键数字加粗）。
点评一句。

结语："今天我最想测/最好奇的是XXX" + 悬念句 + "明天见"
参考来源：全部来源汇总一行
落款：数据来源声明 + "关注我，每天 21 点，一份不掺水的 AI 晚报"
```

条目选取优先级：头条（当日最大）→ 财报/大厂动向 → 模型发布与开源 → 产品发布 → 端侧/硬件。**安全事件、研究论文类默认不入选**（除非用户当期明确要求）。**避免"太普通"的条目**：单纯的产品定价/入口档更新、小版本功能上线这类没有故事性的新闻不选，宁可换成有人味的事件（如机器人运动会、破纪录数据、行业奇观）（用户 2026-08-27 反馈 ChatGPT Work 定价条太普通）。

排版要求（公众号阅读习惯）：
- 每条之间用分隔线 `---`；条目标题用加粗阿拉伯数字（**1.**、**2.**）
- 短段落（每段 1-3 句），关键数字加粗；不用 emoji 序号，公众号版更沉稳
- 每条事实优先、点评克制但必有
- 去 AI 味叠加 humanizer-zh + sound-human 规则
- 发送：node wrapper（send_text.js 模式）--as bot，发用户私聊 bot 会话

## 搜索量规范（2026-08-27 定稿；2026-08-28 用户加码：慢无所谓，搜索时间一定要长）

每期内容生成前，**全网实时检索不少于 30 组关键词**（用户历轮加码：2026-08-27 要求加大搜索量，2026-08-28 要求"搜索时间加长、慢无所谓、一定要长"，**2026-08-29 最终定调：新闻越多越好、宽度广度越多越好、执行时间不设上限，越执行越多**——采集阶段花 2 小时也正常，不许草草 15 组就开写）。每组 top_k=10，搜完横向比对去重；维度登记表（见卡片规范第 7 条）每个维度至少 1 组，热点维度（模型/大厂/资本）各 2-3 组。**采集量只增不减铁律**：每期实际检索组数不得低于历史峰值（历史峰值记录见下），维度登记表每新增一个维度，当期至少追加 1 组对应搜索。建议组合：

| 组 | 关键词方向 | 覆盖面 |
|---|---|---|
| 1 | 「AI 新闻 今天 M月D日 发布 公告」通用扫 | 当日全景 |
| 2 | 头条事件 + 最新进展（如"英伟达 收购 Hugging Face 确认"） | 头条深挖 |
| 3 | 「OpenAI/Google/Meta/xAI/Antropic + 最新消息」 | 海外大厂 |
| 4 | 国内厂商逐家查（智谱/通义/DeepSeek/腾讯混元/月之暗面/MiniMax/Kimi） | 国内大厂 |
| 5 | 「AI 融资 收购 IPO M月D日」 | 资本动向 |
| 6 | 「具身智能 机器人 自动驾驶 M月D日」 | 硬件/具身 |
| 7 | 「AI 芯片 算力 数据中心 M月D日」 | 基础设施 |
| 8 | 「AI 视频 语音 多模态 新产品」 | 应用/产品 |
| 9 | 当天大会议程/活动现场（如 AGIC） | 活动补充 |
| 10 | 头条事件的竞品/关联方反应 | 交叉验证 |
| 11 | 「AI 医疗/教育/金融/法律 垂直应用 M月D日」 | 垂直行业 |
| 12 | 「GitHub 开源 AI 项目 trending 本周」 | 开源社区 |
| 13 | 「AI 高管 跳槽 人才 任命 M月」 | 人才流动 |
| 14 | 「AI 视频 音乐 短剧 多模态 M月D日」 | 内容创作 |
| 15 | 「AI 眼镜 AI PC AI 手机 硬件 M月D日」 | 终端硬件 |
| 16 | 「Robotaxi 智能驾驶 车企 M月D日」 | 智能驾驶 |
| 17 | 「AI 政策 标准 监管 发布 M月」 | 政策监管 |
| 18 | 每期头条主角的官方渠道直查（官网/X/公众号） | 官方源直查 |
| 19 | 每期发现的新公司/新事件，即时加一组搜 | 维度自拓展 |
| 20 | 登记表里每个「已发现维度」各 1 组（维度越多，本组越多） | 维度全覆盖 |
| 21 | 信息源表里每个官方渠道直查 1 组（厂商名 + 官方 announcement/release） | 官方源直查 |
| 22 | 海外隔夜快讯聚合源（AI HOT / TechCrunch / Ars Technica / The Verge 当日流） | 隔夜海外 |

**历史采集峰值登记（只增不减，每期刷新）**：2026-08-28 晚报 30 组 / 2026-08-29 早报 28 组 → **当前基线 30 组**，此后每期不得低于 30，鼓励 40+。

要点：每组 top_k=10；搜完先横向比对去重，再选 8 条；同一事件要交叉验证（如 NVIDIA 收购 HF：TechCrunch 说 129 亿、36kr 说"已达成协议"、金融日报说"待官方确认"——口径差异要标注）；海外事件补中文报道交叉验证时间线。

## 时效性溯源铁律（2026-08-29 用户纠错：推送的新闻全是过时的）

**用户 2026-08-29 实锤反馈**：推送的"新闻"溯源后发现大量旧闻（详见下方踩坑案例）。此前的时间窗规则只约束"采集数据自带的 publishedAt"，而全网检索补搜的条目**没有日期核验步骤**，搜索引擎 snippet 不带日期或带的是转载/修订日期，导致旧闻混进日报。

**每条入选前必须过溯源关，缺一不可**：

1. **溯源到原始页面核对首发日期**——不能只信搜索 snippet。凡是要进卡片的条目，从 URL 指向的原始页面（官网/官方博客/论文页/媒体报道页）确认发布日期，与本期时间窗比对。溯源不了的条目宁可弃选
2. **URL 日期自检（最廉价的第一道闸）**——URL 里带日期的必须比对：
   - `techcrunch.com/2026/08/26/...`、`finance.sina.com.cn/.../2026-08-26/...` → 报道日期
   - `cnews.chinadaily.com.cn/a/202606/02/...` → 2026-06-02（当期 8 月报却收录了 6 月旧闻，实锤踩坑）
   - `arxiv.org/abs/2606.xxxxx` → **2606 = 2026 年 6 月提交**（2608 才是 8 月）
   - `qbitai.com/2026/08/479919.html` → 年/月目录可判
3. **arXiv 修订日期陷阱**——搜索结果里显示的可能是 v2/v3 修订时间，不是首发时间。`abs` 页面上的 "Submitted" v1 日期才是真实首发。一篇 6 月提交、8 月修订的论文，8 月报里只能按"8 月修订"口径收，且默认不作为"今日新闻"收录（论文类本来就默认不进公众号版）
4. **转载/重发旧闻陷阱**——中文门户（百度号/头条号/微信公号）会重发数月前的旧闻，搜索时按相关度召回。判定方法：溯源到原始信源（厂商官方渠道或首发媒体）核对；找不到原始信源首发日期的，标注「旧闻重发」直接弃选
5. **时间窗硬校验（复核而非只信采集字段）**：
   - 卡片汇总/公众号晚报：条目实际首发距今超过 24h 剔除（晚报标准：当天北京时间）
   - 小红书版：上限 3 天，超龄弃选
   - 复核以**原始页面日期**为准，不以 RSS publishedAt / 搜索引擎日期为准——两者都可能指向修订时间
6. **去重时顺带查龄**——sent.json 里 7 天内已推送过的 URL 一律不重推（现有 hash TTL 机制只防重发，不防"旧闻当新闻"）；查到已推送过的**同主题不同 URL**（同一事件换媒体源），也要按首次报道时间算龄

**2026-08-29 踩坑案例（溯源实锤，引以为戒）**：
- `arxiv.org/abs/2606.13610`：8/27 作为新闻推送，实际 v1 提交于 **6/11**，8/24 只是 v2 修订——旧论文当新研究
- `cnews.chinadaily.com.cn/a/202606/02/...`：8/27 推送，实际发布于 **6/2**——近 3 个月旧闻混进日报
- 对比合格项：`anthropic.com/research/enabling-independent-research`（8/26 发布、8/27 推送）——说明溯源流程可行，只是没执行

**执行位置**：本铁律插在评分/选条之前——步骤 2 评分时先逐条过溯源关，过不了的条目直接出池，不参与评分。

## 官方信息源优先清单（2026-08-27 增补）

采集和检索时**优先官方渠道**，同等热度下官方源条目优先入选：

国内厂商官方渠道（现有 RSS 白名单未覆盖，靠 AI HOT + 全网检索补）：
| 厂商 | 官方渠道 |
|---|---|
| 智谱 | zhipuai.cn/zh/research、chatglm.cn、X：@ZhipuAI、唐杰 @jietang |
| 阿里通义 | qwen.ai、X：@Alibaba_Qwen、tongyi.aliyun.com |
| DeepSeek | api-docs.deepseek.com/zh-cn/updates |
| 腾讯混元 | 公众号「腾讯混元」、hunyuan.tencent.com |
| 字节豆包/火山 | volcengine.com、公众号「火山引擎」 |
| 月之暗面 | platform.moonshot.cn、kimi.com |
| 面壁智能 | X：@OpenBMB |
| MiniMax | minimax.io、X：@MiniMaxAI |

海外官方（多数已在 RSS 白名单）：OpenAI news / Anthropic news / Google DeepMind blog / **Google Research blog（research.google，白名单未收，靠检索补）** / Meta AI & Engineering / NVIDIA blog / Apple Newsroom / Microsoft Research / HuggingFace blog+papers。

**Midjourney Updates（updates.midjourney.com RSS，模型/编辑功能发布）/ LMSYS Blog（Chatbot Arena 团队基准测试）/ Ars Technica AI（诉讼与政策类硬新闻）——2026-08-28 晚报维度发现补录**。

**中新网（chinanews.com.cn，产业大会与报告类现场报道）/ 凤凰网科技（tech.ifeng.com，海外大厂冲突与人事快讯）/ 格隆汇（新浪财经转载渠道，X 平台回应类快讯）——2026-08-29 晚报维度发现补录**。

**快讯聚合类高频信源（2026-08-29 早报维度发现补录）**：钛媒体 Edge AI Daily 早报（tmtpost.com，隔夜海外 + 当日晨间速递，条目含关键数字）、财联社电报（cls.cn，资本市场与官宣快讯，时间戳精确到分）、汇通财经快讯（fx678.com，海外财经/地缘类 AI 快讯）。早报场景（凌晨到上午海外发布高峰）优先扫这三家的当日晨报/电报流。

**信息源自进化铁律（2026-08-29 用户定调：信息源要自进化拓展，广度也要自进化拓展，越执行越多）**：
1. 每期遇到新的公司/消息源出现在新闻里，检索确认其官方渠道后**当场**补进本表——不等期末，发现即录
2. 新闻里提到的每家公司、每个消息源都是潜在信源：顺着新闻里的公司名/人名/产品名去查它的官方网页、官方博客、官方 X 账号，实时搜取第一时间信息
3. 本表与维度登记表**只增不减**：信源表每期只允许变长，严禁缩减或替换；条数本身就是一个自进化指标——每期盘点行数，只许比上期多
4. 大厂公告、大模型厂商最新公告、最新动向是最高优先级信源，每期必扫
5. 新信源当期立即启用：补录进表的当期就加一组对应搜索，验证产出

## 公众号排版与草稿箱直推（md2wechat，2026-08-27 全链路打通）

md2wechat-skill 已安装：CLI 二进制 `md2wechat.exe`（v3.2.0），skill 文档 `~/.claude/skills/md2wechat-skill/`。

配置：`~/.config/md2wechat/config.yaml`（已配公众号 AppID/Secret + default_theme: ocean-calm）。**IP 白名单已加 <your-ip>**（动态 IP，若再报 40164 按报错里的新 IP 提醒用户更新白名单）。

## 晚报三版齐推（2026-08-28 定稿：每晚 21:00 必须齐推三版，缺一即错）

每晚晚报固定产出并推送**三个版本**，全部完成才算交付（用户 2026-08-28 明确纠错：此前只有公众号版、漏推小红书版和卡片汇总版）：

**① 卡片汇总版（飞书 Interactive Card）**
- 按「整点速报卡片规范」构造 schema 2.0 卡片：蓝色 header「🤖 AI 晚报 · M月D日」+ 副标题（共 N 条），晚报全部条目入卡，**全局连续序号 + 每条来源可跳转链接**
- node wrapper 发送，`--as bot`，发用户私聊

**② 小红书版（私聊文本）**
- 按「小红书文风模板 v2」+ **500 字铁律 v3**：正文原始长度（含空格、换行、标签）≤500，头条 + 4 条 + 悬念收尾 + 5-8 标签
- 蹭热点优先：当日出圈 AI 社会事件 > 行业新闻
- 同源条目合并；头条对照事件不在正文重复展开
- node wrapper（send_text.js 模式）发用户私聊文本

**③ 微信公众号版（私聊预览 + 草稿箱直推）**
- md 文本 + 排版 HTML 以 bot 身份发用户私聊；封面 + 草稿箱流程见下

### 公众号版四件套

1. 晚报 md 存 `.tmpfiles/evening_paper.md`，node wrapper（send_text.js 模式）发送文本
2. 排版 HTML：运行 `md2wechat convert <md> --mode ai --theme ocean-calm --json` 拿「深海静谧」设计规范 → 手写纯内联样式 HTML（淡蓝背景 #f0f4f8 / 主文字 #3a4150 / 强调 #4a7c9b / 卡片白底网格纹理+圆角14px+深海阴影 / ◆发光标题 / 每个 p 显式 color）存 `.tmpfiles/evening_paper.html`，send_file.js（cwd=项目根，相对路径）发送
3. 封面：mcp__image__generate 出「AI 晚报·M月D日」封面（**16:9**），风格严格按下方「封面图片风格规范（Zine 统一规范）」执行——与小红书封面同一套规范，仅比例从 3:4 换 16:9
4. 推草稿箱（关键顺序）：
   - `upload_image <封面> --json` → 拿 thumb media_id
   - 构造 draft JSON（`{"articles":[{"title","digest","content":<HTML正文去body标签>,"thumb_media_id"}]}`），**必须无 BOM UTF-8**（用 `[IO.File]::WriteAllText($path, $json, [Text.UTF8Encoding]::new($false))`，PowerShell 默认 UTF8 带 BOM 会报 `invalid character 'ï'`）
   - **标题/摘要铁律（2026-08-28 用户纠错，违反打回）**：
     - 标题 = `AI晚报 | <头条事件钩子>，<副事件钩子>`，与当晚**最终版 md 首行**事件严格一致，≤64 字（超长先砍副钩子修饰词）
     - 摘要 = 最终版 md 的导语事实句（含头条关键数字 + "今天一天的事，N 条，全是今天的"），≤120 字；**禁止出现与正文不符的条数、未入选或已删除的事件**
     - **payload 必须从当晚最终版 md/HTML 现场生成**——md 被用户改动后旧 payload 一律作废重新生成，严禁复用旧 title/digest（2026-08-28 踩坑：内容改成 8 条后摘要仍写"5 条速览"、引用已删条目）
   - `create_draft <json> --json` → 成功返回草稿 media_id
   - 用户在公众号后台「草稿」里预览 → 手动发布；提醒用户删除同日旧草稿（同晚会累积多版）
- HTML 里的 `<body>`/`</body>` 标签要剥掉再填 content
- API 模式（48 个高级主题+布局模块）需 ¥199 永久 key（MD2WECHAT_API_KEY），用户未购买，勿切 API 模式

## 去 AI 味精华（2026-08-28 定稿：三源全量汇总，速报场景专用）

**四个去味源，写作时全部生效**（用户 2026-08-28 要求"所有去除 AI 味的 skill 都要运用，不要偷懒"；同日追加网络方法）：
1. `humanizer-zh` skill — 中文 AI 腔清单（A 词汇/B 结构/C 排版/D 语气四类 15 条）+ **反例黑名单 8 条** + 注入人味 6 条 + clean/humanize 两档
2. `sound-human` skill — 33 条模式（格言公式/假坦白开场/制造 punchline/aphorism 等）+ **Detection Guidance（什么不是 AI 味，防误杀）** + 人味信号清单 + personality-soul（无魂写作 vs 有心跳写作）
3. `md2wechat humanize` — 24 种 AI 痕迹模式 + 4 档强度（gentle/medium/aggressive/authentic），authentic 档为六维真人写作规则
4. **网络方法汇总（2026-08-28 检索）** — GPTZero 检测原理（困惑度+突发性）及反制技巧：
   - **突发性（Burstiness）**：检测器量化句子长度方差，人类写作长短句方差大、AI 四平八稳。反制：一段里必须有 1 个 <10 字短句 + 1 个 25 字以上长句
   - **单句控长**：AI 爱多修饰长复合句。规则：单句 ≤25 字（中文），避免一句话连用 3 个以上连词
   - **深层改写才有效**：同义词替换/语序调换是浅层改写，几乎无效；"结构不改等于白改，AI 味还在骨子里"——必须从写作逻辑、段落结构层面调整
   - **去上帝视角**：AI 爱站在全知视角陈述；套具体身份（"我"、某个岗位视角）、加个人思考和小质疑更真实
   - **允许微小不完美**：人类写作有细微的错误、停顿和跳脱感；全文完美流畅本身就是信号
   - **套路连接词全局搜删**：首先/其次/最后/综上所述/不可否认的是——写完全文搜一遍

### 速报场景黑名单（三源合并，出现即改写）

**① 格言收尾公式**（sound-human §31/§32 + humanizer B2）：
- 「"XXX"，这个 Y 本身就是信号」「这不是 X，而是 Y」「恰恰说明」「背后的逻辑是」「真正的看点是」
- 病灶：把普通事实包装成金句。速报的点评要**有立场**，但立场用大白话说，不造格言
- 反例：「'太强所以晚两周发'，这个节奏本身就是信号：模型攻防已经强到厂商自己都要掂量」
- 正例：「敢因为这个原因推迟开源，说明安全团队真的被吓到了」

**② 自造口语压缩（2026-08-28 实际踩坑，humanizer 反例黑名单第 1 条）**：
- 「最硬一条」「这波稳了」「含金量拉满」这类硬凹出来的压缩短语——**为去 AI 腔强行堆自造口语，是从一种假换成另一种假**
- 反例：「长文最硬一条：景甜要的 5000 万美元，是 Claude 劝他别给的」（"最硬一条"是生造的，没人这么说话）
- 正例：「长文里提到，景甜要的 5000 万美元，是 Claude 劝他别给的」
- 判别法：把句子念出声，**日常说话不会说的压缩词**就是自造。自然口语的标志是完整句子，不是电报体

**③ 修辞化包装动词**：
- 「按下暂停键」「交出答卷」「打响第一枪」「落下实锤」「画上句号」——每段最多容忍一个，连续出现就是套模板
- 「引爆」「背刺」「碾压」「霸榜」这类戏剧动词单个可用，三个连用就是 AI 腔

**④ AI 高频词（humanizer A 类 + md2wechat 词汇表合并）**：
- 值得注意的是 / 综上所述 / 不仅…更是 / 涌现出（滥用时）/ 意味着 / 标志着 / 预示着 / 正在重塑 / 赋能 / 助力 / 深度融合 / 强强联合 / 里程碑 / 新篇章 / 划时代
- 「罕见」这个词 2026 年被 LLM 用滥了，见到必删

**⑤ 工整三段式结构**：
- 「事实句 + 事实句 + 升华句」的完美对称本身就是 AI 信号。破坏方法：长短句交替、允许某条只有事实没有点评（真人写 8 条不会每条都配金句）
- 警惕：**每条都用双短句对仗收尾**（「XX，YY。」×4 条连续出现）本身就是新模板

**⑥ -ing 式肤浅分析中文版**：
- 「推动着」「重塑着」「加速着」+ 空泛宾语 → 写清楚具体推动了什么，或删

**⑦ 过度对称的证据排列**：
- 「两个数字值得记住：X 和 Y」「三个信号：…」→ 数字包装去掉，直接说

**⑧ 假坦白/表演式口语开场**（sound-human §33）：
- 「说实话？」「讲真」「说白了吧」做独立开场再抖包袱 → 真人直接说事

### 保留的人味（三源一致，别误杀）

- **具体数字**：4.6 跳到 28.3、单日 +4200 亿美元——数字越具体越像人写的，保留
- **变节奏**：长短句交替（personality-soul: Short punchy sentences. Then longer ones that take their time.）
- **有观点**：对事实有反应、有判断，中立罗列反而无魂
- **认复杂**：偶尔写「这块我还没想清楚」「效果等实测」比强行下结论更像人
- **允许不齐整**：半句点评、无关紧要的插入语、偶尔的跑题
- **完整句子**：真人写新闻速报是完整叙述句，不是电报体压缩

### 误杀警告（sound-human Detection Guidance，改写前必读）

- 单个破折号/单个"然而"/单个短句不是 AI 信号——**看聚集，不看孤立**
- 工整语法、正式词汇、干瘪文风都不是 AI 证据；AI 有**特定的**高频词，不是所有书面语
- 去味目标是从假到真，不是从书面到口水

### 三版各自的应用要点（2026-08-28 增补，全部要做）

**小红书版**：
- 叙述用完整句子（不用电报体压缩）；头条 3-4 行里保证长短句方差（一行短一行长）
- 点评句式四条不得相同；允许某条只有事实不点评
- 对照式点评是招牌但每期限用 2 次，防止形成新模板
- 引语一字不改（宁删别处字数，不动引语）

**公众号版（md + HTML）**：
- 单句 ≤25 字，长句拆短；每段必须长短句混合（突发性）
- 8 条的点评不得全是「XX，YY。」双短句对仗——至少 2 条改成完整长句点评或追问式
- 引用块点评里的句式跨条要变化：陈述/反问/假设/留白交替
- 导语和结语用人称视角（"各位晚上好，这里是 AI 晚报"已符合），正文偶尔出现"我"的判断
- 写完全文全局搜：首先/其次/最后/综上所述/值得注意的是——发现即删

**卡片汇总版**：
- 条目主体是"一句话事实 + 来源链接"，天然中性，重点是**事实句本身的写法**：不要每条都用「主语 + 动词 + 数字 + 定性升华」的同构句式
- 板块间条目密度允许不均（某板块 1 条、某板块 6 条都正常，真人整理就是这样）

### 交叉验证流程（每版发出前，缺一不可）

1. **人工三源扫**：写完对照上方 ①-⑧ 逐项过一遍
2. **flavor_check.py**：`python scripts/flavor_check.py <文本>`，退出码 0 才继续（含自造口语检测）
3. **结构校验**：小红书跑 `xhs_check.py`，卡片跑 `card_check.py`
4. **md2wechat humanize 交叉验证**（可选但推荐）：`md2wechat humanize <md文件> --show-changes -i gentle` 看它标的 AI 痕迹；与本 skill 判断冲突时**从严**处理
5. 全部通过才发送。flavor_check ERROR → 重写命中句再跑，不许删规则放行

## License

MIT
