#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
review_setup.py — cpp-codereview 的确定性准备阶段

职责（全部由脚本保证，不依赖模型自觉）：
  1. 收集未提交改动（SVN 优先，Git 兜底）
  2. 给 diff 加真实行号标注（新行号 / 旧行号）
  3. 解析每个 hunk 的行号范围，供审查阶段做"行号必须落在改动行"校验
  4. 按「每组 <= MAX_FILES 个文件 且 <= MAX_LINES 变更行」切分审查单元
  5. 扫描 .ai_review/rules/*.md 作为项目自定义规则

两种传输方式：
  local — 本机 svn/git 可用（Windows 上工作副本格式过旧时会失败）
  ssh   — 通过 ssh 在远端 Linux 跑 svn（本项目：Z: 盘是远端 ~/<your-branch> 的 Samba 映射）

自动探测顺序：local svn -> local git -> ssh（若给了 --ssh）

产出目录结构（写在本地，便于 agent 直接 Read）：
  <code_dir>/reviewsession/ctx_<MMDD_HHMM>/
    ├── index.json     分组索引 + 行号范围 + 规则清单（小，先读它）
    ├── s001.diff      第 1 组带行号的 diff
    └── ...

用法：
  python review_setup.py
  python review_setup.py --ssh user@<your-host> --remote-dir ~/<your-branch>
  python review_setup.py --vcs git --max-files 5 --max-lines 300
"""

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

MAX_FILES_PER_GROUP = 5
MAX_LINES_PER_GROUP = 300
MAX_RULE_FILES = 10
MAX_TOTAL_RULE_SIZE = 200_000


def _run(cmd, cwd=None, timeout=60, shell_str=None):
    """跑命令。shell_str 非空时按 shell 字符串执行（用于 ssh）。"""
    try:
        if shell_str is not None:
            r = subprocess.run(shell_str, shell=True, capture_output=True,
                               timeout=timeout)
        else:
            r = subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)
        try:
            out = r.stdout.decode('utf-8')
        except UnicodeDecodeError:
            out = r.stdout.decode('latin-1', errors='replace')
        err = b''
        try:
            err = r.stderr.decode('utf-8', errors='replace')
        except Exception:
            pass
        return r.returncode, out, err
    except subprocess.TimeoutExpired:
        return -1, '', 'timeout'
    except Exception as e:
        return -1, '', str(e)


# ───────────────────────── 传输层 ─────────────────────────

class LocalTransport:
    kind = 'local'

    def __init__(self, code_dir):
        self.code_dir = code_dir

    def sh(self, cmd_str, timeout=60):
        return _run(None, cwd=self.code_dir, timeout=timeout, shell_str=cmd_str)

    def describe(self):
        return 'local:%s' % self.code_dir


class SshTransport:
    kind = 'ssh'

    def __init__(self, target, remote_dir, local_dir):
        self.target = target
        self.remote_dir = remote_dir
        self.local_dir = local_dir

    def sh(self, cmd_str, timeout=120):
        inner = 'cd %s && %s' % (self.remote_dir, cmd_str)
        full = 'ssh -o BatchMode=yes -o StrictHostKeyChecking=no %s %s' % (
            self.target, json.dumps(inner))
        return _run(None, timeout=timeout, shell_str=full)

    def describe(self):
        return 'ssh:%s:%s' % (self.target, self.remote_dir)


# ───────────────────────── 改动收集 ─────────────────────────

def detect_vcs(t):
    rc, _, _ = t.sh('svn info', timeout=20)
    if rc == 0:
        return 'svn'
    rc, _, _ = t.sh('git rev-parse --is-inside-work-tree', timeout=20)
    if rc == 0:
        return 'git'
    return ''


def collect_svn(t):
    rc, out, err = t.sh('svn status --depth infinity', timeout=120)
    if rc != 0:
        raise RuntimeError('svn status failed: %s' % err.strip()[:200])
    changes = []
    for line in out.splitlines():
        if not line or line[0] in ('?', 'X', '!', '~', 'I'):
            continue
        s = line[0]
        path = line[8:].strip()
        if not path:
            continue
        if s in ('A',):
            ct = 'new'
        elif s in ('D',):
            ct = 'deleted'
        elif s in ('M', 'R', 'C'):
            ct = 'modified'
        else:
            continue
        changes.append((path, ct))
    return changes


def collect_git(t):
    rc, out, _ = t.sh('git status --porcelain', timeout=60)
    if rc != 0:
        raise RuntimeError('git status failed')
    changes = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        xy, path = line[:2], line[3:].strip()
        if ' -> ' in path:
            path = path.split(' -> ')[-1]
        if xy.strip() == '??':
            continue
        ct = 'deleted' if 'D' in xy else ('new' if ('A' in xy or 'R' in xy) else 'modified')
        changes.append((path, ct))
    return changes


def get_diff(t, vcs, path):
    q = json.dumps(path)
    if vcs == 'svn':
        cmd = 'svn diff -x "-U 5 -p --ignore-eol-style" -- %s' % q
    else:
        cmd = 'git diff HEAD -- %s' % q
    rc, out, _ = t.sh(cmd, timeout=180)
    if rc != 0 or not out.strip():
        if vcs == 'git':
            rc, out, _ = t.sh('git diff --cached -- %s' % q, timeout=180)
    return out if rc == 0 else ''


# ───────────────────────── diff 加工 ─────────────────────────

HUNK_RE = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')


def annotate_and_map(diff_text):
    """给 diff 加行号；返回 (annotated_text, [(new_start, new_end), ...])"""
    out, ranges = [], []
    old_line = new_line = 0
    started = False
    new_start = new_end = 0

    for line in diff_text.split('\n'):
        m = HUNK_RE.match(line)
        if m:
            if started:
                ranges.append((new_start, new_end))
            new_line = int(m.group(3))
            new_start = new_line
            new_end = new_line + max(1, int(m.group(4) or 1)) - 1
            old_line = int(m.group(1))
            started = True
            out.append(line)
        elif line.startswith(('+++', '---', 'Index:', '=====')) or line == '':
            out.append(line)
        elif line.startswith('+'):
            out.append('%4d + %s' % (new_line, line[1:]))
            new_line += 1
        elif line.startswith('-'):
            out.append('%4d - %s' % (old_line, line[1:]))
            old_line += 1
        elif line.startswith(' '):
            out.append('%4d   %s' % (new_line, line[1:]))
            old_line += 1
            new_line += 1
        else:
            out.append(line)

    if started:
        ranges.append((new_start, new_end))
    return '\n'.join(out), ranges


def count_change_lines(diff_text):
    return sum(1 for l in diff_text.splitlines()
               if l.startswith(('+', '-')) and not l.startswith(('+++', '---')))


def group_by_size(items, max_files, max_lines):
    groups, current, cur_lines = [], [], 0
    for it in items:
        n = it[2]
        if current and (len(current) >= max_files or cur_lines + n > max_lines):
            groups.append(current)
            current, cur_lines = [], 0
        current.append(it)
        cur_lines += n
    if current:
        groups.append(current)
    return groups


# ───────────────────────── 项目规则扫描（本地文件系统） ─────────────────────────

def _ancestor_dirs(file_path):
    parent = Path(file_path).parent
    if str(parent) in ('', '.'):
        return []
    parts = parent.parts
    return [Path(*parts[:i + 1]).as_posix() for i in range(len(parts))]


def scan_project_rules(code_root, files):
    root = Path(code_root)
    seen_dirs, rule_dirs = set(), []

    d0 = root / '.ai_review' / 'rules'
    if d0.is_dir():
        seen_dirs.add(d0.as_posix())
        rule_dirs.append(d0)

    for fp in files:
        for rel in _ancestor_dirs(fp):
            d = root / rel / '.ai_review' / 'rules'
            k = d.as_posix()
            if d.is_dir() and k not in seen_dirs:
                seen_dirs.add(k)
                rule_dirs.append(d)

    ordered, skipped, total, seen_files = [], [], 0, set()
    for d in rule_dirs:
        for rf in sorted(d.glob('*.md')):
            k = rf.as_posix()
            if k in seen_files:
                continue
            seen_files.add(k)
            try:
                sz = rf.stat().st_size
            except OSError:
                continue
            if len(ordered) >= MAX_RULE_FILES or total + sz > MAX_TOTAL_RULE_SIZE:
                skipped.append(k)
                continue
            ordered.append(k)
            total += sz
    return {'rule_files': ordered, 'skipped': skipped}


# ───────────────────────── 主流程 ─────────────────────────

def main():
    ap = argparse.ArgumentParser(description='cpp-codereview setup stage')
    ap.add_argument('--vcs', choices=['svn', 'git'], default=None)
    ap.add_argument('--dir', default=None, help='local code dir (default: cwd)')
    ap.add_argument('--ssh', default=None, help='user@host for remote svn')
    ap.add_argument('--remote-dir', default=None, help='remote working copy path')
    ap.add_argument('--max-files', type=int, default=MAX_FILES_PER_GROUP)
    ap.add_argument('--max-lines', type=int, default=MAX_LINES_PER_GROUP)
    args = ap.parse_args()

    code_dir = os.path.abspath(args.dir or os.getcwd())

    # 选择传输方式
    transport, vcs = None, None
    if args.ssh:
        if not args.remote_dir:
            print('ERROR: --ssh requires --remote-dir')
            return 2
        transport = SshTransport(args.ssh, args.remote_dir, code_dir)
        vcs = args.vcs or detect_vcs(transport)
    else:
        transport = LocalTransport(code_dir)
        vcs = args.vcs or detect_vcs(transport)
        if not vcs and os.environ.get('REVIEW_SSH'):
            target = os.environ['REVIEW_SSH']
            rdir = os.environ.get('REVIEW_REMOTE_DIR', '.')
            transport = SshTransport(target, rdir, code_dir)
            vcs = args.vcs or detect_vcs(transport)

    if not vcs:
        print('ERROR: no VCS detected. Use --vcs, or --ssh user@host --remote-dir PATH')
        return 1

    try:
        changes = collect_svn(transport) if vcs == 'svn' else collect_git(transport)
    except RuntimeError as e:
        print('ERROR: %s' % e)
        return 1

    reviewable = [(p, ct) for p, ct in changes if ct != 'deleted']
    deleted = [p for p, ct in changes if ct == 'deleted']
    if not reviewable:
        print('NO_CHANGES')
        return 0

    def fetch(item):
        path, _ct = item
        raw = get_diff(transport, vcs, path)
        if not raw.strip():
            return None
        annotated, ranges = annotate_and_map(raw)
        return (path, annotated, count_change_lines(raw), ranges)

    with ThreadPoolExecutor(max_workers=min(8, max(1, len(reviewable)))) as ex:
        fetched = [r for r in ex.map(fetch, reviewable) if r]

    if not fetched:
        print('NO_CHANGES')
        return 0

    ts = datetime.now().strftime('%m%d_%H%M')
    out_dir = Path(code_dir) / 'reviewsession' / ('ctx_%s' % ts)
    out_dir.mkdir(parents=True, exist_ok=True)

    groups = group_by_size(fetched, args.max_files, args.max_lines)
    sessions = []
    for i, grp in enumerate(groups, 1):
        sid = 's%03d' % i
        diff_path = out_dir / ('%s.diff' % sid)
        parts, line_ranges = [], {}
        for path, annotated, _n, ranges in grp:
            parts.append('=== FILE: %s ===\n%s' % (path, annotated))
            line_ranges[path] = ranges
        diff_path.write_text('\n\n'.join(parts), encoding='utf-8')
        sessions.append({
            'session_id': sid,
            'files': [g[0] for g in grp],
            'change_lines': sum(g[2] for g in grp),
            'diff_path': str(diff_path),
            'line_ranges': line_ranges,
        })

    index = {
        'vcs': vcs,
        'transport': transport.describe(),
        'code_root_local': code_dir,
        'total_files': len(fetched),
        'total_change_lines': sum(f[2] for f in fetched),
        'deleted_files': deleted,
        'project_rules': scan_project_rules(code_dir, [f[0] for f in fetched]),
        'sessions': sessions,
    }
    index_path = out_dir / 'index.json'
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding='utf-8')

    print('OK')
    print('INDEX=%s' % index_path)
    print('TRANSPORT=%s VCS=%s' % (transport.describe(), vcs))
    print('FILES=%d GROUPS=%d LINES=%d' % (len(fetched), len(sessions),
                                           index['total_change_lines']))
    for s in sessions:
        print('  %s: %d files, %d lines -> %s' % (s['session_id'], len(s['files']),
                                                   s['change_lines'], s['diff_path']))
    if deleted:
        print('  (skipped %d deleted files)' % len(deleted))
    return 0


if __name__ == '__main__':
    sys.exit(main())
