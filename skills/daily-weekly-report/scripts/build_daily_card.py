#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_daily_card.py — 构建「工作日早间梳理」飞书卡片（schema 2.0）并发送到当前用户个人会话。

用法：
  python build_daily_card.py content.json            # 构建并发送
  python build_daily_card.py content.json --dry-run  # 只打印卡片 JSON，不发送

content.json 格式（由上层 LLM 分析后产出）：
{
  "title": "🗓 工作日早间梳理｜08-14 周五",
  "template": "blue",                    # 可选，默认 blue
  "sections": [                          # 每个元素是一个 lark_md 文本块，块间自动加分割线
    "**孙家栋(Lucky)，早上好！**...",
    "## 📋 第一部分：昨日回望\n..."
  ],
  "footer": "💡 备注文字"                 # 可选，底部灰色小字
}

成功后打印：✅ message_id=... chat_id=...
"""
import argparse
import json
import subprocess
import sys

import larklib


def build_card(content):
    elements = []
    sections = content.get("sections") or []
    for i, sec in enumerate(sections):
        if i > 0:
            elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md", "content": sec},
        })
    if content.get("footer"):
        elements.append({"tag": "hr"})
        elements.append({
            "tag": "div",
            "text": {"tag": "lark_md",
                     "content": f'<font color="grey">{content["footer"]}</font>'},
        })
    return {
        "schema": "2.0",
        "header": {
            "title": {"tag": "plain_text",
                      "content": content.get("title", "工作梳理")},
            "template": content.get("template", "blue"),
        },
        "body": {"direction": "vertical", "elements": elements},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content_file")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with open(args.content_file, encoding="utf-8") as f:
        content = json.load(f)
    card = build_card(content)
    card_json = json.dumps(card, ensure_ascii=False)

    if args.dry_run:
        print(card_json)
        return

    me = larklib.get_identity()
    # 发到当前用户自己的个人会话（--user-id 传自己 = 发给自己）
    out, err = larklib.run_cli(
        ["im", "+messages-send", "--user-id", me["open_id"],
         "--msg-type", "interactive", "--content", card_json,
         "--as", "bot", "--json"], timeout=40)
    data = None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        pass
    if not data or data.get("ok") is False:
        sys.stderr.write(f"ERROR: 发送失败\n{out}\n{err}\n")
        sys.exit(1)
    d = data.get("data") or {}
    print(f"✅ message_id={d.get('message_id')} chat_id={d.get('chat_id')} "
          f"time={d.get('create_time')}")


if __name__ == "__main__":
    main()
