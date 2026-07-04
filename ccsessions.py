#!/usr/bin/env python3
"""ccsessions - list / search Claude Code sessions and print resume commands.

Reads the JSONL transcripts Claude Code stores under
    ~/.claude/projects/<encoded-project-path>/<session-uuid>.jsonl

Usage:
    python ccsessions.py                 # sessions touched in last 2h
    python ccsessions.py --since 30m     # custom window (30m / 2h / 1d)
    python ccsessions.py --all           # no time filter
    python ccsessions.py --grep "keyword"  # search across message content
    python ccsessions.py --project acl   # only projects whose path contains "acl"
    python ccsessions.py --limit 20      # cap number shown
    python ccsessions.py --show <uuid>   # dump a single session transcript

Notes:
    - Subagent transcripts (<session>/subagents/*.jsonl) are skipped in listings.
    - Output is forced to UTF-8 (session content is often non-ASCII).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout: session content is frequently non-ASCII and the Windows
# console defaults to cp1252, which raises UnicodeEncodeError otherwise.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ── ANSI styling ──────────────────────────────────────────────────────────
# Colors are enabled only for a real terminal, unless overridden by --color.
# NO_COLOR (https://no-color.org/) is respected.
_ANSI = {
    "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m", "italic": "\033[3m",
    "red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
    "blue": "\033[34m", "magenta": "\033[35m", "cyan": "\033[36m",
    "white": "\033[37m", "gray": "\033[90m",
    "bred": "\033[91m", "bgreen": "\033[92m", "byellow": "\033[93m",
    "bcyan": "\033[96m",
}
COLOR = True  # resolved in main()


def enable_color(mode: str) -> None:
    global COLOR
    if mode == "always":
        COLOR = True
    elif mode == "never":
        COLOR = False
    else:  # auto
        import os
        COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
    # Windows 10+: enable virtual-terminal processing so ANSI renders.
    if COLOR and sys.platform == "win32":
        try:
            import ctypes
            k = ctypes.windll.kernel32
            k.SetConsoleMode(k.GetStdHandle(-11), 7)
        except Exception:
            pass


def c(text, *styles) -> str:
    if not COLOR or not styles:
        return str(text)
    return "".join(_ANSI[s] for s in styles) + str(text) + _ANSI["reset"]

# USD per 1M tokens (input, output). Cost figures below are ESTIMATES — pricing
# changes over time and cache multipliers are approximate. Edit to taste.
# Source: Anthropic model pricing (claude-api skill, cached 2026-06-24).
PRICING = {
    "claude-fable-5": (10.0, 50.0),
    "claude-mythos-5": (10.0, 50.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-opus-4-5": (5.0, 25.0),
    "claude-opus-4-1": (5.0, 25.0),
    "claude-opus-4-0": (5.0, 25.0),
    "claude-sonnet-5": (3.0, 15.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-4-5": (3.0, 15.0),
    "claude-sonnet-4-0": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}
DEFAULT_PRICE = (5.0, 25.0)  # unknown model → assume Opus-tier

# Cache multipliers relative to base input price (5-minute TTL).
CACHE_WRITE_MULT = 1.25
CACHE_READ_MULT = 0.10


def price_for(model: str):
    if not model:
        return DEFAULT_PRICE
    if model in PRICING:
        return PRICING[model]
    for key, val in PRICING.items():
        if key in model:  # tolerate suffixes like -fast / dated snapshots
            return val
    return DEFAULT_PRICE


def sessions_root() -> Path:
    return Path.home() / ".claude" / "projects"


def parse_duration(text: str) -> float:
    """Convert '2h' / '30m' / '1d' / '90s' to seconds."""
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([smhd])?\s*", text.lower())
    if not m:
        raise argparse.ArgumentTypeError(f"bad duration: {text!r} (use 30m, 2h, 1d)")
    value = float(m.group(1))
    unit = m.group(2) or "h"
    return value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


def block_text(content) -> str:
    """Extract human-readable text from a message .content field.

    content may be a plain string, or a list of blocks
    (text / tool_use / thinking / ...). We keep only text blocks.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict) and b.get("type") == "text":
                parts.append(b.get("text", ""))
        return " ".join(parts)
    return ""


