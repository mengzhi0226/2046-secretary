# Investment agent (touziz)
Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$today = (python -c 'import datetime; print(datetime.date.today())').Trim()
$outDir = [System.IO.Path]::Combine((Get-Location), [System.Text.Encoding]::UTF8.GetString([byte[]](0xE6,0x8A,0x95,0xE8,0xB5,0x84,0x7A)))
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outFile = [System.IO.Path]::Combine($outDir, "$today.md")

Write-Host "[$today] touziz: fetching stock data..."
python scripts/get_stock_data.py AAPL MSFT GOOGL AMZN META NVDA TSLA MU 2>&1 | Out-File temp_stock_data.txt -Encoding UTF8

$stockData = Get-Content temp_stock_data.txt -Raw -Encoding UTF8

$promptFile = "temp_prompt_touzi.txt"
$promptLines = @(
  "Output a stock investment analysis report in Simplified Chinese, Markdown format only.",
  "Today: $today. Watchlist: AAPL MSFT GOOGL AMZN META NVDA TSLA MU",
  "Real-time stock data:",
  $stockData,
  "Search 'US stock market news today' for macro context.",
  "Format:",
  "# Investment Report $today",
  "## Macro Environment",
  "## Individual Stocks (price, RSI, MA, options Call/Put with strike+expiry, risk note)",
  "## Today Focus",
  "---",
  "*Disclaimer: for reference only, not investment advice.*"
)
$promptLines -join "`n" | Out-File $promptFile -Encoding UTF8

Write-Host "[$today] touziz: generating report..."
$prompt = Get-Content $promptFile -Raw -Encoding UTF8
$report = & claude --dangerously-skip-permissions --print $prompt
$report | Out-File -FilePath $outFile -Encoding UTF8

Remove-Item $promptFile -ErrorAction SilentlyContinue
Remove-Item temp_stock_data.txt -ErrorAction SilentlyContinue
Write-Host "[$today] touziz: done -> $outFile"
