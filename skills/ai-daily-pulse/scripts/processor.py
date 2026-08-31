#!/usr/bin/env python3
"""AI Daily Pulse - 文章后处理(去重 + 兜底评分 + 分类配额)

本模块只做不依赖 LLM 的处理:
  1. 跨分类模糊去重 (Jaccard bigram)
  2. 兜底规则评分 (无 LLM 时使用)
  3. 分类保底选择 (确保每个分类至少 N 条)

LLM 评分由调用方 (主 Agent) 完成,本脚本不再发起任何 HTTP 请求。
"""

import json
import sys
from typing import List, Dict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import CATEGORIES


# ============================================================
# 模糊去重
# ============================================================
def _bigrams(text: str) -> set:
    """提取文本的字符 bigram 集合"""
    import re
    text = re.sub(r'[^\w]', '', text.lower())
    if len(text) < 2:
        return {text}
    return {text[i:i + 2] for i in range(len(text) - 1)}


def _jaccard_similarity(text_a: str, text_b: str) -> float:
    """Jaccard bigram 相似度"""
    set_a = _bigrams(text_a)
    set_b = _bigrams(text_b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def deduplicate_cross_category(articles: List[Dict], threshold: float = 0.65) -> List[Dict]:
    """跨分类去重: 同一篇文章只保留分数最高的那条"""
    if not articles:
        return articles

    keep = [True] * len(articles)
    for i in range(len(articles)):
        if not keep[i]:
            continue
        for j in range(i + 1, len(articles)):
            if not keep[j]:
                continue
            sim = _jaccard_similarity(articles[i].get('title', ''), articles[j].get('title', ''))
            if sim >= threshold:
                score_i = articles[i].get('score', 0)
                score_j = articles[j].get('score', 0)
                if score_j > score_i:
                    keep[i] = False
                    break
                else:
                    keep[j] = False

    result = [a for a, k in zip(articles, keep) if k]
    removed = len(articles) - len(result)
    if removed:
        print(f"  [Dedup] Cross-category removed {removed} duplicates", file=sys.stderr)
    return result


# ============================================================
# 兜底规则评分 (无 LLM 时使用)
# ============================================================
def fallback_scoring(articles: List[Dict]) -> List[Dict]:
    """基于规则的简单评分,在没有 LLM 时使用"""
    hot_keywords = [
        'release', 'launch', 'announce', 'new', 'open source',
        '发布', '开源', '突破', 'gpt', 'claude', 'gemini',
    ]

    # 信源品质加权(自我进化): 品质>0.5 的信源 +1, <0.5 的 -1
    quality_map = {}
    try:
        from evolve import source_quality_map
        quality_map = source_quality_map()
    except ImportError:
        quality_map = {}

    for a in articles:
        score = 5

        if a.get('tier') == 1:
            score += 1

        upvotes = a.get('extra', {}).get('upvotes', 0)
        if upvotes > 50:
            score += 2
        elif upvotes > 20:
            score += 1

        stars = a.get('extra', {}).get('weekly_stars', 0)
        if stars > 500:
            score += 2
        elif stars > 100:
            score += 1

        title_lower = a.get('title', '').lower()
        if any(kw in title_lower for kw in hot_keywords):
            score += 1

        # 信源品质信用加权
        qs = quality_map.get(a.get('source_key', ''), 0.5)
        score += round((qs - 0.5) * 2)

        a['score'] = max(1, min(score, 10))
        if not a.get('summary'):
            a['summary'] = (a.get('description') or '')[:50]

    return articles


# ============================================================
# 分类保底选择
# ============================================================
def select_with_category_quota(scored: List[Dict], top_n: int, min_per_category: int = 1) -> List[Dict]:
    """分类保底: 每个有内容的分类至少保留 min_per_category 条"""
    if not scored:
        return []

    by_category: Dict[str, List[Dict]] = {}
    for a in scored:
        cat = a.get('category', 'media')
        by_category.setdefault(cat, []).append(a)

    for cat in by_category:
        by_category[cat].sort(key=lambda x: x.get('score', 0), reverse=True)

    selected = []
    selected_keys = set()
    for cat, items in by_category.items():
        for a in items[:min_per_category]:
            selected.append(a)
            selected_keys.add(a.get('url') or a.get('title', ''))

    remaining = top_n - len(selected)
    if remaining > 0:
        rest = [a for a in scored
                if (a.get('url') or a.get('title', '')) not in selected_keys]
        rest.sort(key=lambda x: x.get('score', 0), reverse=True)
        selected.extend(rest[:remaining])

    selected.sort(key=lambda x: x.get('score', 0), reverse=True)
    return selected[:top_n]


# ============================================================
# 主流程: 仅做去重 + 兜底评分 + 选取
# ============================================================
def post_process(articles: List[Dict], top_n: int = 20, already_scored: bool = False) -> List[Dict]:
    """对文章做后处理(去重 + 选取)

    Args:
        articles: 待处理文章列表
        top_n: 最终返回数量
        already_scored: 是否已由 LLM 评分(否则走兜底评分)
    """
    if not articles:
        return []

    if not already_scored:
        articles = fallback_scoring(articles)

    for a in articles:
        if a.get('category') not in CATEGORIES:
            a['category'] = 'media'

    articles = deduplicate_cross_category(articles)
    return select_with_category_quota(articles, top_n)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Post-process collected articles')
    parser.add_argument('--top-n', type=int, default=20)
    parser.add_argument('--scored', action='store_true', help='输入已含 score/summary/category')
    args = parser.parse_args()

    if sys.stdin.isatty():
        print("Usage: cat articles.json | python3 processor.py [--top-n N] [--scored]", file=sys.stderr)
        sys.exit(1)

    articles = json.loads(sys.stdin.read())
    result = post_process(articles, top_n=args.top_n, already_scored=args.scored)
    print(json.dumps(result, ensure_ascii=False, indent=2))
