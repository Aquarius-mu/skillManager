---
name: daily-weekly-report
description: >
  日报周报工作分析。三个模式：
  (1) 工作日早间梳理——扫描昨天全部飞书群聊+私聊中与我相关的消息，结合今日任务日程，
  生成飞书卡片发到我的个人会话；触发词：工作梳理、早间梳理、日报、automation 早间定时触发。
  (2) 工作日一天总结——回顾今天实际完成/推进的工作与未收尾事项，生成卡片发到个人会话；
  触发词：一天总结、晚间总结、今日复盘、automation 晚间定时触发。
  (3) 周报总结——扫描本周全部飞书消息+文档活动，按项目归类生成结果导向周报，写入飞书文档；
  触发词：周报、写周报、生成本周周报、automation 周五定时触发。
  全流程只依赖 lark-cli（im:message 权限即可，不需要 search:message），用户身份动态获取，可推广给任何人使用。
---

# 日报周报工作分析

把飞书聊天记录自动变成三种产出：

| 模式 | 产出 | 去向 | 建议定时 |
|---|---|---|---|
| **早间梳理** | 飞书卡片（昨日回望 + 今日安排） | 用户个人会话 | 工作日 10:00 |
| **一天总结** | 飞书卡片（今日完成/推进/未收尾） | 用户个人会话 | 工作日 19:00 |
| **周报总结** | 结构化周报文档 | 新建飞书文档，链接发个人会话 | 周五 12:00 |

脚本在 `scripts/`，三个模式的详细规则分别在 `references/morning-brief.md`、`references/evening-summary.md`、`references/weekly-report.md`。

## 数据源（双引擎互补，实测结论）

| 数据 | 来源 | 说明 |
|---|---|---|
| **消息**（核心） | 本 skill `scan_messages.py` | 全量群+私聊，不依赖 search:message 权限 |
| 日历 / 妙记 / 文档活动 | `lark-daily-tasks` skill 的 `run.py collect-day` | 它的消息采集依赖 search:message 会失败，**只用它的日历/妙记/文档部分** |
| 审批 / 邮件 / 视频会议 / 任务活动 | `collect_all.py` 内置补采（`collect_supplementary`） | lark-cli approval/mail/vc/task，各自独立降级，某类失败标 `covered:false` 不中断 |
| 任务待办 | `lark-cli task +get-my-tasks` | 今日到期 / 逾期未完成 |
| 今日日程 | `lark-cli calendar +agenda` | 早间梳理用 |

`collect_all.py` 已把消息扫描、lark-daily-tasks 采集和补采（审批/邮件/视频会议/任务活动）合并为一个 context JSON，优先用它。

**补采输出字段**（context JSON 顶层）：`approvals`（pending 待我处理 + cc 抄送我；该 API 无时间过滤、无 create_time，全量返回由你按标题/摘要判断相关性；topic 3「我发起」实测不可用不采）、`mails`（按日期区间过滤）、`vc_meetings`（实际参会）、`task_activity`（created 新建 + completed 完成）。每类含 `covered` 布尔标记，为 false 表示该渠道未采到（权限不足或无数据），写报告时如实标注"未覆盖"，不得伪造。

## 通用化设计（推广全公司的前提）

- **零硬编码**：用户身份（open_id、姓名、检索关键词）全部从 `lark-cli auth status` 动态获取。任何人登录自己的 lark-cli 后直接可用。
- **不依赖 search:message 权限**：消息用 `im +chat-messages-list` 逐会话拉取。
- **相关性判定宁多勿漏**：我发的 + @我的 + 提到我名字的 + 私聊里对方发的，全部保留；纯机器人私聊自动过滤；语义取舍由你（LLM）在总结阶段完成。

## 前置条件

1. 用户已 `lark-cli auth login`（user 身份 ready）。先 `lark-cli auth status` 确认。
2. Python 3 可用（脚本用标准库）。
3. （可选，增强）安装了 `lark-daily-tasks` skill 则有日历/妙记/文档活动；没有也不影响消息主线，脚本会自动降级。

## 模式 A：早间梳理（工作日 10:00）

1. **判断工作日**：`date +"%Y-%m-%d %A"`。周一~周五才执行；周末一句话告知不发。
2. **采集**：
   ```bash
   python scripts/collect_all.py --date <昨天YYYY-MM-DD> --out <tmp>/ctx.json
   ```
