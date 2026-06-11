# coding: utf-8
"""
Windows 防火墙检测模块
"""

import subprocess


class FirewallModule:
    def run(self, os_detect, config):
        issues = []

        # 获取防火墙状态
        firewall_profiles = self.get_firewall_profiles()

        # 检查是否有防火墙关闭
        for profile in firewall_profiles:
            if not profile['enabled']:
                issues.append({
                    "level": "warning",
                    "module": "firewall",
                    "desc": f"防火墙 {profile['name']} 未启用"
                })

        # 获取防火墙规则
        rules = self.get_firewall_rules()

        return {
            "status": "ok" if not issues else "warning",
            "profiles": firewall_profiles,
            "enabled_rules_count": sum(1 for r in rules if r.get('enabled')),
            "rules": rules[:20],  # 限制返回数量
            "issues": issues
        }

    def get_firewall_profiles(self):
        """获取防火墙配置文件"""
        profiles = []
        profile_names = {
            'Domain': '域网络',
            'Private': '专用网络',
            'Public': '公用网络'
        }

        try:
            ps_script = """
            Get-NetFirewallProfile |
            Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction |
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
                    profiles = data
                else:
                    profiles = [data]

                # 转换名称
                for p in profiles:
                    p['display_name'] = profile_names.get(p['Name'], p['Name'])

        except Exception:
            pass

        return profiles

    def get_firewall_rules(self):
        """获取防火墙规则"""
        rules = []

        try:
            ps_script = """
            Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True |
            Select-Object Name, DisplayName, Direction, Action, Profile, Enabled |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                if isinstance(data, list):
                    rules = data
                elif isinstance(data, dict):
                    rules = [data]

        except Exception:
            pass

        return rules