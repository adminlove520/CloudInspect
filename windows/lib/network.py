# coding: utf-8
"""
Windows 网络状态检测模块
"""

import psutil
import socket


class NetworkModule:
    def run(self, os_detect, config):
        issues = []

        # 网卡信息
        net_io = psutil.net_io_counters()
        interfaces = []

        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface, addr_list in addrs.items():
            iface_info = {
                "name": iface,
                "up": stats.get(iface, None) and stats[iface].isup,
                "addresses": []
            }

            for addr in addr_list:
                if addr.family.name == 'AF_INET':
                    iface_info['addresses'].append({
                        "type": "IPv4",
                        "address": addr.address,
                        "netmask": addr.netmask
                    })
                elif addr.family.name == 'AF_INET6':
                    # 跳过 IPv6 link-local
                    if not addr.address.startswith('fe80'):
                        iface_info['addresses'].append({
                            "type": "IPv6",
                            "address": addr.address,
                            "netmask": addr.netmask
                        })
                elif addr.family.name == 'AF_PACKET':
                    iface_info['mac'] = addr.address

            if iface_info['addresses']:
                interfaces.append(iface_info)

        # TCP 连接统计
        connections = psutil.net_connections()
        tcp_states = {}
        for conn in connections:
            if conn.type == 1:  # SOCK_STREAM
                state = conn.status
                tcp_states[state] = tcp_states.get(state, 0) + 1

        # 检查可疑连接
        suspicious = self.check_suspicious_connections(connections)
        if suspicious:
            issues.extend(suspicious)

        return {
            "status": "ok" if not issues else "warning",
            "interfaces": interfaces,
            "bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "tcp_states": tcp_states,
            "issues": issues
        }

    def check_suspicious_connections(self, connections):
        """检查可疑连接"""
        issues = []

        # 检测连接到境外 IP (示例 - 需完善)
        suspicious_ips = []  # 可配置的可疑 IP 列表

        for conn in connections:
            if conn.status == 'ESTABLISHED' and conn.raddr:
                ip = conn.raddr.ip
                # 这里可以添加更复杂的检查逻辑
                # 例如检查是否是境外 IP

        return issues