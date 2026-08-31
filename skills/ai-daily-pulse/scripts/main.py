#!/usr/bin/env python3
"""AI Daily Pulse - 主入口

设计原则:
  - 脚本只负责 [采集 + 去重 + 输出] ,不主动调用任何 LLM
  - LLM 评分/分类/摘要 由调用方(Claude 主 Agent)在采集后、推送前完成
  - 输出端根据 config.feishu_configured() 自动选择 Feishu Card 或 Markdown stdout

子命令:
  collect   仅采集 + 精确/历史去重,输出文章 JSON 到 stdout
  deliver   读取(已含或未含 score 的) JSON,做后处理 + 输出
  pipeline  采集 + 兜底评分 + 输出(无 LLM 时的纯规则模式,适合 cron)
  test      采集 + 去重统计(不输出文章列表)
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import (
    TIER1_RSS_SOURCES, TIER2_WEB_SOURCES,
    DATA_DIR, CACHE_DIR, LOG_FILE, TOP_N_ARTICLES,
    get_all_rss_sources,
)
from collectors import rss_collector, api_collector, github_collector, web_collector
from dedup import deduplicate, mark_as_sent
from processor import post_process
from pusher import deliver as pusher_deliver
from evolve import discover_sources, record_selection, record_stale, quality_report


def _log_run(mode: str, tier: int, total: int, pushed: int, duration: float, error: str = ''):
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'mode': mode,
        'tier': tier,
        'total_collected': total,
        'pushed': pushed,
        'duration_seconds': round(duration, 1),
        'error': error,
    }
    log_data = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, encoding='utf-8') as f:
                log_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            log_data = []
    log_data.append(entry)
    log_data = log_data[-100:]
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


# ============================================================
# 采集
# ============================================================
def collect_articles(tier: int = 2, source_key: str = None) -> list:
    all_articles = []

    if source_key:
        rss_sources = get_all_rss_sources()
        all_sources = rss_sources + TIER2_WEB_SOURCES
        target = next((s for s in all_sources if s['key'] == source_key), None)
        if target:
            if target in rss_sources:
                return rss_collector.fetch_single_source(target, use_cache=False)
            return web_collector.fetch_single_source(target)
        if source_key == 'github_trending':
            return github_collector.fetch_all(use_cache=False)
        if source_key == 'huggingface_papers':
            return api_collector.fetch_huggingface_papers(use_cache=False)
        print(f"[ERROR] Unknown source: {source_key}", file=sys.stderr)
        return []

    print("\n=== Tier 1: RSS Sources ===", file=sys.stderr)
    rss_articles = rss_collector.fetch_all()
    print(f"  Total RSS: {len(rss_articles)} articles", file=sys.stderr)
    all_articles.extend(rss_articles)

    print("\n=== Tier 1: API Sources ===", file=sys.stderr)
    api_articles = api_collector.fetch_all()
    print(f"  Total API: {len(api_articles)} articles", file=sys.stderr)
    all_articles.extend(api_articles)

    if tier >= 2:
        print("\n=== Tier 2: GitHub Trending ===", file=sys.stderr)
        github_articles = github_collector.fetch_all()
        print(f"  Total GitHub: {len(github_articles)} articles", file=sys.stderr)
        all_articles.extend(github_articles)

        print("\n=== Tier 2: Web Sources ===", file=sys.stderr)
        web_articles = web_collector.fetch_all()
        print(f"  Total Web: {len(web_articles)} articles", file=sys.stderr)
        all_articles.extend(web_articles)

    return all_articles


# ============================================================
# 子命令实现
# ============================================================
def cmd_collect(args):
    """仅采集 + 去重(SHA + 历史),输出 JSON"""
    articles = collect_articles(tier=args.tier or 2, source_key=args.source)

    # 自我进化: 从采集结果自动发现新信源(探测 feed 并注册,只增不减)
    if args.evolve and articles:
        try:
            discover_sources(articles, max_probe=args.max_probe)
        except Exception as e:
            print(f"[Evolve] 信源发现失败(不影响主流程): {e}", file=sys.stderr)

    if args.no_dedup:
        unique = articles
    else:
        unique = deduplicate(articles)
    print(f"[Collect] {len(articles)} -> {len(unique)} (after dedup)", file=sys.stderr)
    print(json.dumps(unique, ensure_ascii=False, indent=2))


def cmd_deliver(args):
    """读取 JSON 输入(可由主 Agent 评分后传入),做后处理 + 输出"""
    if sys.stdin.isatty() and not args.input:
        print("[ERROR] Provide articles via --input <file> or stdin", file=sys.stderr)
        sys.exit(1)

    if args.input:
        with open(args.input) as f:
            articles = json.load(f)
    else:
        articles = json.loads(sys.stdin.read())

    selected = post_process(articles, top_n=args.top_n, already_scored=args.scored)
    print(f"[Deliver] selected {len(selected)} articles", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        return

    ok = pusher_deliver(selected, chat_id=args.chat_id, force_stdout=args.stdout)
    if ok and not args.no_mark_sent:
        mark_as_sent(selected)
        # 自我进化: 被选中推送 = 正反馈,抬高其信源信用
        record_selection(selected)


def cmd_pipeline(args):
    """完整流程(规则评分,无 LLM): collect -> dedup -> fallback score -> deliver"""
    start = time.time()
    tier = args.tier or 2
    print(f"[Pipeline] tier={tier}", file=sys.stderr)

    articles = collect_articles(tier=tier, source_key=args.source)
    if not articles:
        print("[WARN] No articles collected.", file=sys.stderr)
        _log_run('pipeline', tier, 0, 0, time.time() - start, 'no_articles')
        return

    # 自我进化: 自动发现新信源(探测 feed 并注册)
    if args.evolve:
        try:
            discover_sources(articles, max_probe=args.max_probe)
        except Exception as e:
            print(f"[Evolve] 信源发现失败(不影响主流程): {e}", file=sys.stderr)

    unique = deduplicate(articles)
    print(f"[Dedup] {len(articles)} -> {len(unique)}", file=sys.stderr)
    if not unique:
        _log_run('pipeline', tier, len(articles), 0, time.time() - start, 'all_duplicated')
        return

    selected = post_process(unique, top_n=args.top_n, already_scored=False)
    print(f"[Selected] top {len(selected)}", file=sys.stderr)

    pushed = 0
    if args.dry_run:
        print(json.dumps(selected, ensure_ascii=False, indent=2))
    else:
        ok = pusher_deliver(selected, chat_id=args.chat_id, force_stdout=args.stdout)
        if ok:
            pushed = len(selected)
            mark_as_sent(selected)
            # 自我进化: 选中推送 = 正反馈
            record_selection(selected)

    _log_run('pipeline', tier, len(articles), pushed, time.time() - start)
    print(f"\n[Done] {time.time() - start:.1f}s", file=sys.stderr)


def cmd_evolve(args):
    """自我进化: 信源发现 / 品质报告 / 旧闻标记"""
    if args.sub == 'discover':
        articles = []
        if getattr(args, 'input', None):
            with open(args.input) as f:
                articles = json.load(f)
        elif not sys.stdin.isatty():
            articles = json.loads(sys.stdin.read())
        found = discover_sources(articles, max_probe=args.max_probe, dry_run=args.dry_run)
        print(f"[Evolve] 本轮探测 {len(found)} 个候选信源", file=sys.stderr)
    elif args.sub == 'report':
        print(quality_report())
    elif args.sub == 'mark-stale':
        record_stale(args.source)
        print(f"[Evolve] 已标记 {len(args.source)} 个信源出旧闻(降信用)", file=sys.stderr)


def cmd_test(args):
    """测试模式"""
    articles = collect_articles(tier=args.tier or 1, source_key=args.source)
    unique = deduplicate(articles)
    print(f"Collected: {len(articles)}")
    print(f"After dedup: {len(unique)}")
    by_source = {}
    for a in unique:
        src = a.get('source', 'unknown')
        by_source[src] = by_source.get(src, 0) + 1
    print("\nBy source:")
    for src, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  {src}: {count}")


# ============================================================
# CLI
# ============================================================
def build_parser():
    parser = argparse.ArgumentParser(description='AI Daily Pulse')
    sub = parser.add_subparsers(dest='cmd', required=True)

    # collect
    p = sub.add_parser('collect', help='采集 + 去重,输出 JSON')
    p.add_argument('--tier', type=int, choices=[1, 2])
    p.add_argument('--source', help='单源 key')
    p.add_argument('--no-dedup', action='store_true', help='跳过去重')
    p.add_argument('--evolve', dest='evolve', action='store_true', default=True, help='信源自发现(默认开)')
    p.add_argument('--no-evolve', dest='evolve', action='store_false', help='跳过信源自发现')
    p.add_argument('--max-probe', type=int, default=10, help='每轮最多探测的新域名数')
    p.set_defaults(func=cmd_collect)

    # deliver
    p = sub.add_parser('deliver', help='读取 JSON,后处理 + 输出')
    p.add_argument('--input', help='文章 JSON 文件;不传则从 stdin 读')
    p.add_argument('--scored', action='store_true', help='输入已含 score/summary/category')
    p.add_argument('--top-n', type=int, default=TOP_N_ARTICLES)
    p.add_argument('--chat-id', help='飞书群 chat_id')
    p.add_argument('--stdout', action='store_true', help='强制 Markdown 输出')
    p.add_argument('--dry-run', action='store_true', help='仅输出选中的 JSON')
    p.add_argument('--no-mark-sent', action='store_true', help='不写入 sent 历史')
    p.set_defaults(func=cmd_deliver)

    # pipeline (无 LLM 全流程)
    p = sub.add_parser('pipeline', help='完整流程(规则评分,无 LLM)')
    p.add_argument('--tier', type=int, choices=[1, 2])
    p.add_argument('--source', help='单源 key')
    p.add_argument('--top-n', type=int, default=TOP_N_ARTICLES)
    p.add_argument('--chat-id', help='飞书群 chat_id')
    p.add_argument('--stdout', action='store_true', help='强制 Markdown 输出')
    p.add_argument('--dry-run', action='store_true', help='仅打印选中的 JSON')
    p.add_argument('--evolve', dest='evolve', action='store_true', default=True, help='信源自发现(默认开)')
    p.add_argument('--no-evolve', dest='evolve', action='store_false', help='跳过信源自发现')
    p.add_argument('--max-probe', type=int, default=10, help='每轮最多探测的新域名数')
    p.set_defaults(func=cmd_pipeline)

    # evolve (自我进化)
    p = sub.add_parser('evolve', help='自我进化: 信源发现 / 品质报告 / 旧闻标记')
    esub = p.add_subparsers(dest='sub', required=True)
    d = esub.add_parser('discover', help='从 stdin/--input 读文章 JSON,探测并注册新信源')
    d.add_argument('--input', help='文章 JSON 文件')
    d.add_argument('--max-probe', type=int, default=15)
    d.add_argument('--dry-run', action='store_true')
    d.set_defaults(func=cmd_evolve)
    r = esub.add_parser('report', help='输出信源品质信用报告')
    r.set_defaults(func=cmd_evolve)
    s = esub.add_parser('mark-stale', help='标记信源出旧闻(负反馈降信用)')
    s.add_argument('--source', action='append', required=True, help='源 key,可多次')
    s.set_defaults(func=cmd_evolve)

    # test
    p = sub.add_parser('test', help='采集 + 去重统计')
    p.add_argument('--tier', type=int, choices=[1, 2])
    p.add_argument('--source', help='单源 key')
    p.set_defaults(func=cmd_test)

    return parser


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    args = build_parser().parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
