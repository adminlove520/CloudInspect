# coding: utf-8
"""
Windows 后门检测模块
检测常见的后门和入侵痕迹
"""

import subprocess
import os
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_RULES_FILE = Path(__file__).parent.parent / "rules" / "backdoor_rules.yaml"


def _load_rules() -> list:
    """加载后门检测规则，失败时返回空列表"""
    try:
        import yaml
        if _RULES_FILE.exists():
            with open(_RULES_FILE, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("windows_rules", [])
    except Exception as e:
        logger.warning(f"加载后门规则失败: {e}")
    return []


# 预加载规则（模块级别缓存，文件不存在时为空列表）
_RULES = _load_rules()


class BackdoorModule:
    def run(self, os_detect, config):
        issues = []

        checks = [
            ("启动项", self.check_startup_backdoors),
            ("计划任务", self.check_scheduled_backdoors),
            ("可疑服务", self.check_service_backdoors),
            ("网络连接", self.check_network_backdoors),
            ("注册表", self.check_registry_backdoors),
            ("账户", self.check_account_backdoors),
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

        # 使用规则文件中的自定义规则
        for rule in _RULES:
            try:
                issues.extend(self._apply_rule(rule))
            except Exception as e:
                logger.warning(f"应用规则 {rule.get('id', '?')} 失败: {e}")

        return {
            "status": "ok" if not issues else "warning",
            "checks": {name: True for name, _ in checks},
            "issues": issues
        }

    def check_startup_backdoors(self):
        """检查可疑的启动项后门"""
        issues = []
        suspicious_paths = [
            'temp', 'tmp', 'appdata\\local\\temp', 'downloads',
            'desktop', 'public', 'inetpub'
        ]

        try:
            ps_script = """
            $startup = @()
            # 注册表启动项
            $regPaths = @(
                'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
                'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run',
                'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce'
            )
            foreach ($path in $regPaths) {
                if (Test-Path $path) {
                    Get-ItemProperty $path | ForEach-Object {
                        $_.PSObject.Properties | Where-Object {$_.Name -notlike 'PS*'} | ForEach-Object {
                            $startup += [PSCustomObject]@{
                                Location = $path
                                Name = $_.Name
                                Command = $_.Value
                            }
                        }
                    }
                }
            }
            $startup | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    items = [data] if isinstance(data, dict) else data
                    for item in items:
                        cmd = item.get('Command', '').lower()
                        for sus in suspicious_paths:
                            if sus in cmd:
                                issues.append({
                                    "level": "warning",
                                    "module": "backdoor",
                                    "desc": f"可疑启动项: {item.get('Name', 'Unknown')} -> {item.get('Command', '')[:50]}"
                                })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return issues

    def check_scheduled_backdoors(self):
        """检查可疑的计划任务后门"""
        issues = []
        suspicious_keywords = ['temp', 'tmp', 'download', 'update', 'check', 'sync']

        try:
            ps_script = """
            Get-ScheduledTask | Where-Object {$_.State -eq 'Running' -or $_.State -eq 'Ready'} |
            ForEach-Object {
                $action = ($_.Actions | Select-Object -First 1).Execute
                [PSCustomObject]@{
                    TaskName = $_.TaskName
                    State = $_.State
                    Action = $action
                }
            } | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    tasks = [data] if isinstance(data, dict) else data
                    for task in tasks:
                        action = task.get('Action', '').lower()
                        name = task.get('TaskName', '').lower()
                        for kw in suspicious_keywords:
                            if kw in action or kw in name:
                                issues.append({
                                    "level": "warning",
                                    "module": "backdoor",
                                    "desc": f"可疑计划任务: {task.get('TaskName')} -> {task.get('Action', '')[:50]}"
                                })
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

        return issues

    def check_service_backdoors(self):
        """检查可疑的服务后门"""
        issues = []
        suspicious_service_names = ['update', 'sync', 'check', 'monitor', 'agent']

        try:
            ps_script = """
            Get-Service | Where-Object {$_.StartType -eq 'Automatic'} |
            ForEach-Object {
                $wmiSvc = Get-WmiObject -Class Win32_Service -Filter "Name='$($_.Name)'" -ErrorAction SilentlyContinue
                [PSCustomObject]@{
                    Name = $_.Name
                    DisplayName = $_.DisplayName
                    StartType = $_.StartType
                    PathName = $wmiSvc.PathName
                }
            } | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    services = [data] if isinstance(data, dict) else data
                    for svc in services:
                        name = svc.get('Name', '').lower()
                        path = svc.get('PathName', '').lower()
                        for sus in suspicious_service_names:
                            if sus in name or sus in path:
                                issues.append({
                                    "level": "warning",
                                    "module": "backdoor",
                                    "desc": f"可疑服务: {svc.get('DisplayName', svc.get('Name'))}"
                                })
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

        return issues

    def check_network_backdoors(self):
        """检查可疑的网络连接后门"""
        issues = []
        suspicious_ports = [4444, 5555, 6666, 7777, 8888, 31337]  # 常见后门端口

        try:
            ps_script = """
            Get-NetTCPConnection -State Established |
            Select-Object -First 50 LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess |
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
                    conns = [data] if isinstance(data, dict) else data
                    for conn in conns:
                        remote_port = conn.get('RemotePort', 0)
                        if remote_port in suspicious_ports:
                            issues.append({
                                "level": "warning",
                                "module": "backdoor",
                                "desc": f"可疑端口连接: {conn.get('RemoteAddress')}:{remote_port}"
                            })
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

        return issues

    def check_registry_backdoors(self):
        """检查可疑的注册表后门"""
        issues = []

        # 检查 RDP 相关的注册表
        rdp_backdoors = self.check_rdp_backdoor()
        if rdp_backdoors:
            issues.extend(rdp_backdoors)

        return issues

    def check_rdp_backdoor(self):
        """检查 RDP 相关的后门"""
        issues = []

        try:
            ps_script = """
            $regPath = 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server'
            $fDenyTS = (Get-ItemProperty -Path $regPath -Name 'fDenyTSConnections' -ErrorAction SilentlyContinue).fDenyTSConnections
            $fAllowUnsolicit = (Get-ItemProperty -Path "$regPath\\WinStations\\RDP-Tcp" -Name 'fAllowUnsolicitNEDPG' -ErrorAction SilentlyContinue).fAllowUnsolicitNEDPG
            @{
                RDPEnabled = ($fDenyTS -eq 0)
                UnsolicitedRemote = ($fAllowUnsolicitNEDPG -eq 1)
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
                    if data.get('UnsolicitedRemote'):
                        issues.append({
                            "level": "warning",
                            "module": "backdoor",
                            "desc": "注册表: 检测到 RDP 无请求远程协助已启用"
                        })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

        return issues

    def check_account_backdoors(self):
        """检查账户后门"""
        issues = []

        try:
            ps_script = """
            Get-LocalUser | Select-Object Name, Enabled, LastLogon, Description |
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
                    users = [data] if isinstance(data, dict) else data

                    for user in users:
                        name = user.get('Name', '').lower()
                        # 检查可疑用户名
                        if any(x in name for x in ['hacker', 'backdoor', 'malware', 'virus', 'crack']):
                            issues.append({
                                "level": "critical",
                                "module": "backdoor",
                                "desc": f"发现可疑用户名: {user.get('Name')}"
                            })

                        # 检查新建的管理员账户
                        if 'administrators' in str(user.get('Description', '')).lower():
                            issues.append({
                                "level": "warning",
                                "module": "backdoor",
                                "desc": f"可疑管理员账户描述: {user.get('Name')}"
                            })
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass

        return issues

    def _apply_rule(self, rule: dict) -> list:
        """根据规则类型执行检测"""
        issues = []
        rule_id = rule.get("id", "unknown")
        check_type = rule.get("check_type", "")

        if check_type == "registry_key":
            path = rule.get("path", "")
            expected_value = rule.get("expected_value")
            try:
                ps = f'Get-ItemProperty -Path "{path}" -ErrorAction SilentlyContinue | Out-String'
                r = subprocess.run(['powershell', '-Command', ps], capture_output=True, text=True, timeout=15)
                if r.returncode == 0:
                    content = r.stdout
                    if expected_value is not None:
                        if expected_value not in content:
                            issues.append({"level": rule.get("severity", "warning"),
                                           "module": "backdoor",
                                           "desc": f"{rule.get('name', rule_id)}: 值不匹配"})
                    elif content.strip():
                        issues.append({"level": rule.get("severity", "warning"),
                                       "module": "backdoor",
                                       "desc": f"{rule.get('name', rule_id)}: 存在"})
            except Exception:
                pass

        elif check_type == "account":
            account = rule.get("account", "")
            if account.lower() == "guest":
                try:
                    ps = '(Get-LocalUser -Name "Guest" -ErrorAction SilentlyContinue).Enabled'
                    r = subprocess.run(['powershell', '-Command', ps], capture_output=True, text=True, timeout=10)
                    if r.returncode == 0 and "True" in r.stdout:
                        issues.append({"level": rule.get("severity", "warning"),
                                       "module": "backdoor",
                                       "desc": f"{rule.get('name', rule_id)}: Guest 账户已启用"})
                except Exception:
                    pass

        elif check_type == "admin_count":
            threshold = rule.get("threshold", 3)
            try:
                ps = '(Get-LocalGroupMember -Group "Administrators" -ErrorAction SilentlyContinue).Count'
                r = subprocess.run(['powershell', '-Command', ps], capture_output=True, text=True, timeout=10)
                if r.returncode == 0:
                    count = int(r.stdout.strip() or 0)
                    if count >= threshold:
                        issues.append({"level": rule.get("severity", "warning"),
                                       "module": "backdoor",
                                       "desc": f"{rule.get('name', rule_id)}: 管理员数量 {count} 超过阈值 {threshold}"})
            except Exception:
                pass

        return issues