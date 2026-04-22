Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  财务z — Claude 月度用量分析" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

$month = (Get-Date).ToString("yyyy-MM")
Write-Host "分析月份: $month" -ForegroundColor Yellow
Write-Host ""

python scripts\analyze_usage.py $month

if ($LASTEXITCODE -ne 0) {
    Write-Host "分析失败，请检查 Python 环境" -ForegroundColor Red
    pause
    exit 1
}

$reportPath = "财务z\$month.md"
Write-Host ""
Write-Host "报告路径: $reportPath" -ForegroundColor Green
Write-Host ""

$choice = Read-Host "是否提交报告到 GitHub？(Y/N)"
if ($choice -eq 'Y' -or $choice -eq 'y') {
    git add "财务z/"
    git commit -m "feat: 财务z $month 用量报告"
    git push origin main
    Write-Host "已推送到 GitHub" -ForegroundColor Green
} else {
    Write-Host "已跳过 GitHub 推送" -ForegroundColor Yellow
}

Write-Host ""
pause
