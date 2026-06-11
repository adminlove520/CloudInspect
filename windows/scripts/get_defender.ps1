# CloudInspect - Windows Defender 状态检测

Write-Host "CloudInspect - Windows Defender 状态" -ForegroundColor Cyan
Write-Host "=" * 50

# 获取 Defender 状态
Write-Host "`n[Windows Defender]" -ForegroundColor Green
try {
    $status = Get-MpComputerStatus

    # 防病毒启用状态
    if ($status.AntivirusEnabled) {
        Write-Host "  [OK] 防病毒已启用" -ForegroundColor Green
    } else {
        Write-Host "  [!] 防病毒未启用" -ForegroundColor Red
    }

    # 实时保护
    if ($status.RealTimeProtectionEnabled) {
        Write-Host "  [OK] 实时保护已启用" -ForegroundColor Green
    } else {
        Write-Host "  [!] 实时保护已关闭" -ForegroundColor Yellow
    }

    # 行为监控
    if ($status.BehaviorMonitorEnabled) {
        Write-Host "  [OK] 行为监控已启用" -ForegroundColor Green
    } else {
        Write-Host "  [!] 行为监控已关闭" -ForegroundColor Yellow
    }

    # 签名信息
    Write-Host "`n[病毒定义]" -ForegroundColor Green
    Write-Host "  版本: $($status.AntivirusSignatureVersion)"
    Write-Host "  年龄: $($status.AntivirusSignatureAge) 天"

    if ($status.AntivirusSignatureAge -gt 7) {
        Write-Host "  [!] 病毒定义已超过 7 天未更新" -ForegroundColor Yellow
    } elseif ($status.AntivirusSignatureAge -gt 14) {
        Write-Host "  [!] 病毒定义已超过 14 天未更新" -ForegroundColor Red
    }

    # 最后扫描时间
    if ($status.FullScanEndTime -and $status.FullScanEndTime -ne [DateTime]::MinValue) {
        Write-Host "  上次完整扫描: $($status.FullScanEndTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    } else {
        Write-Host "  上次完整扫描: 从未" -ForegroundColor Yellow
    }

    # 最后快速扫描
    if ($status.QuickScanEndTime -and $status.QuickScanEndTime -ne [DateTime]::MinValue) {
        Write-Host "  上次快速扫描: $($status.QuickScanEndTime.ToString('yyyy-MM-dd HH:mm:ss'))"
    }

} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
    Write-Host "  提示: 确保以管理员身份运行此脚本" -ForegroundColor Gray
}

# 检查第三方防病毒
Write-Host "`n[第三方防病毒]" -ForegroundColor Green
try {
    $antivirusProducts = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction SilentlyContinue

    if ($antivirusProducts) {
        foreach ($product in $antivirusProducts) {
            $status = switch ($product.productState) {
                { ($_ -band 0x4000) -eq 0x4000 } { "启用" }
                default { "禁用或过期" }
            }

            Write-Host "  $($product.displayName): $status" -ForegroundColor White

            # 检查签名日期
            if ($product.productState) {
                Write-Host "    状态代码: $($product.productState)" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  [!] 未检测到防病毒软件" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [INFO] 无法获取第三方防病毒信息" -ForegroundColor Gray
}

Write-Host "`n" + "=" * 50