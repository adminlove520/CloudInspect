# 09 - Rootkit 检测

**Rootkit 特征库检测模块**

---

## 功能说明

Rootkit 检测模块使用特征库检测主机上的 Rootkit 入侵，包括：
- LKM (Loadable Kernel Module) Rootkit
- 文件级 Rootkit 特征
- 隐藏进程检测
- 隐藏网络连接检测

**注意**: 此模块仅在 `emergency` 和 `full` 模式下运行。

---

## 检测内容

### LKM Rootkit 检测

| 检测项 | 说明 |
|---|---|
| 可疑内核模块 | 检查未知的 .ko 模块 |
| 隐藏模块 | 检查 /proc/modules 中隐藏的模块 |
| 模块签名 | 检查可疑的模块文件名 |

### 文件级 Rootkit 检测

| 检测项 | 说明 |
|---|---|
| 替换的系统命令 | 检查被篡改的 ps, ls, netstat 等 |
| 可疑二进制文件 | 检测已知的恶意程序特征 |
| 敏感目录检查 | 检查 /lib, /usr/lib 下的可疑文件 |

### Rootkit 特征库

CloudInspect 内置以下 Rootkit 特征：

| 特征名 | 类型 | 说明 |
|---|---|---|
| diamorphine | LKM | Linux Rootkit |
| reptilian | LKM | Linux Rootkit |
| Azazel | LKM | Linux Rootkit |
| jynx2 | LKM | Linux Rootkit |
| adore-ng | LKM | 经典 Linux Rootkit |
| knark | LKM | 经典 Linux Rootkit |

### 隐藏检测

| 检测项 | 方法 |
|---|---|
| 隐藏进程 | 对比 /proc 和 ps 输出 |
| 隐藏网络 | 对比 /proc/net 和 ss/netstat 输出 |
| 隐藏文件 | 检查可疑的隐藏文件/目录 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  🦠 Rootkit 检测                         │
├─────────────────────────────────────────┤
│  LKM 检查:                                │
│  ├─ 已加载模块: 45 个                      │
│  ├─ 可疑模块: 0 个                        │
│  └─ 状态: 未发现异常                      │
│                                         │
│  文件检查:                                │
│  ├─ 系统命令: 正常                        │
│  ├─ 敏感目录: 正常                        │
│  └─ 状态: 未发现异常                      │
│                                         │
│  隐藏检测:                                │
│  ├─ 隐藏进程: 未发现                      │
│  ├─ 隐藏网络: 未发现                      │
│  └─ 状态: 未发现异常                      │
│                                         │
│  ⚠️ Rootkit 检测完成                       │
│  └─ 建议使用 rkhunter 进行深度扫描         │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "rootkit": {
    "lkm_check": {
      "loaded_modules": 45,
      "suspicious_modules": [],
      "status": "ok"
    },
    "file_check": {
      "modified_commands": [],
      "suspicious_files": [],
      "status": "ok"
    },
    "hidden_check": {
      "hidden_processes": 0,
      "hidden_network": 0,
      "status": "ok"
    },
    "signatures_matched": [],
    "issues": []
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 可疑内核模块 | 发现未知模块 | 严重 | 可能是 Rootkit |
| 替换系统命令 | ps/ls/netstat 被修改 | 严重 | 可能是 Rootkit |
| 隐藏进程 | /proc 与 ps 不一致 | 严重 | 可能是 Rootkit |
| 隐藏网络 | /proc/net 与 ss 不一致 | 严重 | 可能是 Rootkit |
| 特征匹配 | 匹配已知 Rootkit 特征 | 严重 | 确认被感染 |

---

## 使用场景

### 应急排查

```bash
# 完整 Rootkit 检测（30-60 分钟）
./inspect.sh -m emergency

# 或 Bash 版本
./inspect.sh -m emergency
```

### 完全扫描

```bash
# 最深度扫描（60+ 分钟）
./inspect.sh -m full
```

### 手动检测

```bash
# 1. 检查内核模块
lsmod
cat /proc/modules

# 2. 检查可疑的模块名
grep -E "hide|root|kit|inject|hook" /proc/modules

# 3. 检查系统命令完整性
rpm -Va 2>/dev/null | grep -E "^[SM5]." | head -20
# 或
debsums -a 2>/dev/null | grep -E "^[SM5]." | head -20

# 4. 使用 rkhunter（需安装）
rkhunter --check --skip-keypress

# 5. 使用 chkrootkit（需安装）
chkrootkit
```

---

## 配合工具

### rkhunter

```bash
# 安装
yum install rkhunter    # RHEL/CentOS
apt install rkhunter     # Debian/Ubuntu

# 更新特征库
rkhunter --update

# 检测
rkhunter --check --skip-keypress

# 查看报告
cat /var/log/rkhunter/rkhunter.log
```

### chkrootkit

```bash
# 安装
yum install chkrootkit  # RHEL/CentOS
apt install chkrootkit   # Debian/Ubuntu

# 检测
chkrootkit

# 查看详细输出
chkrootkit -v
```

---

## 故障排查

**Q: 发现可疑内核模块**

```bash
# 1. 查看模块详情
lsmod | grep suspicious_module

# 2. 查看模块信息
modinfo suspicious_module

# 3. 查看模块文件
cat /sys/module/suspicious_module/holders 2>/dev/null

# 4. 如果确认是恶意模块
rmmod suspicious_module

# 5. 防止模块加载
echo "blacklist suspicious_module" >> /etc/modprobe.d/blacklist.conf
```

**Q: 发现系统命令被修改**

```bash
# 1. 确认文件哈希
md5sum /bin/ps

# 2. 重新安装包
yum reinstall procps-ng  # RHEL/CentOS
apt-get reinstall procps  # Debian/Ubuntu

# 3. 检查文件来源
rpm -qf /bin/ps
dpkg -S /bin/ps
```

**Q: 检测到隐藏进程**

```bash
# 1. 交叉验证
ps aux | wc -l
ls /proc | grep "^[0-9]" | wc -l

# 2. 使用 unhide 工具
unhide proc

# 3. 检查内核完整性
cat /proc/self/cmdline
ls -la /proc/self/exe

# 4. 建议立即重装系统或恢复备份
```

---

*最后更新: 2026-06-11*