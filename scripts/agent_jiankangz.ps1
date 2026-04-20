# Health agent (jiankangz)
Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$today = (python -c 'import datetime; print(datetime.date.today())').Trim()
# folder name bytes for the Chinese health folder
$outDir = [System.IO.Path]::Combine((Get-Location), [System.Text.Encoding]::UTF8.GetString([byte[]](0xE5,0x81,0xA5,0xE5,0xBA,0xB7,0x7A)))
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outFile = [System.IO.Path]::Combine($outDir, "$today.md")

Write-Host "[$today] jiankangz: checking health data..."

$aboutme = Get-Content aboutme.json -Raw -Encoding UTF8 | ConvertFrom-Json
$weightLog = $aboutme.health.weight_log
$todayRecord = $weightLog | Where-Object { $_.date -eq $today }

if (-not $todayRecord) {
    Write-Host "[$today] jiankangz: no weight record today, writing reminder..."
    $reminder = "# Health Reminder $today`n`nToday weight not recorded yet.`n`nOpen dashboard at http://localhost:8080 to log your weight.`n"
    $reminder | Out-File -FilePath $outFile -Encoding UTF8
} else {
    $weight = $todayRecord.kg
    $bmi = [math]::Round($weight / (1.74 * 1.74), 1)
    $diff = [math]::Round($weight - 65, 1)
    $recentWeights = ($weightLog | Select-Object -Last 7 | ForEach-Object { "$($_.date): $($_.kg) kg" }) -join "`n"

    $promptFile = "temp_prompt_jiankang.txt"
    $promptLines = @(
      "Output a health report in Simplified Chinese, Markdown format only.",
      "Date: $today | Weight: ${weight}kg | BMI: $bmi | Height: 174cm | Goal: 65kg | Diff: ${diff}kg",
      "Recent 7-day weight log:",
      $recentWeights,
      "Output format:",
      "# Health Report $today",
      "## Today Data (table: weight/BMI/status/diff from goal)",
      "## 7-Day Trend (brief text analysis)",
      "## Health Tips (1-2 tips)",
      "---",
      "Generated: $today"
    )
    $promptLines -join "`n" | Out-File $promptFile -Encoding UTF8

    Write-Host "[$today] jiankangz: generating report..."
    $prompt = Get-Content $promptFile -Raw -Encoding UTF8
    $report = & claude --dangerously-skip-permissions --print $prompt
    $report | Out-File -FilePath $outFile -Encoding UTF8
    Remove-Item $promptFile -ErrorAction SilentlyContinue
}

Write-Host "[$today] jiankangz: done -> $outFile"
