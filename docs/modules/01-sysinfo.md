# 01 - 系统信息采集

**系统基本信息采集模块**

---

## 功能说明

系统信息模块采集主机的基本信息，包括：
- 主机名、IP、MAC 地址
- 操作系统版本、内核版本
- CPU 型号、核心数、使用率
- 内存总量、使用率
- 负载情况
- 运行时间
- SELinux 状态
- 防火墙状态
- 虚拟化类型

---

## 检测内容

### 基础信息

| 检测项 | 来源 | 说明 |
|---|---|---|
| 主机名 | `hostname` | 短主机名和完整域名 |
| IP 地址 | `ip addr` | 优先显示内网 IP |
| MAC 地址 | `/sys/class/net/` | 默认网关 MAC |
| 操作系统 | `/etc/os-release` | 发行版名称和版本 |
| 内核版本 | `uname -r` | 内核版本号 |
| 系统架构 | `uname -m` | x86_64 / aarch64 |

### CPU 信息

| 检测项 | 来源 | 说明 |
|---|---|---|
| CPU 型号 | `/proc/cpuinfo` | model name |
| CPU 核心数 | `nproc` | 逻辑核心数 |
| CPU 频率 | `/proc/cpuinfo` | cpu MHz |
| CPU 使用率 | `top` 或 `/proc/stat` | 实时使用率 |
| 负载 | `/proc/loadavg` | 1/5/15 分钟负载 |

### 内存信息

| 检测项 | 来源 | 说明 |
|---|---|---|
| 总内存 | `/proc/meminfo` | MemTotal |
| 可用内存 | `/proc/meminfo` | MemAvailable |
| 使用率 | 计算得出 | (总-可用)/总 |
| Swap 总计 | `/proc/meminfo` | SwapTotal |
| Swap 使用率 | 计算得出 | - |

### 安全状态

| 检测项 | 检测方法 | 说明 |
|---|---|---|
| SELinux | `getenforce` 或 `/sys/fs/selinux/` | 启用/禁用/未安装 |
| 防火墙 | `systemctl is-active` | firewalld/UFW/iptables |
| 虚拟化 | `systemd-detect-virt` 或 DMI | VMware/KVM/Hyper-V 等 |

---

## 检测阈值

| 指标 | 警告阈值 | 严重阈值 | 说明 |
|---|---|---|---|
| CPU 使用率 | 80% | 90% | 可通过 config 调整 |
| 内存使用率 | 85% | 95% | 可通过 config 调整 |
| 负载 | CPU 核心数 × 2 | CPU 核心数 × 4 | 超过核心数视为异常 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  🖥️ 系统信息                              │
├─────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐             │
│  │ CPU 45%  │ │ 内存 62%  │             │
│  │ 核心: 8  │ │ 总计: 16G │             │
│  └──────────┘ └──────────┘             │
│                                         │
│  主机名: web-server-01                  │
│  IP: 10.0.0.10                          │
│  OS: Huawei Cloud EulerOS 2.0           │
│  内核: 5.10.0-60.18.0.50.hce2.x8664     │
│  架构: x86_64                           │
│  SELinux: 未安装                         │
│  防火墙: firewalld (active)              │
│  虚拟化: VMware                          │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "sysinfo": {
    "hostname": "web-server-01",
    "ip": "10.0.0.10",
    "os": "Huawei Cloud EulerOS 2.0",
    "kernel": "5.10.0-60.18.0.50.hce2.x8664",
    "cpu_model": "Intel(R) Xeon(R) Platinum 8280L",
    "cpu_cores": 8,
    "cpu_usage_pct": 45,
    "mem_total_bytes": 17179869184,
    "mem_used_pct": 62,
    "load_1": 1.5,
    "load_5": 1.2,
    "load_15": 0.8,
    "selinux": "未安装",
    "firewall": "firewalld (active)",
    "virt": "VMware"
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| CPU 过高 | > 80% | 警告 | CPU 使用率超过 80% |
| CPU 严重 | > 90% | 严重 | CPU 使用率超过 90% |
| 内存过高 | > 85% | 警告 | 内存使用率超过 85% |
| 内存严重 | > 95% | 严重 | 内存使用率超过 95% |
| 负载过高 | > 核心数×2 | 警告 | 系统负载异常 |
| SELinux 开启 | Enforcing | 信息 | 安全加固项 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含系统信息采集
```

### 快速检查

```bash
./inspect.sh -m quick
# 仅采集核心系统状态
```

### 导出 JSON

```bash
./inspect.sh -f json -o /tmp/sysinfo.json
# 用于监控系统集成
```

---

## 与其他模块的关系

```
系统信息采集
    │
    ├── 触发: 磁盘告警（内存不足可能导致）
    ├── 触发: 进程告警（CPU 负载分析）
    ├── 触发: 网络告警（带宽分析）
    │
    └── 依赖: 其他模块的上下文信息
```

---

## 故障排查

**Q: CPU 使用率显示 0% 或异常值**

```bash
# 检查 /proc/stat 权限
ls -la /proc/stat
cat /proc/stat | head -5

# 手动计算 CPU 使用率
top -bn1 | grep "Cpu(s)"
```

**Q: 内存信息不准确**

```bash
# 检查 /proc/meminfo
cat /proc/meminfo | grep -E "MemTotal|MemAvailable|MemFree"

# 计算公式: (MemTotal - MemAvailable) / MemTotal * 100
```

**Q: 虚拟化检测失败**

```bash
# 手动检测
systemd-detect-virt
cat /sys/class/dmi/id/product_name
dmidecode -s system-product-name 2>/dev/null || echo "需要 root 权限"
```

---

*最后更新: 2026-06-11*