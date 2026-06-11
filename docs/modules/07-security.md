# 07 - 安全基线检测

**系统安全配置检查模块**

---

## 功能说明

安全基线模块检测主机的安全配置，包括：
- SSH 配置检查
- 账户安全检查
- SUID/SGID 文件检查
- 可写文件检查
- 密码策略检查

---

## 检测内容

### SSH 安全配置

| 检查项 | 安全值 | 说明 |
|---|---|---|
| SSH 协议版本 | Protocol 2 | 禁止 SSHv1 |
| root 登录 | PermitRootLogin no | 禁止 root 直接登录 |
| 密码认证 | PasswordAuthentication no | 禁止密码认证 |
| 公钥认证 | PubkeyAuthentication yes | 启用公钥认证 |
| 空密码 | PermitEmptyPasswords no | 禁止空密码 |
| SSH 空闲超时 | ClientAliveInterval 300 | 建议设置 |

### 账户安全

| 检查项 | 说明 | 安全要求 |
|---|---|---|
| 空密码账户 | /etc/shadow 密码字段为空 | 不允许 |
| UID 0 账户 | UID=0 的非 root 账户 | 严重风险 |
| 可疑账户 | 无 home 目录的系统账户 | 需确认 |
| 弱密码策略 | 密码复杂度要求 | 建议启用 |

### SUID/SGID 文件

| 说明 | 命令 |
|---|---|
| SUID 文件 | `find / -perm -4000 -ls 2>/dev/null` |
| SGID 文件 | `find / -perm -2000 -ls 2>/dev/null` |
| 可疑 SUID | 已知后门程序（nmap, python 等被利用） |

### 可写文件检查

| 路径 | 说明 | 风险 |
|---|---|---|
| `/etc/passwd` 可写 | 任何人可修改用户 | 高 |
| `/etc/shadow` 可写 | 任何人可修改密码 | 高 |
| `/etc/group` 可写 | 任何人可修改组 | 中 |
| `/etc/sudoers` 可写 | 任何人可修改 sudo | 高 |
| `/etc/crontab` 可写 | 任何人可添加 cron | 高 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  🔒 安全基线                              │
├─────────────────────────────────────────┤
│  SSH 配置:                                │
│  ├─ ✓ Protocol 2                         │
│  ├─ ✓ PermitRootLogin no                 │
│  ├─ ✓ PasswordAuthentication no          │
│  └─ ✓ PubkeyAuthentication yes           │
│                                         │
│  账户安全:                                 │
│  ├─ ✓ 无空密码账户                         │
│  ├─ ✓ 无多余 UID 0 账户                    │
│  └─ ⚠️ 存在 3 个可登录普通账户              │
│                                         │
│  SUID/SGID:                              │
│  ├─ /usr/bin/passwd (SUID)               │
│  ├─ /usr/bin/sudo (SUID)                 │
│  └─ ⚠️ /usr/bin/newgrp (SUID, 可疑)      │
│                                         │
│  ⚠️ 发现 2 个安全风险                       │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "security": {
    "ssh": {
      "protocol": "2",
      "root_login": false,
      "password_auth": false,
      "pubkey_auth": true,
      "status": "ok"
    },
    "accounts": {
      "empty_password": false,
      "uid0_accounts": ["root"],
      "login_users": 3,
      "status": "ok"
    },
    "suid_files": [
      "/usr/bin/passwd",
      "/usr/bin/sudo",
      "/usr/bin/newgrp"
    ],
    "writable_files": [],
    "issues": [
      {
        "level": "info",
        "module": "security",
        "desc": "存在 3 个可登录普通账户，建议审查"
      }
    ]
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| SSH root 登录开启 | PermitRootLogin yes | 严重 | 建议禁用 |
| 空密码账户 | 存在空密码用户 | 严重 | 立即修复 |
| 多余 UID 0 | 存在非 root 的 UID 0 | 严重 | 立即检查 |
| 敏感文件可写 | passwd/shadow/sudoers 可写 | 严重 | 立即修复 |
| 可疑 SUID | 未知程序有 SUID | 警告 | 需审查 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含安全基线检测
```

### 快速安全检查

```bash
# SSH 配置
sshd -T | grep -i "permitrootlogin\|passwordauth"

# 检查空密码账户
awk -F: '($2=="") {print $1}' /etc/shadow

# 检查 UID 0
awk -F: '($3==0) {print $1}' /etc/passwd

# 检查 SUID
find / -perm -4000 -ls 2>/dev/null | head -20
```

### 加固建议

```bash
# 禁止 root SSH 登录
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl restart sshd

# 设置密码策略
# 编辑 /etc/security/pwquality.conf

# 检查 sudoers
visudo
```

---

## 故障排查

**Q: 发现空密码账户**

```bash
# 1. 列出所有空密码账户
awk -F: '($2=="") {print $1}' /etc/shadow

# 2. 设置密码（如果需要保留账户）
passwd username

# 3. 如果不需要，锁定账户
passwd -l username

# 4. 或者删除账户
userdel username
```

**Q: 发现可疑 SUID 文件**

```bash
# 1. 查看文件详情
ls -la /path/to/suspicious

# 2. 检查文件类型
file /path/to/suspicious

# 3. 查看文件内容（如果是脚本）
head -20 /path/to/suspicious

# 4. 检查哈希
sha256sum /path/to/suspicious

# 5. 如果确认是后门
chmod -s /path/to/suspicious
rm /path/to/suspicious
```

---

*最后更新: 2026-06-11*