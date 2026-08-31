#!/usr/bin/env python3
"""AI Daily Pulse - 自我进化引擎

两个维度,全部代码级自动执行、状态持久化到 data/ 下(运行期生成,不进公开库):

1. 信源自我拓展 (source self-expansion)
   - 从已采集新闻的 URL 提取新域名
   - 对每个新域名探测常见 RSS/Atom feed 路径
   - 探测有效(能抓到含 <item>/<entry> 的 XML)即注册进信源库,只增不减
   - 动态信源与 config.py 白名单合并后参与采集

2. 品质自我进化 (quality self-evolution)
   - 每个信源维护一份信用档案: 抓取可靠性 / 产出价值率 / 旧闻命中惩罚
   - 综合成 quality_score ∈ [0,1],评分时给该信源的新闻加权
   - 反馈闭环: 被选中推送 = 正反馈; 抓取失败 / 溯源判旧闻 = 负反馈

持久化文件:
  data/source_registry.json   # 自动发现的动态信源(只增不减)
  data/source_quality.json    # 信源品质信用档案(随反馈持续更新)
"""

import json
import re
import ssl
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    DATA_DIR, DEFAULT_HEADERS, TIER1_RSS_SOURCES, TIER1_API_SOURCES, TIER2_WEB_SOURCES,
    SOURCE_REGISTRY_FILE, SOURCE_QUALITY_FILE,
)


# ============================================================
# 信源发现: 常见 feed 路径探测
# ============================================================
FEED_PATH_CANDIDATES = [
    'feed', 'feed.xml', 'rss', 'rss.xml', 'atom.xml', 'index.xml',
    'feeds/posts/default',           # Blogger
    'blog/feed', 'blog/feed.xml', 'blog/rss.xml', 'blog/atom.xml',
    'news/feed', 'news/rss.xml',
    'zh/feed', 'en/feed',
    'feed/', 'rss/',
]

# 域名关键词 → 分类猜测(新信源默认归 media,命中才覆盖)
DOMAIN_CATEGORY_HINTS = [
    (re.compile(r'arxiv|paper|research|paperswithcode', re.I), 'research'),
    (re.compile(r'github|gitlab|gitee|opensource', re.I), 'opensource'),
    (re.compile(r'security|snyk|owasp|cve|nist', re.I), 'security'),
    (re.compile(r'36kr|qbitai|jiqizhixin|leiphone|ithome|pingwest|chinaz', re.I), 'domestic'),
    (re.compile(r'openai|anthropic|deepmind|meta|nvidia|microsoft|google|aws|apple', re.I), 'official'),
]


