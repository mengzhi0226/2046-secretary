# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal AI secretary team for 孟之 (mengzhi0226@gmail.com, UTC+8/Singapore). Four agents run daily via Anthropic Cloud RemoteTrigger (CCR), write Markdown reports to per-agent folders, send email summaries via Gmail SMTP, and push results back to GitHub. A local Python dashboard renders all reports at `http://localhost:8080`.

## Architecture

### Primary Flow (CCR — Production)
```
claude.ai/code/scheduled (cron)
  → CCR clones https://github.com/mengzhi0226/2046-secretary
  → agent runs (WebSearch + Read/Write tools)
  → writes AgentName/YYYY-MM-DD.md
  → python scripts/send_email.py
  → git push origin main (uses PAT from aboutme.json.github_pat)

Local machine:
  git pull origin main
  → python scripts/dashboard_server.py → http://localhost:8080
```

### Agents & Schedules (UTC)
| Agent | Folder | Cron (UTC) | Singapore |
|---|---|---|---|
| 新闻z | `新闻z/` | `0 23 * * *` | 07:00 |
| 投资z | `投资z/` | `30 23 * * *` | 07:30 |
| 健康z | `健康z/` | `0 0 * * *` | 08:00 |
| 牛马z | `牛马z/` | `30 0 * * *` | 08:30 |

Report path: `AgentName/YYYY-MM-DD.md` — never date-subdirectory layout.

CCR trigger IDs: 新闻z `trig_012UGD5FJW6i3YC9HeUjXhbt` · 投资z `trig_018kv9P28MGha4aiSkqHCbky` · 健康z `trig_015MrNfJ185tCgYzARSRW1YF` · 牛马z `trig_0198r98AGTKzJRLxYBrPeWtK`

To edit agent prompts or run manually: https://claude.ai/code/scheduled

### Data Stores

**`aboutme.json`** — single source of truth. Always read this first.
- `health.weight_log` — `[{date, kg}]` appended by dashboard `/weight` POST or direct instruction
- `health.bmi_history` — parallel array, updated alongside weight_log
- `finance.watchlist` — stocks for 投资z (AAPL MSFT GOOGL AMZN META NVDA TSLA MU)
- `interests.news_topics` — topics for 新闻z
- `todo.recurring` — permanent tasks injected into 牛马z daily
- `smtp` — Gmail App Password credentials, read by `send_email.py` when env vars absent
- `github_pat` — Personal Access Token (repo scope) used by CCR agents to `git push` to private repo

**`pnl_log.json`** — daily P&L entries: `{"entries": [{date, pnl, currency, note}]}`. Updated via dashboard `/pnl` POST or direct instruction. SGD currency.

**`new_tasks.txt`** — one task per line (optional `|priority` suffix). CCR 牛马z reads and deletes on next run. Gitignored — must be created manually.

### Local Dashboard (`scripts/dashboard_server.py`)
Stdlib-only Python HTTP server on port 8080. Five tabs: 📰新闻z / 📈投资z / 💪健康z / ✅牛马z / 💰盈亏

Routes:
- `GET /` → redirect to today
- `GET /YYYY-MM-DD` → full dashboard for that date
- `POST /weight` → append to `aboutme.json` health arrays, redirect back
- `POST /task/toggle` → toggle `- [ ]` ↔ `- [x]` in 牛马z md file
- `POST /add-task` → append to `new_tasks.txt`
- `POST /pnl` → upsert entry in `pnl_log.json`, redirect back

The 💰盈亏 tab shows: monthly stats cards, Tiger Trade-style calendar (green/red cells), cumulative equity Chart.js line chart, daily P&L input form.

Health tab: BMI cards + Chart.js 7-day weight trend + weight input form (shown when today missing).

### Interactive Butler (`管家.bat` → `scripts/butler.ps1`)
Opens an interactive Claude CLI session with a comprehensive system prompt. On first message: reads `aboutme.json`, gets date, fetches Singapore weather, checks which agent reports exist today, greets with full status summary. Handles all query types conversationally:
- **Stocks**: asks for ticker → runs `python scripts/get_stock_data.py TICKER` → WebSearch for news → structured analysis with Call/Put recommendations
- **Health**: reads weight_log, calculates BMI trend, can update `aboutme.json` directly
- **News**: reads today's `新闻z/` report or does live WebSearch
- **Tasks**: reads today's `牛马z/` report, can append to `new_tasks.txt`
- **P&L**: reads `pnl_log.json`, can update entries

### Stock Data (`scripts/get_stock_data.py`)
Uses `yfinance`. Call with one or more tickers. Outputs: current price, change %, MA5/MA20, RSI(14), ATM Call/Put IV with nearest expiry. Used by butler.ps1 and `问投资z实时.bat` for real-time data; CCR agents use WebSearch instead.

### Email (`scripts/send_email.py`)
SMTP credentials priority: env vars (`SMTP_HOST/PORT/USER/PASS/EMAIL_TO`) → `aboutme.json .smtp`. Usage: `python scripts/send_email.py --subject "..." --body-file path/to/file.md`

## Common Commands

```bash
# Interactive butler (primary daily interface)
管家.bat

# Quick pre-market single-stock analysis (prompts for ticker)
问投资z实时.bat

# Start local dashboard
python scripts/dashboard_server.py
# or: scripts\start_dashboard.bat

# Sync latest CCR reports from GitHub
scripts\pull_reports.bat
# or: git pull origin main

# Fetch real-time stock data
python scripts/get_stock_data.py NVDA MU TSLA

# Run a single agent locally (Windows, Claude CLI required)
powershell -ExecutionPolicy Bypass -File scripts/agent_touziz.ps1

# Send test email
python scripts/send_email.py --subject "Test" --body-file README.md

# Manually fire a CCR trigger (via Claude Code with RemoteTrigger tool)
# trigger IDs listed above
```

## Windows-Specific Notes

`.ps1` scripts contain **no Chinese characters** — folder names are built via UTF-8 byte arrays:
```powershell
$outDir = [System.Text.Encoding]::UTF8.GetString([byte[]](0xE6,0x8A,0x95,0xE8,0xB5,0x84,0x7A))  # 投资z
```
`.bat` files are pure ASCII. `Set-Location` always uses the 8.3 short path: `C:\Users\hrgap\OneDrive\Desktop\2046CC~1`. Never use `python -c '...strftime("%Y-%m-%d")...'` in PowerShell — double quotes are lost; use `Get-Date -Format "yyyy-MM-dd"` instead.

## Key Rules
- All report content in Simplified Chinese
- Reports at `AgentName/YYYY-MM-DD.md` — never subdirectory layout
- `aboutme.json` is committed (repo is private; contains SMTP password and GitHub PAT)
- CCR agents must end with: read PAT from `aboutme.json`, `git remote set-url origin https://${PAT}@github.com/mengzhi0226/2046-secretary.git`, then `git push origin main`
- Dashboard runs on port 8080; `dashboard_server.py` uses stdlib only (no pip dependencies)
