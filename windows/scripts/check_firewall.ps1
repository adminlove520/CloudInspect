# CloudInspect - Windows 防火墙状态检测

Write-Host "CloudInspect - Windows 防火墙状态" -ForegroundColor Cyan
Write-Host "=" * 50

# 获取防火墙配置文件
Write-Host "`n[防火墙配置文件]" -ForegroundColor Green
try {
    $profiles = Get-NetFirewallProfile

    foreach ($profile in $profiles) {
        $status = if ($profile.Enabled) { "启用" } else { "禁用" }
        $color = if ($profile.Enabled) { "Green" } else { "Red" }

        Write-Host "  $($profile.Name): " -NoNewline
        Write-Host $status -ForegroundColor $color

        if ($profile.DefaultInboundAction -eq "NotConfigured") {
            Write-Host "    入站默认: 未配置 (允许)" -ForegroundColor Yellow
        }

        if ($profile.DefaultOutboundAction -eq "NotConfigured") {
            Write-Host "    出站默认: 未配置 (允许)" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
}

# 获取启用的规则数量
Write-Host "`n[防火墙规则统计]" -ForegroundColor Green
try {
    $enabledRules = (Get-NetFirewallRule -Enabled True | Measure-Object).Count
    $disabledRules = (Get-NetFirewallRule -Enabled False | Measure-Object).Count

    Write-Host "  启用规则: $enabledRules"
    Write-Host "  禁用规则: $disabledRules"
} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
}

# 获取重要的入站规则
Write-Host "`n[重要入站规则 (Top 10)]" -ForegroundColor Green
try {
    $rules = Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True |
        Sort-Object -Property Name |
        Select-Object -First 10

    foreach ($rule in $rules) {
        $portFilter = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule -ErrorAction SilentlyContinue

        if ($portFilter) {
            $protocol = $portFilter.Protocol
            $localPort = $portFilter.LocalPort

            Write-Host "  $($rule.DisplayName)" -ForegroundColor White
            Write-Host "    协议: $protocol, 端口: $localPort" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
}

Write-Host "`n" + "=" * 50