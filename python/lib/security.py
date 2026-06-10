# coding: utf-8
"""
安全基线检测模块
"""

import os
import pwd


class SecurityModule:
    def run(self, os_detect, config):
        issues = []

        # SSH 配置检查
        ssh_config = "/etc/ssh/sshd_config"
        if os.path.exists(ssh_config):
            with open(ssh_config) as f:
                content = f.read()
                if "PermitRootLogin yes" in content:
                    issues.append({
                        "level": "warning",
                        "module": "security",
                        "desc": "SSH 允许 root 登录: PermitRootLogin yes"
                    })

        # UID=0 非 root 账户
        uid0_users = []
        for entry in pwd.getpwall():
            if entry.pw_uid == 0 and entry.pw_name not in ["root", "sync", "shutdown", "halt"]:
                uid0_users.append(entry.pw_name)
        if uid0_users:
            issues.append({
                "level": "critical",
                "module": "security",
                "desc": f"发现非 root 的 UID=0 账户: {', '.join(uid0_users)}"
            })

        # 空密码账户
        empty_pass = []
        with open("/etc/shadow") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) >= 2 and parts[1] in ["", "!"]:
                    empty_pass.append(parts[0])
        if empty_pass:
            issues.append({
                "level": "critical",
                "module": "security",
                "desc": f"发现空密码账户: {', '.join(empty_pass)}"
            })

        return {
            "status": "critical" if issues else "ok",
            "uid0_users": uid0_users,
            "empty_passwd": empty_pass,
            "issues": issues
        }