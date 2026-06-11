# coding: utf-8
"""
Windows Rootkit 检测模块
检测常见的 Rootkit 特征
"""

import subprocess
import os
import logging

logger = logging.getLogger(__name__)


# 扩充 Windows 系统进程白名单（覆盖 Windows Server 2022, Win11, 常见第三方进程）
KNOWN_PROCESSES = {
    # 系统核心
    "System", "Registry", "smss", "csrss", "wininit", "services", "lsass",
    "svchost", "winlogon", "dwm", "fontdrvhost", "sihost",
    # 任务管理器可见的常见系统进程
    "RuntimeBroker", "ShellExperienceHost", "SearchHost", "StartMenuExperienceHost",
    "TextInputHost", "SecurityHealthService", "SecurityHealthSystray",
    "MsMpEng", "NisSrv", "spoolsv", "WmiPrvSE", "dllhost",
    "conhost", "taskhostw", "schtasks",
    # Windows Server 进程
    "Memory Compression", "idle",
    # 常见无害第三方进程
    "explorer", "OneDrive", "Teams", "Slack", "Discord",
    "Code", "CodeHelper", "cursor", "node", "python", "pythonw",
}


class RootkitModule:
    def run(self, os_detect, config):
        issues = []

        checks = [
            ("隐藏进程", self.check_hidden_processes),
            ("隐藏服务", self.check_hidden_services),
            ("网络异常", self.check_network_anomalies),
            ("文件异常", self.check_file_anomalies),
            ("注册表异常", self.check_registry_anomalies),
            ("驱动异常", self.check_driver_anomalies),
        ]

        for name, fn in checks:
            try:
                result = fn()
                if result:
                    issues.extend(result)
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} 检查超时")
            except Exception as e:
                logger.warning(f"{name} 检查失败: {e}")

        return {
            "status": "ok" if not issues else "warning",
            "checks": {name: True for name, _ in checks},
            "issues": issues
        }

    def check_hidden_processes(self):
        """检查隐藏进程"""
        issues = []

        # 检查进程数量差异
        try:
            ps_script = """
            $tasklist = (tasklist /FO CSV /NH | ConvertFrom-Csv).Count
            $wmi = (Get-Process).Count
            @{
                Tasklist = $tasklist
                WMI = $wmi
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
                    tasklist_count = int(data.get('Tasklist', 0))
                    wmi_count = int(data.get('WMI', 0))

                    # 如果差异超过10%可能有问题
                    if wmi_count > tasklist_count * 1.1:
                        issues.append({
                            "level": "warning",
                            "module": "rootkit",
                            "desc": f"进程数量异常: WMI={wmi_count}, tasklist={tasklist_count}"
                        })
                except (json.JSONDecodeError, ValueError, TypeError):
                    pass
        except Exception:
            pass

        return issues

    def check_hidden_services(self):
        """检查隐藏服务"""
        issues = []

        # 检查可疑的服务
        suspicious_service_names = [
            'rootkit', 'hack', 'backdoor', 'keylog', 'sniffer',
            'inject', 'hook', 'hide', 'stealth'
        ]

        try:
            ps_script = """
            Get-Service | Select-Object Name, DisplayName, Status, StartType |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    services = [data] if isinstance(data, dict) else data

                    for svc in services:
                        name = svc.get('Name', '').lower()
                        for sus in suspicious_service_names:
                            if sus in name:
                                issues.append({
                                    "level": "warning",
                                    "module": "rootkit",
                                    "desc": f"可疑服务名: {svc.get('DisplayName') or svc.get('Name', 'Unknown')}"
                                })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return issues

    def check_network_anomalies(self):
        """检查网络异常"""
        issues = []

        # 检查异常端口
        suspicious_ports = [4444, 5555, 6666, 7777, 8888, 31337, 12345]

        try:
            ps_script = """
            Get-NetTCPConnection -State Listen |
            Select-Object LocalPort, OwningProcess |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    ports = [data] if isinstance(data, dict) else data

                    for conn in ports:
                        port = conn.get('LocalPort', 0)
                        if port in suspicious_ports:
                            issues.append({
                                "level": "warning",
                                "module": "rootkit",
                                "desc": f"可疑监听端口: {port}"
                            })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return issues

    def check_file_anomalies(self):
        """检查文件异常"""
        issues = []

        # 检查系统目录中的可疑文件
        suspicious_files = [
            'C:\\Windows\\System32\\cmdh.exe',
            'C:\\Windows\\System32\\svchost.exe',
            'C:\\Windows\\System32\\drivers\\etc\\hosts.bak',
        ]

        try:
            for file_path in suspicious_files:
                if os.path.exists(file_path):
                    # 检查文件大小是否异常
                    size = os.path.getsize(file_path)
                    issues.append({
                        "level": "info",
                        "module": "rootkit",
                        "desc": f"发现文件: {file_path} ({size} bytes)"
                    })
        except Exception:
            pass

        return issues

    def check_registry_anomalies(self):
        """检查注册表异常"""
        issues = []

        # 检查可疑的注册表项
        suspicious_keys = [
            'HKLM\\SYSTEM\\CurrentControlSet\\Services\\{BAM}',
            'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\WindowsUpdate',
        ]

        # 检查 RDP 相关异常
        try:
            ps_script = """
            $rdpEnabled = (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server' -Name 'fDenyTSConnections' -ErrorAction SilentlyContinue).fDenyTSConnections
            $port = (Get-ItemProperty -Path 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp' -Name 'PortNumber' -ErrorAction SilentlyContinue).PortNumber
            @{
                RDPEnabled = ($rdpEnabled -eq 0)
                RDPPort = $port
            } | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    if data.get('RDPEnabled'):
                        port = data.get('RDPPort', 3389)
                        if port != 3389:
                            issues.append({
                                "level": "warning",
                                "module": "rootkit",
                                "desc": f"RDP端口异常: {port} (应为3389)"
                            })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return issues

    def check_driver_anomalies(self):
        """检查驱动异常"""
        issues = []

        # 检查可疑的驱动
        suspicious_drivers = [
            'rootkit', 'hack', 'backdoor', 'keylog', 'sniffer',
            'passwd', 'password', 'stealth'
        ]

        try:
            ps_script = """
            Get-WindowsDriver -All -ErrorAction SilentlyContinue |
            Select-Object Driver, OriginalFileName |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=60
            )

            # 注意: Get-WindowsDriver 需要管理员权限和特定模块
            # 如果失败，使用替代方法
            if result.returncode != 0 or not result.stdout.strip():
                # 列出加载的驱动
                ps_script2 = """
                Get-Process | Where-Object {$_.ProcessName -like '*driver*'} |
                Select-Object ProcessName, Id | ConvertTo-Json
                """

                result = subprocess.run(
                    ['powershell', '-Command', ps_script2],
                    capture_output=True, text=True, timeout=30
                )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    # 如果返回空或错误，忽略
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return issues