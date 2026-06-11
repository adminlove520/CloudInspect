# 10 - 日志分析

**系统日志分析模块**

---

## 功能说明

日志分析模块检测系统日志中的异常事件，包括：
- 登录失败记录
- SSH 异常登录
- sudo 使用记录
- 系统错误和警告
- 硬件错误
- OOM 事件

---

## 检测内容

### 登录失败分析

| 日志来源 | 说明 |
|---|---|
| `/var/log/secure` | RHEL/CentOS 登录日志 |
| `/var/log/auth.log` | Debian/Ubuntu 登录日志 |
| `/var/log/btmp` | 失败登录记录（lastb） |

| 检测规则 | 说明 |
|---|---|
| 短时间内多次失败 | 5 分钟内 > 10 次失败 |
| 境外 IP 登录失败 | 非国内 IP 登录失败 |
| 异常用户名尝试 | 尝试 admin, root, test 等 |

### SSH 异常检测

| 检测项 | 说明 |
|---|---|
| 暴力破解痕迹 | 短时间内大量失败 |
| 成功登录（异常时间） | 凌晨 2-6 点登录 |
| 成功登录（异常 IP） | 境外 IP 登录成功 |
| Root 登录成功 | root 直接登录 |

### Sudo 使用记录

| 检测项 | 说明 |
|---|---|
| sudo 失败 | 权限不足 |
| 可疑 sudo 命令 | wget, curl, bash 等 |
| 大量 sudo 使用 | 短时间内多次 |

### 系统错误

| 日志来源 | 检测内容 |
|---|---|
| `/var/log/messages` | 内核、硬件错误 |
| `/var/log/syslog` | 系统错误 |
| dmesg | 引导和硬件消息 |
| journalctl | systemd 日志 |

| 检测类型 | 说明 |
|---|---|
| OOM (Out of Memory) | 内存耗尽杀进程 |
| 硬件错误 | CPU、内存、磁盘错误 |
| 网络错误 | 网卡、路由错误 |
| 文件系统错误 | EXT4/XFS 等错误 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  📋 日志分析                              │
├─────────────────────────────────────────┤
│  登录统计:                                │
│  ├─ 今日登录: 45 次                       │
│  ├─ 失败登录: 12 次                       │
│  └─ 境外登录: 0 次                        │
│                                         │
│  SSH 分析:                                │
│  ├─ 成功登录: 33 次                       │
│  ├─ 失败登录: 12 次                       │
│  └─ Root 登录: 1 次 (本地)                │
│                                         │
│  ⚠️ 发现可疑事件:                          │
│  └─ 10.0.0.100 在 5 分钟内 15 次登录失败  │
│     可能正在暴力破解                       │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "log_analysis": {
    "login_stats": {
      "total_logins": 45,
      "failed_logins": 12,
      "successful_logins": 33,
      "foreign_logins": 0
    },
    "ssh_events": [
      {
        "time": "2026-06-11 03:15:22",
        "user": "root",
        "ip": "10.0.0.100",
        "status": "failed",
        "desc": "密码错误"
      }
    ],
    "sudo_events": [],
    "system_errors": [],
    "issues": [
      {
        "level": "warning",
        "module": "log_analysis",
        "desc": "10.0.0.100 在 5 分钟内 15 次登录失败"
      }
    ]
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 暴力破解 | 5 分钟内 > 10 次失败 | 严重 | 可能正在入侵 |
| 境外成功登录 | 境外 IP 登录成功 | 严重 | 需确认合法性 |
| 异常时间登录 | 凌晨 2-6 点登录 | 警告 | 需确认 |
| OOM 事件 | 发生 OOM | 警告 | 内存可能不足 |
| 可疑 sudo | 执行了可疑命令 | 警告 | 需审查 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含日志分析
```

### 查看登录历史

```bash
# 查看成功登录
last

# 查看失败登录
lastb

# 查看特定用户登录
last root

# 查看某个 IP 的登录
last | grep 10.0.0.100

# 查看 SSH 登录
last | grep ssh
```

### 查看日志

```bash
# 查看认证日志
cat /var/log/secure  # RHEL/CentOS
cat /var/log/auth.log  # Debian/Ubuntu

# 查找登录失败
grep "Failed password" /var/log/secure | tail -20

# 查找 SSH 登录
grep "sshd" /var/log/secure | tail -20

# 查看 sudo 使用
grep "sudo" /var/log/secure | tail -20

# 查看系统错误
grep -i "error\|oom\|fail" /var/log/messages | tail -20
```

---

## 故障排查

**Q: 发现暴力破解攻击**

```bash
# 1. 查看攻击者 IP
grep "Failed password" /var/log/secure | awk '{print $11}' | sort | uniq -c | sort -rn | head -10

# 2. 封禁 IP（使用 firewalld）
firewall-cmd --permanent --add-rich-rule='rule family="ipv4" source address="10.0.0.100" reject'
firewall-cmd --reload

# 3. 或使用 iptables
iptables -A INPUT -s 10.0.0.100 -j DROP

# 4. 检查是否有成功登录
grep "Accepted" /var/log/secure | grep 10.0.0.100

# 5. 如果有成功登录，立即更改密码
passwd username
```

**Q: 发现境外登录**

```bash
# 1. 查看登录详情
grep "Accepted" /var/log/secure | grep "境外IP"

# 2. 确认是否合法
# 联系用户确认是否本人操作

# 3. 如果非本人
# - 立即断开该会话
# - 更改密码
# - 封禁该 IP
# - 检查该 IP 访问了哪些内容
```

**Q: 发现 OOM 事件**

```bash
# 1. 查看 OOM 详情
dmesg | grep -i "out of memory"
cat /var/log/messages | grep -i "out of memory"

# 2. 查看被杀死的进程
dmesg | grep -i "killed process"

# 3. 分析原因
# - 内存泄漏？
# - 配置的内存限制太小？
# - 是否有恶意进程消耗内存？

# 4. 解决方案
# - 增加内存
# - 调整 swap
# - 优化程序内存使用
# - 使用 OOM killer 配置
```

---

*最后更新: 2026-06-11*