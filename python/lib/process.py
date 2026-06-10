# coding: utf-8
"""
进程检测模块
"""

import psutil


class ProcessModule:
    def run(self, os_detect, config):
        issues = []
        top_n = config.get("scan.top_n", 10)

        # 僵尸进程
        zombies = [p for p in psutil.process_iter(['pid', 'name', 'status'])
                   if p.info['status'] == psutil.STATUS_ZOMBIE]
        if zombies:
            issues.append({
                "level": "warning",
                "module": "process",
                "desc": f"发现 {len(zombies)} 个僵尸进程"
            })

        # CPU TOP
        cpu_top = []
        for p in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                        key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:top_n]:
            try:
                cpu_top.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "cpu_pct": round(p.info['cpu_percent'] or 0, 1),
                    "mem_pct": round(p.info['memory_percent'] or 0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 内存 TOP
        mem_top = []
        for p in sorted(psutil.process_iter(['pid', 'name', 'memory_percent']),
                        key=lambda x: x.info['memory_percent'] or 0, reverse=True)[:top_n]:
            try:
                mem_top.append({
                    "pid": p.info['pid'],
                    "name": p.info['name'],
                    "mem_pct": round(p.info['memory_percent'] or 0, 1),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return {
            "status": "ok" if not zombies else "warning",
            "zombie_count": len(zombies),
            "cpu_top": cpu_top,
            "mem_top": mem_top,
            "issues": issues
        }