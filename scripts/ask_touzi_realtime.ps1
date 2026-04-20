# Real-time single-stock options analysis for 孟之
Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ticker = $args[0]
if (-not $ticker) {
    Write-Host ""
    Write-Host "  ======================================" -ForegroundColor Cyan
    Write-Host "   投资z 实时盘前查询" -ForegroundColor Cyan
    Write-Host "  ======================================" -ForegroundColor Cyan
    Write-Host ""
    $ticker = Read-Host "  请输入股票代码 (如 NVDA, TSLA, AAPL)"
    $ticker = $ticker.Trim().ToUpper()
}

if (-not $ticker) {
    Write-Host "未输入代码，退出。" -ForegroundColor Red
    exit
}

$now = (python -c 'import datetime; print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))').Trim()
$today = (python -c 'import datetime; print(datetime.date.today())').Trim()

Write-Host ""
Write-Host "  正在查询 $ticker 盘前实时数据，请稍候（约30-60秒）..." -ForegroundColor Yellow
Write-Host ""

$outDir = "投资z"
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$outFile = "$outDir\realtime_${ticker}_${today}.md"

$prompt = @"
你是投资秘书「投资z」，现在是 $now（北京时间），盘前交易时段。

孟之的交易风格：开盘后30分钟内完成80%操作，目标每日盈利\$500，策略为买入Call Option + 卖出Put Option。

任务：对 $ticker 进行盘前实时深度分析，输出完整期权交易建议。直接开始，不要介绍自己。

请按以下步骤执行：

1. WebSearch 搜索 '$ticker stock premarket $today' — 获取当前盘前价格、涨跌幅
2. WebSearch 搜索 '$ticker news today $today' — 找出盘前异动的具体原因（新闻/财报/行业事件/宏观）
3. WebSearch 搜索 '$ticker options unusual activity $today' — 查看大单期权动态
4. WebSearch 搜索 'US market premarket futures VIX $today' — 了解大盘背景

然后输出以下格式的分析报告（全部简体中文）：

---
# 📊 $ticker 盘前实时分析 $now

## 🚀 盘前异动速览

| 项目 | 数据 |
|------|------|
| 当前盘前价 | \$XXX |
| 盘前涨跌 | +X.X% |
| 昨收价 | \$XXX |
| 异动原因 | 一句话核心原因 |

## 📰 催化剂详情

（2-3段，解释清楚：是什么消息/事件导致了这次盘前走势？板块联动情况如何？这个信息是利好还是利空，持续性如何？）

## 🌍 大盘背景

| 指标 | 数值 | 对 $ticker 影响 |
|------|------|----------------|
| 标普500期货 | \$XXXX (+X%) | 顺风/逆风 |
| VIX | XX.X | 低/高波动 |
| 相关板块 | XX板块 | 整体涨/跌X% |

## 🐋 期权异动信号

| 方向 | 行权价 | 到期日 | 成交量 | IV | 机构解读 |
|------|--------|--------|--------|----|----------|
| Call/Put | \$XXX | MM/DD | XXXK | XX% | 看涨/看跌信号 |

（如无异常大单，注明「暂无明显机构异动」）

## 🎯 开盘操作建议

> **基于当前盘前情况，综合评级：🟢做多 / 🟡观望 / 🔴规避**

### ✅ 操作1 — Buy Call（如评级🟢）

| 项目 | 详情 |
|------|------|
| **期权合约** | \$XXX Call，到期 YYYY-MM-DD |
| **建议买入价** | \$X.XX – \$X.XX（开盘后确认方向再入场） |
| **目标卖出价** | \$X.XX（+50%止盈） |
| **止损价** | \$X.XX（-30%止损） |
| **入场时机** | 开盘后X分钟，确认站稳\$XXX后 |
| **仓位** | 总仓位20%，约\$1000 |
| **预计盈亏比** | 1:1.7 |

### ✅ 操作2 — Sell Put（如支撑位明确）

| 项目 | 详情 |
|------|------|
| **期权合约** | \$XXX Put，到期 YYYY-MM-DD |
| **卖出权利金目标** | \$X.XX |
| **最大风险点** | 若跌破\$XXX平仓 |
| **预计收益** | \$XXX/张 |
| **仓位** | 总仓位15% |

## ⚠️ 关键风险

- （1-2条最需要警惕的风险点，如"盘前数据未必持续到开盘"、"财报不确定性"等）

---
*查询时间：$now | 投资z实时查询*
"@

$promptFile = "temp_prompt_realtime.txt"
$prompt | Out-File $promptFile -Encoding UTF8

$result = & claude --dangerously-skip-permissions --print (Get-Content $promptFile -Raw -Encoding UTF8)
$result | Out-File -FilePath $outFile -Encoding UTF8

Remove-Item $promptFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  ====== 分析完成 ======" -ForegroundColor Green
Write-Host "  已保存至: $outFile" -ForegroundColor Green
Write-Host ""
$result
Write-Host ""
Write-Host "  按任意键关闭..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
