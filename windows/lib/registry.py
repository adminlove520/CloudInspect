# coding: utf-8
"""
Windows 注册表安全检测模块
"""

import subprocess


class RegistryModule:
    def run(self, os_detect, config):
        issues = []

        # 检查自启动项
        startup_items = self.get_startup_items()
        if len(startup_items) > 10:
            issues.append({
                "level": "info",
                "module": "registry",
                "desc": f"发现 {len(startup_items)} 个自启动项"
            })

        # 检查可疑自启动
        suspicious = self.check_suspicious_startup(startup_items)
        if suspicious:
            issues.extend(suspicious)

        # 检查 RDP 状态
        rdp_enabled = self.check_rdp_status()
        if rdp_enabled:
            issues.append({
                "level": "info",
                "module": "registry",
                "desc": "远程桌面 (RDP) 已启用"
            })

        return {
            "status": "ok" if not issues else "warning",
            "startup_items": startup_items,
            "rdp_enabled": rdp_enabled,
            "issues": issues
        }

    def get_startup_items(self):
        """获取自启动项"""
        items = []

        try:
            ps_script = """
            Get-CimInstance -ClassName Win32_StartupCommand |
            Select-Object Name, Command, Location, User |
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
                    items = data
                elif isinstance(data, dict):
                    items = [data]

        except Exception:
            pass

        return items

    def check_suspicious_startup(self, items):
        """检查可疑自启动项"""
        issues = []

        suspicious_paths = [
            'temp', 'tmp', 'appdata\\local\\temp',
            'downloads', 'desktop'
        ]

        for item in items:
            command = item.get('Command', '').lower()
            location = item.get('Location', '').lower()

            for sus_path in suspicious_paths:
                if sus_path in command or sus_path in location:
                    issues.append({
                        "level": "warning",
                        "module": "registry",
                        "desc": f"可疑自启动项: {item.get('Name', 'Unknown')}"
                    })
                    break

        return issues

    def check_rdp_status(self):
        """检查 RDP 状态"""
        try:
            ps_script = """
            (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name "fDenyTSConnections").fDenyTSConnections
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0:
                # 0 = RDP 启用, 1 = RDP 禁用
                return "0" in result.stdout

        except Exception:
            pass

        return False