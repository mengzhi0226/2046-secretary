# 以管理员身份运行此脚本，注册每天 09:00 自动 git pull 的计划任务
# 用法：右键 → 以管理员身份运行 PowerShell，然后执行此脚本

$taskName   = "2046Secretary-DailyPull"
$scriptPath = "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC\scripts\pull_reports.bat"
$logDir     = "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC\logs"

# 创建 logs 目录
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir }

# 删除同名旧任务（如存在）
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

# 创建新任务：每天 09:00 运行
$action  = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At "09:00"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action   $action   `
    -Trigger  $trigger  `
    -Settings $settings `
    -RunLevel Highest   `
    -Force

Write-Host "✅ 任务已注册：每天 09:00 自动 git pull 到本地文件夹"
Write-Host "   查看任务：任务计划程序 → 任务计划程序库 → $taskName"
