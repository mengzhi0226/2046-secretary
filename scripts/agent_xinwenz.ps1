# News agent (xinwenz)
Set-Location "C:\Users\hrgap\OneDrive\Desktop\2046CC~1"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$today = (python -c 'import datetime; print(datetime.date.today())').Trim()
$outDir = [System.IO.Path]::Combine((Get-Location), [System.Text.Encoding]::UTF8.GetString([byte[]](0xE6,0x96,0xB0,0xE9,0x97,0xBB,0x7A)))
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
$outFile = [System.IO.Path]::Combine($outDir, "$today.md")

Write-Host "[$today] xinwenz: generating news brief..."
$promptFile = "temp_prompt_xinwen.txt"
$promptLines = @(
  "TASK: Generate a daily news brief. Output ONLY the markdown report below. Do NOT introduce yourself. Do NOT ask questions. Start immediately with the markdown content.",
  "",
  "Use WebSearch to find:",
  "- Search 'AI technology news $today' -> pick best 3 articles",
  "- Search 'tobacco industry news $today' -> pick best 2 articles",
  "- Search 'factory automation smart manufacturing news $today' -> pick best 2 articles",
  "",
  "For each article include: headline, 2-3 sentence summary, source name, and article URL.",
  "If you find an image URL for the article, include it as: ![img](URL)",
  "",
  "OUTPUT FORMAT (start immediately with # header, no preamble):",
  "# Daily Brief $today",
  "",
  "## AI Technology",
  "### [Headline](article_url)",
  "![img](image_url_if_available)",
  "Summary text here.",
  "Source: Name",
  "",
  "## Tobacco Industry",
  "(same format)",
  "",
  "## Factory Digitalization",
  "(same format)",
  "",
  "---",
  "Generated $today"
)
$promptLines -join "`n" | Out-File $promptFile -Encoding UTF8

$prompt = Get-Content $promptFile -Raw -Encoding UTF8
$report = & claude --dangerously-skip-permissions --print $prompt
$report | Out-File -FilePath $outFile -Encoding UTF8

Remove-Item $promptFile -ErrorAction SilentlyContinue
Write-Host "[$today] xinwenz: done -> $outFile"
