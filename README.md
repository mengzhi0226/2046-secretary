# 2046 孟之 AI 秘书团

个人 AI 助理系统：每天 07:00 SGT 自动生成晨报（新闻+市场+总结），本地仪表盘实时查询，多个工具助手随时可用。

---

## 入口

| 入口 | 用途 |
|---|---|
| `管家.bat` | 主交互：股票查询、查看晨报、记录盈亏 |
| `工作z.bat` | 办公助手：PPT生成、数据分析、知识库、图片生成 |
| `财务z.bat` | 月度 Claude 用量分析和成本报告 |
| `问投资z实时.bat` | 快速盘前单股分析（提示输入代码） |
| `scripts\start_dashboard.bat` | 本地仪表盘 http://localhost:8080 |

---

## 晨报z（每日 07:00 SGT 自动生成）

CCR 触发器每天 23:00 UTC 运行，生成 `晨报z/YYYY-MM-DD.md` 并发邮件至 mengzhi0226@gmail.com。

内容：AI/烟草/工厂数字化 7 条新闻 + 8 只股票盘前快照 + 管家总结

触发器管理：https://claude.ai/code/scheduled（ID: `trig_012UGD5FJW6i3YC9HeUjXhbt`）

---

## 本地仪表盘（3 标签）

运行 `scripts\start_dashboard.bat` 启动，访问 http://localhost:8080

| 标签 | 内容 |
|---|---|
| 📋 晨报z | 当日晨报 Markdown 渲染 |
| 📊 实时行情 | 输入股票代码 → 实时价格/RSI/MA/ATM期权 |
| 💰 盈亏 | 月度统计 + 日历视图 + 累计走势图 |

---

## 数据文件

| 文件 | 用途 |
|---|---|
| `aboutme.json` | 个人信息、SMTP、自选股、GitHub PAT |
| `pnl_log.json` | 每日盈亏记录（SGD） |
| `晨报z/` | CCR 生成的每日晨报 |
| `财务z/` | 本地月度 Claude 用量报告 |
| `kb/` | 工作z 知识库 |

---

## 常用操作

```bash
# 同步最新晨报
scripts\pull_reports.bat   # 或 git pull origin main

# 获取实时股票数据
python scripts/get_stock_data.py MU NVDA TSLA

# 月度用量分析
财务z.bat

# 手动触发晨报z（通过 Claude Code RemoteTrigger）
# 见 claude.ai/code/scheduled
```

---

## 修改晨报内容或股票列表

- 股票自选股：编辑 `aboutme.json` → `finance.watchlist`
- 晨报格式/新闻主题：在 [claude.ai/code/scheduled](https://claude.ai/code/scheduled) 编辑触发器 Prompt
- 邮件收件人/SMTP：编辑 `aboutme.json` → `smtp`

---

## 架构

```
CCR (23:00 UTC daily)
  → clone github.com/mengzhi0226/2046-secretary
  → WebSearch 新闻+市场数据
  → 写入 晨报z/YYYY-MM-DD.md
  → send_email.py → mengzhi0226@gmail.com
  → git push origin main

本地:
  git pull → 晨报z/ 更新
  dashboard_server.py → http://localhost:8080
    POST /stock-query → get_stock_data.py (yfinance)
    POST /pnl → pnl_log.json
```
