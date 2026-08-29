#!/usr/bin/env python3
"""AI Daily Pulse - API 采集器（HuggingFace Papers 等）"""

import json
import sys
import ssl
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import TIER1_API_SOURCES, DEFAULT_HEADERS, CACHE_DIR

API_CACHE_FILE = CACHE_DIR / 'api_cache.json'
CACHE_TTL = 12 * 3600  # 12 小时


def _fetch_json(url: str, timeout: int = 30) -> any:
    """获取 JSON 数据"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = dict(DEFAULT_HEADERS)
    headers['Accept'] = 'application/json'

    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout, context=ctx) as response:
            return json.loads(response.read().decode('utf-8'))
    except (HTTPError, URLError, Exception) as e:
        print(f"  [WARN] API fetch failed: {url} - {e}", file=sys.stderr)
        return None


def _load_cache() -> Dict:
    if not API_CACHE_FILE.exists():
        return {}
    try:
        with open(API_CACHE_FILE) as f:
            cache = json.load(f)
        now = time.time()
        return {k: v for k, v in cache.items() if now - v.get('_ts', 0) < CACHE_TTL}
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cache(cache: Dict):
    with open(API_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)


def fetch_huggingface_papers(use_cache: bool = True) -> List[Dict]:
    """采集 HuggingFace Papers API"""
    cache = _load_cache() if use_cache else {}

    if 'huggingface_papers' in cache and use_cache:
        return cache['huggingface_papers'].get('items', [])

    url = 'https://huggingface.co/api/papers?limit=20'
    data = _fetch_json(url)
    if not data or not isinstance(data, list):
        return []

    articles = []
    for paper in data[:15]:
        paper_id = paper.get('id', '')
        title = paper.get('title', '')
        summary = paper.get('summary', '')[:300] if paper.get('summary') else ''
        upvotes = paper.get('upvotes', 0)

        if not title:
            continue

        articles.append({
            'title': title,
            'url': f'https://huggingface.co/papers/{paper_id}',
            'description': summary,
            'source': 'HuggingFace Papers',
            'source_key': 'huggingface_papers',
            'category': 'research',
            'published': paper.get('publishedAt', ''),
            'tier': 1,
            'extra': {'upvotes': upvotes},
        })

    # 按 upvotes 排序，取 top 10
    articles.sort(key=lambda x: x.get('extra', {}).get('upvotes', 0), reverse=True)
    articles = articles[:10]

    if use_cache:
        cache['huggingface_papers'] = {'items': articles, '_ts': time.time()}
        _save_cache(cache)

    return articles


def fetch_all(use_cache: bool = True) -> List[Dict]:
    """采集所有 API 源"""
    all_articles = []

    print(f"  [API] Fetching HuggingFace Papers...", file=sys.stderr)
    papers = fetch_huggingface_papers(use_cache=use_cache)
    print(f"  [API] HuggingFace Papers: {len(papers)} articles", file=sys.stderr)
    all_articles.extend(papers)

    return all_articles


if __name__ == '__main__':
    results = fetch_all(use_cache=False)
    print(json.dumps(results, ensure_ascii=False, indent=2))
