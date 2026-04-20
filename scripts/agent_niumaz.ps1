# Todo agent (niumaz)
Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$today    = (python -c 'import datetime; print(datetime.date.today())').Trim()
$yesterday= (python -c 'import datetime; d=datetime.date.today()-datetime.timedelta(days=1); print(d)').Trim()
# folder name bytes for the Chinese todo folder
$outDir = [System.IO.Path]::Combine((Get-Location), [System.Text.Encoding]::UTF8.GetString([byte[]](0xE7,0x89,0x9B,0xE9,0xA9,0xAC,0x7A)))
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outFile = [System.IO.Path]::Combine($outDir, "$today.md")

Write-Host "[$today] niumaz: collecting tasks..."

# Read yesterday unchecked tasks
$carryover = ""
$yesterdayFile = [System.IO.Path]::Combine($outDir, "$yesterday.md")
if (Test-Path $yesterdayFile) {
    $lines = Get-Content $yesterdayFile -Encoding UTF8
    $unchecked = $lines | Where-Object { $_ -match "^- \[ \]" -and $_ -notmatch "~~" }
    if ($unchecked) { $carryover = ($unchecked -join "`n") }
}

# Read new tasks
$newTasks = ""
if (Test-Path "new_tasks.txt") {
    $newTasks = Get-Content "new_tasks.txt" -Raw -Encoding UTF8
    Remove-Item "new_tasks.txt"
}

$promptFile = "temp_prompt_niuma.txt"
$promptLines = @(
  "Output a task list in Simplified Chinese, Markdown format only.",
  "Date: $today",
  "New tasks (format: name|priority): $newTasks",
  "Carryover from yesterday: $carryover",
  "Classify all tasks using Eisenhower Matrix.",
  "Output format:",
  "# Task List $today",
  "## First Quadrant - Urgent+Important",
  "- [ ] task",
  "## Second Quadrant - Important not Urgent",
  "- [ ] task",
  "## Third Quadrant - Urgent not Important",
  "- [ ] task",
  "## Fourth Quadrant - Low Priority",
  "- [ ] task",
  "## Yesterday Carryover",
  $carryover,
  "---",
  "Generated: $today"
)
$promptLines -join "`n" | Out-File $promptFile -Encoding UTF8

Write-Host "[$today] niumaz: generating task list..."
$prompt = Get-Content $promptFile -Raw -Encoding UTF8
$report = & claude --dangerously-skip-permissions --print $prompt
$report | Out-File -FilePath $outFile -Encoding UTF8

Remove-Item $promptFile -ErrorAction SilentlyContinue
Write-Host "[$today] niumaz: done -> $outFile"
