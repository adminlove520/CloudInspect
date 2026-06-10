# coding: utf-8
"""
服务状态检测模块
"""

import os


class ServiceModule:
    def run(self, os_detect, config):
        # 定义要检测的服务列表
        services = [
            "sshd", "crond", "firewalld", "ufw", "docker", "podman",
            "nginx", "httpd", "mysqld", "mariadb", "postgresql",
            "redis", "mongod", "elasticsearch", "php-fpm", "tomcat",
            "kubelet", "zabbix-agent", "prometheus", "grafana-server",
            "haproxy", "keepalived", "postfix", "smbd", "named",
            "chronyd", "ntpd", "snmpd"
        ]

        results = []
        running = stopped = 0

        for svc in services:
            # 使用 systemctl 检测
            status = "notfound"
            if os_detect.has_systemd():
                r = os.popen(f"systemctl is-active {svc} 2>/dev/null").read().strip()
                status = r if r in ["active", "inactive"] else "notfound"

            results.append({"name": svc, "status": status})
            if status == "active":
                running += 1
            elif status == "inactive":
                stopped += 1

        return {
            "status": "ok",
            "running": running,
            "stopped": stopped,
            "services": results,
            "issues": []
        }