3. **补任务数据**（今日到期 / 逾期未完成 / 今日日程），命令见 `references/morning-brief.md`。
4. **你阅读 ctx.json + 任务 + 日程**，按 `references/morning-brief.md` 的规则写内容（昨日@我消息的处理状态、我的事项进展、遗漏；今日到期任务、待回复、会议、P0/P1/P2 排序）。
5. **发卡片**：写 content.json（格式见下）后：
   ```bash
   python scripts/build_daily_card.py <tmp>/content.json
   ```

## 模式 B：一天总结（工作日 19:00）

1. **判断工作日**（同上）。
2. **采集今天**：
   ```bash
   python scripts/collect_all.py --date <今天YYYY-MM-DD> --out <tmp>/today.json
   ```
3. **补任务数据**：今日到期未完成、近两天完成/新建。
4. **按 `references/evening-summary.md` 的四个视角**总结：完成了什么 / 推进中什么 / 未收尾什么 / 明天接什么。
5. **发卡片**（title 用 `🌙 工作日一天总结｜MM-DD 周X`，template 用 `green`）。

## 模式 C：周报总结（周五 12:00）

1. **采集本周**（周一~今天）：
   ```bash
   python scripts/collect_all.py --start <周一YYYY-MM-DD> --end <今天YYYY-MM-DD> --out <tmp>/week.json
   ```
2. **按 `references/weekly-report.md` 的模板**写周报 markdown（本周概览 → 工作事项分项目 → 跨团队协作；结果导向、保留术语、只算我参与的）。
3. **写入飞书文档**：周报 md 文件**首行加 `<title>标题</title>`**，然后（cd 到文件目录用相对路径）：
   ```bash
   lark-cli docs +create --doc-format markdown --content @./week_report.md --as user
   ```
   ⚠️ 实测要点：标题放 content 首行，**不要用 --title flag**；`@file` 只接受相对路径。
4. **把文档链接发给用户**：用 `build_daily_card.py` 发一张简短卡片（含文档链接），或直接在对话中给链接。
   > 自动化场景下无需人工确认直接创建文档；人工触发场景先给用户看周报全文再创建。

content.json 格式（模式 A/B 通用）：
```json
{
  "title": "🗓 工作日早间梳理｜MM-DD 周X",
  "template": "blue",
  "sections": ["**问候+总述**", "## 段落1\n...", "## 段落2\n..."],
  "footer": "💡 一句话备注"
}
```

## 定时任务（AI Mana 自动化）

三个模式已配置为 AI Mana 自动化（用 create_automation/update_automation 管理，不用系统 cron）：

| 任务名 | 频率 | 时间 |
|---|---|---|
| 工作日早间工作梳理 | 工作日（周一~周五） | 10:00 |
| 工作日一天总结 | 工作日（周一~周五） | 19:00 |
| 周报总结 | 每周五 | 12:00 |

自动化 prompt 要点：先判断工作日 → 调本 skill 脚本采集 → 按对应 reference 规则生成内容 → 卡片发用户个人会话（周报先建文档）。

## 常见坑（实测沉淀，务必遵守）

1. **不要只看 @我 的消息**：必须拉全量消息再判断相关性。scan_messages.py 已经这么做了，不要绕过它。
2. **lark-cli 版本差异**：`+chat-list` 排序 flag 新旧版不同（--sort/--sort-type），脚本不传排序参数保证兼容；`+chat-messages-list` 排序是 `--sort asc`（不是 --order）；`docs +create` 新版废弃 --title flag。
3. **`-q .data.total` 返回纯数字**：run_cli_json 已兼容标量。空输出≠出错，可能只是该会话无消息。
4. **Windows**：lark-cli 实际是 `lark-cli.cmd`，subprocess 需 `shell=True`；勿绕过 larklib.run_cli 直接调。
5. **私聊消息天然相关**，但纯机器人私聊要跳过（脚本已自动过滤）。
6. **发送目标**：卡片一律发到用户自己的个人会话，不发群，除非用户明确要求。
7. **lark-daily-tasks 消息采集会失败**（缺 search:message）——合并 context 时忽略它的 messages 字段，消息以 scan_messages 为准。
8. **文档"打开过"≠"完成了"**：写总结时不要把浏览活动当成工作产出。
9. **审批 API**：`approval tasks query` 用 `--params '{"topic":"1","page_size":100}'` 传参（不是 --topic/--start-timestamp flag）；topic 1=待我处理、2=我已处理、17=抄送我、**3=我发起实测返回 field validation failed 不可用**；任务对象无 create_time、API 无时间过滤，只能全量返回按标题判断相关性。
