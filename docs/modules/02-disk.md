# 02 - 磁盘状态检测

**磁盘使用率、Inode、大文件检测模块**

---

## 功能说明

磁盘状态模块检测主机的磁盘健康状态，包括：
- 文件系统使用率
- Inode 使用率
- 大文件扫描
- 磁盘 IO 状态

---

## 检测内容

### 文件系统使用率

| 检测项 | 来源 | 说明 |
|---|---|---|
| 文件系统 | `df -h` | 挂载点 |
| 总容量 | `df` | 总空间 |
| 已用 | `df` | 已使用空间 |
| 可用 | `df` | 剩余空间 |
| 使用率 | `df` | 百分比 |

### Inode 使用率

| 检测项 | 来源 | 说明 |
|---|---|---|
| Inode 总数 | `df -i` | 总 Inode 数 |
| 已用 Inode | `df -i` | 已使用 Inode |
| 使用率 | `df -i` | 百分比 |

**注意**: Inode 耗尽会导致 "No space left on device"，即使磁盘空间充足。

### 大文件扫描

扫描指定目录下的超大文件，默认扫描：
- `/var` - 日志文件
- `/home` - 用户文件
- `/opt` - 应用目录
- `/usr/local` - 手动安装的软件

| 阈值 | 默认值 | 说明 |
|---|---|---|
| 大文件阈值 | 100MB | 超过此大小报告 |
| 扫描深度 | 3 层 | 目录递归深度 |
| 忽略目录 | `/proc`, `/sys`, `/dev` | 系统目录 |

---

## 检测阈值

| 指标 | 警告 | 严重 | 说明 |
|---|---|---|---|
| 磁盘使用率 | 85% | 95% | 单个分区超过阈值告警 |
| Inode 使用率 | 85% | 95% | 单个分区超过阈值告警 |
| 大文件 | > 100MB | > 1GB | 超过阈值报告 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  💾 磁盘状态                              │
├─────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐             │
│  │ 根分区    │ │ /home    │             │
│  │ 已用 62%  │ │ 已用 45%  │             │
│  │ 可用 120G │ │ 可用 200G │             │
│  └──────────┘ └──────────┘             │
│                                         │
│  ⚠️ /var/log 使用率 82% (接近阈值)        │
│                                         │
│  大文件 (Top 5):                         │
│  - /var/log/nginx/access.log (2.1GB)   │
│  - /var/log/messages (1.5GB)            │
│  - /opt/backup/db.tar.gz (800MB)        │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "disk": {
    "filesystems": [
      {
        "mount": "/",
        "total_gb": 500,
        "used_gb": 310,
        "available_gb": 170,
        "usage_pct": 62,
        "status": "ok"
      },
      {
        "mount": "/home",
        "total_gb": 1000,
        "used_gb": 450,
        "available_gb": 530,
        "usage_pct": 45,
        "status": "ok"
      }
    ],
    "inodes": [
      {
        "mount": "/",
        "total": 32768000,
        "used": 8923456,
        "usage_pct": 27,
        "status": "ok"
      }
    ],
    "large_files": [
      {
        "path": "/var/log/nginx/access.log",
        "size_gb": 2.1,
        "modified": "2026-06-11"
      }
    ],
    "issues": [
      {
        "level": "warning",
        "mount": "/var/log",
        "usage_pct": 82,
        "desc": "/var/log 使用率 82%，接近 85% 阈值"
      }
    ]
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 处理建议 |
|---|---|---|---|
| 磁盘空间不足 | 使用率 > 85% | 警告 | 清理日志或扩展磁盘 |
| 磁盘空间严重 | 使用率 > 95% | 严重 | 立即清理，否则服务中断 |
| Inode 不足 | 使用率 > 85% | 警告 | 清理小文件 |
| 大文件占用 | 文件 > 100MB | 信息 | 评估是否可清理 |
| 超大文件 | 文件 > 1GB | 警告 | 建议压缩或清理 |

---

## 使用场景

### 日常巡检

```bash
./inspect.sh -m routine
# 自动包含磁盘检测
```

### 排查磁盘问题

```bash
# 快速查看磁盘使用率
df -h

# 查看 Inode 使用率
df -i

# 查找大文件
find /var -type f -size +100M -ls 2>/dev/null
```

### 深度扫描（包含超多文件）

```bash
./inspect.sh -m full
# 扫描更多目录和更深的层级
```

---

## 配置说明

在 `config/default.yaml` 中调整阈值：

```yaml
thresholds:
  disk_warn: 85       # 磁盘警告阈值
  disk_crit: 95       # 磁盘严重阈值
  inode_warn: 85      # Inode 警告阈值

scan:
  large_file_size: "100M"   # 大文件阈值
  search_paths:             # 扫描路径
    - /var
    - /home
    - /opt
    - /usr/local
```

---

## 故障排查

**Q: 磁盘空间足够但写入失败**

```bash
# 检查 Inode 使用率
df -i

# 查找 Inode 消耗最多的目录
for i in /*; do echo -n "$i: "; find "$i" -maxdepth 1 2>/dev/null | wc -l; done
```

**Q: 日志文件占用大量空间**

```bash
# 查找最大的日志文件
find /var/log -type f -size +10M -ls

# 查看日志目录大小
du -sh /var/log/*

# 清理旧日志（谨慎操作）
# journalctl --vacuum-time=7d
# truncate -s 0 /var/log/messages
```

**Q: 大文件扫描太慢**

```bash
# 跳过某些目录
# 编辑 config/default.yaml
scan:
  exclude_paths:
    - /var/cache
    - /tmp
```

---

*最后更新: 2026-06-11*