#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
message_map.py —— 消息清单机械盘点器(对抗性业务验收 Step 0 的兜底工具)

用途:验收前需要列出功能的全部"消息入口/应答/推送/异步回调/错误码返回",
手列容易漏。本脚本按可配置的正则扫描代码目录,输出分类清单(file:line),
与人工清单对照,漏列的消息入口一目了然。

它只做盘点,不做分支分析——分支怎么回包仍必须人工读代码。

用法:
    python message_map.py --dir <功能代码目录> [--config message-map.example.json] [--json]

配置:JSON 文件,字段见 message-map.example.json。每个团队的框架命名不同,
第一次使用时把 regex 改成你们项目自己的约定,之后复用。
仅依赖 Python 标准库(3.6+),Windows/Linux/macOS 通用。
"""
import argparse
import json
import os
import re
import sys

DEFAULT_CONFIG = {
    "_comment": "示例配置:regex 需按你们项目的框架命名修改。",
    "include_ext": [".cpp", ".h", ".hpp", ".cc", ".c", ".lua", ".py", ".js", ".ts"],
    "exclude_dirs": ["build", "bin", ".svn", ".git", "node_modules", "__pycache__"],
    "max_file_bytes": 2 * 1024 * 1024,
    "max_results_per_pattern": 500,
    "patterns": [
        {"name": "消息处理器", "regex": r"handle_\w+"},
        {"name": "应答/回包", "regex": r"sendResponse\s*\("},
        {"name": "主动推送", "regex": r"sendPush\s*\(|push\w*Status\s*\("},
        {"name": "异步回调", "regex": r"callback_\w+"},
        {"name": "错误码返回", "regex": r"return\s+Error_\w+"},
    ],
}


def load_config(path):
    if not path:
        return DEFAULT_CONFIG
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    for key in ("include_ext", "patterns"):
        if key not in cfg:
            sys.exit("[错误] 配置缺少必需字段: %s" % key)
    return cfg


def is_probably_binary(chunk):
    return b"\x00" in chunk


def scan_file(path, compiled, max_bytes):
    try:
        if os.path.getsize(path) > max_bytes:
            return None
        with open(path, "rb") as f:
            head = f.read(8192)
        if is_probably_binary(head):
            return None
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError:
        return None
    hits = []
    for lineno, line in enumerate(lines, 1):
        for name, rx in compiled:
            if rx.search(line):
                hits.append((name, lineno, line.strip()[:160]))
    return hits


def walk(root, include_ext, exclude_dirs, max_bytes, compiled):
    results = {name: [] for name, _ in compiled}
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in include_ext:
                continue
            full = os.path.join(dirpath, fn)
            hits = scan_file(full, compiled, max_bytes)
            if hits is None:
                continue
            scanned += 1
            rel = os.path.relpath(full, root)
            for name, lineno, snippet in hits:
                results[name].append({"file": rel, "line": lineno, "code": snippet})
    return results, scanned


def main():
    ap = argparse.ArgumentParser(description="消息清单机械盘点器")
    ap.add_argument("--dir", default=".", help="要扫描的代码目录(默认当前目录)")
    ap.add_argument("--config", default=None, help="配置 JSON 路径(默认用内置示例配置)")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出(供程序消费)")
    args = ap.parse_args()

    cfg = load_config(args.config)
    compiled = []
    for p in cfg["patterns"]:
        try:
            compiled.append((p["name"], re.compile(p["regex"])))
        except re.error as e:
            sys.exit("[错误] 模式 %r 的正则非法: %s" % (p.get("name"), e))

    include_ext = {e.lower() for e in cfg["include_ext"]}
    exclude_dirs = set(cfg.get("exclude_dirs", []))
    max_bytes = int(cfg.get("max_file_bytes", 2 * 1024 * 1024))
    cap = int(cfg.get("max_results_per_pattern", 500))

    results, scanned = walk(args.dir, include_ext, exclude_dirs, max_bytes, compiled)

    if args.json:
        print(json.dumps({"scanned_files": scanned, "results": results},
                         ensure_ascii=False, indent=2))
        return

    print("扫描目录: %s (共 %d 个文件)\n" % (os.path.abspath(args.dir), scanned))
    if args.config is None:
        print("[提示] 正在使用内置示例配置。请复制 scripts/message-map.example.json")
        print("       并把 regex 改成你们项目的命名约定,再用 --config 指定。\n")
    for name, _ in compiled:
        hits = results[name]
        print("== %s: %d 处 ==" % (name, len(hits)))
        for h in hits[:cap]:
            print("  %s:%d  %s" % (h["file"], h["line"], h["code"]))
        if len(hits) > cap:
            print("  ... 另有 %d 处未显示(可调 max_results_per_pattern)" % (len(hits) - cap))
        print()
    print("盘点完成。请用手列的消息清单对照以上结果:")
    print("  - 清单里有、脚本没扫到 → 确认命名是否不在配置里,或该消息确实缺失")
    print("  - 脚本扫到、清单里没有 → 漏列了一条反馈路径,补进验收靶子")


if __name__ == "__main__":
    main()
