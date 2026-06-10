# coding: utf-8
"""
历史命令分析模块
"""

import os
import pwd
import re


class HistoryModule:
    def run(self, os_detect, config):
        issues = []

        # 反弹 shell 模式
        shell_patterns = [
            r"bash.*-i", r"/dev/tcp", r"nc\s.*-e", r"ncat",
            r"bash.*-c.*base64", r"python.*-c.*import.*socket",
            r"php.*-r.*socket"
        ]

        # 可疑下载
        download_patterns = [
            r"wget.*境外", r"curl.*境外", r"wget\s+http://",
            r"curl.*-O.*http://"
        ]

        all_users = pwd.getpwall()
        suspicious_count = 0

        for entry in all_users[:20]:  # 限制检查前20个用户
            home = entry.pw_dir
            hist_files = [".bash_history", ".sh_history", ".history"]

            for hf in hist_files:
                hist_path = os.path.join(home, hf)
                if not os.path.exists(hist_path):
                    continue

                try:
                    with open(hist_path) as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue

                            for pat in shell_patterns:
                                if re.search(pat, line, re.I):
                                    issues.append({
                                        "level": "critical",
                                        "module": "history",
                                        "desc": f"反弹shell命令: {entry.pw_name} - {line[:80]}"
                                    })
                                    suspicious_count += 1

                            for pat in download_patterns:
                                if re.search(pat, line, re.I):
                                    issues.append({
                                        "level": "warning",
                                        "module": "history",
                                        "desc": f"可疑下载: {entry.pw_name} - {line[:80]}"
                                    })
                                    suspicious_count += 1
                except Exception:
                    pass

        return {
            "status": "critical" if issues else "ok",
            "suspicious_count": suspicious_count,
            "issues": issues[:50]  # 限制返回数量
        }