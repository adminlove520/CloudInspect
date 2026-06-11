# coding: utf-8
"""
Windows OS 检测层
"""

import os
import platform
import subprocess


class OSDetect:
    def __init__(self):
        self.family = "windows"
        self.id = ""
        self.pretty = ""
        self.version = ""
        self.major = ""
        self.build = ""
        self.edition = ""
        self.detect()

    def detect(self):
        """检测 Windows 操作系统"""
        # 获取基本系统信息
        self.pretty = platform.platform()
        self.version = platform.version()
        self.major = platform.version().split('.')[0]

        # 获取详细版本信息
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 '(Get-WmiObject -Class Win32_OperatingSystem).Caption'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.id = result.stdout.strip()
        except Exception:
            pass

        # 获取 Build 号
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 '[Environment]::OSVersion.Version.Build'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.build = result.stdout.strip()
        except Exception:
            pass

        # 获取 Edition (专业版/企业版等)
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 '(Get-WmiObject -Class Win32_OperatingSystem).WindowsProductName'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                self.edition = result.stdout.strip()
        except Exception:
            pass

        # 判断是否为 Server
        if "server" in self.pretty.lower() or "server" in self.id.lower():
            self.family = "windows_server"
        else:
            self.family = "windows_desktop"

    def has_defender(self):
        """检测是否启用 Windows Defender"""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-MpComputerStatus -ErrorAction SilentlyContinue | '
                 'Select-Object -ExpandProperty AntivirusEnabled'],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0 and "True" in result.stdout
        except Exception:
            return False

    def has_firewall(self):
        """检测防火墙状态"""
        try:
            result = subprocess.run(
                ['powershell', '-Command',
                 'Get-NetFirewallProfile | '
                 'Select-Object -ExpandProperty Enabled'],
                capture_output=True, text=True, timeout=30
            )
            return result.returncode == 0
        except Exception:
            return False

    def get_info(self):
        return {
            "id": self.id or platform.win32_ver()[0],
            "family": self.family,
            "pretty": self.pretty,
            "version": self.version,
            "major": self.major,
            "build": self.build,
            "edition": self.edition,
            "machine": platform.machine(),
            "has_defender": self.has_defender(),
            "has_firewall": self.has_firewall(),
        }