# coding: utf-8
"""
日志分析模块
"""

import os
import re


class LogAnalysisModule:
    def run(self, os_detect, config):
        issues = []
        log_lines = config.get("scan.log_lines", 20)

        # secure 日志
        secure_logs = ["/var/log/secure", "/var/log/auth.log"]
        failed_auth = 0
        for log_file in secure_logs:
            if os.path.exists(log_file):
                try:
                    lines = os.popen(f"tail -{log_lines} {log_file} 2>/dev/null").read()
                    failed_auth += len(re.findall(r"failed|password|invalid", lines, re.I))
                except Exception:
                    pass

        if failed_auth > 10:
            issues.append({
                "level": "warning",
                "module": "log_analysis",
                "desc": f"发现 {failed_auth} 次认证失败记录"
            })

        # OOM 事件
        oom_count = 0
        if os.path.exists("/var/log/messages"):
            try:
                result = os.popen("grep -c 'Out of memory' /var/log/messages 2>/dev/null").read()
                oom_count = int(result.strip()) if result.strip().isdigit() else 0
            except Exception:
                pass

        if oom_count > 0:
            issues.append({
                "level": "warning",
                "module": "log_analysis",
                "desc": f"发现 {oom_count} 次 OOM 事件"
            })

        return {
            "status": "warning" if issues else "ok",
            "failed_auth": failed_auth,
            "oom_count": oom_count,
            "issues": issues
        }