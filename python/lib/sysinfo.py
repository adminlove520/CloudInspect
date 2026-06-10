# coding: utf-8
"""
系统信息采集模块
"""

import os
import platform
import psutil


class SysinfoModule:
    def run(self, os_detect, config):
        hostname = platform.node()
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        mem_percent = mem.percent

        load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (0, 0, 0)

        boot_time = psutil.boot_time()
        uptime_hours = (psutil.time.time() - boot_time) / 3600

        return {
            "status": "ok",
            "hostname": hostname,
            "os": os_detect.pretty,
            "kernel": platform.release(),
            "machine": platform.machine(),
            "cpu_count": cpu_count,
            "cpu_usage": cpu_percent,
            "cpu_model": platform.processor() or "未知",
            "mem_total_gb": round(mem.total / (1024**3), 2),
            "mem_usage": mem_percent,
            "load_1": round(load_avg[0], 2),
            "load_5": round(load_avg[1], 2),
            "load_15": round(load_avg[2], 2),
            "uptime_hours": round(uptime_hours, 1),
            "issues": []
        }