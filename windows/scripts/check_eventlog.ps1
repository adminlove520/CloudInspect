# CloudInspect Windows - PowerShell 辅助脚本
# 用于深度系统检测

# 获取事件日志
param(
    [string]$LogName = "Security",
    [int]$Hours = 24,
    [int]$MaxEvents = 50
)

$startTime = (Get-Date).AddHours(-$Hours)

Write-Host "CloudInspect - Windows 事件日志分析" -ForegroundColor Cyan
Write-Host "=" * 50

try {
    $events = Get-WinEvent -FilterHashtable @{
        LogName = $LogName
        StartTime = $startTime
    } -MaxEvents $MaxEvents -ErrorAction Stop

    Write-Host "`n[$LogName] 最近 $Hours 小时事件: $($events.Count) 条" -ForegroundColor Green

    foreach ($event in $events) {
        $level = switch ($event.Level) {
            1 {"Critical"}
            2 {"Error"}
            3 {"Warning"}
            4 {"Info"}
            default {"Info"}
        }

        Write-Host "[$($event.TimeCreated.ToString('yyyy-MM-dd HH:mm:ss'))] " -NoNewline
        Write-Host "[$level] " -NoNewline -ForegroundColor (
            if ($level -eq "Error") { "Red" }
            elseif ($level -eq "Warning") { "Yellow" }
            else { "White" }
        )
        Write-Host "ID: $($event.Id) - $($event.ProviderName)" -ForegroundColor Gray
    }

} catch {
    Write-Host "[ERROR] 无法获取事件日志: $_" -ForegroundColor Red
}

Write-Host "`n" + "=" * 50