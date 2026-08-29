#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 味检测脚本（速报/晚报场景专用）。

用法:
    python flavor_check.py <文本文件>
    python flavor_check.py <文本文件> --json   # 机器可读输出

规则来源: SKILL.md「去 AI 味精华」章节,蒸馏自 humanizer-zh + sound-human。
退出码: 0 = 干净(或仅 WARN), 1 = 有 ERROR 级命中(格言公式/高频词)。
"""
import argparse
import json
import re
import sys
from pathlib import Path

# ---- 检测规则 ---------------------------------------------------------------

# ERROR 级: 出现即必须重写
APHRISM_FORMULAS = [
    (r"这个[^。]{0,6}本身就是", "格言收尾公式: 「这个X本身就是Y」"),
    (r"不是[^。]{1,20}[，,]?\s*(而|是)(一[种次个]|更)", "否定排比: 「不是X，而是Y」"),
    (r"(恰恰|正好|恰恰就)说明", "格言公式: 「恰恰说明」"),
    (r"背后的逻辑是", "格言公式: 「背后的逻辑是」"),
    (r"真正的? (看点|问题|意义)是", "格言公式: 「真正的看点是」"),
    (r"这(不仅|不止)是[^。]{1,15}[，,]更", "否定排比: 「这不仅X，更Y」"),
    (r"值得记住的是", "填充词: 「值得记住的是」"),
]

HIGH_FREQ_WORDS = [
    "值得注意的是", "综上所述", "总的来说", "赋能", "助力", "深度融合",
    "强强联合", "里程碑", "新篇章", "划时代", "按下暂停键", "交出答卷",
    "打响第一枪", "落下实锤", "画上句号", "掀起波澜", "注入强心剂",
    "可谓", "堪称教科书", "罕见",
]

# WARN 级: 提示但不阻断(单次出现可容忍)
DRAMA_WORDS = ["引爆", "背刺", "碾压", "霸榜", "狂飙", "杀疯", "王炸", "炸裂", "暴击"]
ING_ANALYSIS = [r"推动着", r"重塑着", r"加速着", r"改变着", r"引领着"]
MARKERS = [r"标志着", r"预示着", r"意味着", r"宣告着"]

# 自造口语压缩(humanizer 反例黑名单第1条: 为去AI腔强行堆自造口语)
# 2026-08-28 实际踩坑: 「最硬一条」
FAUX_COLLOQUIAL = [
    r"最硬一", r"这波稳", r"含金量拉满", r"格局打开", r"直接封神",
    r"赢麻", r"杀疯了", r"泪目", r"破防了",
]

# 数字包装: 「两个数字值得记住」「三个信号」
NUMBER_WRAP = [r"[两三]个(数字|信号|看点|细节|关键词)"]


def check_text(text: str) -> dict:
    errors, warns = [], []
    lines = text.splitlines()

    # 逐行扫(便于报行号)
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        for pattern, desc in APHRISM_FORMULAS:
            for m in re.finditer(pattern, line):
                errors.append({"line": i, "type": desc, "hit": m.group(0)[:40],
                               "context": line.strip()[:60]})
        for w in HIGH_FREQ_WORDS:
            if w in line:
                errors.append({"line": i, "type": f"AI 高频词: 「{w}」", "hit": w,
                               "context": line.strip()[:60]})
        for w in DRAMA_WORDS:
            if w in line:
                warns.append({"line": i, "type": f"戏剧动词(单次可容忍): 「{w}」", "hit": w,
                              "context": line.strip()[:60]})
        for pat in ING_ANALYSIS + MARKERS:
            for m in re.finditer(pat, line):
                warns.append({"line": i, "type": f"-ing 式分析/标记词: 「{m.group(0)}」",
                              "hit": m.group(0), "context": line.strip()[:60]})
        for pat in FAUX_COLLOQUIAL:
            for m in re.finditer(pat, line):
                errors.append({"line": i, "type": f"自造口语压缩(「{m.group(0)}…」,没人这么说话,改完整句子)",
                               "hit": m.group(0), "context": line.strip()[:60]})
        for pat in NUMBER_WRAP:
            for m in re.finditer(pat, line):
                warns.append({"line": i, "type": f"数字包装: 「{m.group(0)}」",
                              "hit": m.group(0), "context": line.strip()[:60]})

    # 戏剧动词密度: 全文 >=3 个不同戏剧动词 → 升 ERROR
    distinct_drama = {w for w in DRAMA_WORDS if w in text}
    if len(distinct_drama) >= 3:
        errors.append({"line": 0, "type": f"戏剧动词堆叠(≥3 种不同): {sorted(distinct_drama)}",
                       "hit": "", "context": ""})

    # 工整结构提示: 连续 3+ 行长度接近(±15%)且都 >20 字 → WARN
    lens = [len(l.strip()) for l in lines if len(l.strip()) > 20]
    if len(lens) >= 3:
        for k in range(len(lens) - 2):
            trio = lens[k:k + 3]
            avg = sum(trio) / 3
            if all(abs(x - avg) / avg < 0.15 for x in trio):
                warns.append({"line": 0, "type": "疑似工整对称段落(连续3行长接近)",
                              "hit": "", "context": f"长度 {trio}"})
                break

    return {"errors": errors, "warns": warns}


def main():
    # Windows GBK 控制台兜底: 强制 UTF-8 输出
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="AI 味检测(速报场景)")
    ap.add_argument("file", help="待检测文本文件")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    p = Path(args.file)
    if not p.is_file():
        print(json.dumps({"error": f"file not found: {args.file}"}, ensure_ascii=False))
        return 2

    text = p.read_text(encoding="utf-8", errors="replace")
    result = check_text(text)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        n_err, n_warn = len(result["errors"]), len(result["warns"])
        print(f"AI 味检测: {p.name} — ERROR {n_err} 处 / WARN {n_warn} 处\n")
        for e in result["errors"]:
            loc = f"L{e['line']}" if e["line"] else "全文"
            print(f"  ✗ [{loc}] {e['type']}")
            if e["context"]:
                print(f"       {e['context']}")
        for w in result["warns"]:
            loc = f"L{w['line']}" if w["line"] else "全文"
            print(f"  △ [{loc}] {w['type']}")
        if n_warn:
            print("\n  △ = 可容忍提示;  ✗ = 必须重写后再发")
        if n_err == 0 and n_warn == 0:
            print("  干净,可发。")

    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
