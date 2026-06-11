# coding: utf-8
"""
Windows 历史命令分析模块
分析 PowerShell 和 CMD 历史记录
"""

import subprocess
import os
import logging

logger = logging.getLogger(__name__)


class HistoryModule:
    def run(self, os_detect, config):
        issues = []

        checks = [
            ("PowerShell历史", self.get_powershell_history),
            ("CMD历史", self.get_cmd_history),
            ("最近执行", self.get_recent_execs),
        ]

        for name, fn in checks:
            try:
                result = fn()
                if result:
                    issues.extend(self._analyze(name, result))
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} 检查超时")
            except Exception as e:
                logger.warning(f"{name} 检查失败: {e}")

        return {
            "status": "ok" if not issues else "warning",
            "powershell_history_lines": len([r for r in issues if "powershell" in str(r)]),
            "cmd_history_lines": len([r for r in issues if "cmd" in str(r)]),
            "recent_execs_count": len(issues),
            "issues": issues
        }

    def get_powershell_history(self):
        """获取 PowerShell 历史"""
        history = []
        try:
            # PowerShell 命令历史
            ps_script = """
            if (Test-Path $env:APPDATA\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt) {
                Get-Content "$env:APPDATA\\Microsoft\\Windows\\PowerShell\\PSReadLine\\ConsoleHost_history.txt" -Tail 100
            }
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                history = result.stdout.strip().split('\n')
        except Exception:
            pass

        return history

    def get_cmd_history(self):
        """获取 CMD 历史"""
        history = []
        try:
            # DOSKEY 历史 (当前会话)
            result = subprocess.run(
                ['cmd', '/c', 'doskey /history'],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                history = result.stdout.strip().split('\n')
        except Exception:
            pass

        return history

    def get_recent_execs(self):
        """获取最近执行的程序"""
        execs = []
        try:
            ps_script = """
            Get-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\RunMRU' |
            ForEach-Object {
                $_.PSObject.Properties | Where-Object {$_.Name -ne '(default)'} |
                Select-Object -First 50 Value
            } | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    execs = [data] if isinstance(data, dict) else data
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return execs

    def _analyze(self, source: str, lines: list) -> list:
        """分析历史命令，检测可疑模式"""
        issues = []
        suspicious = [
            "Invoke-WebRequest", "IEX", "DownloadString",
            "DownloadFile", "Net.WebClient",
            "bash -i", "nc ", "/dev/tcp", "rm -rf /",
            "-enc ", "-encodedCommand",
        ]
        for line in lines:
            line_str = str(line)
            for pattern in suspicious:
                if pattern.lower() in line_str.lower():
                    issues.append({
                        "level": "warning",
                        "module": "history",
                        "source": source,
                        "desc": f"可疑命令: {line_str[:100]}"
                    })
                    break
        return issues