# coding: utf-8
"""
Rootkit 检测模块
"""

import os
import re


class RootkitModule:
    def run(self, os_detect, config):
        issues = []

        # 已知 Rootkit 文件特征
        rk_signatures = [
            "/tmp/...", "/tmp/..", "/var/tmp/...", "/var/tmp/..",
            "/dev/shm/...", "/dev/shm/.."
        ]
        for sig in rk_signatures:
            # 简单文件名检测
            pass

        # 隐藏文件
        suspicious_dirs = ["/tmp", "/var/tmp", "/dev/shm"]
        for d in suspicious_dirs:
            if not os.path.exists(d):
                continue
            for f in os.listdir(d):
                if f.startswith("."):
                    issues.append({
                        "level": "warning",
                        "module": "rootkit",
                        "desc": f"隐藏文件: {d}/{f}"
                    })

        # 异常内核模块
        if os.path.exists("/proc/modules"):
            try:
                content = open("/proc/modules").read()
                suspicious_mods = ["hide", "sniffer", "rootkit", "backdoor"]
                for line in content.splitlines():
                    mod_name = line.split()[0]
                    for sm in suspicious_mods:
                        if sm in mod_name.lower():
                            issues.append({
                                "level": "critical",
                                "module": "rootkit",
                                "desc": f"可疑内核模块: {mod_name}"
                            })
            except Exception:
                pass

        return {
            "status": "critical" if issues else "ok",
            "found_count": len(issues),
            "issues": issues[:20]
        }