# ============================================================
# 通用 JSON 读写(带容错)
# ============================================================
def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def _write_json(path: Path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


# ============================================================
# 1. 信源注册表 (source_registry.json)
# ============================================================
def load_registry() -> dict:
    """加载动态信源注册表"""
    return _read_json(SOURCE_REGISTRY_FILE, {'sources': []})


def load_dynamic_sources() -> list:
    """返回已注册的动态 RSS 信源列表(供采集器合并使用)"""
    reg = load_registry()
    return reg.get('sources', [])


def _known_domains() -> set:
    """收集所有已注册/白名单信源的主域名(用于发现时去重)"""
    domains = set()

    def _add(url):
        if not url:
            return
        netloc = urlparse(url).netloc.lower()
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        if netloc:
            domains.add(netloc)

    for s in TIER1_RSS_SOURCES + TIER1_API_SOURCES + TIER2_WEB_SOURCES:
        _add(s.get('url', ''))
    for s in load_dynamic_sources():
        _add(s.get('url', ''))
    return domains


def _domain_of(url: str) -> str:
    """从 URL 提取主域名(去 www.)"""
    if not url:
        return ''
    netloc = urlparse(url).netloc.lower()
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    return netloc


def _guess_category(domain: str) -> str:
    for pattern, cat in DOMAIN_CATEGORY_HINTS:
        if pattern.search(domain):
            return cat
    return 'media'


def _fetch(url: str, timeout: int = 8) -> str:
    """轻量抓取(不验证 SSL,与 rss_collector 一致)"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    headers = dict(DEFAULT_HEADERS)
    headers['Accept'] = 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout, context=ctx) as response:
            return response.read().decode('utf-8', errors='replace')
    except (HTTPError, URLError, OSError, ValueError, Exception):
        return ''


def _looks_like_feed(xml: str) -> bool:
    """判断文本是否像 RSS/Atom feed(含 item/entry 标签)"""
    if not xml:
        return False
    return bool(re.search(r'<(item|entry)\b', xml, re.IGNORECASE))


def probe_feed(domain: str) -> str:
    """对域名探测常见 feed 路径,返回第一个有效的 feed URL,否则 ''"""
    if not domain:
        return ''
    for path in FEED_PATH_CANDIDATES:
        url = f'https://{domain}/{path}'
        xml = _fetch(url)
        if _looks_like_feed(xml):
            return url
    return ''


def discover_sources(articles: list, max_probe: int = 15, dry_run: bool = False) -> list:
    """从已采集新闻中发现新信源,验证通过则注册(只增不减)

    返回本次新发现并注册的信源列表。dry_run=True 时只探测不写入。
    """
    known = _known_domains()
    registry = load_registry()
    existing_keys = {s.get('key') for s in registry.get('sources', [])}

    # 收集候选域名(去重、排除已知、排除无域名的文章)
    candidates = []
    seen = set()
    for a in articles:
        dom = _domain_of(a.get('url', ''))
        if dom and dom not in known and dom not in seen:
            seen.add(dom)
            candidates.append({'domain': dom, 'from_url': a.get('url', '')})

    discovered = []
    probed = 0
    for c in candidates:
        if probed >= max_probe:
            break
        probed += 1
        feed_url = probe_feed(c['domain'])
        if not feed_url:
            continue
        src = {
            'key': c['domain'],
            'name': c['domain'],
            'url': feed_url,
            'category': _guess_category(c['domain']),
            'discovered_from': c['from_url'],
            'discovered_at': _now_iso(),
        }
        discovered.append(src)

    if discovered and not dry_run:
        # 只增不减: 已存在的 key 跳过
        new_sources = [s for s in discovered if s['key'] not in existing_keys]
        if new_sources:
            registry.setdefault('sources', []).extend(new_sources)
            _write_json(SOURCE_REGISTRY_FILE, registry)
            print(f"  [Evolve] +{len(new_sources)} 新信源已注册: "
                  f"{', '.join(s['key'] for s in new_sources)}", file=sys.stderr)
        else:
            print(f"  [Evolve] 发现的 {len(discovered)} 个信源均已存在,跳过", file=sys.stderr)
    elif discovered:
        print(f"  [Evolve] (dry-run) 发现 {len(discovered)} 个候选信源: "
              f"{', '.join(s['key'] for s in discovered)}", file=sys.stderr)

    return discovered


# ============================================================
# 2. 信源品质信用档案 (source_quality.json)
# ============================================================
def load_quality() -> dict:
    """加载信源品质信用档案"""
    return _read_json(SOURCE_QUALITY_FILE, {})


def quality_score(rec: dict) -> float:
    """计算信源综合信用分 [0,1]

    0.4 * 抓取可靠性 + 0.4 * 产出价值率 + 0.2 * (1 - 旧闻惩罚)
    中性默认 0.5(无档案时)。
    """
    attempts = rec.get('attempts', 0)
    successes = rec.get('successes', 0)
    articles = max(rec.get('articles', 0), 1)
    selected = rec.get('selected', 0)
    stale_hits = rec.get('stale_hits', 0)

    # 无抓取记录 = 未知,取中性 0.5(不因"没记录"而误伤)
    if attempts == 0:
        reliability = 0.5
    else:
        reliability = successes / attempts
    value_rate = min(selected / articles, 1.0)
    staleness_penalty = min(stale_hits * 5 / articles, 0.5)  # 每 5% 旧闻率扣一半上限
    return round(0.4 * reliability + 0.4 * value_rate + 0.2 * (1 - staleness_penalty), 3)


def record_fetch_result(source_key: str, ok: bool, n_articles: int = 0):
    """记录一次抓取结果(成功/失败 + 产出条数)"""
    if not source_key:
        return
    q = load_quality()
    rec = q.setdefault(source_key, {})
    rec['attempts'] = rec.get('attempts', 0) + 1
    if ok:
        rec['successes'] = rec.get('successes', 0) + 1
        rec['articles'] = rec.get('articles', 0) + max(n_articles, 0)
    rec['last_seen'] = _now_iso()
    _write_json(SOURCE_QUALITY_FILE, q)


def record_selection(articles: list):
    """记录被选中推送的文章 → 其信源获得正反馈"""
    if not articles:
        return
    q = load_quality()
    for a in articles:
        key = a.get('source_key', '')
        if not key:
            continue
        rec = q.setdefault(key, {})
        rec['selected'] = rec.get('selected', 0) + 1
        rec.setdefault('articles', 1)
        rec['last_seen'] = _now_iso()
    _write_json(SOURCE_QUALITY_FILE, q)


def record_stale(source_keys: list):
    """记录被溯源判为旧闻的信源 → 负反馈(降信用)"""
    if not source_keys:
        return
    q = load_quality()
    for key in source_keys:
        if not key:
            continue
        rec = q.setdefault(key, {})
        rec['stale_hits'] = rec.get('stale_hits', 0) + 1
        rec.setdefault('articles', 1)
        rec['last_seen'] = _now_iso()
    _write_json(SOURCE_QUALITY_FILE, q)


def source_quality_map() -> dict:
    """返回 {source_key: quality_score} 供评分使用(无档案默认 0.5)"""
    q = load_quality()
    return {k: quality_score(v) for k, v in q.items()}


def quality_report() -> str:
    """生成信源品质报告(按信用分降序)"""
    q = load_quality()
    if not q:
        return "(暂无品质档案,运行几期后自动累积)"

    rows = []
    for key, rec in q.items():
        qs = quality_score(rec)
        rows.append((qs, key, rec.get('attempts', 0), rec.get('successes', 0),
                     rec.get('articles', 0), rec.get('selected', 0), rec.get('stale_hits', 0)))
    rows.sort(key=lambda r: -r[0])

    lines = [f"{'score':>6}  {'source':<28} {'att':>4} {'ok':>4} {'art':>5} {'sel':>5} {'stale':>5}"]
    for qs, key, att, ok, art, sel, stale in rows:
        lines.append(f"{qs:>6.2f}  {key:<28} {att:>4} {ok:>4} {art:>5} {sel:>5} {stale:>5}")
    return '\n'.join(lines)


# ============================================================
# 3. 评分加权
# ============================================================
def score_delta_for_source(source_key: str) -> int:
    """信源品质对评分的加权值(∈ {-1, 0, +1})

    显式阈值: 品质 ≥0.7 加分, ≤0.3 减分, 中间为死区(中性,避免小幅波动抖动)。
    """
    qs = source_quality_map().get(source_key, 0.5)
    if qs >= 0.70:
        return 1
    if qs <= 0.30:
        return -1
    return 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='AI Daily Pulse 进化引擎')
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('report', help='输出信源品质报告')
    p.set_defaults(func=lambda a: print(quality_report()))

    p = sub.add_parser('discover', help='从 stdin 读文章 JSON,探测并注册新信源')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--max-probe', type=int, default=15)
    p.set_defaults(func=lambda a: discover_sources(json.loads(sys.stdin.read()) if not sys.stdin.isatty() else [], max_probe=a.max_probe, dry_run=a.dry_run))

    p = sub.add_parser('mark-stale', help='标记信源出旧闻(负反馈)')
    p.add_argument('--source', action='append', required=True, help='源 key,可多次')
    p.set_defaults(func=lambda a: record_stale(a.source))

    args = parser.parse_args()
    args.func(args)
