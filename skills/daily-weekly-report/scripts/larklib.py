#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""larklib.py — 日报周报工作分析 skill 的公共库。

提供 lark-cli 调用封装、当前用户身份识别、会话列表拉取。
全公司通用：不硬编码任何用户/群信息，一切从 `lark-cli auth status` 动态获取。
"""
import json
import os
import re
import shutil
import subprocess
import sys

IS_WINDOWS = os.name == "nt"


def find_cli():
    """定位 lark-cli 可执行文件。"""
    candidates = []
    w = shutil.which("lark-cli")
    if w:
        candidates.append(w)
    if IS_WINDOWS:
        candidates.append(os.path.expanduser(
            r"~\.ClaudeDesktop\nodejs\lark-cli.cmd"))
        w2 = shutil.which("lark-cli.cmd")
        if w2:
            candidates.insert(0, w2)
    for c in candidates:
        if c and os.path.exists(c):
            return c
    sys.stderr.write("ERROR: 找不到 lark-cli，请先安装并 `lark-cli auth login`\n")
    sys.exit(2)


CLI = find_cli()


def run_cli(args, timeout=40):
    """调用 lark-cli，返回 (stdout, stderr)。args 不含可执行文件名。"""
    cmd = [CLI] + args
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            shell=IS_WINDOWS, encoding="utf-8", errors="replace")
        return (r.stdout or "").strip(), (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT"
    except Exception as e:  # noqa: BLE001
        return "", f"EXC:{e}"


def run_cli_json(args, timeout=40):
    """调用 lark-cli 并解析 JSON；失败返回 None。"""
    out, err = run_cli(args, timeout)
    if not out:
        return None
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and data.get("ok") is False:
        return None
    return data  # 可能是 dict，也可能是标量（-q 提取结果）


def get_identity():
    """获取当前登录用户身份：{open_id, name, keywords}。"""
    data = run_cli_json(["auth", "status"])
    if not data:
        sys.stderr.write("ERROR: 无法获取 lark-cli 身份，请先 `lark-cli auth login`\n")
        sys.exit(2)
    user = (data.get("identities") or {}).get("user") or {}
    open_id = user.get("openId")
    name = user.get("userName") or ""
    if not open_id:
        sys.stderr.write("ERROR: 当前无 user 身份，请先 `lark-cli auth login`\n")
        sys.exit(2)
    return {"open_id": open_id, "name": name, "keywords": name_keywords(name)}


def name_keywords(name):
    """从显示名提取检索关键词。'张三(ZhangSan)' → ['张三','ZhangSan']。"""
    kws = []
    name = (name or "").strip()
    m = re.match(r"^(.+?)\s*[（(]\s*(.+?)\s*[)）]\s*$", name)
    if m:
        cn, en = m.group(1).strip(), m.group(2).strip()
        if cn:
            kws.append(cn)
        if en:
            kws.append(en)
    elif name:
        kws.append(name)
    # 去重保序；过滤过短关键词避免误报
    seen, out = set(), []
    for k in kws:
        if len(k) >= 2 and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def list_chats(max_pages=10):
    """拉取当前用户全部会话（群 + 私聊），自动翻页。

    不传排序参数：不同 lark-cli 版本 flag 名不同（--sort / --sort-type），
    全量扫描场景下排序非必需，省略可保证版本兼容。
    """
    chats, token = [], None
    for _ in range(max_pages):
        args = ["im", "+chat-list", "--types", "group,p2p",
                "--page-size", "100", "--json"]
        if token:
            args += ["--page-token", token]
        data = run_cli_json(args)
        if not data:
            break
        d = data.get("data") or {}
        chats.extend(d.get("chats") or [])
        if not d.get("has_more"):
            break
        token = d.get("page_token")
        if not token:
            break
    return chats
