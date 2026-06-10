# coding: utf-8
"""
Webshell 检测模块
"""

import os
import re


class WebshellModule:
    def run(self, os_detect, config):
        issues = []

        # Webshell 特征模式
        patterns = [
            r"eval\s*\(", r"base64_decode\s*\(", r"system\s*\(",
            r"shell_exec\s*\(", r"passthru\s*\(", r"exec\s*\(",
            r"preg_replace.*\/e", r"assert\s*\(", r"call_user_func\s*\(",
            r"usort\s*\(", r"ini_set.*disable_functions",
        ]

        scan_paths = ["/var/www", "/home", "/opt"]
        extensions = [".php", ".jsp", ".asp", ".aspx", ".py", ".htm", ".html"]
        found_count = 0

        for scan_path in scan_paths:
            if not os.path.exists(scan_path):
                continue

            for root, dirs, files in os.walk(scan_path):
                # 跳过过大目录
                if "/node_modules" in root or "/.git" in root or "/venv" in root:
                    continue

                for fname in files[:200]:  # 每目录最多200个文件
                    if not any(fname.endswith(ext) for ext in extensions):
                        continue

                    fpath = os.path.join(root, fname)
                    try:
                        size = os.path.getsize(fpath)
                        if size > 2 * 1024 * 1024:  # 跳过 > 2MB
                            continue

                        with open(fpath, "r", errors="ignore") as f:
                            content = f.read(8192)  # 只读前8KB

                        for pat in patterns:
                            if re.search(pat, content, re.I):
                                issues.append({
                                    "level": "critical",
                                    "module": "webshell",
                                    "desc": f"疑似Webshell: {fpath} (匹配 {pat})"
                                })
                                found_count += 1
                                break
                    except Exception:
                        pass

        return {
            "status": "critical" if issues else "ok",
            "found_count": found_count,
            "issues": issues[:20]  # 限制返回
        }