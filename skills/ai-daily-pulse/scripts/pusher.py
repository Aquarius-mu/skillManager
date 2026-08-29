#!/usr/bin/env python3
"""AI Daily Pulse - 输出层

两种输出方式:
  1. 飞书 Bot 已配置 -> 推送 Interactive Card 到飞书群
  2. 未配置 -> 输出 Markdown 到 stdout (调用方/Agent 可直接展示给用户)

判断逻辑由 config.feishu_configured() 决定。
"""

import json
import re
import sys
import ssl
import html
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import List, Dict, Optional
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import (
    FEISHU_APP_ID, FEISHU_APP_SECRET,
    FEISHU_DEFAULT_CHAT_ID, FEISHU_SOURCE_CHAT_ID,
    feishu_configured, CATEGORIES,
)

FEISHU_BASE = 'https://open.feishu.cn/open-apis'

CATEGORY_ORDER = ['media', 'coding_agent', 'engineering', 'domestic',
                  'security', 'opensource', 'research', 'official']


# ============================================================
# 通用工具
# ============================================================
def _today_str() -> str:
    tz = timezone(timedelta(hours=8))
    return datetime.now(tz).strftime('%Y-%m-%d')


def _weekday_cn() -> str:
    tz = timezone(timedelta(hours=8))
    weekdays = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    return weekdays[datetime.now(tz).weekday()]


def _group_by_category(articles: List[Dict]) -> Dict[str, List[Dict]]:
    grouped = {}
    for a in articles:
        cat = a.get('category', 'media')
        grouped.setdefault(cat, []).append(a)
    return grouped


_HTML_TAG_RE = re.compile(r'<[^>]+>')
_WHITESPACE_RE = re.compile(r'\s+')


def _clean_text(text: str, max_len: int = 80) -> str:
    """剥离 HTML 标签 + 解码实体 + 折叠空白,用于摘要展示。

    RSS 源 description 常含 <img>、<br>、&#8217; 等噪声,直接展示会损害可读性。
    """
    if not text:
        return ''
    cleaned = _HTML_TAG_RE.sub(' ', text)
    cleaned = html.unescape(cleaned)
    cleaned = _WHITESPACE_RE.sub(' ', cleaned).strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip() + '...'
    return cleaned


# ============================================================
# Markdown 输出 (无 Bot 时使用)
# ============================================================
def render_markdown(articles: List[Dict]) -> str:
    """渲染为 Markdown,直接打到 stdout"""
    today = _today_str()
    weekday = _weekday_cn()

    lines = [f"# 🤖 AI Daily Pulse | {today}({weekday})", ""]

    if not articles:
        lines.append("> 今日暂无 AI 新闻更新 🌙")
        return '\n'.join(lines)

    grouped = _group_by_category(articles)
    for cat_key in CATEGORY_ORDER:
        if cat_key not in grouped:
            continue
        cat_info = CATEGORIES.get(cat_key, {'name': cat_key, 'emoji': '📌'})
        lines.append(f"## {cat_info['emoji']} {cat_info['name']}")
        lines.append("")
        for a in grouped[cat_key]:
            title = _clean_text(a.get('title', ''), max_len=200)
            url = a.get('url', '')
            raw_summary = a.get('summary') or a.get('description') or ''
            summary = _clean_text(raw_summary, max_len=80)
            score = a.get('score', '')
            score_tag = f" `{score}/10`" if score else ''

            if url:
                lines.append(f"- **[{title}]({url})**{score_tag}")
            else:
                lines.append(f"- **{title}**{score_tag}")
            if summary:
                lines.append(f"  - {summary}")
        lines.append("")

    tier1 = sum(1 for a in articles if a.get('tier') == 1)
    tier2 = sum(1 for a in articles if a.get('tier') == 2)
    lines.append(f"---")
    lines.append(f"*共 {len(articles)} 条 | Tier 1: {tier1} | Tier 2: {tier2}*")
    return '\n'.join(lines)


