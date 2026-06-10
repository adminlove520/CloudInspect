# coding: utf-8
"""
后门检测模块 — 参考 GScan 设计
"""

import os
import glob


class BackdoorModule:
    def run(self, os_detect, config):
        issues = []
        findings = []

        # 1. LD_PRELOAD 后门
        env_files = ["/root/.bashrc", "/root/.bash_profile", "/etc/bashrc", "/etc/profile"]
        for f in env_files:
            if os.path.exists(f):
                with open(f) as fh:
                    for line in fh:
                        if "LD_PRELOAD" in line and not line.strip().startswith("#"):
                            issues.append({
                                "level": "warning",
                                "module": "backdoor",
                                "desc": f"LD_PRELOAD 后门: {f}: {line.strip()}"
                            })
                            findings.append(f"LD_PRELOAD: {f}")

        # 2. ld.so.preload 后门
        if os.path.exists("/etc/ld.so.preload"):
            with open("/etc/ld.so.preload") as f:
                content = f.read()
                if content.strip() and not content.strip().startswith("#"):
                    issues.append({
                        "level": "critical",
                        "module": "backdoor",
                        "desc": "ld.so.preload 后门: 文件存在且非空"
                    })
                    findings.append("ld.so.preload 存在")

        # 3. Cron 后门检测
        cron_dirs = ["/var/spool/cron/", "/etc/cron.d/", "/etc/cron.daily/",
                     "/etc/cron.weekly/", "/etc/cron.hourly/"]
        suspicious_patterns = ["wget", "curl", "境外", "nc ", "bash -i", "/dev/tcp", "base64"]
        for cron_dir in cron_dirs:
            if not os.path.exists(cron_dir):
                continue
            for cron_file in glob.glob(f"{cron_dir}/*"):
                if not os.path.isfile(cron_file):
                    continue
                try:
                    with open(cron_file) as f:
                        content = f.read()
                        for pat in suspicious_patterns:
                            if pat in content and not content.strip().startswith("#"):
                                issues.append({
                                    "level": "critical",
                                    "module": "backdoor",
                                    "desc": f"Cron 后门: {cron_file} 包含 {pat}"
                                })
                                findings.append(f"Cron: {cron_file}")
                except Exception:
                    pass

        # 4. SSH 后门（ln -sf /usr/sbin/sshd /tmp/su）
        suspicious_sshd = [f for f in ["/tmp/su", "/tmp/sudu", "/var/tmp/su"]
                           if os.path.exists(f)]
        for f in suspicious_sshd:
            issues.append({
                "level": "critical",
                "module": "backdoor",
                "desc": f"SSH 后门替身: {f}"
            })
            findings.append(f"SSH替身: {f}")

        # 5. setuid 后门
        suid_blacklist = ["/tmp/", "/var/tmp/", "/dev/shm/"]
        try:
            for line in os.popen("find / -type f -perm -4000 2>/dev/null").read().splitlines():
                for blk in suid_blacklist:
                    if line.startswith(blk):
                        issues.append({
                            "level": "warning",
                            "module": "backdoor",
                            "desc": f"可疑 SUID 文件: {line}"
                        })
                        findings.append(f"SUID后门: {line}")
        except Exception:
            pass

        return {
            "status": "critical" if issues else "ok",
            "found_count": len(issues),
            "findings": findings,
            "issues": issues
        }