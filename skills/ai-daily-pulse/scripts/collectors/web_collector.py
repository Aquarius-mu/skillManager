#!/usr/bin/env python3
"""AI Daily Pulse - Web 抓取采集器（Tier 2 源）"""

import json
import sys
import subprocess
import re
from typing import List, Dict, Optional
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TIER2_WEB_SOURCES, SCRIPTS_DIR

_ALLOWED_SCHEMES = {'http', 'https'}


def _is_safe_url(url: str) -> bool:
    """仅允许 http/https。拒绝 file://、ftp://、data:、javascript: 等可能被滥用的 scheme。

    Cisco 静态扫描会把 url 标成 user input(尽管实际只来自 config.py 白名单),
    显式校验既能消除告警,也是合理的纵深防御。
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme.lower() in _ALLOWED_SCHEMES and bool(parsed.netloc)


def _fetch_with_browser(url: str, selector: str = 'body', timeout: int = 60) -> Optional[Dict]:
    """使用 Puppeteer 抓取网页"""
    if not _is_safe_url(url):
        print(f"  [WARN] Rejected unsafe URL: {url}", file=sys.stderr)
        return None

    script_path = SCRIPTS_DIR / 'fetch_with_browser.js'

    if not script_path.exists():
        print(f"  [WARN] fetch_with_browser.js not found", file=sys.stderr)
        return None

    try:
        result = subprocess.run(
            ['node', str(script_path), url, selector],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(script_path.parent)
        )

        if result.returncode == 0 and result.stdout.strip():
            try:
                return json.loads(result.stdout.strip())
            except json.JSONDecodeError:
                return None
        else:
            error = result.stderr.strip() if result.stderr else 'Unknown error'
            print(f"  [WARN] Browser fetch error: {error[:100]}", file=sys.stderr)
            return None

    except subprocess.TimeoutExpired:
        print(f"  [WARN] Browser timeout: {url}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print(f"  [WARN] Node.js not found", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  [WARN] Browser error: {e}", file=sys.stderr)
        return None


def _check_browser_available() -> bool:
    """检查 Puppeteer 是否可用"""
    script_path = SCRIPTS_DIR / 'fetch_with_browser.js'
    if not script_path.exists():
        return False
    node_modules = SCRIPTS_DIR / 'node_modules'
    return node_modules.exists()


def _parse_links_from_html(html: str, base_url: str, selector_hint: str) -> List[Dict]:
    """从 HTML 中提取文章链接（简单正则解析）"""
    articles = []

    # 提取所有链接
    links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)

    for href, text in links:
        text = re.sub(r'<[^>]+>', '', text).strip()
        if not text or len(text) < 5 or len(text) > 200:
            continue

        # 构建完整 URL
        if href.startswith('/'):
            url = base_url.rstrip('/') + href
        elif href.startswith('http'):
            url = href
        else:
            continue

        # 过滤导航链接等
        skip_patterns = ['/tag/', '/category/', '/author/', '#', 'javascript:', '/page/']
        if any(p in href for p in skip_patterns):
            continue

        articles.append({
            'title': text,
            'url': url,
        })

    return articles


def fetch_single_source(source: Dict) -> List[Dict]:
    """采集单个 Tier 2 Web 源"""
    key = source['key']
    name = source['name']
    url = source['url']
    category = source['category']
    selector = source.get('selector', 'body')
    base_url = source.get('base_url', '')

    # GitHub Trending 由专门的 collector 处理
    if source.get('parser') == 'github_trending':
        return []

    if not _check_browser_available():
        print(f"  [SKIP] {name}: Puppeteer not available", file=sys.stderr)
        return []

    result = _fetch_with_browser(url, selector)
    if not result or not result.get('success'):
        return []

    content = result.get('content', '')
    if not content:
        return []

    # 解析文章链接
    raw_links = _parse_links_from_html(content, base_url, selector)

    articles = []
    for link in raw_links[:8]:  # 每个 Tier 2 源最多 8 条
        articles.append({
            'title': link['title'],
            'url': link['url'],
            'description': '',
            'source': name,
            'source_key': key,
            'category': category,
            'published': '',
            'tier': 2,
        })

    return articles


def fetch_all(sources: Optional[List[Dict]] = None, use_cache: bool = True) -> List[Dict]:
    """采集所有 Tier 2 Web 源"""
    if sources is None:
        sources = TIER2_WEB_SOURCES

    if not _check_browser_available():
        print("  [SKIP] All Tier 2 sources: Puppeteer not installed", file=sys.stderr)
        print("  [INFO] Run: cd scripts && npm init -y && npm install puppeteer", file=sys.stderr)
        return []

    all_articles = []
    for source in sources:
        if source.get('parser') == 'github_trending':
            continue  # 由 github_collector 处理
        print(f"  [WEB] Fetching {source['name']}...", file=sys.stderr)
        articles = fetch_single_source(source)
        print(f"  [WEB] {source['name']}: {len(articles)} articles", file=sys.stderr)
        all_articles.extend(articles)

    return all_articles


if __name__ == '__main__':
    if not _check_browser_available():
        print("Puppeteer not available. Install: cd scripts && npm init -y && npm install puppeteer")
    else:
        results = fetch_all()
        print(f"Total: {len(results)} articles from Tier 2 sources")
        for a in results[:5]:
            print(f"  [{a['source']}] {a['title']}")
