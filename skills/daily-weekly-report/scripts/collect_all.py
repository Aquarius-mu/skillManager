#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect_all.py — 一站式采集：消息 + 日历 + 妙记 + 文档活动。

整合两个来源（互补，避免各自短板）：
  - 消息：本 skill 的 scan_messages.py（不需要 search:message 权限，全量群+私聊）
  - 日历/妙记/文档活动：lark-daily-tasks skill 的 run.py collect-day
    （它的消息采集依赖 search:message 会失败，合并时忽略其 messages 字段）

用法：
  python collect_all.py --date 2026-08-13 --out context.json          # 单日
  python collect_all.py --start 2026-08-10 --end 2026-08-14 --out week.json  # 区间（周报）

输出 JSON：
{
  "me": {...}, "range": {...},
  "messages": {...scan_messages 结果...},
  "calendar": {"items": [...], "count": N},          # 区间内逐日合并
  "minutes": {"items": [...], "count": N},
  "documents": {"opened": [...], "edited": [...], "commented": [...], "created": [...],
                "unique_count": N}
}
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

import larklib
import scan_messages

LDT_SKILL_DIR = os.path.expanduser(r"~\.claude\skills\lark-daily-tasks")


def run_ldt_collect(date):
    """调用 lark-daily-tasks collect-day，返回 dict 或 None。"""
    run_py = os.path.join(LDT_SKILL_DIR, "run.py")
    if not os.path.exists(run_py):
        return None
    try:
        r = subprocess.run(
            [sys.executable, "-X", "utf8", run_py, "collect-day", "--date", date],
            capture_output=True, text=True, timeout=280,
            cwd=LDT_SKILL_DIR, encoding="utf-8", errors="replace")
        if r.returncode != 0 or not (r.stdout or "").strip():
            return None
        return json.loads(r.stdout)
    except Exception:  # noqa: BLE001
        return None


def dates_between(start, end):
    d0 = dt.date.fromisoformat(start)
    d1 = dt.date.fromisoformat(end)
    days, d = [], d0
    while d <= d1:
        days.append(d.isoformat())
        d += dt.timedelta(days=1)
    return days


def simplify_cal(it):
    """精简日程条目。"""
    if not isinstance(it, dict):
        return None
    return {
        "summary": it.get("summary") or "",
        "start": (it.get("start_time") or {}).get("datetime", ""),
        "end": (it.get("end_time") or {}).get("datetime", ""),
        "organizer": (it.get("event_organizer") or {}).get("display_name", ""),
        "rsvp": it.get("self_rsvp_status", ""),
        "meeting_url": (it.get("vchat") or {}).get("meeting_url", ""),
    }


def merge_ldt(merged, ldt):
    """把单日 ldt 结果合并进 merged（日历/妙记/文档）。"""
    if not ldt:
        return
    cal = ldt.get("calendar") or {}
    if cal.get("ok") and cal.get("items"):
        for it in cal["items"]:
            s = simplify_cal(it)
            if s:
                merged["calendar"]["items"].append(s)
    mi = ldt.get("minutes") or {}
    if mi.get("ok") and mi.get("items"):
        for it in mi["items"]:
            if isinstance(it, dict):
                merged["minutes"]["items"].append({
                    "topic": it.get("topic") or it.get("title") or "",
                    "url": it.get("url") or it.get("minute_url") or "",
                    "create_time": it.get("create_time") or "",
                })
    docs = ldt.get("documents") or {}
    for key in ("opened", "edited", "commented", "created"):
        blk = docs.get(key) or {}
        items = blk.get("items") if isinstance(blk, dict) else None
        if items:
            merged["documents"][key].extend(items)
    # 注意：不合并 ldt 的 messages（依赖 search:message，通常失败；消息以 scan 为准）


def simplify_doc(it):
    """把 ldt 文档条目精简为 LLM 友好格式。"""
    if not isinstance(it, dict):
        return None
    rm = it.get("result_meta") or {}
    title = (it.get("title_highlighted") or "").strip()
    # title_highlighted 可能带 <em> 高亮标签
    title = title.replace("<em>", "").replace("</em>", "")
    return {
        "title": title or "(无标题)",
        "type": rm.get("doc_types") or it.get("entity_type") or "",
        "token": rm.get("token") or "",
        "url": rm.get("url") or "",
        "activity_time": rm.get("last_open_time_iso")
                         or rm.get("update_time_iso") or "",
    }


