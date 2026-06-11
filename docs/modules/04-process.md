# 04 - 进程状态检测

**进程状态、僵尸进程、资源占用分析模块**

---

## 功能说明

进程状态模块检测主机的进程健康状态，包括：
- 僵尸进程检测
- CPU/内存 TOP 进程
- 隐藏进程检测
- 异常进程识别

---

## 检测内容

### 僵尸进程

| 检测项 | 说明 | 正常值 |
|---|---|---|
| 僵尸进程数 | 状态为 Z 的进程 | 0 |
| 僵尸进程列表 | PID、名称、父进程 | - |

**僵尸进程说明**: 僵尸进程是已经结束但未被父进程回收的进程。大量僵尸进程可能表示程序存在 bug 或父进程异常。

### TOP 进程

| 类型 | 说明 | 默认数量 |
|---|---|---|
| CPU TOP | 按 CPU 使用率排序 | 10 |
| 内存 TOP | 按内存使用率排序 | 10 |

### 隐藏进程检测

通过以下方法检测隐藏进程：
1. `/proc` 目录 PID 数量 vs `ps` 输出数量
2. 进程树完整性检查
3. 进程文件描述符检查

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  📊 进程状态                              │
├─────────────────────────────────────────┤
│  CPU TOP 10:                             │
│  ├─ PID 12345 nginx    CPU: 45.2%        │
│  ├─ PID 23456 python   CPU: 23.1%        │
│  └─ ...                                  │
│                                         │
│  内存 TOP 10:                             │
│  ├─ PID 12345 nginx    MEM: 12.5%        │
│  ├─ PID 34567 java     MEM: 8.3%         │
│  └─ ...                                  │
│                                         │
│  ⚠️ 发现 2 个僵尸进程                      │
│  └─ PID 5678, name: old_process          │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "process": {
    "zombie_count": 2,
    "zombies": [
      {"pid": 5678, "name": "old_process", "ppid": 1234}
    ],
    "cpu_top": [
      {"pid": 12345, "name": "nginx", "cpu_pct": 45.2, "mem_pct": 12.5},
      {"pid": 23456, "name": "python", "cpu_pct": 23.1, "mem_pct": 8.3}
    ],
    "mem_top": [
      {"pid": 12345, "name": "nginx", "mem_pct": 12.5},
      {"pid": 34567, "name": "java", "mem_pct": 8.3}
    ],
    "issues": [
      {
        "level": "warning",
        "module": "process",
        "desc": "发现 2 个僵尸进程"
      }
    ]
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 僵尸进程 | 数量 > 0 | 警告 | 存在僵尸进程 |
| CPU 占用过高 | 单进程 > 80% | 警告 | 可能异常 |
| 内存占用过高 | 单进程 > 50% | 警告 | 可能内存泄漏 |
| 隐藏进程 | 检测到差异 | 严重 | 可能被 rootkit 修改 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含进程检测
```

### 排查高 CPU 进程

```bash
# 查看 CPU 使用率最高的进程
top -bn1 | head -20

# 查看具体进程
ps aux --sort=-%cpu | head -10

# 查看进程树
pstree -p
```

### 排查僵尸进程

```bash
# 查看所有僵尸进程
ps aux | grep " Z "

# 查看僵尸进程的父进程
pstree -p $(pgrep -f "zombie_parent")

# 杀死父进程（谨慎）
kill -9 $(pgrep -f "zombie_parent")
```

### 检测隐藏进程

```bash
# 方法1: 对比 /proc 和 ps
ls /proc | grep "^[0-9]" | wc -l
ps aux | wc -l

# 方法2: 使用 chkrootkit（需安装）
chkrootkit -q

# 方法3: 使用 rkhunter（需安装）
rkhunter --check
```

---

## 故障排查

**Q: 发现僵尸进程**

```bash
# 1. 查看僵尸进程详情
ps -ef | grep Z

# 2. 查看父进程
pstree -p $(ps aux | grep " Z " | awk '{print $2}')

# 3. 如果父进程是已终止的程序
#    解决方案：重启服务或杀死父进程
kill -9 $(ps aux | grep " Z " | awk '{print $3}' | head -1)
```

**Q: CPU 占用异常**

```bash
# 1. 找出高 CPU 进程
top -bn1 | head -20

# 2. 查看进程详情
ps -p 12345 -o pid,ppid,cmd,%cpu,%mem

# 3. 查看进程打开的文件
lsof -p 12345

# 4. 查看进程的网络连接
ss -tlnp | grep 12345

# 5. 跟踪系统调用（需要 strace）
strace -p 12345 -c
```

**Q: 检测到隐藏进程**

```bash
# 1. 确认是否误报（高负载系统可能）
uptime

# 2. 使用多个工具交叉验证
ps aux | wc -l
ls /proc | grep "^[0-9]" | wc -l

# 3. 使用 Rootkit 检测工具
./inspect.sh -m emergency
# emergency 模式会调用 Rootkit 检测模块

# 4. 检查内核模块
lsmod
cat /proc/modules | grep -i "hide\|root\|kit"
```

---

*最后更新: 2026-06-11*