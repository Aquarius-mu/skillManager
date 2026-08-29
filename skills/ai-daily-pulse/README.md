# AI Daily Pulse

每日 AI 行业新闻聚合 Skill。脚本只负责 [采集 + 去重 + 输出],评分/分类/摘要由主 Claude Agent 完成。
飞书 Bot 可选——未配置则自动 fallback 到 stdout Markdown。

## 特性

- **零 API Key 依赖**: 脚本本身不调用任何 LLM
- **30+ 白名单源**: 官方博客 / arXiv / GitHub Trending / HuggingFace / 国内媒体...
- **多级去重**: SHA-256 精确 + Jaccard 模糊 + 7 天历史
- **8 大分类智能配额**: 每个有内容的分类至少保留 1 条,确保多样性
- **双输出模式**: 飞书 Interactive Card / stdout Markdown(自动选择)
- **零第三方依赖**: 仅 Python 3.8+ 标准库;Tier 2 SPA 抓取按需用 Puppeteer

## 快速开始

### 1. 触发方式

在 Claude Code 中输入 "AI日报" / "今日AI新闻" / "AI Daily Pulse" 即可。

### 2. 主 Agent 编排流程

```bash
# 步骤 1: 采集
python3 scripts/main.py collect --tier 2 > /tmp/raw.json

# 步骤 2: 主 Agent 读取 raw.json,对每篇打分 + 分类 + 摘要,产出 scored.json

# 步骤 3: 后处理 + 输出
cat /tmp/scored.json | python3 scripts/main.py deliver --scored --top-n 20
```

### 3. 一键无 LLM 模式(适合 cron)

```bash
python3 scripts/main.py pipeline --tier 2
```

## 飞书 Bot 配置(可选)

参见 [SKILL.md](SKILL.md) 中的「飞书自建机器人创建与授权指南」。简化版:

1. <https://open.feishu.cn/app> 创建企业自建应用
2. 开通 `im:message` 权限,启用机器人
3. 把机器人加进目标群,获取 chat_id
4. 复制 `config.example.json` 到 `~/.config/ai-daily-pulse/config.json`,填入 App ID/Secret/chat_id

未配置时,Skill 会直接把 Markdown 结果输出到 stdout,主 Agent 可直接展示给你。

## 子命令

| 子命令 | 用途 |
|--------|------|
| `collect` | 采集 + 去重,输出 JSON |
| `deliver` | 读 JSON 后处理 + 推送/输出 |
| `pipeline` | 完整流程(规则评分,无 LLM) |
| `test` | 采集 + 去重统计 |

详见 `python3 scripts/main.py <cmd> --help`。

## 目录结构

```
ai-daily-pulse/
├── SKILL.md
├── README.md
├── LICENSE
├── config.example.json
├── .env.example
├── scripts/
│   ├── main.py         # CLI 入口
│   ├── config.py       # 源配置 + 凭证读取
│   ├── collectors/     # 采集器(rss/api/github/web)
│   ├── dedup.py        # SHA + 历史去重
│   ├── processor.py    # 跨分类去重 + 兜底评分 + 选取
│   └── pusher.py       # 飞书卡片 / Markdown 输出
└── data/               # 运行期生成,缓存与日志
```

## 自定义数据源

编辑 `scripts/config.py` 中的 `TIER1_RSS_SOURCES` / `TIER2_WEB_SOURCES` 即可增删。
RSS 源只需 `key / name / url / category`;Web 源额外需要 `selector / base_url`。

## License

MIT