# ============================================================
# 飞书卡片
# ============================================================
def _feishu_request(url: str, method: str = 'POST', headers: dict = None,
                    body: dict = None, timeout: int = 30) -> Optional[Dict]:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req_headers = {'Content-Type': 'application/json; charset=utf-8'}
    if headers:
        req_headers.update(headers)

    data = json.dumps(body).encode('utf-8') if body else None

    try:
        req = Request(url, data=data, headers=req_headers, method=method)
        with urlopen(req, timeout=timeout, context=ctx) as response:
            return json.loads(response.read().decode('utf-8'))
    except HTTPError as e:
        error_body = ''
        try:
            error_body = e.read().decode('utf-8')
        except Exception:
            pass
        print(f"  [WARN] Feishu API error: {e} | body: {error_body[:500]}", file=sys.stderr)
        if error_body:
            try:
                return json.loads(error_body)
            except json.JSONDecodeError:
                pass
        return None
    except (URLError, Exception) as e:
        print(f"  [WARN] Feishu API error: {e}", file=sys.stderr)
        return None


def _get_tenant_access_token() -> str:
    url = f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal"
    body = {'app_id': FEISHU_APP_ID, 'app_secret': FEISHU_APP_SECRET}
    result = _feishu_request(url, body=body)
    if result and result.get('code') == 0:
        return result.get('tenant_access_token', '')
    print(f"  [ERROR] Failed to get token: {result.get('msg') if result else 'No response'}",
          file=sys.stderr)
    return ''


def build_card(articles: List[Dict]) -> Dict:
    """构建飞书 Interactive Card"""
    today = _today_str()
    weekday = _weekday_cn()

    elements = []
    grouped = _group_by_category(articles)
    first_section = True

    for cat_key in CATEGORY_ORDER:
        if cat_key not in grouped:
            continue
        cat_info = CATEGORIES.get(cat_key, {'name': cat_key, 'emoji': '📌'})

        if not first_section:
            elements.append({'tag': 'hr'})
        first_section = False

        elements.append({
            'tag': 'div',
            'text': {
                'content': f"**{cat_info['emoji']} {cat_info['name']}**",
                'tag': 'lark_md',
            },
        })

        for a in grouped[cat_key]:
            title = _clean_text(a.get('title', ''), max_len=200)
            raw_summary = a.get('summary') or a.get('description') or ''
            summary = _clean_text(raw_summary, max_len=60)
            url = a.get('url', '')

            content_parts = [f"**{title}**"]
            if summary:
                content_parts.append(summary)
            if url:
                content_parts.append(f"[📖 查看原文]({url})")

            elements.append({
                'tag': 'div',
                'text': {
                    'content': '\n'.join(content_parts),
                    'tag': 'lark_md',
                },
            })

    tier1 = sum(1 for a in articles if a.get('tier') == 1)
    tier2 = sum(1 for a in articles if a.get('tier') == 2)
    elements.append({'tag': 'hr'})
    elements.append({
        'tag': 'div',
        'text': {
            'content': f"*🤖 AI Daily Pulse | 共 {len(articles)} 条 | Tier 1: {tier1} | Tier 2: {tier2}*",
            'tag': 'lark_md',
        },
    })

    return {
        'config': {'wide_screen_mode': True},
        'header': {
            'template': 'blue',
            'title': {
                'content': f"🤖 AI Daily Pulse | {today}({weekday})",
                'tag': 'plain_text',
            },
        },
        'elements': elements,
    }


def _check_card_size(card: Dict) -> Dict:
    """卡片大小检查,超 28KB 时截断"""
    card_json = json.dumps(card, ensure_ascii=False)
    size = len(card_json.encode('utf-8'))
    if size <= 28000:
        return card

    print(f"  [WARN] Card size {size} bytes > 28KB, truncating...", file=sys.stderr)
    for elem in card.get('elements', []):
        if elem.get('tag') == 'div':
            text = elem.get('text', {})
            content = text.get('content', '')
            new_lines = []
            for line in content.split('\n'):
                if not line.startswith('**') and not line.startswith('[') and len(line) > 30:
                    new_lines.append(line[:30] + '...')
                else:
                    new_lines.append(line)
            text['content'] = '\n'.join(new_lines)

    card_json = json.dumps(card, ensure_ascii=False)
    size = len(card_json.encode('utf-8'))
    if size <= 28000:
        return card

    elements = card['elements']
    while size > 28000 and len(elements) > 5:
        elements.pop(-3)
        size = len(json.dumps(card, ensure_ascii=False).encode('utf-8'))
    return card


