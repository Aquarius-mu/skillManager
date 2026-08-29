#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""小红书版规范校验脚本。

用法:
    python xhs_check.py <文本文件>
    python xhs_check.py <文本文件> --json

校验项(对照 SKILL.md 小红书规范 v3 — 2026-08-29 500 字铁律):
  1. 字数铁律: 正文原始长度(含空格、换行、话题标签, 即小红书编辑器计数) ≤ 500
  2. 标题格式: 首行「M月D日AI速报｜...」
  3. 结构: 有「今日头条」、条目数 ≤ 4、有悬念收尾(最想测/最好奇/见分晓)
  4. 话题标签: 末尾有 #...[话题]# 且数量 5-10
退出码: 0 = 通过, 1 = 有硬性违规。
"""
import argparse
import json
import re
import sys
from pathlib import Path


def check(text: str) -> dict:
    issues, oks = [], []
    lines = text.splitlines()
    stripped = "".join(text.split())  # 净字数(去全部空白)

    # 1. 字数(500 字铁律 v3 — 编辑器计数, 含空格换行标签)
    net, raw = len(stripped), len(text)
    if raw <= 500:
        oks.append(f"编辑器计数 {raw} ≤ 500 ✓ (净字数 {net})")
    else:
        issues.append(f"编辑器计数 {raw} > 500 (含空格换行标签),需删 {raw - 500} 字")
    if net > 460:
        issues.append(f"净字数 {net} > 460,排版空白余量不足")

    # 2. 标题(允许「8 月 28 日」带空格写法)
    first = next((l for l in lines if l.strip()), "")
    if re.match(r"^\s*\d{1,2}\s*月\s*\d{1,2}\s*日\s*AI\s*速报\s*[｜|]", first):
        oks.append("标题格式 ✓")
    else:
        issues.append(f"标题格式不符(应为「M月D日AI速报｜…」): {first[:30]}")

    # 3. 结构
    if "今日头条" in text:
        oks.append("今日头条 ✓")
    else:
        issues.append("缺「今日头条」板块")
    # emoji 序号(1️⃣ = '1' + FE0F + 20E3 组合字符)或数字序号
    digit_entries = len(re.findall(r"(?m)^\s*\d[️⃣]", text))
    if digit_entries == 0:
        digit_entries = len(re.findall(r"(?m)^\s*\d[、.．]\s", text))
    if digit_entries <= 4:
        oks.append(f"条目数 {digit_entries} ≤ 4 ✓")
    else:
        issues.append(f"条目数 {digit_entries} > 4(500 字铁律下最多 4 条)")
    if re.search(r"(最想测|最好奇|见分晓|等?着?看|晚上见)", text):
        oks.append("悬念收尾 ✓")
    else:
        issues.append("缺悬念式收尾(最想测/最好奇/见分晓)")

    # 4. 话题标签
    tags = re.findall(r"#([^#\n]{1,30}?)\s*\[话题\]#", text)
    if 5 <= len(tags) <= 10:
        oks.append(f"话题标签 {len(tags)} 个 ✓")
    else:
        issues.append(f"话题标签 {len(tags)} 个(建议 5-10)")

    return {"net_chars": net, "raw_chars": raw, "entries": digit_entries,
            "tags": len(tags), "issues": issues, "oks": oks}


def main():
    # Windows GBK 控制台兜底: 强制 UTF-8 输出
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="小红书版规范校验")
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    p = Path(args.file)
    if not p.is_file():
        print(json.dumps({"error": f"file not found: {args.file}"}, ensure_ascii=False))
        return 2

    result = check(p.read_text(encoding="utf-8", errors="replace"))

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"小红书规范校验: {p.name}")
        print(f"  编辑器计数 {result['raw_chars']} / 净字数 {result['net_chars']} / "
              f"条目 {result['entries']} / 标签 {result['tags']}\n")
        for ok in result["oks"]:
            print(f"  ✓ {ok}")
        for iss in result["issues"]:
            print(f"  ✗ {iss}")
        if not result["issues"]:
            print("\n  全部通过,可发。")
        else:
            print("\n  ✗ 项为硬性违规,改完再发。")

    return 1 if result["issues"] else 0


if __name__ == "__main__":
    sys.exit(main())
