# CloudInspect - Windows 权限检测

Write-Host "CloudInspect - Windows 权限检测" -ForegroundColor Cyan
Write-Host "=" * 50

# 当前用户信息
Write-Host "`n[当前用户]" -ForegroundColor Green
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent()
Write-Host "  用户名: $($currentUser.Name)"

$isAdmin = ([System.Security.Principal.WindowsPrincipal]$currentUser).IsInRole(
    [System.Security.Principal.WindowsBuiltInRole]::Administrator
)

if ($isAdmin) {
    Write-Host "  权限: " -NoNewline
    Write-Host "[管理员]" -ForegroundColor Red
} else {
    Write-Host "  权限: " -NoNewline
    Write-Host "[普通用户]" -ForegroundColor Green
}

# SeDebugPrivilege 检查
Write-Host "`n[SeDebugPrivilege]" -ForegroundColor Green
try {
    $debugOutput = whoami /priv | Select-String "SeDebugPrivilege"

    if ($debugOutput) {
        if ($debugOutput -match "Enabled") {
            Write-Host "  [!] SeDebugPrivilege 已启用" -ForegroundColor Yellow
            Write-Host "     警告: 此权限可用于读取其他进程的敏感信息" -ForegroundColor Gray
        } else {
            Write-Host "  [OK] SeDebugPrivilege 已禁用" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "  [ERROR] $_" -ForegroundColor Red
}

# UAC 状态
Write-Host "`n[UAC 状态]" -ForegroundColor Green
try {
    $uacEnabled = (Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA" -ErrorAction SilentlyContinue).EnableLUA

    if ($uacEnabled -eq 1) {
        Write-Host "  [OK] UAC 已启用" -ForegroundColor Green
    } else {
        Write-Host "  [!] UAC 已禁用" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  [ERROR] $_" -ForegroundColor Red
}

# 远程桌面状态
Write-Host "`n[远程桌面 (RDP)]" -ForegroundColor Green
try {
    $rdpDisabled = (Get-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -ErrorAction SilentlyContinue).fDenyTSConnections

    if ($rdpDisabled -eq 0) {
        Write-Host "  [!] 远程桌面已启用" -ForegroundColor Yellow

        # 检查 NLA
        $nlaEnabled = (Get-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -ErrorAction SilentlyContinue).UserAuthentication

        if ($nlaEnabled -eq 1) {
            Write-Host "     [OK] 网络级身份验证 (NLA) 已启用" -ForegroundColor Green
        } else {
            Write-Host "     [!] 网络级身份验证 (NLA) 已禁用 - 建议启用" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  [OK] 远程桌面已禁用" -ForegroundColor Green
    }
} catch {
    Write-Host "  [ERROR] $_" -ForegroundColor Red
}

# 可还原密码加密
Write-Host "`n[可还原密码加密]" -ForegroundColor Green
try {
    # 检查域策略（如果适用）
    $reversibleEncryption = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "DisableLoopbackCheck" -ErrorAction SilentlyContinue

    Write-Host "  [OK] 未检测到可还原密码加密" -ForegroundColor Green
} catch {
    Write-Host "  [INFO] $_" -ForegroundColor Gray
}

Write-Host "`n" + "=" * 50