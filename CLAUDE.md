# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal AI secretary system for 孟之 (mengzhi0226@gmail.com, UTC+8/Singapore). One CCR agent runs daily at 07:00 SGT generating a combined morning report (news + market + summary), sent via Gmail SMTP and pushed to GitHub. A local Python dashboard renders reports and enables interactive stock queries. Additional local assistants handle office work and usage analytics.

## Architecture

### Primary Flow (CCR — Production)
```
claude.ai/code/scheduled (23:00 UTC = 07:00 SGT)
  → CCR clones https://github.com/mengzhi0226/2046-secretary
  → WebSearch: 7 news articles (AI/tobacco/factory) + 8 stocks premarket
  → writes 晨报z/YYYY-MM-DD.md
  → python scripts/send_email.py → mengzhi0226@gmail.com
  → git push origin main

Local machine:
  git pull → 晨报z/ synced
  python scripts/dashboard_server.py → http://localhost:8080
```

### CCR Trigger
| Agent | Folder | Trigger ID | Cron (UTC) | SGT |
|---|---|---|---|---|
| 晨报z | `晨报z/` | `trig_012UGD5FJW6i3YC9HeUjXhbt` | `0 23 * * *` | 07:00 |

Disabled: 投资z `trig_018kv9V28MGha4aiSkqHCbky` · 健康z `trig_015MrNfJ185tCgYzARSRW1YF` · 牛马z `trig_0198r98AGTKzJRLxYBrPeWtK`

Edit prompt or run manually: https://claude.ai/code/scheduled

### Data Stores

**`aboutme.json`** — single source of truth.
- `finance.watchlist` — stocks for CCR market snapshot (AAPL MSFT GOOGL AMZN META NVDA TSLA MU)
- `interests.news_topics` — topics for 晨报z news section
- `smtp` — Gmail App Password credentials, used by `send_email.py`
- `github_pat` — placeholder; CCR push uses Anthropic platform auth

**`pnl_log.json`** — daily P&L: `{"entries": [{date, pnl, currency, note}]}`. SGD. Updated via dashboard `/pnl` POST.

### Local Dashboard (`scripts/dashboard_server.py`)
Stdlib-only Python HTTP server, port 8080. Three tabs:

| Tab | Key | Description |
|---|---|---|
| 📋 晨报z | chenbaoz | Renders `晨报z/YYYY-MM-DD.md` |
| 📊 实时行情 | live | AJAX → POST /stock-query → subprocess get_stock_data.py → HTML cards |
| 💰 盈亏 | pnl | Monthly stats, Tiger-style calendar, cumulative chart, P&L input |

Routes: `GET /YYYY-MM-DD`, `POST /stock-query` (JSON response with HTML), `POST /pnl`

### Interactive Butler (`管家.bat` → `scripts/butler.ps1`)
Opens Claude CLI session. On first message: reads `aboutme.json`, gets SGT date, fetches Singapore weather, checks `晨报z/TODAY.md`.
- **Stocks**: ticker → `get_stock_data.py` (price/RSI/MA ground truth) + WebSearch (news/catalysts) → Call/Put recommendations
- **Morning report**: reads `晨报z/TODAY.md` or live WebSearch fallback
- **P&L**: reads/updates `pnl_log.json`

### Office Assistant (`工作z.bat` → `scripts/gongzuoz.ps1`)
Claude CLI with system prompt: PPT structure generation, data analysis (pandas/matplotlib), knowledge base CRUD (`kb/`), nanobanana image prompt → clipboard + open https://nanobananaimg.com

### Usage Analytics (`财务z.bat` → `scripts/analyze_usage.ps1` → `scripts/analyze_usage.py`)
Scans `~/.claude/projects/` JSONL, estimates token/cost (Sonnet: $3/M input, $15/M output), checks Memory health. Writes `财务z/YYYY-MM.md`.

### Stock Data (`scripts/get_stock_data.py`)
Uses `yfinance`. Args: tickers. Outputs: price, Δ%, MA5/MA20, RSI(14), volume ratio, ATM Call/Put IV. Ground-truth price source for butler and dashboard.

### Email (`scripts/send_email.py`)
Credentials: env vars first → `aboutme.json .smtp`. Usage: `python scripts/send_email.py --subject "..." --body-file path.md`

## Common Commands

```bash
管家.bat                          # Daily butler (stocks, news, P&L)
工作z.bat                         # Office assistant
财务z.bat                         # Monthly usage report
问投资z实时.bat                    # Quick single-stock analysis
scripts\start_dashboard.bat       # http://localhost:8080
scripts\pull_reports.bat          # git pull (sync CCR reports)
python scripts/get_stock_data.py MU NVDA TSLA
```

## Windows-Specific Notes

`.ps1` scripts build Chinese folder names via UTF-8 byte arrays (no Chinese chars in .ps1 files).
`.bat` files are pure ASCII. `Set-Location` uses 8.3 short path: `C:\Users\hrgap\OneDrive\Desktop\2046CC~1`.
Use `Get-Date -Format "yyyy-MM-dd"` not `python -c '...strftime...'` in PowerShell.

## Key Rules
- All report content in Simplified Chinese
- Reports: `AgentName/YYYY-MM-DD.md` — never subdirectory layout
- CCR date: `(datetime.datetime.utcnow()+datetime.timedelta(hours=8)).date()` — never `datetime.date.today()`
- CCR agents must git push via PAT remote URL from `aboutme.json`
- `aboutme.json` committed (repo is private)
- Dashboard: stdlib only (no pip deps)
- Stock price ground truth: `get_stock_data.py`; WebSearch for news only
