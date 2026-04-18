# 2046 孟之 AI Secretary Team

## Project Owner
- Name: 孟之
- Email: mengzhi0226@gmail.com
- Timezone: Asia/Shanghai (UTC+8)

## How to Start Every Agent Session
1. Run this to get today's date:
   ```
   python -c "import datetime; print(datetime.date.today())"
   ```
2. Read `aboutme.json` to load user profile, health data, and preferences.

## Directory Layout
- Personal profile: `aboutme.json` (always read this first)
- Daily outputs: `YYYY-MM-DD/` subdirectories (create if missing)
- Email script: `scripts/send_email.py`
- Project root: `c:/Users/hrgap/OneDrive/Desktop/2046孟之CC/`

## Output Language
All reports are written in **Simplified Chinese** unless otherwise specified.
All file writes use UTF-8 encoding.

## Email
Send completed reports via:
```
python scripts/send_email.py --subject "标题" --body-file YYYY-MM-DD/filename.md
```

## Agent Roster
| Agent | Schedule | Output |
|---|---|---|
| 新闻z | 07:00 CST | `YYYY-MM-DD/news.md` |
| 投资z | 07:30 CST | `YYYY-MM-DD/invest.md` |
| 健康z | 08:00 CST | `YYYY-MM-DD/health.md` |
| 牛马z | 08:30 CST | `YYYY-MM-DD/todo.md` |

## Permissions
You have permission to:
- Read/Write/Edit all files in this project directory
- Use WebSearch and WebFetch for live data
- Run `python scripts/send_email.py` to send email
- Run `python -c "..."` to get dates or do calculations
- Run `mkdir` to create date subdirectories
