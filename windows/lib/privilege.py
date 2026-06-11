# coding: utf-8
"""
Windows 权限检测模块
"""

import subprocess


class PrivilegeModule:
    def run(self, os_detect, config):
        issues = []

        # 检查当前用户权限
        current_privileges = self.get_current_privileges()

        # 检查 SeDebugPrivilege
        debug_enabled = self.check_debug_privilege()
        if debug_enabled:
            issues.append({
                "level": "info",
                "module": "privilege",
                "desc": "SeDebugPrivilege 已启用"
            })

        # 检查可还原密码
        reversible_encryption = self.check_reversible_encryption()
        if reversible_encryption:
            issues.append({
                "level": "warning",
                "module": "privilege",
                "desc": "可逆密码加密已启用"
            })

        return {
            "status": "ok" if not issues else "warning",
            "current_user": current_privileges.get('user', 'Unknown'),
            "is_admin": current_privileges.get('is_admin', False),
            "debug_enabled": debug_enabled,
            "issues": issues
        }

    def get_current_privileges(self):
        """获取当前用户权限"""
        info = {}

        try:
            # 获取当前用户
            result = subprocess.run(
                ['powershell', '-Command',
                 '[System.Security.Principal.WindowsIdentity]::GetCurrent().Name'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                info['user'] = result.stdout.strip()

            # 检查是否是管理员
            result = subprocess.run(
                ['powershell', '-Command',
                 '([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                info['is_admin'] = "True" in result.stdout

        except Exception:
            pass

        return info

    def check_debug_privilege(self):
        """检查 SeDebugPrivilege 是否启用"""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'whoami /priv | Select-String SeDebugPrivilege'],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0 and "Enabled" in result.stdout

        except Exception:
            return False

    def check_reversible_encryption(self):
        """检查是否启用了可逆密码加密"""
        try:
            ps_script = """
            Get-ADUser -Filter * -Properties "userAccountControl" |
            Where-Object { $_.userAccountControl -band 128 } |
            Select-Object -First 1 Name |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )
            # 如果有输出表示有用户启用了可逆加密
            return result.returncode == 0 and result.stdout.strip()

        except Exception:
            pass

        return False