def iter_events(path: Path):
    """Yield parsed JSON objects from a JSONL file, skipping bad lines."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def scan_session(path: Path) -> dict:
    """Read one session file and summarize it."""
    cwd = None
    last_user = None
    last_assistant = None
    last_role = None          # last role that produced visible text
    msg_count = 0
    tok_in = tok_out = tok_cw = tok_cr = 0
    cost = 0.0

    for obj in iter_events(path):
        if obj.get("cwd"):
            cwd = obj["cwd"]
        t = obj.get("type")
        if t not in ("user", "assistant"):
            continue
        msg = obj.get("message", {})

        # Accumulate token usage + estimated cost from assistant messages.
        if t == "assistant":
            usage = msg.get("usage") or {}
            if usage:
                inp = usage.get("input_tokens", 0) or 0
                out = usage.get("output_tokens", 0) or 0
                cw = usage.get("cache_creation_input_tokens", 0) or 0
                cr = usage.get("cache_read_input_tokens", 0) or 0
                tok_in += inp
                tok_out += out
                tok_cw += cw
                tok_cr += cr
                pin, pout = price_for(msg.get("model"))
                cost += (
                    inp * pin
                    + out * pout
                    + cw * pin * CACHE_WRITE_MULT
                    + cr * pin * CACHE_READ_MULT
                ) / 1_000_000

        txt = block_text(msg.get("content")).strip()
        if not txt:
            continue
        msg_count += 1
        if t == "user":
            last_user = txt
            last_role = "user"
        else:
            last_assistant = txt
            last_role = "assistant"

    return {
        "path": path,
        "uuid": path.stem,
        "cwd": cwd,
        "mtime": path.stat().st_mtime,
        "last_user": last_user,
        "last_assistant": last_assistant,
        "last_role": last_role,
        "msg_count": msg_count,
        "tokens": tok_in + tok_out + tok_cw + tok_cr,
        "cost": cost,
    }


def collect_grep_text(path: Path) -> str:
    """Concatenate all user+assistant text from a session (for --grep)."""
    parts = []
    for obj in iter_events(path):
        if obj.get("type") in ("user", "assistant"):
            parts.append(block_text(obj.get("message", {}).get("content")))
    return "\n".join(parts)


def find_sessions(root: Path):
    """Yield top-level session files (skip subagents/*)."""
    for path in root.glob("*/*.jsonl"):
        if "subagents" in path.parts:
            continue
        yield path


def ago(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m"
    if seconds < 86400:
        return f"{int(seconds // 3600)}h"
    return f"{int(seconds // 86400)}d"


def fmt_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def cost_style(cost: float) -> str:
    """Green / yellow / red by spend magnitude (USD, estimate)."""
    if cost < 5:
        return "green"
    if cost < 15:
        return "yellow"
    return "bred"


def proj_name(cwd: str | None) -> str:
    if not cwd:
        return "(unknown)"
    return cwd.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]


def truncate(text: str | None, n: int) -> str:
    if not text:
        return ""
    text = " ".join(text.split())  # collapse whitespace/newlines
    return text if len(text) <= n else text[: n - 1] + "…"


def cmd_list(args) -> int:
    root = sessions_root()
    if not root.exists():
        print(f"No Claude Code projects dir at {root}", file=sys.stderr)
        return 1

    now = time.time()
    cutoff = None if args.all else now - parse_duration(args.since)
    grep_re = re.compile(args.grep, re.IGNORECASE) if args.grep else None

    rows = []
    for path in find_sessions(root):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if cutoff is not None and mtime < cutoff:
            continue
        info = scan_session(path)
        if args.project and args.project.lower() not in (info["cwd"] or "").lower():
            continue
        if grep_re:
            haystack = collect_grep_text(path)
            if not grep_re.search(haystack):
                continue
        rows.append(info)

    rows.sort(key=lambda r: r["mtime"], reverse=True)
    if args.limit:
        rows = rows[: args.limit]

    if not rows:
        print("No sessions match.")
        return 0

    # Interactive picker: number every session, prompt, then resume.
    if args.pick:
        return run_picker(rows)

    now = time.time()
    # Group by cwd, preserving mtime-desc order.
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(r["cwd"] or "(unknown cwd)", []).append(r)

    total_cost = sum(r["cost"] for r in rows)
    window = "all time" if args.all else f"last {args.since}"

    # Banner.
    print()
    print(c("  ⬢ Claude Code sessions", "bold", "bcyan"),
          c(f"· {window} · {len(rows)} session(s) · ~${total_cost:.2f} est",
            "dim"))

    rail = c("│", "gray")
    for cwd, items in groups.items():
        sub = c(f"— {len(items)}", "dim")
        print(f"\n{c('◆', 'bcyan')} {c(proj_name(cwd), 'bold', 'white')}  {sub}")
        print(f"  {c(cwd, 'dim')}")
        for r in items:
            when = c(datetime.fromtimestamp(r["mtime"]).strftime("%H:%M"), "bcyan")
            rel = c(f"{ago(now - r['mtime'])} ago", "dim")
            msgs = c(f"{r['msg_count']} msg", "gray")
            toks = c(f"{fmt_tokens(r['tokens'])} tok", "gray")
            money = c(f"~${r['cost']:.2f}", cost_style(r["cost"]))
            flag = c("  ⚠ unfinished", "byellow", "bold") if r["last_role"] == "user" else ""
            print(f"  {rail} {when} {c('·', 'gray')} {rel}   {msgs}   {toks}   {money}{flag}")
            if r["last_user"]:
                print(f"  {rail}   {c('▸', 'blue')} {truncate(r['last_user'], args.width)}")
            if r["last_assistant"]:
                print(f"  {rail}   {c('◂', 'gray')} {c(truncate(r['last_assistant'], args.width), 'dim')}")
            print(f"  {rail}   {c('↻ claude --resume ' + r['uuid'], 'dim', 'italic')}")
            print(f"  {rail}")
    print(c(f"\n  {len(rows)} session(s) · ~${total_cost:.2f} total (estimate)\n",
            "dim"))
    return 0


def run_picker(rows: list) -> int:
    """List numbered sessions, prompt for a choice, run `claude --resume`."""
    import subprocess

    now = time.time()
    print(c("\n  ⬢ Pick a session to resume\n", "bold", "bcyan"))
    for i, r in enumerate(rows, 1):
        when = c(datetime.fromtimestamp(r["mtime"]).strftime("%H:%M"), "bcyan")
        rel = c(f"{ago(now - r['mtime'])} ago", "dim")
        money = c(f"~${r['cost']:.2f}", cost_style(r["cost"]))
        flag = c(" ⚠", "byellow", "bold") if r["last_role"] == "user" else ""
        num = c(f"{i:>2}", "bold", "bgreen")
        proj = c(proj_name(r["cwd"]), "white")
        print(f"  {num}  {proj}  {when} {c('·', 'gray')} {rel}   {money}{flag}")
        print(f"      {c(truncate(r['last_user'], 96), 'dim')}")

    try:
        choice = input(c("\n  Resume # (Enter to cancel): ", "bold")).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return 0
    if not choice:
        return 0
    if not choice.isdigit() or not (1 <= int(choice) <= len(rows)):
        print(c("  Invalid selection.", "bred"), file=sys.stderr)
        return 1

    picked = rows[int(choice) - 1]
    cwd = picked["cwd"]
    cmd = ["claude", "--resume", picked["uuid"]]
    print(c(f"  → cd {cwd}  &&  {' '.join(cmd)}", "green"))
    return subprocess.call(cmd, cwd=cwd if cwd and Path(cwd).is_dir() else None)


def cmd_show(args) -> int:
    root = sessions_root()
    matches = [p for p in find_sessions(root) if p.stem == args.show]
    if not matches:
        print(f"No session with uuid {args.show}", file=sys.stderr)
        return 1
    path = matches[0]
    for obj in iter_events(path):
        t = obj.get("type")
        if t not in ("user", "assistant"):
            continue
        txt = block_text(obj.get("message", {}).get("content")).strip()
        if not txt:
            continue
        print(f"\n[{t}]\n{txt}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="List/search Claude Code sessions.")
    p.add_argument("--since", default="2h", type=str,
                   help="time window, e.g. 30m, 2h, 1d (default 2h)")
    p.add_argument("--all", action="store_true", help="ignore time window")
    p.add_argument("--grep", help="regex to search across message content")
    p.add_argument("--project", help="filter by substring of project cwd")
    p.add_argument("--limit", type=int, default=0, help="max sessions to show")
    p.add_argument("--width", type=int, default=160, help="preview text width")
    p.add_argument("--pick", action="store_true",
                   help="interactive picker: choose a session and resume it")
    p.add_argument("--color", choices=("auto", "always", "never"), default="auto",
                   help="colorize output (default auto: on for a terminal)")
    p.add_argument("--show", help="dump full transcript of one session uuid")
    args = p.parse_args(argv)

    enable_color(args.color)

    if args.show:
        return cmd_show(args)
    return cmd_list(args)


if __name__ == "__main__":
    raise SystemExit(main())
