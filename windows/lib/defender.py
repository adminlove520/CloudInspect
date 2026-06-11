# coding: utf-8
"""
Windows Defender 检测模块
"""

import subprocess


class DefenderModule:
    def run(self, os_detect, config):
        issues = []

        # 获取 Defender 状态
        defender_status = self.get_defender_status()

        if not defender_status.get('enabled', False):
            issues.append({
                "level": "critical",
                "module": "defender",
                "desc": "Windows Defender 未启用!"
            })

        if not defender_status.get('real_time_protection', False):
            issues.append({
                "level": "warning",
                "module": "defender",
                "desc": "实时保护已关闭"
            })

        # 检查签名更新
        outdated = self.check_signature_outdated(defender_status)
        if outdated:
            issues.append({
                "level": "warning",
                "module": "defender",
                "desc": f"病毒定义已 {outdated} 天未更新"
            })

        return {
            "status": "ok" if not issues else "warning",
            "enabled": defender_status.get('enabled', False),
            "real_time_protection": defender_status.get('real_time_protection', False),
            "signature_age_days": defender_status.get('signature_age_days', 0),
            "signature_version": defender_status.get('signature_version', 'Unknown'),
            "last_scan": defender_status.get('last_scan', 'Unknown'),
            "issues": issues
        }

    def get_defender_status(self):
        """获取 Defender 状态"""
        status = {}

        try:
            ps_script = """
            $Status = Get-MpComputerStatus
            @{
                Enabled = $Status.AntivirusEnabled
                RealTimeProtection = $Status.RealTimeProtectionEnabled
                SignatureAge = $Status.AntivirusSignatureAge
                SignatureVersion = $Status.AntivirusSignatureVersion
                LastScan = $Status.FullScanEndTime
            } | ConvertTo-Json
            """

            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                status = {
                    'enabled': data.get('Enabled', False),
                    'real_time_protection': data.get('RealTimeProtection', False),
                    'signature_age_days': data.get('SignatureAge', 0),
                    'signature_version': data.get('SignatureVersion', 'Unknown'),
                    'last_scan': str(data.get('LastScan', 'Unknown'))
                }

        except Exception:
            pass

        return status

    def check_signature_outdated(self, status):
        """检查签名是否过期"""
        days = status.get('signature_age_days', 0)
        if days > 7:
            return days
        return 0