# coding: utf-8
"""
磁盘检测模块
"""

import os
import psutil


class DiskModule:
    def run(self, os_detect, config):
        issues = []
        partitions = psutil.disk_partitions()
        disk_data = []

        for p in partitions:
            if not os.path.exists(p.mountpoint):
                continue
            try:
                usage = psutil.disk_usage(p.mountpoint)
                disk_data.append({
                    "fs": p.device,
                    "mount": p.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "free_gb": round(usage.free / (1024**3), 1),
                    "percent": usage.percent,
                })

                warn = config.get("thresholds.disk_warn", 85)
                crit = warn + config.get("thresholds.crit_offset", 10)
                if usage.percent >= crit:
                    issues.append({
                        "level": "critical",
                        "module": "disk",
                        "desc": f"磁盘 {p.mountpoint} 使用率严重: {usage.percent}%"
                    })
                elif usage.percent >= warn:
                    issues.append({
                        "level": "warning",
                        "module": "disk",
                        "desc": f"磁盘 {p.mountpoint} 使用率较高: {usage.percent}%"
                    })
            except Exception:
                pass

        return {
            "status": "ok" if not issues else "warning",
            "partitions": disk_data,
            "issues": issues
        }