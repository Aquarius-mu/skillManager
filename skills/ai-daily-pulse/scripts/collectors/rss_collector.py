#!/usr/bin/env python3
"""AI Daily Pulse - RSS/Atom 采集器"""

import re
import sys
import ssl
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import List, Dict, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TIER1_RSS_SOURCES, DEFAULT_HEADERS, CACHE_DIR, CACHE_TTL_RSS, AI_FILTER_KEYWORDS

RSS_CACHE_FILE = CACHE_DIR / 'rss_cache.json'


def _parse_date(date_str: str) -> Optional[datetime]:
    """解析多种日期格式"""
    if not date_str:
        return None
    date_str = date_str.strip()

    # 常见 RSS 日期格式
    formats = [
        '%a, %d %b %Y %H:%M:%S %z',       # RFC 822
        '%a, %d %b %Y %H:%M:%S %Z',
        '%Y-%m-%dT%H:%M:%S%z',             # ISO 8601
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f%z',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
    ]

    # 清理常见问题
    date_str = re.sub(r'\s+GMT$', ' +0000', date_str)
    date_str = re.sub(r'\s+UTC$', ' +0000', date_str)
    date_str = re.sub(r'\s+EST$', ' -0500', date_str)
    date_str = re.sub(r'\s+PST$', ' -0800', date_str)

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return None


def _extract_items_from_xml(xml_text: str) -> List[Dict]:
    """从 RSS/Atom XML 中提取条目（正则解析，无外部依赖）"""
    items = []

    # RSS <item> 格式
    rss_items = re.findall(r'<item[^>]*>(.*?)</item>', xml_text, re.DOTALL)
    for item_xml in rss_items:
        title = _extract_tag(item_xml, 'title')
        link = _extract_tag(item_xml, 'link') or _extract_attr(item_xml, 'link', 'href')
        pub_date = _extract_tag(item_xml, 'pubDate') or _extract_tag(item_xml, 'dc:date')
        description = _extract_tag(item_xml, 'description')
        if title:
            items.append({
                'title': _clean_html(title),
                'url': link or '',
                'published': pub_date or '',
                'description': _clean_html(description or '')[:300],
            })

    # Atom <entry> 格式
    if not items:
        atom_entries = re.findall(r'<entry[^>]*>(.*?)</entry>', xml_text, re.DOTALL)
        for entry_xml in atom_entries:
            title = _extract_tag(entry_xml, 'title')
            link = _extract_attr(entry_xml, 'link', 'href') or _extract_tag(entry_xml, 'link')
            updated = _extract_tag(entry_xml, 'updated') or _extract_tag(entry_xml, 'published')
            summary = _extract_tag(entry_xml, 'summary') or _extract_tag(entry_xml, 'content')
            if title:
                items.append({
                    'title': _clean_html(title),
                    'url': link or '',
                    'published': updated or '',
                    'description': _clean_html(summary or '')[:300],
                })

    # arXiv RDF 格式 (<rdf:li>)
    if not items:
        rdf_items = re.findall(r'<item\s[^>]*>(.*?)</item>', xml_text, re.DOTALL)
        for item_xml in rdf_items:
            title = _extract_tag(item_xml, 'title')
            link = _extract_tag(item_xml, 'link') or _extract_attr(item_xml, 'link', 'href')
            desc = _extract_tag(item_xml, 'description')
            date = _extract_tag(item_xml, 'dc:date')
            if title:
                items.append({
                    'title': _clean_html(title),
                    'url': link or '',
                    'published': date or '',
                    'description': _clean_html(desc or '')[:300],
                })

    return items


