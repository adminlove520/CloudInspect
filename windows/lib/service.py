# coding: utf-8
"""
Windows 服务状态检测模块
"""

import subprocess


class ServiceModule:
    def run(self, os_detect, config):
        issues = []

        # Windows 服务列表
        services_to_check = [
            # Windows 基础服务
            'wuauserv',      # Windows Update
            'WinDefend',     # Windows Defender
            'BITS',          # Background Intelligent Transfer
            'EventLog',      # Windows Event Log
            'RpcSs',         # RPC
            'PlugPlay',      # Plug and Play

            # 网络相关服务
            'w3svc',         # IIS Web 服务
            'IISADMIN',      # IIS Admin
            'MpsSvc',        # Windows Firewall
            'SharedAccess',  # Internet Connection Sharing

            # 数据库服务
            'MSSQLSERVER',   # SQL Server
            'MSSQL$SQLEXPRESS',  # SQL Server Express
            'MySQL',         # MySQL
            'PostgreSQL',    # PostgreSQL

            # Web 服务
            'W3SVC',         # World Wide Web Publishing
            'Apache2.4',     # Apache
            'nginx',         # Nginx

            # 安全相关
            'VeeamAgent',    # Veeam Backup Agent
            'VeeamBackup',   # Veeam Backup
            'Wbackup',       # Windows Backup

            # 其他常见服务
            'Spooler',       # Print Spooler
            'Schedule',      # Task Scheduler
            'WSearch',       # Windows Search
        ]

        results = []
        running = stopped = 0

        for svc in services_to_check:
            status = self.get_service_status(svc)
            results.append({
                "name": svc,
                "status": status['status'],
                "start_type": status.get('start_type', 'unknown'),
                "description": status.get('description', '')
            })

            if status['status'] == 'running':
                running += 1
            elif status['status'] == 'stopped':
                stopped += 1

        # 检查关键服务
        critical_services = ['WinDefend', 'MpsSvc', 'RpcSs', 'PlugPlay']
        for svc_name in critical_services:
            for svc in results:
                if svc['name'].lower() == svc_name.lower():
                    if svc['status'] != 'running':
                        issues.append({
                            "level": "warning",
                            "module": "service",
                            "desc": f"关键服务 {svc_name} 未运行"
                        })

        return {
            "status": "ok" if not issues else "warning",
            "running": running,
            "stopped": stopped,
            "services": results,
            "issues": issues
        }

    def get_service_status(self, service_name):
        """获取服务状态"""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 f'Get-Service -Name "{service_name}" -ErrorAction SilentlyContinue | '
                 'Select-Object Status, StartType, DisplayName | ConvertTo-Json'],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                return {
                    "status": "running" if data.get('Status') == 1 else "stopped",
                    "start_type": data.get('StartType', 'unknown'),
                    "description": data.get('DisplayName', '')
                }

        except Exception:
            pass

        return {"status": "notfound", "start_type": "unknown", "description": ""}