# coding: utf-8
"""
Windows 事件日志分析模块
"""

import subprocess
from datetime import datetime, timedelta


class EventlogModule:
    def run(self, os_detect, config):
        issues = []
        recent_days = config.get('scan.recent_days', 7)

        # 事件日志分析
        log_entries = []

        # 安全日志 - 登录失败
        logon_failures = self.get_logon_failures(recent_days)
        if logon_failures:
            issues.append({
                "level": "warning",
                "module": "eventlog",
                "desc": f"发现 {len(logon_failures)} 次登录失败"
            })
            log_entries.extend(logon_failures)

        # 系统日志 - 错误
        system_errors = self.get_system_errors(recent_days)
        if system_errors:
            issues.append({
                "level": "warning",
                "module": "eventlog",
                "desc": f"发现 {len(system_errors)} 条系统错误"
            })
            log_entries.extend(system_errors)

        # 应用日志 - 错误
        app_errors = self.get_app_errors(recent_days)
        if app_errors:
            issues.append({
                "level": "info",
                "module": "eventlog",
                "desc": f"发现 {len(app_errors)} 条应用错误"
            })
            log_entries.extend(app_errors)

        return {
            "status": "ok" if not issues else "warning",
            "total_events": len(log_entries),
            "logon_failures": len(logon_failures),
            "system_errors": len(system_errors),
            "app_errors": len(app_errors),
            "events": log_entries[:50],  # 限制返回数量
            "issues": issues
        }

    def get_logon_failures(self, days=7):
        """获取登录失败事件"""
        events = []
        try:
            # Windows 安全日志 Event ID 4625 = 登录失败
            # Event ID 4624 = 登录成功
            ps_script = f"""
            Get-WinEvent -FilterHashtable @{{
                LogName='Security'
                ID=4625
                StartTime=(Get-Date).AddDays(-{days})
            }} -MaxEvents 50 -ErrorAction SilentlyContinue |
            Select-Object TimeCreated, Id, Message |
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
                    for event in data:
                        events.append({
                            "time": str(event.get('TimeCreated', '')),
                            "event_id": event.get('Id', ''),
                            "type": "logon_failure",
                            "source": "Security"
                        })
                elif isinstance(data, dict):
                    events.append({
                        "time": str(data.get('TimeCreated', '')),
                        "event_id": data.get('Id', ''),
                        "type": "logon_failure",
                        "source": "Security"
                    })

        except Exception:
            pass

        return events

    def get_system_errors(self, days=7):
        """获取系统错误"""
        events = []
        try:
            ps_script = f"""
            Get-WinEvent -FilterHashtable @{{
                LogName='System'
                Level=2
                StartTime=(Get-Date).AddDays(-{days})
            }} -MaxEvents 30 -ErrorAction SilentlyContinue |
            Select-Object TimeCreated, Id, ProviderName, Message |
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
                    for event in data[:20]:
                        events.append({
                            "time": str(event.get('TimeCreated', '')),
                            "event_id": event.get('Id', ''),
                            "source": event.get('ProviderName', ''),
                            "type": "system_error"
                        })

        except Exception:
            pass

        return events

    def get_app_errors(self, days=7):
        """获取应用错误"""
        events = []
        try:
            ps_script = f"""
            Get-WinEvent -FilterHashtable @{{
                LogName='Application'
                Level=2
                StartTime=(Get-Date).AddDays(-{days})
            }} -MaxEvents 20 -ErrorAction SilentlyContinue |
            Select-Object TimeCreated, Id, ProviderName |
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
                    for event in data[:10]:
                        events.append({
                            "time": str(event.get('TimeCreated', '')),
                            "event_id": event.get('Id', ''),
                            "source": event.get('ProviderName', ''),
                            "type": "app_error"
                        })

        except Exception:
            pass

        return events