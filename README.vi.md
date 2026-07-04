<div align="center">

[English](README.md) · **Tiếng Việt**

# claude-resume

**Liệt kê, tìm kiếm và resume các phiên [Claude Code](https://claude.com/claude-code) ngay trên terminal — kèm số token và chi phí ước tính cho từng phiên.**

</div>

---

## Mục đích

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

## Yêu cầu

- Python 3.8+
- Claude Code (có transcript trong `~/.claude/projects/`)
- Tùy chọn: PowerShell (dùng cho wrapper `ccs` trên Windows)

## Cách dùng

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

## Tùy chọn

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

## Ghi chú

- Transcript của subagent (`<session>/subagents/*.jsonl`) bị bỏ qua khi liệt kê.
- Output ép về UTF-8 (nội dung phiên thường không phải ASCII).
- Trên Windows 10+, màu ANSI được bật qua virtual-terminal processing.

## Giấy phép

MIT
