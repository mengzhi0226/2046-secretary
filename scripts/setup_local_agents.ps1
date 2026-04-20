# ============================================================
# 2046 秘书团队 - 本地 Agent 一键安装脚本
# 以管理员身份运行：右键 → 以管理员身份运行 PowerShell
# ============================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$GmailAppPassword
)

$cwd = "c:\Users\hrgap\OneDrive\Desktop\2046孟之CC"

# 1. 将 Gmail App Password 写入系统环境变量（永久生效）
[System.Environment]::SetEnvironmentVariable("SMTP_PASS", $GmailAppPassword, "User")
[System.Environment]::SetEnvironmentVariable("SMTP_USER", "mengzhi0226@gmail.com", "User")
[System.Environment]::SetEnvironmentVariable("SMTP_HOST", "smtp.gmail.com", "User")
[System.Environment]::SetEnvironmentVariable("SMTP_PORT", "587", "User")
[System.Environment]::SetEnvironmentVariable("EMAIL_TO",  "mengzhi0226@gmail.com", "User")
Write-Host "✅ Gmail 环境变量已设置"

# 2. 创建 logs 目录
New-Item -ItemType Directory -Force -Path "$cwd\logs" | Out-Null

# 3. 注册 4 个计划任务
$tasks = @(
    @{ Name="Secretary-XinwenZ";  Hour=7;  Minute=0;  Agent="xinwenz"  },
    @{ Name="Secretary-TouziZ";   Hour=7;  Minute=30; Agent="touziz"   },
    @{ Name="Secretary-JiankangZ";Hour=8;  Minute=0;  Agent="jiankangz"},
    @{ Name="Secretary-NiumaZ";   Hour=8;  Minute=30; Agent="niumaz"   }
)

foreach ($t in $tasks) {
    $scriptFile = "$cwd\scripts\agent_$($t.Agent).bat"
    $action   = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptFile`" >> `"$cwd\logs\$($t.Agent).log`" 2>&1"
    $trigger  = New-ScheduledTaskTrigger -Daily -At "$($t.Hour):$($t.Minute.ToString('D2'))"
    $settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable
    Unregister-ScheduledTask -TaskName $t.Name -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $t.Name -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null
    Write-Host "✅ 已注册：$($t.Name)  每天 $($t.Hour):$($t.Minute.ToString('D2')) SGT"
}

Write-Host ""
Write-Host "🎉 安装完成！明天早上 7:00 起秘书团队将自动运行。"
Write-Host "   日志位置：$cwd\logs\"
