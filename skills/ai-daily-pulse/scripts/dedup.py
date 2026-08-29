#!/usr/bin/env python3
"""AI Daily Pulse - 去重引擎"""

import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Set

from config import CACHE_DIR, CACHE_TTL_SENT


SENT_HASHES_FILE = CACHE_DIR / 'sent_hashes.json'


def _compute_hash(url: str, title: str) -> str:
    """SHA-256(url + title) 精确去重"""
    content = f"{url.strip().lower()}|{title.strip().lower()}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _bigrams(text: str) -> Set[str]:
    """提取文本的 bigram 集合"""
    text = text.lower().strip()
    if len(text) < 2:
        return {text}
    return {text[i:i+2] for i in range(len(text) - 1)}


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    """Jaccard bigram 相似度"""
    set_a = _bigrams(text_a)
    set_b = _bigrams(text_b)
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union = set_a | set_b
    return len(intersection) / len(union)


def _load_sent_hashes() -> Dict[str, float]:
    """加载已推送 hash（含时间戳）"""
    if not SENT_HASHES_FILE.exists():
        return {}
    try:
        with open(SENT_HASHES_FILE) as f:
            data = json.load(f)
        # 清理过期记录
        now = time.time()
        return {k: v for k, v in data.items() if now - v < CACHE_TTL_SENT}
    except (json.JSONDecodeError, IOError):
        return {}


def _save_sent_hashes(hashes: Dict[str, float]):
    """保存已推送 hash"""
    with open(SENT_HASHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(hashes, f)


def deduplicate(articles: List[Dict]) -> List[Dict]:
    """
    三层去重：
    1. SHA-256(url+title) 精确去重（批次内）
    2. Jaccard bigram similarity > 0.7 模糊去重（批次内）
    3. sent_hashes.json 历史去重（7 天窗口）
    """
    sent_hashes = _load_sent_hashes()
    seen_hashes: Set[str] = set()
    result: List[Dict] = []

    for article in articles:
        url = article.get('url', '')
        title = article.get('title', '')

        # Layer 1: 精确 hash 去重
        h = _compute_hash(url, title)

        # 历史去重
        if h in sent_hashes:
            continue

        # 批次内精确去重
        if h in seen_hashes:
            continue

        # Layer 2: 模糊去重（与已选文章对比标题）
        is_duplicate = False
        for existing in result:
            sim = _jaccard_similarity(title, existing.get('title', ''))
            if sim > 0.7:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        seen_hashes.add(h)
        article['_hash'] = h
        result.append(article)

    return result


def mark_as_sent(articles: List[Dict]):
    """将已推送的文章记录到历史 hash"""
    sent_hashes = _load_sent_hashes()
    now = time.time()
    for article in articles:
        h = article.get('_hash') or _compute_hash(article.get('url', ''), article.get('title', ''))
        sent_hashes[h] = now
    _save_sent_hashes(sent_hashes)
