# coding: utf-8
"""
OS 检测层
支持: Rocky / RHEL / CentOS / Ubuntu / Debian / Kylin / EulerOS / UOS / SUSE / Arch / Alpine / Gentoo 等主流操作系统
"""

import os
import platform


class OSDetect:
    def __init__(self):
        self.family = ""
        self.id = ""
        self.pretty = ""
        self.version = ""
        self.major = ""
        self.detect()

    def detect(self):
        """检测操作系统类型"""
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("ID="):
                        self.id = line.split("=")[1].strip().strip('"')
                    elif line.startswith("VERSION_ID="):
                        self.version = line.split("=")[1].strip().strip('"')
                    elif line.startswith("PRETTY_NAME="):
                        self.pretty = line.split("=")[1].strip().strip('"')

        # 兜底检测
        if not self.id:
            if os.path.exists("/etc/kylin-release"):
                self.id = "kylin"
                with open("/etc/kylin-release") as f:
                    self.pretty = f.readline().strip()
            elif os.path.exists("/etc/euler-release"):
                self.id = "euler"  # EulerOS
                with open("/etc/euler-release") as f:
                    self.pretty = f.readline().strip()
            elif os.path.exists("/etc/centos-release"):
                self.id = "centos"
                with open("/etc/centos-release") as f:
                    self.pretty = f.readline().strip()
            elif os.path.exists("/etc/alpine-release"):
                self.id = "alpine"
                with open("/etc/alpine-release") as f:
                    self.pretty = f"Alpine {f.read().strip()}"
            elif os.path.exists("/etc/arch-release"):
                self.id = "arch"
                self.pretty = "Arch Linux"

        self.major = self.version.split(".")[0] if self.version else ""

        # 判断家族
        rhel_ids = ["rhel", "centos", "rocky", "almalinux", "ol", "fedora", "amazon", "euler"]
        debian_ids = ["debian", "ubuntu", "kali", "mint"]
        suse_ids = ["suse", "sles", "opensuse"]

        if self.id in ["kylin", "neokylin"]:
            self.family = "kylin"
        elif self.id in ["euler"]:
            self.family = "rhel"  # EulerOS 基于 RHEL，归入 rhel 家族
        elif self.id in rhel_ids:
            self.family = "rhel"
        elif self.id in debian_ids:
            self.family = "debian"
        elif self.id in suse_ids:
            self.family = "suse"
        elif self.id == "alpine":
            self.family = "alpine"
        elif self.id == "arch":
            self.family = "arch"
        elif self.id == "gentoo":
            self.family = "gentoo"
        else:
            self.family = "other"

    def has_systemd(self):
        """检测是否有 systemd"""
        return os.path.exists("/run/systemd/system")

    def has_docker(self):
        return os.path.exists("/var/run/docker.sock")

    def has_podman(self):
        return os.path.exists("/var/run/containers.sock")

    def get_info(self):
        return {
            "id": self.id,
            "family": self.family,
            "pretty": self.pretty,
            "version": self.version,
            "major": self.major,
            "machine": platform.machine(),
            "has_systemd": self.has_systemd(),
        }