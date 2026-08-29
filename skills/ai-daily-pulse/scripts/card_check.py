#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书卡片 JSON 校验脚本(schema 2.0 速报卡片专用)。

用法:
    python card_check.py <卡片JSON文件>
    python card_check.py <卡片JSON文件> --json

校验项(对照 SKILL.md 卡片规范):
  1. schema == "2.0"
  2. 无 note 标签(schema 2.0 不支持,报 unsupported tag note)——落款应为 div+notation
  3. 全局连续序号: markdown 条目里 **N. 开头的编号必须从 1 连续递增,跨板块不重置
  4. 每条目带来源链接: 编号条目后应跟 [来源 · 时间 · 类型](url) 格式链接
  5. header 结构: title + subtitle + template
退出码: 0 = 通过, 1 = 违规。
"""
import argparse
import json
import re
import sys
from pathlib import Path


def iter_elements(node):
    """深度遍历所有 dict 节点。"""
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from iter_elements(v)
    elif isinstance(node, list):
        for item in node:
            yield from iter_elements(item)


def check(card: dict) -> dict:
    issues, oks = [], []

    # 1. schema
    if card.get("schema") == "2.0":
        oks.append("schema 2.0 ✓")
    else:
        issues.append(f"schema 应为 2.0,实际 {card.get('schema')!r}")

    # 2. note 标签
    note_tags = [n for n in iter_elements(card) if isinstance(n, dict) and n.get("tag") == "note"]
    if not note_tags:
        oks.append("无 note 标签 ✓")
    else:
        issues.append(f"发现 {len(note_tags)} 处 note 标签(schema 2.0 已不支持,改用 div + notation 灰字)")

    # 3+4. 条目序号与链接
    md_blocks = [n["content"] for n in iter_elements(card)
                 if isinstance(n, dict) and n.get("tag") == "markdown" and "content" in n]
    all_md = "\n\n".join(md_blocks)
    nums = [int(m) for m in re.findall(r"\*\*(\d+)\.\s", all_md)]
    if nums:
        expect = list(range(1, len(nums) + 1))
        if nums == expect:
            oks.append(f"全局连续序号 1-{len(nums)} ✓")
        else:
            bad = [f"{i}:{n}" for i, n in enumerate(nums, 1) if n != i]
            issues.append(f"序号不连续: 位置{bad[:5]}(应从 1 连续递增,跨板块不重置)")
        # 链接覆盖: 每个编号条目后面应有 markdown 链接
        blocks = re.split(r"\n\s*\n", all_md)
        missing_link = []
        for b in blocks:
            m = re.match(r"\*\*(\d+)\.", b.strip())
            if m and "](" not in b:
                missing_link.append(m.group(1))
        if missing_link:
            issues.append(f"条目 {missing_link} 缺来源链接([来源 · 时间 · 类型](url))")
        elif nums:
            oks.append(f"全部 {len(nums)} 条带来源链接 ✓")
    else:
        issues.append("未找到编号条目(**N. 格式)")

    # 5. header
    header = card.get("header", {})
    if header.get("title", {}).get("content") and header.get("subtitle", {}).get("content") \
            and header.get("template"):
        oks.append(f"header ✓ ({header['title']['content']})")
    else:
        issues.append("header 缺 title/subtitle/template")

    return {"entries": len(nums), "issues": issues, "oks": oks}


def main():
    # Windows GBK 控制台兜底: 强制 UTF-8 输出
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="飞书速报卡片 JSON 校验")
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    p = Path(args.file)
    if not p.is_file():
        print(json.dumps({"error": f"file not found: {args.file}"}, ensure_ascii=False))
        return 2
    try:
        card = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return 2

    result = check(card)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"卡片校验: {p.name}(条目 {result['entries']} 条)\n")
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
