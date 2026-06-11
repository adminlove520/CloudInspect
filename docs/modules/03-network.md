# 03 - 网络状态检测

**网卡、端口、连接、混杂模式检测模块**

---

## 功能说明

网络状态模块检测主机的网络健康状态，包括：
- 网卡信息（IP、MAC、流量）
- TCP 连接状态统计
- 监听端口检测
- 网卡混杂模式检测
- DNS 配置检查

---

## 检测内容

### 网卡信息

| 检测项 | 来源 | 说明 |
|---|---|---|
| 接口名 | `ip addr` | eth0, ens33 等 |
| IPv4 地址 | `ip addr` | 内网 IP |
| MAC 地址 | `ip link` | 物理地址 |
| 接收流量 | `/proc/net/dev` | RX bytes |
| 发送流量 | `/proc/net/dev` | TX bytes |

### TCP 连接状态

| 状态 | 说明 | 正常范围 |
|---|---|---|
| ESTABLISHED | 活跃连接 | 业务连接数 |
| TIME_WAIT | 等待关闭 | < 1000 |
| CLOSE_WAIT | 等待关闭 | < 100 |
| SYN_RECV | 半开连接 | 异常高可能有攻击 |
| LISTEN | 监听中 | 服务端口 |

### 混杂模式检测

| 检测项 | 方法 | 风险 |
|---|---|---|
| 混杂模式 | `ip link show` | 可能正在抓包 |

**混杂模式说明**: 正常情况下网卡只接收发往本机的数据包。开启混杂模式后，网卡会接收所有经过的数据包，可能用于网络抓包或中间人攻击。

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  🌐 网络状态                              │
├─────────────────────────────────────────┤
│  网卡信息:                                │
│  ├─ eth0: 10.0.0.10 (UP)                │
│  │  MAC: 52:54:00:12:34:56              │
│  │  RX: 1.5GB  TX: 856MB                │
│  └─ lo: 127.0.0.1 (UP)                  │
│                                         │
│  TCP 连接状态:                            │
│  ├─ ESTABLISHED: 45                     │
│  ├─ TIME_WAIT: 128                       │
│  ├─ CLOSE_WAIT: 5                        │
│  └─ LISTEN: 23                           │
│                                         │
│  ⚠️ 检测到 1 个可疑连接                   │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "network": {
    "interfaces": [
      {
        "iface": "eth0",
        "ip": "10.0.0.10",
        "mac": "52:54:00:12:34:56",
        "rx_mb": 1536.5,
        "tx_mb": 876.2,
        "status": "up"
      }
    ],
    "tcp_states": {
      "ESTABLISHED": 45,
      "TIME_WAIT": 128,
      "CLOSE_WAIT": 5,
      "LISTEN": 23
    },
    "promisc_ifaces": [],
    "issues": []
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 混杂模式 | 发现混杂网卡 | 严重 | 可能正在抓包 |
| TIME_WAIT 过多 | > 5000 | 警告 | 连接未正确关闭 |
| CLOSE_WAIT 过多 | > 500 | 警告 | 服务可能有问题 |
| SYN_RECV 过多 | > 500 | 警告 | 可能遭受 SYN Flood |
| 异常连接 | 境外 IP 连接 | 警告 | 需人工确认 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含网络检测
```

### 检测可疑连接

```bash
# 查看所有 TCP 连接
ss -tan

# 查看 ESTABLISHED 连接
ss -tan state established

# 查看监听端口
ss -tlnp

# 查看异常连接（境外 IP）
ss -tan | grep -v "10\.\|192\.168\.\|172\.(1[6-9]|2[0-9]|3[01])\|127\."
```

### 检测混杂模式

```bash
# 检查所有网卡
ip link show | grep PROMISC

# 使用 netstat
netstat -i | grep -v "Iface\|lo" | grep "P"
```

---

## 故障排查

**Q: 发现混杂模式告警**

```bash
# 1. 确认是否人为开启
ip link show eth0 | grep PROMISC

# 2. 查看开启混杂模式的进程
tcpdump -i eth0 -nn 2>/dev/null || echo "需要 root"

# 3. 检查是否有抓包工具
which tcpdump wireshark tshark
ps aux | grep -E "tcpdump|wireshark|ettercap"

# 4. 如非人为开启，需进一步排查
```

**Q: TIME_WAIT 连接过多**

```bash
# 查看 TIME_WAIT 连接
ss -tan state time-wait

# 原因通常是程序未正确关闭连接
# 检查应用程序的超时设置

# 临时解决方案：调整内核参数
echo 1 > /proc/sys/net/ipv4/tcp_tw_reuse
```

**Q: 端口检测失败**

```bash
# 手动查看监听端口
ss -tlnp
# 或
netstat -tlnp

# 检查权限
ss --version 2>/dev/null || echo "ss 版本过低"
```

---

*最后更新: 2026-06-11*