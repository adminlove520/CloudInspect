# coding: utf-8
"""
Windows 用户和组检测模块
"""

import subprocess
import os


class UserModule:
    def run(self, os_detect, config):
        issues = []

        # 获取用户列表
        users = self.get_local_users()

        # 获取管理员组成员
        admins = self.get_administrators()

        # 检查可疑用户
        suspicious = self.check_suspicious_users(users)
        if suspicious:
            issues.extend(suspicious)

        # 检查空密码用户 (仅检查，不做告警)
        empty_password = self.check_empty_password_users(users)
        if empty_password:
            issues.append({
                "level": "critical",
                "module": "user",
                "desc": f"发现 {len(empty_password)} 个空密码账户!"
            })

        # 检查 Guest 用户状态
        guest_disabled = any(
            u.get('name', '').lower() == 'guest' and not u.get('enabled', True) == False
            for u in users if isinstance(u, dict)
        )
        if not guest_disabled:
            issues.append({
                "level": "warning",
                "module": "user",
                "desc": "Guest 用户未禁用"
            })

        return {
            "status": "ok" if not issues else "warning",
            "users": users,
            "administrators": admins,
            "issues": issues
        }

    def get_local_users(self):
        """获取本地用户列表"""
        users = []

        try:
            ps_script = """
            Get-LocalUser |
            Select-Object Name, Enabled, LastLogon, Description, PasswordRequired |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    users = data
                else:
                    users = [data]

        except Exception:
            pass

        return users

    def get_administrators(self):
        """获取管理员组成员"""
        admins = []

        try:
            ps_script = """
            Get-LocalGroupMember -Group "Administrators" |
            Select-Object Name, ObjectClass, PrincipalSource |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    admins = data
                elif isinstance(data, dict):
                    admins = [data]

        except Exception:
            pass

        return admins

    def check_suspicious_users(self, users):
        """检查可疑用户"""
        issues = []

        # 可疑用户名列表
        suspicious_names = ['hacker', 'backdoor', 'malicious', 'test123', 'admin2']

        for user in users:
            name_lower = user.get('name', '').lower()
            for sus_name in suspicious_names:
                if sus_name in name_lower:
                    issues.append({
                        "level": "warning",
                        "module": "user",
                        "desc": f"发现可疑用户名: {user.get('name')}"
                    })
                    break

        return issues

    def check_empty_password_users(self, users):
        """检查空密码用户"""
        empty_pwd_users = []

        # 注意: 这里无法直接检测密码为空，只能检测密码要求
        for user in users:
            if not user.get('PasswordRequired', True):
                # 密码不是必需的，可能为空
                if user.get('name', '').lower() not in ['defaultaccount', 'wdagutilityaccount']:
                    empty_pwd_users.append(user)

        return empty_pwd_users