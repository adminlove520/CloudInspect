# coding: utf-8
"""
Windows 系统信息采集模块
"""

import os
import platform
import subprocess
import psutil
import time as time_module


class SysinfoModule:
    def run(self, os_detect, config):
        issues = []
        thresholds = config.get_thresholds()

        # 基本信息
        hostname = platform.node()
        os_info = platform.platform()
        kernel = platform.version()
        machine = platform.machine()

        # CPU 信息
        cpu_count = psutil.cpu_count(logical=True)
        cpu_physical = psutil.cpu_count(logical=False)
        cpu_percent = psutil.cpu_percent(interval=1)

        cpu_warn = thresholds.get('cpu_warn', 80)
        cpu_crit = thresholds.get('cpu_crit', 90)
        if cpu_percent >= cpu_warn:
            level = "warning" if cpu_percent < cpu_crit else "critical"
            issues.append({
                "level": level,
                "module": "sysinfo",
                "desc": f"CPU 使用率 {cpu_percent}% (阈值: {cpu_warn}%)"
            })

        # 内存信息
        mem = psutil.virtual_memory()
        mem_percent = mem.percent
        mem_total_gb = round(mem.total / (1024**3), 2)
        mem_used_gb = round(mem.used / (1024**3), 2)

        mem_warn = thresholds.get('mem_warn', 85)
        mem_crit = thresholds.get('mem_crit', 95)
        if mem_percent >= mem_warn:
            level = "warning" if mem_percent < mem_crit else "critical"
            issues.append({
                "level": level,
                "module": "sysinfo",
                "desc": f"内存使用率 {mem_percent}% (阈值: {mem_warn}%)"
            })

        # 磁盘信息
        disk_info = []
        disk_warn = thresholds.get('disk_warn', 85)
        disk_crit = thresholds.get('disk_crit', 95)
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "drive": partition.device,
                    "mount": partition.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "percent": usage.percent
                })

                if usage.percent >= disk_warn:
                    level = "warning" if usage.percent < disk_crit else "critical"
                    issues.append({
                        "level": level,
                        "module": "sysinfo",
                        "desc": f"磁盘 {partition.device} 使用率 {usage.percent}% (阈值: {disk_warn}%)"
                    })
            except Exception:
                pass

        # 系统运行时间
        boot_time = psutil.boot_time()
        uptime_hours = round((time_module.time() - boot_time) / 3600, 1)

        # Windows 专用信息
        windows_info = self.get_windows_info()

        return {
            "status": "ok" if not issues else "warning",
            "hostname": hostname,
            "os": os_info,
            "kernel": kernel,
            "machine": machine,
            "cpu_count": cpu_count,
            "cpu_physical": cpu_physical,
            "cpu_percent": cpu_percent,
            "mem_total_gb": mem_total_gb,
            "mem_used_gb": mem_used_gb,
            "mem_percent": mem_percent,
            "disk": disk_info,
            "uptime_hours": uptime_hours,
            "windows": windows_info,
            "issues": issues
        }

    def get_windows_info(self):
        """获取 Windows 专用信息"""
        info = {}

        # 计算机名
        info['computer_name'] = os.environ.get('COMPUTERNAME', '未知')

        # Windows 版本
        try:
            result = subprocess.run(
                ['powershell', '-Command', '(Get-WmiObject -Class Win32_OperatingSystem).Caption'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                info['edition'] = result.stdout.strip()
        except Exception:
            pass

        # 域信息
        try:
            result = subprocess.run(
                ['powershell', '-Command', '[System.Environment]::GetEnvironmentVariable("USERDOMAIN")'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                info['domain'] = result.stdout.strip()
        except Exception:
            pass

        return info