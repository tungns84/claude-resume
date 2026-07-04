# claude-resume (ccsessions)

> List, search, and resume your [Claude Code](https://claude.com/claude-code) sessions from the terminal — with token usage and estimated cost per session.

_[Tiếng Việt bên dưới ↓](#tiếng-việt)_

---

## English

### Purpose

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

### Requirements

- Python 3.8+
- Claude Code (transcripts under `~/.claude/projects/`)
- Optional: PowerShell (for the `ccs` wrapper on Windows)

### Usage

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

### Options

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

### Notes

- Subagent transcripts (`<session>/subagents/*.jsonl`) are skipped in listings.
- Output is forced to UTF-8 (session content is frequently non-ASCII).
- On Windows 10+, ANSI colors are enabled via virtual-terminal processing.

---

## Tiếng Việt

### Mục đích

Claude Code lưu mỗi phiên làm việc dưới dạng file JSONL tại
`~/.claude/projects/<đường-dẫn-mã-hóa>/<session-uuid>.jsonl`.

`ccsessions` đọc các file này và hiển thị tổng quan nhanh, có màu:

- **Các phiên chạy gần đây**, nhóm theo dự án.
- **Xem trước tin nhắn cuối** của user / assistant cho từng phiên.
- **Tổng số token và chi phí USD ước tính** (đổi màu theo mức chi tiêu).
- Cờ **⚠ unfinished** khi lượt cuối là tin nhắn của user (chưa có phản hồi).
- Lệnh **`claude --resume <uuid>`** sẵn sàng copy cho mỗi phiên.
- **Trình chọn tương tác** (`--pick`) để resume phiên đã chọn ngay lập tức.

Chi phí là **ước tính** — giá thay đổi theo thời gian và hệ số cache chỉ gần đúng.
Chỉnh bảng `PRICING` trong `ccsessions.py` nếu cần.

### Yêu cầu

- Python 3.8+
- Claude Code (có transcript trong `~/.claude/projects/`)
- Tùy chọn: PowerShell (dùng cho wrapper `ccs` trên Windows)

### Cách dùng

Chạy trực tiếp script Python:

```bash
python ccsessions.py                  # các phiên trong 2h gần nhất
python ccsessions.py --since 30m      # khoảng thời gian tùy chỉnh (30m / 2h / 1d / 90s)
python ccsessions.py --all            # bỏ lọc thời gian
python ccsessions.py --grep "tu-khoa" # tìm trong nội dung tin nhắn (regex)
python ccsessions.py --project acl    # chỉ dự án có đường dẫn chứa "acl"
python ccsessions.py --limit 20       # giới hạn số phiên hiển thị
python ccsessions.py --pick           # trình chọn tương tác → resume phiên
python ccsessions.py --show <uuid>    # in toàn bộ transcript của một phiên
```

Trên Windows, dùng wrapper PowerShell `ccs.ps1` (tự tìm Python, ép UTF-8):

```powershell
.\ccs.ps1                 # 2h gần nhất
.\ccs.ps1 --since 30m     # khoảng thời gian tùy chỉnh
.\ccs.ps1 --all           # bỏ lọc thời gian
.\ccs.ps1 --grep "threat" # tìm trong nội dung tin nhắn
.\ccs.ps1 --project acl   # lọc theo đường dẫn dự án
.\ccs.ps1 --pick          # trình chọn tương tác → resume
.\ccs.ps1 --show <uuid>   # in transcript của một phiên
```

Đặt `ccs.ps1` vào `PATH` (hoặc tạo alias) để gọi `ccs` từ bất cứ đâu.

### Tùy chọn

| Cờ | Mô tả |
|------|-------------|
| `--since <dur>` | Khoảng thời gian: `30m`, `2h`, `1d`, `90s` (mặc định `2h`). |
| `--all` | Bỏ qua lọc thời gian. |
| `--grep <regex>` | Lọc phiên có nội dung khớp regex (không phân biệt hoa thường). |
| `--project <str>` | Lọc theo chuỗi con trong thư mục làm việc của dự án. |
| `--limit <n>` | Hiển thị tối đa `n` phiên. |
| `--width <n>` | Độ rộng text xem trước (mặc định `160`). |
| `--pick` | Trình chọn tương tác; chọn phiên và resume. |
| `--color <mode>` | `auto` / `always` / `never` (tôn trọng `NO_COLOR`). |
| `--show <uuid>` | In toàn bộ transcript của một phiên. |

### Ghi chú

- Transcript của subagent (`<session>/subagents/*.jsonl`) bị bỏ qua khi liệt kê.
- Output ép về UTF-8 (nội dung phiên thường không phải ASCII).
- Trên Windows 10+, màu ANSI được bật qua virtual-terminal processing.

---

## License

MIT
