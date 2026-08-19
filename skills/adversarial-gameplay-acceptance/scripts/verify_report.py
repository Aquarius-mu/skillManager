#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_report.py —— 对抗性验收报告的铁律机械校验器

三条铁律里"每条发现必须带 文件:行号"靠自觉容易松,本脚本做交付前的硬闸门:
报告不满足结构要求就不许交付。它不懂业务,只查形式——形式不过,内容免谈。

检查项:
  1. 必备章节齐全(结论/框架机制确认/需求对照/反馈路径表/发现清单/
     对抗场景卡/需确认项/覆盖率声明)
  2. P0/P1/P2 段落里每条发现(每个 bullet 块)必须含 文件:行号 定位
  3. 反馈路径表的数据行必须含证据定位(缺失记 WARN)
  4. 覆盖率声明非空,且"审了/没审"两面都写到

用法:
    python verify_report.py 报告.md
退出码: 0=通过(可有 WARN), 1=不通过(有 FAIL), 2=文件读取失败。
仅依赖 Python 标准库(3.6+)。
"""
import argparse
import re
import sys

REQUIRED_SECTIONS = [
    "结论", "框架机制确认", "需求对照", "反馈路径表",
    "发现清单", "对抗场景卡", "需确认项", "覆盖率声明",
]

# 定位格式: 任意带扩展名的路径 + 冒号(中英文) + 行号(可带范围)
LOC_RE = re.compile(
    r"[\w\./\\\-]+\.\w{1,6}\s*[:：]\s*\d+(?:\s*[-–~]\s*\d+)?"
)

SEVERITY_RE = re.compile(r"^#{1,6}\s.*\bP[012]\b", re.M)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
BULLET_RE = re.compile(r"^\s*[-*]\s+")
TABLE_SEP_RE = re.compile(r"^\s*\|[\s\-:|]+\|\s*$")


def split_sections(text):
    """返回 [(heading_text, body_lines, start_lineno), ...]"""
    sections = []
    cur_head, cur_body, cur_start = "(文档开头)", [], 1
    for i, line in enumerate(text.splitlines(), 1):
        m = HEADING_RE.match(line)
        if m:
            sections.append((cur_head, cur_body, cur_start))
            cur_head, cur_body, cur_start = m.group(2).strip(), [], i
        else:
            cur_body.append(line)
    sections.append((cur_head, cur_body, cur_start))
    return sections


def bullet_blocks(body):
    """把 bullet 列表切成块: bullet 起始行 + 其后缩进/非 bullet 的延续行。"""
    blocks, cur = [], None
    for line in body:
        if BULLET_RE.match(line):
            if cur is not None:
                blocks.append(cur)
            cur = [line]
        elif cur is not None and (line.strip() == "" or line.startswith(" ")):
            cur.append(line)
        else:
            if cur is not None:
                blocks.append(cur)
                cur = None
    if cur is not None:
        blocks.append(cur)
    return blocks


def main():
    ap = argparse.ArgumentParser(description="验收报告铁律校验器")
    ap.add_argument("report", help="报告 markdown 文件路径")
    args = ap.parse_args()

    try:
        with open(args.report, "r", encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print("[错误] 无法读取报告: %s" % e)
        sys.exit(2)

    fails, warns, oks = [], [], []
    sections = split_sections(text)
    heads = [h for h, _, _ in sections]

    # 检查 1: 必备章节
    missing = [s for s in REQUIRED_SECTIONS
               if not any(s in h for h in heads)]
    if missing:
        fails.append("缺少必备章节: %s" % "、".join(missing))
    else:
        oks.append("必备章节齐全 (%d/%d)" % (len(REQUIRED_SECTIONS), len(REQUIRED_SECTIONS)))

    # 检查 2: P0/P1/P2 每条发现必须带定位
    checked, located = 0, 0
    for head, body, start in sections:
        if not re.search(r"\bP[012]\b", head):
            continue
        for block in bullet_blocks(body):
            checked += 1
            joined = "\n".join(block)
            if LOC_RE.search(joined):
                located += 1
            else:
                first = block[0].strip()[:60]
                fails.append("发现缺少 文件:行号 定位 (约第 %d 行): %s"
                             % (start, first))
    if checked:
        oks.append("P0/P1/P2 发现 %d 条,%d 条带定位" % (checked, located))
    else:
        warns.append("未找到任何 P0/P1/P2 发现条目——若确无发现,也请写明'无'")

    # 检查 3: 反馈路径表数据行要有证据
    for head, body, start in sections:
        if "反馈路径表" not in head:
            continue
        rownum = 0
        for line in body:
            s = line.strip()
            if not s.startswith("|") or TABLE_SEP_RE.match(s):
                continue
            rownum += 1
            if rownum == 1:
                continue  # 表头
            if not LOC_RE.search(s) and "待验证" not in s and "无法验证" not in s:
                warns.append("反馈路径表第 %d 个数据行没有证据定位 (约第 %d 行)"
                             % (rownum, start))
        break

    # 检查 4: 覆盖率声明
    for head, body, _ in sections:
        if "覆盖率声明" not in head:
            continue
        content = [l for l in body if l.strip()]
        if not content:
            fails.append("覆盖率声明为空——没审的部分必须写明")
        else:
            joined = "\n".join(content)
            if not (("审了" in joined or "覆盖" in joined) and
                    ("没审" in joined or "未审" in joined or "未覆盖" in joined)):
                warns.append("覆盖率声明建议同时写明'审了什么'和'没审什么'两面")
        break

    # 输出
    for m in oks:
        print("[ OK ] %s" % m)
    for m in warns:
        print("[WARN] %s" % m)
    for m in fails:
        print("[FAIL] %s" % m)

    if fails:
        print("\n结论: 未通过 (%d FAIL, %d WARN) —— 修复 FAIL 后才能交付" %
              (len(fails), len(warns)))
        sys.exit(1)
    print("\n结论: 通过 (%d WARN,交付前建议处理)" % len(warns) if warns
          else "\n结论: 通过,无告警")
    sys.exit(0)


if __name__ == "__main__":
    main()
