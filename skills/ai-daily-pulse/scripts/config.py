#!/usr/bin/env python3
"""AI Daily Pulse - 源配置与常量

凭证读取优先级:
  1. 环境变量 (FEISHU_APP_ID / FEISHU_APP_SECRET / FEISHU_DEFAULT_CHAT_ID)
  2. 本地配置文件 ~/.config/ai-daily-pulse/config.json

未配置飞书凭证时,推送阶段会回退到 stdout 输出 Markdown,不会报错。
"""

import os
import json
from pathlib import Path

# ============================================================
# 路径配置
# ============================================================
SKILL_DIR = Path(__file__).parent.parent
SCRIPTS_DIR = Path(__file__).parent
DATA_DIR = SKILL_DIR / 'data'
CACHE_DIR = DATA_DIR / 'cache'
LOG_FILE = DATA_DIR / 'log.json'
USER_CONFIG_FILE = Path.home() / '.config' / 'ai-daily-pulse' / 'config.json'
# 自我进化状态文件(运行期生成)
SOURCE_REGISTRY_FILE = DATA_DIR / 'source_registry.json'
SOURCE_QUALITY_FILE = DATA_DIR / 'source_quality.json'

DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 用户配置加载
# ============================================================
def _load_user_config() -> dict:
    """从 ~/.config/ai-daily-pulse/config.json 加载用户配置"""
    if USER_CONFIG_FILE.exists():
        try:
            with open(USER_CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _get_setting(env_key: str, config_key: str = None, default: str = '') -> str:
    """三级优先级读取配置: 环境变量 > 用户配置文件 > 默认值"""
    val = os.environ.get(env_key, '')
    if val:
        return val
    cfg = _load_user_config()
    return cfg.get(config_key or env_key, default)


# ============================================================
# 飞书 Bot 配置 (可选)
# ============================================================
FEISHU_APP_ID = _get_setting('FEISHU_APP_ID', 'feishu_app_id')
FEISHU_APP_SECRET = _get_setting('FEISHU_APP_SECRET', 'feishu_app_secret')
FEISHU_DEFAULT_CHAT_ID = _get_setting('FEISHU_DEFAULT_CHAT_ID', 'feishu_default_chat_id')
FEISHU_SOURCE_CHAT_ID = os.environ.get('FEISHU_SOURCE_CHAT_ID', '')


def feishu_configured() -> bool:
    """判断飞书 Bot 是否已配置"""
    return bool(FEISHU_APP_ID and FEISHU_APP_SECRET)


# ============================================================
# 缓存 TTL (秒)
# ============================================================
CACHE_TTL_RSS = 48 * 3600
CACHE_TTL_GITHUB = 24 * 3600
CACHE_TTL_SENT = 7 * 86400


# ============================================================
# 选取参数
# ============================================================
TOP_N_ARTICLES = 20
MIN_SCORE = 5


# ============================================================
# 分类配置
# ============================================================
CATEGORIES = {
    'media': {'name': '行业动态', 'emoji': '📰', 'order': 1},
    'coding_agent': {'name': 'AI Coding & Agent', 'emoji': '🛠️', 'order': 2},
    'engineering': {'name': '工程实践', 'emoji': '⚙️', 'order': 3},
    'domestic': {'name': '国内实践', 'emoji': '🇨🇳', 'order': 4},
    'security': {'name': '安全 & 质量', 'emoji': '🛡️', 'order': 5},
    'opensource': {'name': '开源趋势', 'emoji': '🔥', 'order': 6},
    'research': {'name': '研究论文', 'emoji': '📚', 'order': 7},
    'official': {'name': '官方发布', 'emoji': '🚀', 'order': 8},
}


# ============================================================
# 数据源配置
# ============================================================
TIER1_RSS_SOURCES = [
    # 官方模型/平台
    {'key': 'openai', 'name': 'OpenAI', 'url': 'https://openai.com/blog/rss.xml', 'category': 'official'},
    {'key': 'deepmind', 'name': 'Google DeepMind', 'url': 'https://deepmind.google/blog/rss.xml', 'category': 'official'},
    {'key': 'microsoft_ai', 'name': 'Microsoft AI', 'url': 'https://www.microsoft.com/en-us/ai/blog/feed/', 'category': 'official'},
    {'key': 'aws_ai', 'name': 'AWS AI', 'url': 'https://aws.amazon.com/blogs/machine-learning/feed/', 'category': 'official'},
    {'key': 'nvidia', 'name': 'NVIDIA', 'url': 'https://blogs.nvidia.com/feed/', 'category': 'official', 'filter_ai': True},

    # AI Coding / Agent
    {'key': 'github_blog', 'name': 'GitHub Blog', 'url': 'https://github.blog/feed/', 'category': 'coding_agent', 'filter_ai': True},
    {'key': 'github_changelog', 'name': 'GitHub Changelog', 'url': 'https://github.blog/changelog/feed/', 'category': 'coding_agent', 'filter_ai': True},
    {'key': 'windsurf', 'name': 'Windsurf', 'url': 'https://windsurf.com/feed.xml', 'category': 'coding_agent'},
    {'key': 'openhands', 'name': 'OpenHands', 'url': 'https://github.com/All-Hands-AI/OpenHands/releases.atom', 'category': 'coding_agent'},
    {'key': 'aider', 'name': 'Aider', 'url': 'https://aider.chat/feed.xml', 'category': 'coding_agent'},
    {'key': 'swe_agent', 'name': 'SWE-agent', 'url': 'https://github.com/princeton-nlp/SWE-agent/releases.atom', 'category': 'coding_agent'},

    # 开源趋势
    {'key': 'ossinsight', 'name': 'OSSInsight', 'url': 'https://ossinsight.io/blog/feed.xml', 'category': 'opensource'},

    # 论文
    {'key': 'arxiv_ai', 'name': 'arXiv cs.AI', 'url': 'https://export.arxiv.org/rss/cs.AI', 'category': 'research', 'max_items': 5},
    {'key': 'arxiv_lg', 'name': 'arXiv cs.LG', 'url': 'https://export.arxiv.org/rss/cs.LG', 'category': 'research', 'max_items': 5},
    {'key': 'arxiv_cl', 'name': 'arXiv cs.CL', 'url': 'https://export.arxiv.org/rss/cs.CL', 'category': 'research', 'max_items': 5},

    # 工程实践
    {'key': 'infoq_ai', 'name': 'InfoQ AI/ML', 'url': 'https://feed.infoq.com/ai-ml-data-eng/', 'category': 'engineering'},
    {'key': 'latent_space', 'name': 'Latent Space', 'url': 'https://www.latent.space/feed', 'category': 'engineering'},
    {'key': 'ms_research', 'name': 'Microsoft Research', 'url': 'https://www.microsoft.com/en-us/research/feed/', 'category': 'engineering', 'filter_ai': True},

    # 国内实践
    {'key': 'qbitai', 'name': '量子位', 'url': 'https://www.qbitai.com/feed', 'category': 'domestic'},
    {'key': 'kr36', 'name': '36氪', 'url': 'https://36kr.com/feed', 'category': 'domestic', 'filter_ai': True},

    # 安全 & 质量
    {'key': 'owasp', 'name': 'OWASP', 'url': 'https://owasp.org/feed.xml', 'category': 'security'},
    {'key': 'openssf', 'name': 'OpenSSF', 'url': 'https://openssf.org/feed/', 'category': 'security'},
    {'key': 'snyk', 'name': 'Snyk', 'url': 'https://snyk.io/blog/feed/', 'category': 'security', 'filter_ai': True},
    {'key': 'github_security', 'name': 'GitHub Security Lab', 'url': 'https://github.blog/tag/github-security-lab/feed/', 'category': 'security'},
    {'key': 'swe_bench', 'name': 'SWE-bench', 'url': 'https://github.com/SWE-bench/SWE-bench/releases.atom', 'category': 'security'},

    # 媒体
    {'key': 'techcrunch_ai', 'name': 'TechCrunch AI', 'url': 'https://techcrunch.com/category/artificial-intelligence/feed/', 'category': 'media'},
]

TIER1_API_SOURCES = [
    {'key': 'huggingface_papers', 'name': 'HuggingFace Papers', 'url': 'https://huggingface.co/api/papers?limit=20', 'category': 'research'},
]

TIER2_WEB_SOURCES = [
    {'key': 'anthropic', 'name': 'Anthropic', 'url': 'https://www.anthropic.com/news', 'category': 'official',
     'selector': 'a[href*="/news/"]', 'base_url': 'https://www.anthropic.com'},
    {'key': 'meta_ai', 'name': 'Meta AI', 'url': 'https://ai.meta.com/blog/', 'category': 'official',
     'selector': 'a[href*="/blog/"]', 'base_url': 'https://ai.meta.com'},
    {'key': 'cognition', 'name': 'Cognition/Devin', 'url': 'https://www.cognition.ai/blog', 'category': 'coding_agent',
     'selector': 'a[href*="/blog/"]', 'base_url': 'https://www.cognition.ai'},
    {'key': 'github_trending', 'name': 'GitHub Trending', 'url': 'https://github.com/trending?since=daily', 'category': 'opensource',
     'parser': 'github_trending'},
    {'key': 'jiqizhixin', 'name': '机器之心', 'url': 'https://www.jiqizhixin.com/', 'category': 'domestic',
     'selector': 'a.article-item-title', 'base_url': 'https://www.jiqizhixin.com'},
]

TIER3_SOURCES = []


# ============================================================
# 动态信源合并 (自我进化: 自动发现的新信源与白名单合并)
# ============================================================
def get_all_rss_sources() -> list:
    """合并 config 白名单 + 进化引擎动态注册的信源(只增不减)

    动态注册表 data/source_registry.json 由 evolve.discover_sources() 写入,
    本函数按需读取,避免 import 循环。
    """
    registry_file = SOURCE_REGISTRY_FILE
    dynamic = []
    if registry_file.exists():
        try:
            import json as _json
            with open(registry_file, encoding='utf-8') as f:
                data = _json.load(f)
            dynamic = data.get('sources', [])
        except (_json.JSONDecodeError, IOError):
            dynamic = []
    return list(TIER1_RSS_SOURCES) + list(dynamic)


# ============================================================
# AI 关键词过滤 (用于 filter_ai=True 的源)
# ============================================================
AI_FILTER_KEYWORDS = [
    r'\bai\b', r'\bartificial.?intelligence\b', r'\bmachine.?learning\b',
    r'\bdeep.?learning\b', r'\bllm\b', r'\blarge.?language.?model\b',
    r'\bneural\b', r'\bgpt\b', r'\bclaude\b', r'\bgemini\b', r'\bllama\b',
    r'\btransformer\b', r'\bdiffusion\b', r'\bchatbot\b', r'\bcopilot\b',
    r'\bai.?agent\b', r'\brag\b', r'\bembedding\b', r'\bnlp\b',
    r'\bcomputer.?vision\b', r'\bgenerative\b', r'\bfoundation.?model\b',
    r'\bfine.?tun', r'\bprompt\b', r'\binference\b', r'\bmultimodal\b',
    r'\blangchain\b', r'\bvector\b', r'\bopenai\b', r'\banthropic\b',
    r'\bhugging\s*face\b', r'\bmodel\b', r'\btoken\b',
    r'人工智能', r'大模型', r'机器学习', r'深度学习', r'自然语言',
    r'智能体', r'生成式', r'多模态', r'向量', r'大语言模型',
]

# HTTP 请求头
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8',
}
