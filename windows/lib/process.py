# coding: utf-8
"""
Windows 进程状态检测模块
"""

import psutil
import subprocess


class ProcessModule:
    def run(self, os_detect, config):
        issues = []
        thresholds = config.get_thresholds()
        top_n = config.get('scan.top_n', 10)

        # 进程列表
        processes = []
        cpu_top = []
        mem_top = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
            try:
                info = {
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": round(proc.info['cpu_percent'] or 0, 1),
                    "mem_percent": round(proc.info['memory_percent'] or 0, 2),
                    "username": proc.info['username'] or 'Unknown'
                }
                processes.append(info)

                # CPU TOP
                if info['cpu_percent'] > 0:
                    cpu_top.append(info)

                # 内存 TOP
                if info['mem_percent'] > 0:
                    mem_top.append(info)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # 排序
        cpu_top = sorted(cpu_top, key=lambda x: x['cpu_percent'], reverse=True)[:top_n]
        mem_top = sorted(mem_top, key=lambda x: x['mem_percent'], reverse=True)[:top_n]

        # 僵尸进程 (Windows 很少有僵尸进程，但检查一下)
        zombies = [p for p in processes if p['status'] == 'zombie' if hasattr(p, 'status')]

        # 高 CPU 进程告警
        for proc in cpu_top[:3]:
            if proc['cpu_percent'] > 80:
                issues.append({
                    "level": "warning",
                    "module": "process",
                    "desc": f"高 CPU 进程: {proc['name']} (PID: {proc['pid']}) 使用 {proc['cpu_percent']}%"
                })

        # 检查可疑进程
        suspicious = self.check_suspicious_processes(processes)
        if suspicious:
            issues.extend(suspicious)

        return {
            "status": "ok" if not issues else "warning",
            "total_processes": len(processes),
            "cpu_top": cpu_top,
            "mem_top": mem_top,
            "zombie_count": len(zombies),
            "issues": issues
        }

    def check_suspicious_processes(self, processes):
        """检查可疑进程"""
        issues = []

        # 可疑进程名列表 (示例)
        suspicious_names = [
            'mimikatz', 'pwdump', 'wce', 'fgdump',
            'keylog', 'sniffer', 'nc.exe', 'netcat'
        ]

        for proc in processes:
            name_lower = proc['name'].lower()
            for sus_name in suspicious_names:
                if sus_name in name_lower:
                    issues.append({
                        "level": "critical",
                        "module": "process",
                        "desc": f"发现可疑进程: {proc['name']} (PID: {proc['pid']})"
                    })
                    break

        return issues