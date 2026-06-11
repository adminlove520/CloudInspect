# 08 - 后门检测

**常见后门类型检测模块**

---

## 功能说明

后门检测模块检测主机上常见的入侵后门，包括：
- LD_PRELOAD 后门
- SSH 后门（wrapper）
- 计划任务后门
- 隐藏用户后门
- 网络后门
- 敏感文件后门

---

## 检测的后门类型

### 1. LD_PRELOAD 后门

| 检测项 | 说明 |
|---|---|
| LD_PRELOAD 环境变量 | 检查全局环境变量 |
| /etc/ld.so.preload | 检查预加载库文件 |
| 可疑 .so 文件 | 检查 /etc 下的可疑动态库 |

**说明**: LD_PRELOAD 是一种常见的后门技术，通过预加载恶意动态库来劫持系统函数。

### 2. SSH Wrapper 后门

| 检测项 | 说明 |
|---|---|
| SSH wrapper 脚本 | 检查 /usr/sbin/sshd 是否被替换 |
| 伪造 sshd | 检查可疑的 sshd 二进制文件 |
| 密钥后门 | 检查 /root/.ssh/authorized_keys |

**说明**: SSH wrapper 后门通过替换正常的 sshd 来记录明文密码。

### 3. 计划任务后门

| 检测项 | 说明 |
|---|---|
| 可疑 cron | 检测境外下载、base64 等 |
| 可疑 at 任务 | 检查 at 队列 |
| 系统定时任务 | 检测 /etc/cron* 下的可疑任务 |

### 4. 隐藏用户后门

| 检测项 | 说明 |
|---|---|
| UID 0 后门 | 检查非 root 的 UID 0 用户 |
| 隐藏用户 | 检查以 `.` 开头的用户名 |
| 可疑系统账户 | 无 home 或 shell 的账户 |

### 5. 网络后门

| 检测项 | 说明 |
|---|---|
| 监听异常端口 | 检测非标准端口的监听服务 |
| 反向 shell | 检测对外连接的可疑进程 |
| 端口复用 | 检测隐藏的端口监听 |
| 可疑网络连接 | 检测境外 IP 连接 |

### 6. 敏感文件后门

| 检测项 | 说明 |
|---|---|
| 可疑脚本 | 检查 /tmp, /var/tmp 下的脚本 |
| 恶意二进制 | 检测已知的恶意程序特征 |
| 计划任务脚本 | 检查 cron 调用的脚本 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  🔍 后门检测                              │
├─────────────────────────────────────────┤
│  LD_PRELOAD 检查:                         │
│  ├─ ✓ LD_PRELOAD 未设置                   │
│  ├─ ✓ /etc/ld.so.preload 不存在          │
│  └─ ✓ 无可疑预加载库                      │
│                                         │
│  SSH 后门检查:                            │
│  ├─ ✓ sshd 未被篡改                       │
│  ├─ ✓ 无可疑 sshd wrapper                │
│  └─ ✓ authorized_keys 正常              │
│                                         │
│  ⚠️ 发现 1 个可疑项:                       │
│  └─ /tmp/.hidden_script (已删除)          │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "backdoor": {
    "ld_preload": {
      "env_set": false,
      "preload_exists": false,
      "suspicious_libs": [],
      "status": "ok"
    },
    "ssh_wrapper": {
      "sshd_modified": false,
      "wrapper_detected": false,
      "status": "ok"
    },
    "cron_backdoor": {
      "suspicious_crons": [],
      "status": "ok"
    },
    "hidden_user": {
      "uid0_extras": [],
      "hidden_users": [],
      "status": "ok"
    },
    "network_backdoor": {
      "suspicious_listen": [],
      "reverse_shells": [],
      "status": "ok"
    },
    "issues": []
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| LD_PRELOAD 设置 | 发现 LD_PRELOAD | 严重 | 可能是后门 |
| /etc/ld.so.preload 存在 | 文件存在 | 严重 | 典型后门特征 |
| SSH wrapper 检测 | 发现 wrapper | 严重 | 记录密码的后门 |
| 隐藏用户检测 | 发现隐藏用户 | 严重 | 入侵者账户 |
| 可疑网络连接 | 连接境外 IP | 严重 | 可能外传数据 |
| 可疑 cron | 发现境外下载 | 严重 | 可能是下载器 |

---

## 使用场景

### 日常巡检（routine）

```bash
./inspect.sh -m routine
# 包含基础后门检测
```

### 应急排查（emergency）

```bash
./inspect.sh -m emergency
# 包含完整后门检测 + Rootkit 检测
```

### 手动检测

```bash
# 检查 LD_PRELOAD 后门
echo $LD_PRELOAD
cat /etc/ld.so.preload 2>/dev/null || echo "不存在"
ls -la /etc/*.so 2>/dev/null

# 检查 SSH wrapper
file /usr/sbin/sshd
ls -la /usr/sbin/sshd
md5sum /usr/sbin/sshd

# 检查隐藏用户
cat /etc/passwd | grep -v "^root:"
awk -F: '($3==0 && $1!="root") {print $1}' /etc/passwd

# 检查网络后门
ss -tlnp
netstat -tlnp
```

---

## 故障排查

**Q: 发现 LD_PRELOAD 后门**

```bash
# 1. 查看 LD_PRELOAD 值
echo $LD_PRELOAD

# 2. 检查预加载文件
cat /etc/ld.so.preload

# 3. 分析恶意库
file /path/to/malicious.so
strings /path/to/malicious.so | head -20

# 4. 清除后门
unset LD_PRELOAD
rm /etc/ld.so.preload
rm /path/to/malicious.so

# 5. 检查是否还有其他后门
./inspect.sh -m emergency
```

**Q: 发现 SSH wrapper 后门**

```bash
# 1. 检查 sshd 是否被替换
ls -la /usr/sbin/sshd
file /usr/sbin/sshd

# 2. 查看 sshd 内容（如果是脚本）
head -20 /usr/sbin/sshd

# 3. 恢复正常的 sshd
yum reinstall openssh-server  # RHEL/CentOS
# 或
apt-get reinstall openssh-server  # Debian/Ubuntu

# 4. 更改 SSH 密码
passwd root
```

**Q: 发现隐藏用户**

```bash
# 1. 查看所有用户
cat /etc/passwd

# 2. 查看 UID 0 用户
awk -F: '($3==0) {print}' /etc/passwd

# 3. 删除隐藏用户
userdel suspicious_user

# 4. 检查用户文件
cat /etc/shadow | grep suspicious_user
```

---

*最后更新: 2026-06-11*