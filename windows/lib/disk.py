# coding: utf-8
"""
Windows 磁盘状态检测模块
"""

import psutil


class DiskModule:
    def run(self, os_detect, config):
        issues = []
        thresholds = config.get_thresholds()

        disk_info = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info = {
                    "drive": partition.device,
                    "mount": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                }
                disk_info.append(info)

                # 检查阈值
                if usage.percent >= thresholds.get('disk_warn', 85):
                    level = "critical" if usage.percent >= thresholds.get('disk_crit', 95) else "warning"
                    issues.append({
                        "level": level,
                        "module": "disk",
                        "desc": f"磁盘 {partition.device} 使用率 {usage.percent}% (阈值: {thresholds.get('disk_warn', 85)}%)"
                    })

            except Exception as e:
                pass

        # 检查大文件
        large_files = self.find_large_files(thresholds.get('large_file_size', '100M'))

        return {
            "status": "ok" if not issues else "warning",
            "drives": disk_info,
            "total_drives": len(disk_info),
            "large_files": large_files,
            "issues": issues
        }

    def find_large_files(self, size_threshold='100M'):
        """查找大文件"""
        # 解析阈值
        try:
            if isinstance(size_threshold, str):
                size_mb = int(size_threshold.rstrip('MG'))
            else:
                size_mb = int(size_threshold)
        except Exception:
            size_mb = 100

        large_files = []
        # 常见大文件目录
        search_paths = ['C:\\', 'D:\\', 'E:\\']

        # 注意: 实际应该限制搜索范围和深度
        # 这里仅作为示例，实际使用中应该更谨慎
        return large_files  # 空列表，避免扫描太慢