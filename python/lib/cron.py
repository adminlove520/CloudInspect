# coding: utf-8
"""
定时任务检测模块
"""

import os
import glob
import pwd


class CronModule:
    def run(self, os_detect, config):
        issues = []
        suspicious_patterns = ["wget", "curl", "境外", "nc ", "bash -i", "/dev/tcp"]

        cron_dirs = [
            "/var/spool/cron/", "/etc/cron.d/", "/etc/cron.daily/",
            "/etc/cron.weekly/", "/etc/cron.hourly/", "/etc/cron.monthly/"
        ]

        all_crons = []
        for cron_dir in cron_dirs:
            if not os.path.exists(cron_dir):
                continue
            for cron_file in glob.glob(f"{cron_dir}*"):
                if os.path.isfile(cron_file):
                    try:
                        with open(cron_file) as f:
                            content = f.read()
                            all_crons.append({"file": cron_file, "content": content})
                            for pat in suspicious_patterns:
                                if pat in content:
                                    issues.append({
                                        "level": "warning",
                                        "module": "cron",
                                        "desc": f"可疑 Cron 任务: {cron_file} 包含 {pat}"
                                    })
                    except Exception:
                        pass

        # 用户 crontab
        try:
            for entry in pwd.getpwall():
                try:
                    result = os.popen(f"crontab -u {entry.pw_name} -l 2>/dev/null").read()
                    if result.strip():
                        all_crons.append({"user": entry.pw_name, "content": result})
                        for pat in suspicious_patterns:
                            if pat in result:
                                issues.append({
                                    "level": "warning",
                                    "module": "cron",
                                    "desc": f"用户 {entry.pw_name} 定时任务可疑"
                                })
                except Exception:
                    pass
        except Exception:
            pass

        return {
            "status": "warning" if issues else "ok",
            "cron_count": len(all_crons),
            "suspicious_count": len(issues),
            "issues": issues
        }