def _extract_tag(xml: str, tag: str) -> str:
    """提取 XML 标签内容"""
    # CDATA
    match = re.search(rf'<{tag}[^>]*><!\[CDATA\[(.*?)\]\]></{tag}>', xml, re.DOTALL)
    if match:
        return match.group(1).strip()
    # 普通标签
    match = re.search(rf'<{tag}[^>]*>(.*?)</{tag}>', xml, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ''


def _extract_attr(xml: str, tag: str, attr: str) -> str:
    """提取标签属性值"""
    match = re.search(rf'<{tag}[^>]*{attr}="([^"]*)"', xml)
    if match:
        return match.group(1)
    return ''


def _clean_html(text: str) -> str:
    """清理 HTML 标签"""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&lt;', '<', text)
    text = re.sub(r'&gt;', '>', text)
    text = re.sub(r'&quot;', '"', text)
    text = re.sub(r'&#39;', "'", text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _matches_ai_filter(title: str, description: str) -> bool:
    """检查标题/描述是否匹配 AI 关键词"""
    text = f"{title} {description}".lower()
    for kw in AI_FILTER_KEYWORDS:
        if re.search(kw, text, re.IGNORECASE):
            return True
    return False


def _fetch_rss(url: str, timeout: int = 30) -> str:
    """获取 RSS 内容"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = dict(DEFAULT_HEADERS)
    headers['Accept'] = 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*'

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout, context=ctx) as response:
            return response.read().decode('utf-8', errors='replace')
    except (HTTPError, URLError, Exception) as e:
        print(f"  [WARN] RSS fetch failed: {url} - {e}", file=sys.stderr)
        return ''


def _load_cache() -> Dict:
    """加载 RSS 缓存"""
    if not RSS_CACHE_FILE.exists():
        return {}
    try:
        with open(RSS_CACHE_FILE, encoding='utf-8') as f:
            cache = json.load(f)
        # 清理过期缓存
        now = time.time()
        return {k: v for k, v in cache.items() if now - v.get('_ts', 0) < CACHE_TTL_RSS}
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cache(cache: Dict):
    """保存 RSS 缓存"""
    with open(RSS_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)


def fetch_single_source(source: Dict, use_cache: bool = True) -> List[Dict]:
    """采集单个 RSS 源"""
    key = source['key']
    url = source['url']
    category = source['category']
    filter_ai = source.get('filter_ai', False)
    max_items = source.get('max_items', 10)

    cache = _load_cache() if use_cache else {}

    # 检查缓存
    if key in cache and use_cache:
        return cache[key].get('items', [])

    xml_text = _fetch_rss(url)
    if not xml_text:
        return []

    raw_items = _extract_items_from_xml(xml_text)

    # 过滤最近 7 天内的文章（很多源不是每天发文）
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    articles = []

    for item in raw_items[:max_items * 3]:  # 取更多以便过滤
        pub_date = _parse_date(item.get('published', ''))

        # 如果有日期，过滤旧文章
        if pub_date and pub_date < cutoff:
            continue

        # AI 关键词过滤
        if filter_ai and not _matches_ai_filter(item['title'], item.get('description', '')):
            continue

        articles.append({
            'title': item['title'],
            'url': item['url'],
            'description': item.get('description', ''),
            'source': source['name'],
            'source_key': key,
            'category': category,
            'published': item.get('published', ''),
            'tier': 1,
        })

        if len(articles) >= max_items:
            break

    # 更新缓存
    if use_cache:
        cache[key] = {'items': articles, '_ts': time.time()}
        _save_cache(cache)

    return articles


def fetch_all(sources: Optional[List[Dict]] = None, use_cache: bool = True) -> List[Dict]:
    """采集所有 Tier 1 RSS 源"""
    if sources is None:
        sources = TIER1_RSS_SOURCES

    all_articles = []
    for source in sources:
        print(f"  [RSS] Fetching {source['name']}...", file=sys.stderr)
        articles = fetch_single_source(source, use_cache=use_cache)
        print(f"  [RSS] {source['name']}: {len(articles)} articles", file=sys.stderr)
        all_articles.extend(articles)

    return all_articles


if __name__ == '__main__':
    # 测试单源
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', help='源 key')
    parser.add_argument('--no-cache', action='store_true')
    args = parser.parse_args()

    if args.source:
        src = next((s for s in TIER1_RSS_SOURCES if s['key'] == args.source), None)
        if src:
            results = fetch_single_source(src, use_cache=not args.no_cache)
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"Unknown source: {args.source}", file=sys.stderr)
    else:
        results = fetch_all(use_cache=not args.no_cache)
        print(f"Total: {len(results)} articles")
        for a in results[:5]:
            print(f"  [{a['source']}] {a['title']}")