def dedupe_docs(merged):
    """文档精简 + 按 token 去重。"""
    all_tokens = set()
    for key in ("opened", "edited", "commented", "created"):
        seen, out = set(), []
        for it in merged["documents"][key]:
            s = simplify_doc(it)
            if not s:
                continue
            k = s["token"] or s["url"] or s["title"]
            if k in seen:
                continue
            seen.add(k)
            if s["token"]:
                all_tokens.add(s["token"])
            out.append(s)
        merged["documents"][key] = out
    merged["documents"]["unique_count"] = len(all_tokens)


def _parse_json_lenient(out):
    """有些命令 stdout 前缀有 tip 行，从第一个 '{' 开始解析。"""
    if not out:
        return None
    idx = out.find("{")
    if idx < 0:
        return None
    try:
        return json.loads(out[idx:])
    except json.JSONDecodeError:
        return None


def collect_supplementary(start, end, me_open_id, tz):
    """补采高价值结构化数据源：审批 / 邮件 / 视频会议 / 任务活动。

    每类独立降级——某类失败只标记 covered=False，不中断整体采集。
    对应 lark-daily-tasks SKILL 的"补采范围"，这里把可脚本化的部分固化。
    """
    supp = {
        "approvals": {"pending": [], "cc": [], "covered": False},
        "mails": {"items": [], "count": 0, "covered": False},
        "vc_meetings": {"items": [], "count": 0, "covered": False},
        "task_activity": {"created": [], "completed": [], "covered": False},
    }

    # 1) 审批：待我处理(topic 1) + 抄送我(topic 17)。
    #    该 API 无时间过滤参数、任务对象无 create_time，故全量返回由 LLM 按标题/摘要判断相关性。
    #    topic 3（我发起）实测对多数应用返回 field validation failed，不采集。
    def _slim_appr(t):
        sums = t.get("summaries") or []
        summary = "; ".join(
            f"{s.get('key')}:{s.get('value')}" for s in sums
            if isinstance(s, dict))
        return {"title": t.get("title") or "",
                "definition": t.get("definition_name") or "",
                "status": t.get("status") or "",
                "instance_status": t.get("instance_status") or "",
                "initiator": t.get("initiator_name") or "",
                "summary": summary,
                "link": t.get("link") or ""}
    for topic, key in (("1", "pending"), ("17", "cc")):
        data = larklib.run_cli_json(
            ["approval", "tasks", "query",
             "--params", json.dumps({"topic": topic, "page_size": 100,
                                      "user_id_type": "open_id"}),
             "--json"], timeout=40)
        if isinstance(data, dict):
            tasks = (data.get("data") or {}).get("tasks") or []
            supp["approvals"][key] = [_slim_appr(t) for t in tasks]
            if topic == "1":
                supp["approvals"]["covered"] = True

    # 2) 邮件：triage 拉最近邮件，按 date 字段过滤区间
    out, _err = larklib.run_cli(
        ["mail", "+triage", "--max", "200", "--format", "json"], timeout=60)
    data = _parse_json_lenient(out)
    if data:
        items = data.get("messages") or []
        lo, hi = f"{start} 00:00", f"{end} 23:59"
        kept = []
        for m in items:
            d = (m.get("date") or "")[:16]
            if lo <= d <= hi:
                kept.append({"date": d, "from": m.get("from") or "",
                             "subject": m.get("subject") or "",
                             "folder": m.get("folder") or "",
                             "labels": m.get("labels") or ""})
        supp["mails"]["items"] = kept
        supp["mails"]["count"] = len(kept)
        supp["mails"]["covered"] = True

    # 3) 视频会议实际参会：vc +search 按时间+参与人
    data = larklib.run_cli_json(
        ["vc", "+search", "--start", start, "--end", end,
         "--participant-ids", me_open_id, "--page-size", "30", "--json"],
        timeout=40)
    if data:
        d = data.get("data") or data
        meetings = d.get("meetings") or d.get("items") or []
        for m in meetings:
            if isinstance(m, dict):
                supp["vc_meetings"]["items"].append({
                    "topic": m.get("topic") or m.get("meeting_topic") or "",
                    "start_time": m.get("start_time") or m.get("start") or "",
                    "duration": m.get("duration") or "",
                    "meeting_no": m.get("meeting_no") or "",
                })
        supp["vc_meetings"]["count"] = len(supp["vc_meetings"]["items"])
        supp["vc_meetings"]["covered"] = True

    # 4) 任务活动：区间内新建 + 近两天完成（尽力覆盖）
    created = larklib.run_cli_json(
        ["task", "+get-my-tasks", "--complete=false",
         "--created_at", f"{start}T00:00:00{tz}", "--json"], timeout=40)
    completed = larklib.run_cli_json(
        ["task", "+get-my-tasks", "--complete=true",
         "--created_at", f"{start}T00:00:00{tz}", "--json"], timeout=40)
    if created or completed:
        def _slim(d):
            items = ((d or {}).get("data") or {}).get("items") or []
            return [{"summary": i.get("summary") or "",
                     "due_at": i.get("due_at") or "",
                     "created_at": i.get("created_at") or "",
                     "url": i.get("url") or ""} for i in items]
        supp["task_activity"]["created"] = _slim(created)
        supp["task_activity"]["completed"] = _slim(completed)
        supp["task_activity"]["covered"] = True

    return supp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--out", required=True)
    ap.add_argument("--context", type=int, default=2)
    ap.add_argument("--max-per-chat", type=int, default=200)
    ap.add_argument("--tz", default="+08:00")
    args = ap.parse_args()

    if args.date:
        start = end = args.date
    elif args.start and args.end:
        start, end = args.start, args.end
    else:
        sys.stderr.write("ERROR: 需要 --date 或 --start/--end\n")
        sys.exit(2)

    # 1) 消息扫描（复用 scan_messages 的逻辑，输出到临时文件再读回）
    tmp_scan = args.out + ".scan.tmp"
    sys.argv = ["scan_messages.py", "--start", start, "--end", end,
                "--out", tmp_scan, "--context", str(args.context),
                "--max-per-chat", str(args.max_per_chat), "--tz", args.tz]
    try:
        scan_messages.main()
    except SystemExit:
        pass
    with open(tmp_scan, encoding="utf-8") as f:
        messages = json.load(f)
    os.remove(tmp_scan)

    # 2) lark-daily-tasks 逐日采集日历/妙记/文档
    merged = {
        "calendar": {"items": [], "count": 0},
        "minutes": {"items": [], "count": 0},
        "documents": {"opened": [], "edited": [], "commented": [],
                      "created": [], "unique_count": 0},
    }
    ldt_ok = 0
    for day in dates_between(start, end):
        sys.stderr.write(f"collect lark-daily-tasks {day} ...\n")
        ldt = run_ldt_collect(day)
        if ldt:
            ldt_ok += 1
            merge_ldt(merged, ldt)
    merged["calendar"]["count"] = len(merged["calendar"]["items"])
    merged["minutes"]["count"] = len(merged["minutes"]["items"])
    dedupe_docs(merged)

    # 3) 补采高价值结构化数据源：审批/邮件/视频会议/任务活动（各自降级）
    me_open_id = (messages.get("me") or {}).get("open_id", "")
    sys.stderr.write("collect supplementary (approvals/mails/vc/tasks) ...\n")
    supp = collect_supplementary(start, end, me_open_id, args.tz)

    result = {
        "me": messages.get("me"),
        "range": {"start": start, "end": end},
        "messages": messages,
        "calendar": merged["calendar"],
        "minutes": merged["minutes"],
        "documents": merged["documents"],
        "approvals": supp["approvals"],
        "mails": supp["mails"],
        "vc_meetings": supp["vc_meetings"],
        "task_activity": supp["task_activity"],
        "sources": {
            "messages": "scan_messages.py（全量群+私聊，不依赖 search:message）",
            "calendar_minutes_documents":
                f"lark-daily-tasks collect-day（成功 {ldt_ok}/{len(dates_between(start, end))} 天）",
            "supplementary": "审批/邮件/视频会议/任务活动（lark-cli approval/mail/vc/task，各自独立降级）",
        },
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    docs = merged["documents"]
    ap_n = len(supp["approvals"]["pending"]) + len(supp["approvals"]["cc"])
    sys.stderr.write(
        f"✅ context 已写入 {args.out}：相关消息 {messages.get('relevant_count', 0)} 条、"
        f"日历 {merged['calendar']['count']} 项、妙记 {merged['minutes']['count']} 项、"
        f"文档(去重) {docs['unique_count']} 项、审批 {ap_n} 项、"
        f"邮件 {supp['mails']['count']} 封、视频会议 {supp['vc_meetings']['count']} 场\n")


if __name__ == "__main__":
    main()
