#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_messages.py — 批量扫描飞书全部会话（所有群 + 所有私聊），筛选与当前用户相关的消息。

不依赖 search:message 权限，只用 im +chat-messages-list（im:message 权限即可）。

用法：
  python scan_messages.py --date 2026-08-13                     # 扫单日（日报/早间梳理）
  python scan_messages.py --start 2026-08-10 --end 2026-08-14   # 扫区间（周报）
  可选：
    --out FILE          输出到文件（默认打印到 stdout）
    --context N         每条相关消息保留的前文条数（默认 2）
    --max-per-chat N    单会话最多拉取条数（默认 200）
    --tz +08:00         时区（默认 +08:00）

相关性判定（宁可多收不漏收，语义取舍交给上层 LLM）：
  1. sent_by_me  我发出的消息（私聊/群里都算我的工作痕迹）
  2. mention_me  mentions 里有我
  3. name_hit    消息文本出现我的姓名/英文名（别人提到我）
  4. p2p 会话里对方发来的消息默认全部相关（私聊天然是找我的）
  相关消息的前 N 条同会话消息作为 context 保留。

输出 JSON：
{
  "me": {...}, "range": {"start","end"},
  "chats_total": N, "chats_scanned": N, "chats_with_messages": N,
  "messages_total": N, "relevant_count": N,
  "by_chat": [{"chat_name","chat_mode","total","relevant"}],
  "relevant": [{"chat_name","chat_mode","create_time","sender_name",
                "content","sent_by_me","mention_me","name_hit","context"}]
}
"""
import argparse
import json
import sys

import larklib


def day_range(args):
    tz = args.tz
    if args.date:
        return f"{args.date}T00:00:00{tz}", f"{args.date}T23:59:59{tz}"
    if args.start and args.end:
        return f"{args.start}T00:00:00{tz}", f"{args.end}T23:59:59{tz}"
    sys.stderr.write("ERROR: 需要 --date 或 --start/--end\n")
    sys.exit(2)


def fetch_messages(chat_id, start, end, max_msgs):
    """拉取单个会话时间范围内的消息，自动翻页。"""
    msgs, token = [], None
    while len(msgs) < max_msgs:
        args = ["im", "+chat-messages-list", "--chat-id", chat_id,
                "--start", start, "--end", end, "--sort", "asc",
                "--page-size", "50", "--json"]
        if token:
            args += ["--page-token", token]
        data = larklib.run_cli_json(args, timeout=60)
        if not data:
            break
        d = data.get("data") or {}
        batch = d.get("messages") or []
        msgs.extend(batch)
        if not d.get("has_more") or not batch:
            break
        token = d.get("page_token")
        if not token:
            break
    return msgs[:max_msgs]


def is_relevant(msg, me):
    """返回 (相关?, sent_by_me, mention_me, name_hit)。"""
    sender = msg.get("sender") or {}
    sid = sender.get("id") or ""
    content = msg.get("content") or ""
    sent_by_me = sid == me["open_id"]
    mention_me = any(
        (m.get("id") == me["open_id"]) for m in (msg.get("mentions") or []))
    name_hit = False
    if not sent_by_me:
        for kw in me["keywords"]:
            if kw and kw in content:
                name_hit = True
                break
    return (sent_by_me or mention_me or name_hit), sent_by_me, mention_me, name_hit


def slim(msg, cap=500):
    content = msg.get("content") or ""
    if len(content) > cap:
        content = content[:cap] + "…"
    return {
        "create_time": msg.get("create_time", ""),
        "sender_name": (msg.get("sender") or {}).get("name")
                       or (msg.get("sender") or {}).get("sender_type") or "?",
        "content": content,
        "msg_type": msg.get("msg_type", ""),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--out")
    ap.add_argument("--context", type=int, default=2)
    ap.add_argument("--max-per-chat", type=int, default=200)
    ap.add_argument("--tz", default="+08:00")
    args = ap.parse_args()

    start, end = day_range(args)
    me = larklib.get_identity()
    chats = larklib.list_chats()

    relevant, by_chat = [], []
    chats_with_msgs = 0
    messages_total = 0

    for i, c in enumerate(chats):
        cid = c.get("chat_id")
        cname = c.get("name") or cid
        cmode = c.get("chat_mode") or "group"
        if not cid:
            continue
        # 先看总数，无消息直接跳过（-q 直接返回数字）
        tdata = larklib.run_cli_json(
            ["im", "+chat-messages-list", "--chat-id", cid,
             "--start", start, "--end", end, "-q", ".data.total"], timeout=30)
        total = 0
        if isinstance(tdata, int):
            total = tdata
        elif isinstance(tdata, dict):
            try:
                total = int((tdata.get("data") or {}).get("total") or 0)
            except (TypeError, ValueError):
                total = 0
        if total <= 0:
            continue

        msgs = fetch_messages(cid, start, end, args.max_per_chat)
        if not msgs:
            continue

        # 跳过纯机器人私聊（对方全是 app/bot 的 p2p，如"飞书招聘""任务助手"）
        if cmode == "p2p":
            other_types = {
                (m.get("sender") or {}).get("sender_type")
                for m in msgs
                if (m.get("sender") or {}).get("id") != me["open_id"]
            }
            if other_types and other_types <= {"app", "bot", ""}:
                continue

        chats_with_msgs += 1
        messages_total += len(msgs)

        # 逐条判定相关性
        flags = []
        for m in msgs:
            rel, by_me, mention, name_hit = is_relevant(m, me)
            # 私聊里对方发来的消息天然相关
            if cmode == "p2p" and not by_me and not rel:
                rel = True
            flags.append((rel, by_me, mention, name_hit))

        kept_idx = set()
        for idx, (rel, _b, _m, _n) in enumerate(flags):
            if rel:
                kept_idx.add(idx)
                for j in range(max(0, idx - args.context), idx):
                    kept_idx.add(j)  # 前文上下文

        chat_relevant = 0
        for idx in sorted(kept_idx):
            rel, by_me, mention, name_hit = flags[idx]
            item = slim(msgs[idx])
            item.update({
                "chat_name": cname, "chat_mode": cmode,
                "sent_by_me": by_me, "mention_me": mention,
                "name_hit": name_hit,
                "context": (idx not in (
                    k for k in kept_idx if flags[k][0])) and not rel,
            })
            relevant.append(item)
            if rel:
                chat_relevant += 1

        by_chat.append({"chat_name": cname, "chat_mode": cmode,
                        "total": len(msgs), "relevant": chat_relevant})
        sys.stderr.write(f"\r已扫描 {i + 1}/{len(chats)} 个会话")

    sys.stderr.write("\n")
    relevant.sort(key=lambda x: x["create_time"])

    result = {
        "me": me,
        "range": {"start": start, "end": end},
        "chats_total": len(chats),
        "chats_scanned": len(chats),
        "chats_with_messages": chats_with_msgs,
        "messages_total": messages_total,
        "relevant_count": sum(1 for r in relevant if not r["context"]),
        "by_chat": sorted(by_chat, key=lambda x: -x["relevant"]),
        "relevant": relevant,
    }
    text = json.dumps(result, ensure_ascii=False, indent=1)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        sys.stderr.write(
            f"✅ 已写入 {args.out}：相关消息 {result['relevant_count']} 条"
            f"（含上下文 {len(relevant)} 条）\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
