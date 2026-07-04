<div align="center">

**English** · [Tiếng Việt](README.vi.md)

# claude-resume

**List, search, and resume your [Claude Code](https://claude.com/claude-code) sessions from the terminal — with token usage and estimated cost per session.**

</div>

---

## Purpose

Claude Code stores every session as a JSONL transcript under
`~/.claude/projects/<encoded-project-path>/<session-uuid>.jsonl`.

`ccsessions` reads those transcripts and gives you a fast, colorized overview:

- **Which sessions ran recently**, grouped by project.
- **Last user / assistant message** preview per session.
- **Token totals and estimated USD cost** (color-coded by spend).
- **⚠ unfinished** flag when the last turn was a user message (no reply yet).
- A ready-to-copy **`claude --resume <uuid>`** command for each session.
- An **interactive picker** (`--pick`) that resumes the chosen session directly.

Cost figures are **estimates** — pricing changes over time and cache multipliers
are approximate. Edit the `PRICING` table in `ccsessions.py` to taste.

## Requirements

- Python 3.8+
- Claude Code (transcripts under `~/.claude/projects/`)
- Optional: PowerShell (for the `ccs` wrapper on Windows)

## Usage

Run the Python script directly:

```bash
python ccsessions.py                  # sessions touched in the last 2h
python ccsessions.py --since 30m      # custom window (30m / 2h / 1d / 90s)
python ccsessions.py --all            # no time filter
python ccsessions.py --grep "keyword" # search across message content (regex)
python ccsessions.py --project acl    # only projects whose path contains "acl"
python ccsessions.py --limit 20       # cap number of sessions shown
python ccsessions.py --pick           # interactive picker → resume a session
python ccsessions.py --show <uuid>    # dump one full session transcript
```

On Windows, use the PowerShell wrapper `ccs.ps1` (auto-finds Python, forces UTF-8):

```powershell
.\ccs.ps1                 # last 2h
.\ccs.ps1 --since 30m     # custom window
.\ccs.ps1 --all           # no time filter
.\ccs.ps1 --grep "threat" # search message content
.\ccs.ps1 --project acl   # filter by project path
.\ccs.ps1 --pick          # interactive picker → resume
.\ccs.ps1 --show <uuid>   # dump one transcript
```

Put `ccs.ps1` on your `PATH` (or add an alias) to call `ccs` from anywhere.

## Options

| Flag | Description |
|------|-------------|
| `--since <dur>` | Time window: `30m`, `2h`, `1d`, `90s` (default `2h`). |
| `--all` | Ignore the time window. |
| `--grep <regex>` | Filter sessions whose content matches the regex (case-insensitive). |
| `--project <str>` | Filter by substring of the project working directory. |
| `--limit <n>` | Show at most `n` sessions. |
| `--width <n>` | Preview text width (default `160`). |
| `--pick` | Interactive picker; select a session and resume it. |
| `--color <mode>` | `auto` / `always` / `never` (respects `NO_COLOR`). |
| `--show <uuid>` | Dump the full transcript of one session. |

## Notes

- Subagent transcripts (`<session>/subagents/*.jsonl`) are skipped in listings.
- Output is forced to UTF-8 (session content is frequently non-ASCII).
- On Windows 10+, ANSI colors are enabled via virtual-terminal processing.

## License

MIT
