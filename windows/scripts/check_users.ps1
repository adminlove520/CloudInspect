# CloudInspect - Windows 用户和组检测

Write-Host "CloudInspect - Windows 用户检测" -ForegroundColor Cyan
Write-Host "=" * 50

# 获取本地用户
Write-Host "`n[本地用户]" -ForegroundColor Green
try {
    $users = Get-LocalUser

    $enabled = ($users | Where-Object { $_.Enabled }).Count
    $disabled = ($users | Where-Object { -not $_.Enabled }).Count

    Write-Host "  总数: $($users.Count) | 启用: $enabled | 禁用: $disabled"

    Write-Host "`n  用户列表:" -ForegroundColor Yellow
    foreach ($user in $users) {
        $status = if ($user.Enabled) { "[启用]" } else { "[禁用]" }
        $color = if ($user.Enabled) { "Green" } else { "Red" }

        Write-Host "    $status $($user.Name) " -NoNewline -ForegroundColor $color

        if ($user.LastLogon) {
            Write-Host "- 上次登录: $($user.LastLogon.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
        } else {
            Write-Host "- 从未登录" -ForegroundColor Gray
        }
    }
} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
}

# 获取管理员组成员
Write-Host "`n[管理员组成员]" -ForegroundColor Green
try {
    $admins = Get-LocalGroupMember -Group "Administrators"

    Write-Host "  管理员数量: $($admins.Count)"

    foreach ($admin in $admins) {
        $type = $admin.ObjectClass
        $source = $admin.PrincipalSource

        Write-Host "  - $($admin.Name) [$type, $source]" -ForegroundColor White
    }
} catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
}

# 检查可疑用户
Write-Host "`n[可疑用户检查]" -ForegroundColor Green
$suspiciousPatterns = @("test", "admin2", "backup", "hacker", "guest")

foreach ($user in $users) {
    $nameLower = $user.Name.ToLower()

    foreach ($pattern in $suspiciousPatterns) {
        if ($nameLower -like "*$pattern*") {
            Write-Host "  [!] 发现可疑用户: $($user.Name)" -ForegroundColor Yellow
            break
        }
    }
}

# Guest 用户状态
Write-Host "`n[Guest 用户状态]" -ForegroundColor Green
$guest = Get-LocalUser -Name "Guest" -ErrorAction SilentlyContinue

if ($guest) {
    if ($guest.Enabled) {
        Write-Host "  [!] Guest 用户已启用 - 建议禁用" -ForegroundColor Yellow
    } else {
        Write-Host "  [OK] Guest 用户已禁用" -ForegroundColor Green
    }
} else {
    Write-Host "  [OK] Guest 用户不存在" -ForegroundColor Green
}

Write-Host "`n" + "=" * 50