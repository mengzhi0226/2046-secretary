param([string]$Ticker)
Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ticker = $Ticker.Trim().ToUpper()
$now    = (python -c 'import datetime; print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))').Trim()
$today  = (python -c 'import datetime; print(datetime.date.today())').Trim()

$outDir  = [System.Text.Encoding]::UTF8.GetString([byte[]](0xE6,0x8A,0x95,0xE8,0xB5,0x84,0x7A))  # 投资z
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outFile = [System.IO.Path]::Combine($outDir, "realtime_${ticker}_${today}.md")

$promptFile = "temp_rt_${ticker}.txt"

@"
你是投资秘书「投资z」，现在是 $now（北京时间），盘前交易时段。

孟之的交易风格：开盘后30分钟内完成80%操作，目标每日盈利`$500，策略为买入Call Option + 卖出Put Option。

任务：对 $ticker 进行盘前实时深度分析，输出具体期权交易建议。直接开始，不要介绍自己。

步骤：
1. WebSearch '$ticker stock premarket $today' 获取当前盘前价/涨跌幅
2. WebSearch '$ticker news today $today' 找出盘前异动的具体原因
3. WebSearch '$ticker options unusual activity $today' 查看大单期权动态
4. WebSearch 'US market premarket futures VIX $today' 了解大盘背景

输出格式（简体中文）：

---
# 📊 $ticker 盘前实时分析 $now

## 🚀 盘前快照

| 项目 | 数据 |
|------|------|
| 当前盘前价 | `$XXX |
| 盘前涨跌 | +X.X% |
| 昨收价 | `$XXX |
| 异动核心原因 | 一句话 |

## 📰 催化剂详情

（2-3段：什么事件导致了这次走势？板块联动如何？利好/利空持续性判断？）

## 🌍 大盘背景

| 指标 | 数值 | 对 $ticker 影响 |
|------|------|----------------|
| 标普500期货 | `$XXXX (+X%) | 顺风/逆风 |
| 纳斯达克期货 | `$XXXX (+X%) | 顺风/逆风 |
| VIX | XX.X | 低/高波动 |
| 相关板块 | XX板块 | 整体涨/跌X% |

## 🐋 期权大单异动

| 方向 | 行权价 | 到期日 | 成交量 | IV | 解读 |
|------|--------|--------|--------|----|------|
| Call/Put | `$XXX | MM/DD | XXXK | XX% | 机构看涨/看跌 |

（无明显大单则注明「暂无异常机构异动」）

## 🎯 开盘操作建议

> **综合评级：🟢做多 / 🟡观望 / 🔴规避**（请填入实际评级）

### ✅ 操作1 — Buy Call

| 项目 | 详情 |
|------|------|
| **合约** | $ticker `$XXX Call，到期 YYYY-MM-DD |
| **买入价区间** | `$X.XX – `$X.XX（开盘后5-10分钟确认方向后入场） |
| **止盈目标** | `$X.XX（+50%） |
| **止损点** | `$X.XX（-30%） |
| **入场时机** | 开盘后X分钟，确认站稳`$XXX后 |
| **仓位** | 总仓位20%，约`$1000 |

### ✅ 操作2 — Sell Put

| 项目 | 详情 |
|------|------|
| **合约** | $ticker `$XXX Put，到期 YYYY-MM-DD |
| **目标权利金** | `$X.XX |
| **止损线** | 若跌破`$XXX平仓 |
| **预计收益** | `$XXX/张 |
| **仓位** | 总仓位15% |

## ⚠️ 主要风险

- （1-2条关键风险，如盘前数据不延续至开盘、财报不确定性等）

---
*查询时间：$now | 投资z实时*
"@ | Out-File $promptFile -Encoding UTF8

$result = & claude --dangerously-skip-permissions --print (Get-Content $promptFile -Raw -Encoding UTF8)
$result | Out-File -FilePath $outFile -Encoding UTF8
Remove-Item $promptFile -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "  已保存至: $outFile" -ForegroundColor Green
Write-Host ""
Write-Host $result
