# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal AI secretary team for 孟之 (mengzhi0226@gmail.com, UTC+8). Four agents run daily via Anthropic Cloud RemoteTrigger (CCR), write Markdown reports to per-agent folders, send email summaries, and push results back to this GitHub repo.

## Architecture

### Primary Flow (CCR — Production)
```
claude.ai/code/scheduled (cron) → CCR clones repo → agent runs → writes AgentName/YYYY-MM-DD.md
    → python scripts/send_email.py → git push origin main
Local machine: git pull → python scripts/dashboard_server.py → http://localhost:8080
```

### Agents & Schedules (UTC → CST)
| Agent | Folder | UTC Cron | Beijing |
|---|---|---|---|
| 新闻z | `新闻z/` | `0 23 * * *` | 07:00 |
| 投资z | `投资z/` | `30 23 * * *` | 07:30 |
| 健康z | `健康z/` | `0 0 * * *` | 08:00 |
| 牛马z | `牛马z/` | `30 0 * * *` | 08:30 |

Report files: `AgentName/YYYY-MM-DD.md` (NOT date-subdirectory layout).

### Data Store: `aboutme.json`
Single source of truth. **Always read this first.** Key fields:
- `health.weight_log` — `[{date, kg}]` — appended by dashboard `/weight` POST or direct instruction
- `health.bmi_history` — parallel array updated alongside weight_log
- `finance.watchlist` — stocks for 投资z
- `interests.news_topics` — topics for 新闻z
- `todo.recurring` — permanent tasks injected into 牛马z daily
- `smtp` — SMTP credentials read by `send_email.py` as fallback when env vars absent

### Local Dashboard (`scripts/dashboard_server.py`)
- Stdlib-only Python HTTP server on port 8080
- Routes: `GET /` → today, `GET /YYYY-MM-DD` → date view, `POST /weight` → update `aboutme.json`, `POST /task/toggle` → toggle `- [ ]`↔`- [x]` in md file, `POST /add-task` → append to `new_tasks.txt`
- Tabs: 新闻z / 投资z / 健康z / 牛马z — reads from per-agent folders
- Health tab includes Chart.js 7-day weight trend chart; weight input form shown when today's weight missing
- Run: `python scripts/dashboard_server.py` or double-click `scripts/start_dashboard.bat`

### Email (`scripts/send_email.py`)
Reads SMTP credentials in priority order: env vars (`SMTP_HOST/PORT/USER/PASS/EMAIL_TO`) → `aboutme.json` `.smtp`. Gmail App Password stored in `aboutme.json`.

### Stock Data (`scripts/get_stock_data.py`)
Uses `yfinance`. Outputs price, MA5/MA20, RSI(14), ATM options chain for each ticker. Used by local 投资z ps1 agent (not by CCR which uses WebSearch instead).

## Common Commands

```bash
# Start local dashboard
python scripts/dashboard_server.py

# Run an agent locally (Windows, requires Claude CLI)
powershell -ExecutionPolicy Bypass -File scripts/agent_xinwenz.ps1

# Fetch stock data manually
python scripts/get_stock_data.py AAPL NVDA MSFT

# Send a test email
python scripts/send_email.py --subject "Test" --body-file README.md

# Sync latest reports from cloud agents
git pull origin main
```

## Windows-Specific Notes (local ps1 agents)

The `.ps1` scripts contain **no Chinese characters** — Chinese folder paths are constructed via UTF-8 byte arrays to avoid Windows-1252 encoding parse errors:
```powershell
$outDir = [System.Text.Encoding]::UTF8.GetString([byte[]](0xE6,0x96,0xB0,0xE9,0x97,0xBB,0x7A))  # = 新闻z
```
All `.bat` launcher files are ASCII-only. The project root short path is `C:\Users\hrgap\OneDrive\Desktop\2046CC~1`.

## User Data Operations

**Record weight**: Tell Claude "今天体重 XX kg" → Claude updates `aboutme.json` and commits. Or use the dashboard web form.

**Add tasks for 牛马z**: Create `new_tasks.txt` in repo root (one task per line). The CCR agent reads and deletes it on next run. File is gitignored — must be added manually before the agent's cron fires.

**Edit agent behavior**: Go to https://claude.ai/code/scheduled → click trigger → edit the prompt. No code changes needed.

## Key Rules
- All report content in Simplified Chinese
- Reports always at `AgentName/YYYY-MM-DD.md` (never subdirectory layout)
- `aboutme.json` is committed to the repo (contains SMTP password — repo is private)
- CCR agents always end with `git add ... && git commit && git push origin main`