def _build_empty_card() -> Dict:
    return {
        'config': {'wide_screen_mode': True},
        'header': {
            'template': 'grey',
            'title': {
                'content': f"🤖 AI Daily Pulse | {_today_str()}({_weekday_cn()})",
                'tag': 'plain_text',
            },
        },
        'elements': [{
            'tag': 'div',
            'text': {'content': '今日暂无 AI 新闻更新 🌙', 'tag': 'lark_md'},
        }],
    }


def resolve_chat_id(explicit_id: str = None) -> str:
    """三级优先级: --chat-id > FEISHU_SOURCE_CHAT_ID > FEISHU_DEFAULT_CHAT_ID"""
    if explicit_id:
        return explicit_id
    if FEISHU_SOURCE_CHAT_ID:
        return FEISHU_SOURCE_CHAT_ID
    return FEISHU_DEFAULT_CHAT_ID


def push_to_feishu(articles: List[Dict], chat_id: str = None) -> bool:
    """推送到飞书群"""
    chat_id = resolve_chat_id(chat_id)
    if not chat_id:
        print("  [ERROR] No chat_id provided. Set FEISHU_DEFAULT_CHAT_ID or pass --chat-id.",
              file=sys.stderr)
        return False

    token = _get_tenant_access_token()
    if not token:
        return False

    card = build_card(articles) if articles else _build_empty_card()
    card = _check_card_size(card)

    url = f"{FEISHU_BASE}/im/v1/messages?receive_id_type=chat_id"
    headers = {'Authorization': f'Bearer {token}'}
    body = {
        'receive_id': chat_id,
        'msg_type': 'interactive',
        'content': json.dumps(card, ensure_ascii=False),
    }

    result = _feishu_request(url, headers=headers, body=body)
    if result and result.get('code') == 0:
        print(f"  [OK] Sent to chat {chat_id}", file=sys.stderr)
        return True
    print(f"  [ERROR] Send failed: {result.get('msg') if result else 'No response'}",
          file=sys.stderr)
    return False


# ============================================================
# 统一出口: 自动选择推送方式
# ============================================================
def deliver(articles: List[Dict], chat_id: str = None, force_stdout: bool = False) -> bool:
    """根据配置自动选择输出方式

    Args:
        articles: 待推送文章
        chat_id: 显式指定的群 chat_id
        force_stdout: 强制走 Markdown 输出(忽略飞书配置)

    回退顺序:
      1. force_stdout 或未配置 Bot -> 直接 Markdown
      2. 配置了 Bot 但推送失败 -> 自动 Markdown 兜底,保证用户至少能看到内容
    """
    if force_stdout or not feishu_configured():
        if not feishu_configured() and not force_stdout:
            print("  [INFO] Feishu Bot not configured, falling back to stdout Markdown.",
                  file=sys.stderr)
        print(render_markdown(articles))
        return True

    if push_to_feishu(articles, chat_id=chat_id):
        return True

    print("  [WARN] Feishu push failed, falling back to stdout Markdown.",
          file=sys.stderr)
    print(render_markdown(articles))
    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='AI Daily Pulse - 输出/推送')
    parser.add_argument('--chat-id', help='飞书群 chat_id')
    parser.add_argument('--stdout', action='store_true', help='强制 Markdown 输出')
    args = parser.parse_args()

    if sys.stdin.isatty():
        print("Usage: cat articles.json | python3 pusher.py [--chat-id ID] [--stdout]",
              file=sys.stderr)
        sys.exit(1)

    articles = json.loads(sys.stdin.read())
    ok = deliver(articles, chat_id=args.chat_id, force_stdout=args.stdout)
    sys.exit(0 if ok else 1)
