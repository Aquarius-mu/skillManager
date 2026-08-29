#!/usr/bin/env python3
"""AI Daily Pulse - GitHub Trending 采集器"""

import re
import sys
import ssl
import json
import time
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DEFAULT_HEADERS, CACHE_DIR, CACHE_TTL_GITHUB

GITHUB_CACHE_FILE = CACHE_DIR / 'github_cache.json'

# AI 项目识别关键词
AI_KEYWORDS = {
    'core': [
        r'\bai\b', r'\bartificial.?intelligence\b', r'\bmachine.?learning\b',
        r'\bdeep.?learning\b', r'\bllm\b', r'\blarge.?language.?model\b',
        r'\bneural\b',
    ],
    'models': [
        r'\bgpt\b', r'\bclaude\b', r'\bgemini\b', r'\bllama\b', r'\bmistral\b',
        r'\btransformer\b', r'\bdiffusion\b',
    ],
    'frameworks': [
        r'\bpytorch\b', r'\btensorflow\b', r'\blangchain\b', r'\bllamaindex\b',
        r'\bautogen\b', r'\bcrewai\b', r'\bdspy\b', r'\bhuggingface\b',
    ],
    'applications': [
        r'\bchatbot\b', r'\bcopilot\b', r'\bai.?agent\b', r'\brag\b',
        r'\bembedding\b', r'\bnlp\b', r'\bcomputer.?vision\b', r'\bocr\b',
        r'\bollama\b', r'\bvllm\b',
    ],
}


def _is_ai_project(name: str, description: str) -> bool:
    """判断是否为 AI 相关项目"""
    text = f"{name} {description}".lower()
    for category, keywords in AI_KEYWORDS.items():
        for kw in keywords:
            if re.search(kw, text, re.IGNORECASE):
                return True
    return False


def _fetch_url(url: str, timeout: int = 30) -> str:
    """获取 URL 内容"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = dict(DEFAULT_HEADERS)
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=timeout, context=ctx) as response:
            return response.read().decode('utf-8', errors='replace')
    except (HTTPError, URLError, Exception) as e:
        print(f"  [WARN] GitHub fetch failed: {url} - {e}", file=sys.stderr)
        return ''


def _parse_trending_html(html: str) -> List[Dict]:
    """解析 GitHub Trending HTML（正则方式）"""
    projects = []

    # 查找所有 article.Box-row
    articles = re.findall(r'<article class="Box-row"[^>]*>(.*?)</article>', html, re.DOTALL)

    for article in articles:
        project = {
            'name': '',
            'owner': '',
            'repo': '',
            'description': '',
            'language': '',
            'stars': 0,
            'weekly_stars': 0,
            'url': '',
        }

        # 提取项目名称
        repo_match = re.search(r'href="(/[^/"]+/[^/"]+)"', article)
        if repo_match:
            path = repo_match.group(1)
            parts = path.strip('/').split('/')
            if len(parts) >= 2:
                project['owner'] = parts[0]
                project['repo'] = parts[1]
                project['name'] = f"{parts[0]}/{parts[1]}"
                project['url'] = f"https://github.com{path}"

        # 提取描述
        desc_match = re.search(r'<p[^>]*class="[^"]*color-fg-muted[^"]*"[^>]*>(.*?)</p>', article, re.DOTALL)
        if desc_match:
            project['description'] = re.sub(r'<[^>]+>', '', desc_match.group(1)).strip()

        # 提取语言
        lang_match = re.search(r'itemprop="programmingLanguage"[^>]*>(.*?)</span>', article, re.DOTALL)
        if lang_match:
            project['language'] = lang_match.group(1).strip()

        # 提取本周/今日星标
        stars_match = re.search(r'([\d,]+)\s*stars?\s*(this week|today)', article)
        if stars_match:
            project['weekly_stars'] = int(stars_match.group(1).replace(',', ''))

        # 提取总星标
        total_stars_match = re.findall(r'href="[^"]+/stargazers"[^>]*>.*?([\d,]+)', article, re.DOTALL)
        if total_stars_match:
            project['stars'] = int(total_stars_match[0].replace(',', ''))

        if project['name']:
            projects.append(project)

    return projects


def _load_cache() -> Dict:
    if not GITHUB_CACHE_FILE.exists():
        return {}
    try:
        with open(GITHUB_CACHE_FILE) as f:
            cache = json.load(f)
        now = time.time()
        if now - cache.get('_ts', 0) < CACHE_TTL_GITHUB:
            return cache
        return {}
    except (json.JSONDecodeError, IOError):
        return {}


def _save_cache(cache: Dict):
    with open(GITHUB_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)


def fetch_all(use_cache: bool = True, ai_only: bool = True, top_n: int = 10) -> List[Dict]:
    """采集 GitHub Trending AI 项目"""
    cache = _load_cache() if use_cache else {}

    if cache.get('items') and use_cache:
        return cache['items']

    html = _fetch_url('https://github.com/trending?since=daily')
    if not html:
        return []

    projects = _parse_trending_html(html)

    # 过滤 AI 项目
    if ai_only:
        projects = [p for p in projects if _is_ai_project(p['name'], p['description'])]

    # 按 weekly_stars 排序
    projects.sort(key=lambda x: x.get('weekly_stars', 0), reverse=True)
    projects = projects[:top_n]

    # 转换为标准 article 格式
    articles = []
    for p in projects:
        stars_info = f"⭐ {p['stars']:,}" if p['stars'] else ''
        weekly_info = f"+{p['weekly_stars']:,} today" if p['weekly_stars'] else ''
        lang_info = f"[{p['language']}]" if p['language'] else ''

        desc_parts = [x for x in [p['description'], stars_info, weekly_info, lang_info] if x]
        description = ' | '.join(desc_parts)

        articles.append({
            'title': p['name'],
            'url': p['url'],
            'description': description,
            'source': 'GitHub Trending',
            'source_key': 'github_trending',
            'category': 'opensource',
            'published': '',
            'tier': 2,
            'extra': {
                'stars': p['stars'],
                'weekly_stars': p['weekly_stars'],
                'language': p['language'],
            },
        })

    if use_cache and articles:
        _save_cache({'items': articles, '_ts': time.time()})

    return articles


if __name__ == '__main__':
    results = fetch_all(use_cache=False)
    print(f"Found {len(results)} AI projects on GitHub Trending")
    for a in results:
        print(f"  {a['title']}: {a['description'][:60]}")
