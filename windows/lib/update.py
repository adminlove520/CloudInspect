# coding: utf-8
"""
Windows 更新状态检测模块
"""

import subprocess


class UpdateModule:
    def run(self, os_detect, config):
        issues = []

        # 获取待安装更新
        pending_updates = self.get_pending_updates()

        # 获取最近安装的更新
        recent_updates = self.get_recent_updates()

        # 检查更新状态
        if pending_updates:
            issues.append({
                "level": "info",
                "module": "update",
                "desc": f"有 {len(pending_updates)} 个待安装更新"
            })

        return {
            "status": "ok" if not issues else "warning",
            "pending_updates": len(pending_updates),
            "recent_updates": recent_updates[:10],
            "issues": issues
        }

    def get_pending_updates(self):
        """获取待安装更新"""
        updates = []

        try:
            ps_script = """
            $UpdateSession = New-Object -ComObject Microsoft.Update.Session
            $UpdateSearcher = $UpdateSession.CreateUpdateSearcher()
            $SearchResult = $UpdateSearcher.Search("IsInstalled=0")
            $SearchResult.Updates |
            Select-Object Title, KBArticleIDs, MsrcSeverity |
            ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=120
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, list):
                        updates = data
                    elif isinstance(data, dict):
                        updates = [data]
                except json.JSONDecodeError:
                    pass

        except Exception:
            pass

        return updates

    def get_recent_updates(self):
        """获取最近安装的更新"""
        updates = []

        try:
            ps_script = """
            Get-HotFix |
            Sort-Object -Property InstalledOn -Descending |
            Select-Object -First 20 HotFixID, Description, InstalledOn, InstalledBy |
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
                    updates = data
                elif isinstance(data, dict):
                    updates = [data]

        except Exception:
            pass

        return updates