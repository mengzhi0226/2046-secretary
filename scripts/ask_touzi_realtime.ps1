param([string]$Ticker)
Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ticker = $Ticker.Trim().ToUpper()
$now    = Get-Date -Format "yyyy-MM-dd HH:mm"
$today  = Get-Date -Format "yyyy-MM-dd"

$outDir  = [System.Text.Encoding]::UTF8.GetString([byte[]](0xE6,0x8A,0x95,0xE8,0xB5,0x84,0x7A))  # 投资z
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outFile = [System.IO.Path]::Combine($outDir, "realtime_${ticker}_${today}.md")

# ── Step 1: Get REAL price data from yfinance (accurate, not web-scraped) ──
Write-Host "  Fetching live yfinance data for $ticker..." -ForegroundColor Cyan
$stockData = (python scripts/get_stock_data.py $ticker 2>&1) -join "`n"
Write-Host "  Done. Building analysis prompt..." -ForegroundColor Cyan

$promptFile = "temp_rt_${ticker}.txt"

@"
你是投资秘书「投资z」，现在是 $now（北京时间），盘前交易时段。

孟之的交易风格：开盘后30分钟内完成80%操作，目标每日盈利$500，策略为买入Call Option + 卖出Put Option。

任务：对 $ticker 进行盘前深度分析，输出具体期权交易建议。直接开始，不要介绍自己。

══════════════════════════════════════
【已确认的真实市场数据 — 来自yfinance，请直接使用，不要自行搜索价格】
$stockData
══════════════════════════════════════

使用以上真实数据作为价格基准，然后用 WebSearch 补充：
1. WebSearch '$ticker news premarket $today' — 找出盘前异动的具体新闻原因
2. WebSearch '$ticker options unusual activity $today' — 查看大单期权动态
3. WebSearch 'S&P500 futures VIX premarket $today' — 了解大盘背景

输出格式（简体中文）：

---
# 📊 $ticker 盘前实时分析 $now

## 🚀 盘前快照（数据来自yfinance实时）

| 项目 | 数据 |
|------|------|
| 当前价格 | 从上方yfinance数据取 |
| 涨跌幅 | 从上方yfinance数据取 |
| MA5 / MA20 | 从上方yfinance数据取 |
| RSI(14) | 从上方yfinance数据取 |
| ATM Call IV | 从上方yfinance期权数据取 |
| ATM Put IV | 从上方yfinance期权数据取 |
| 异动核心原因 | 来自WebSearch新闻 |

## 📰 催化剂详情

（基于WebSearch结果：2-3段，具体说明什么事件驱动了今日走势？持续性如何？）

## 🌍 大盘背景

| 指标 | 数值 | 对 $ticker 影响 |
|------|------|----------------|
| 标普500期货 | WebSearch结果 | 顺风/逆风 |
| 纳斯达克期货 | WebSearch结果 | 顺风/逆风 |
| VIX | WebSearch结果 | 低/高波动 |

## 🐋 期权大单异动

| 方向 | 行权价 | 到期日 | 成交量 | IV | 解读 |
|------|--------|--------|--------|----|------|
（来自WebSearch期权异动数据，无则注明「暂无异常」）

## 🎯 开盘操作建议

> **综合评级：🟢做多 / 🟡观望 / 🔴规避**

基于真实RSI、MA趋势和IV数据，给出具体建议：

### ✅ 操作1 — Buy Call（如评级🟢）

| 项目 | 详情 |
|------|------|
| **合约** | $ticker 具体行权价 Call，到期 具体日期 |
| **行权价选择依据** | 基于yfinance ATM Call数据 |
| **买入价区间** | 基于当前IV计算的合理区间 |
| **止盈目标** | +50% |
| **止损点** | -30% |
| **入场时机** | 开盘后X分钟，确认站稳关键位后 |
| **仓位建议** | 总仓位的X%（基于当前IV风险） |

### ✅ 操作2 — Sell Put（如支撑位明确）

| 项目 | 详情 |
|------|------|
| **合约** | $ticker 具体行权价 Put，到期 具体日期 |
| **选择依据** | 基于MA20支撑位和Put IV水平 |
| **目标权利金** | 基于当前ATM Put IV估算 |
| **最大风险** | 跌破MA20则平仓 |
| **预计收益** | 每张合约预计$XXX |

## ⚠️ 主要风险

（基于RSI超买/超卖、IV水平、近期走势给出1-2条关键风险）

---
*数据来源：yfinance实时 + WebSearch新闻 | 查询时间：$now | 投资z*
"@ | Out-File $promptFile -Encoding UTF8

$result = & claude --dangerously-skip-permissions --print (Get-Content $promptFile -Raw -Encoding UTF8)
$result | Out-File -FilePath $outFile -Encoding UTF8
Remove-Item $promptFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  Saved: $outFile" -ForegroundColor Green
Write-Host ""
Write-Host $result
