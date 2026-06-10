# coding: utf-8
"""
网络状态检测模块
"""

import psutil
import socket


class NetworkModule:
    def run(self, os_detect, config):
        issues = []

        # 网卡信息
        net_io = psutil.net_io_counters(pernic=True)
        addrs = psutil.net_if_addrs()

        nic_data = []
        for iface, addrs_list in addrs.items():
            if iface == "lo":
                continue
            ipv4 = ""
            mac = ""
            for addr in addrs_list:
                if addr.family.name == "AF_INET":
                    ipv4 = addr.address
                elif addr.family.name == "AF_PACKET":
                    mac = addr.address
            if ipv4:
                rx_bytes = net_io.get(iface, psutil._common.snetio(0,0,0,0)).bytes_recv
                tx_bytes = net_io.get(iface, psutil._common.snetio(0,0,0,0)).bytes_sent
                nic_data.append({
                    "iface": iface,
                    "ip": ipv4,
                    "mac": mac,
                    "rx_mb": round(rx_bytes / (1024**2), 1),
                    "tx_mb": round(tx_bytes / (1024**2), 1),
                })

        # TCP 连接统计
        connections = psutil.net_connections()
        tcp_states = {}
        for c in connections:
            if c.type == 1:  # SOCK_STREAM (TCP)
                state = c.status
                tcp_states[state] = tcp_states.get(state, 0) + 1

        # 混杂模式检测
        promisc_ifaces = []
        try:
            for iface in net_io.keys():
                stats = psutil.net_if_stats().get(iface)
                if stats and stats.isup and hasattr(stats, 'flags') and stats.flags & 0x80:
                    promisc_ifaces.append(iface)
                    issues.append({
                        "level": "warning",
                        "module": "network",
                        "desc": f"网卡 {iface} 处于混杂模式"
                    })
        except Exception:
            pass

        return {
            "status": "ok" if not issues else "warning",
            "interfaces": nic_data,
            "tcp_states": tcp_states,
            "promisc_ifaces": promisc_ifaces,
            "issues": issues
        }