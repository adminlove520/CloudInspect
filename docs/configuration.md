# 配置说明

**CloudInspect 配置文件详解**

---

## 配置文件位置

| 版本 | 配置文件 | 说明 |
|---|---|---|
| Bash | `config/default.yaml` | 默认配置 |
| Python | `config/default.yaml` | 与 Bash 共用 |
| 自定义 | `config/local.yaml` | 用户自定义（覆盖默认） |

---

## 配置结构

```yaml
# CloudInspect 默认配置
# Bash/Python 共用

thresholds:
  cpu_warn: 80        # CPU 警告阈值 (%)
  cpu_crit: 90        # CPU 严重阈值 (%)
  mem_warn: 85        # 内存警告阈值 (%)
  mem_crit: 95        # 内存严重阈值 (%)
  disk_warn: 85       # 磁盘警告阈值 (%)
  disk_crit: 95       # 磁盘严重阈值 (%)
  inode_warn: 85      # Inode 警告阈值 (%)
  swap_warn: 50       # Swap 使用率警告 (%)
  load_factor: 2     # 负载因子 (核心数 × 此值)
  fd_warn: 80         # 文件描述符警告 (%)
  conn_close_wait: 50 # CLOSE_WAIT 连接数警告
  zombie_warn: 0      # 僵尸进程数警告
  crit_offset: 10     # 严重偏移量 (warn + offset = crit)

scan:
  top_n: 10           # TOP N 显示数量
  fd_top_n: 5         # 文件描述符 TOP N
  log_lines: 20        # 日志显示行数
  large_file_size: "100M"  # 大文件阈值
  recent_days: 7      # 近期文件天数
  recent_file_size: "50M"  # 近期大文件阈值
  search_paths:       # 大文件扫描路径
    - /var
    - /home
    - /opt
    - /usr/local

output:
  report_dir: "/tmp/cloudinspect"  # 报告输出目录
  html_theme: "default"            # HTML 主题
  json_indent: 2                   # JSON 缩进
```

---

## 配置项详解

### thresholds - 阈值配置

| 配置项 | 默认值 | 说明 | 建议 |
|---|---|---|---|
| `cpu_warn` | 80 | CPU 使用率警告阈值 | 生产环境建议 80 |
| `cpu_crit` | 90 | CPU 使用率严重阈值 | 可根据业务调整 |
| `mem_warn` | 85 | 内存使用率警告阈值 | 生产环境建议 85 |
| `mem_crit` | 95 | 内存使用率严重阈值 | 接近 100 时系统可能卡死 |
| `disk_warn` | 85 | 磁盘使用率警告阈值 | 建议 85，预留处理时间 |
| `disk_crit` | 95 | 磁盘使用率严重阈值 | 超过 95 服务可能中断 |
| `inode_warn` | 85 | Inode 使用率警告阈值 | 小文件多时注意 |
| `swap_warn` | 50 | Swap 使用率警告阈值 | 高 swap 可能影响性能 |
| `load_factor` | 2 | 负载因子 | 负载 > 核心数 × 此值 告警 |
| `fd_warn` | 80 | 文件描述符使用率警告 | 高并发服务注意 |
| `conn_close_wait` | 50 | CLOSE_WAIT 连接数警告 | 过多可能表示连接泄漏 |
| `zombie_warn` | 0 | 僵尸进程数警告 | 任何僵尸进程都应关注 |
| `crit_offset` | 10 | 严重偏移量 | warn + crit_offset = 严重阈值 |

### scan - 扫描配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `top_n` | 10 | CPU/内存 TOP N 显示数量 |
| `fd_top_n` | 5 | 文件描述符 TOP N 显示数量 |
| `log_lines` | 20 | 日志分析显示行数 |
| `large_file_size` | "100M" | 大文件阈值（超过此值报告） |
| `recent_days` | 7 | 近期文件天数（最近 N 天内修改的文件） |
| `recent_file_size` | "50M" | 近期大文件阈值 |
| `search_paths` | 列表 | 大文件扫描路径 |

### output - 输出配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `report_dir` | `/tmp/cloudinspect` | 报告输出目录 |
| `html_theme` | `default` | HTML 报告主题 |
| `json_indent` | 2 | JSON 缩进空格数 |

---

## 自定义配置

### 创建本地配置

```bash
# 创建 config/local.yaml
cat > config/local.yaml << 'EOF'
thresholds:
  cpu_warn: 70        # 更严格的 CPU 阈值
  mem_warn: 80        # 更严格的内存阈值

scan:
  top_n: 20           # 显示更多 TOP 进程
  large_file_size: "500M"  # 提高大文件阈值
EOF

# 运行时会自动读取 local.yaml 并覆盖默认配置
```

### 优先级

```
命令行参数 > config/local.yaml > config/default.yaml
```

---

## 配置示例

### 高性能服务器配置

```yaml
thresholds:
  cpu_warn: 90
  cpu_crit: 95
  mem_warn: 90
  mem_crit: 98
  disk_warn: 90
  disk_crit: 98
```

### 严格安全配置

```yaml
thresholds:
  cpu_warn: 60
  mem_warn: 70
  disk_warn: 70
  load_factor: 1      # 更严格的负载告警
  zombie_warn: 0      # 任何僵尸进程都告警
```

### 开发环境配置

```yaml
thresholds:
  cpu_warn: 95
  mem_warn: 95
  disk_warn: 95
  swap_warn: 80

scan:
  top_n: 20
  large_file_size: "1G"
  recent_days: 30
```

---

## 环境变量

可通过环境变量覆盖配置：

| 环境变量 | 对应配置 | 说明 |
|---|---|---|
| `CPU_WARN` | `thresholds.cpu_warn` | CPU 警告阈值 |
| `MEM_WARN` | `thresholds.mem_warn` | 内存警告阈值 |
| `DISK_WARN` | `thresholds.disk_warn` | 磁盘警告阈值 |
| `REPORT_DIR` | `output.report_dir` | 报告输出目录 |
| `MODE` | - | 工作模式（routine/emergency/quick/full） |
| `OUTPUT_FORMAT` | - | 输出格式（html/json/md） |

**示例**:
```bash
export CPU_WARN=70
export MEM_WARN=80
./inspect.sh
```

---

## 验证配置

```bash
# 查看当前配置
./inspect.sh -v 2>&1 | grep -E "threshold|config"

# 测试配置加载
python3 -c "
import yaml
with open('config/default.yaml') as f:
    print(yaml.safe_load(f))
"
```

---

*最后更新: 2026-06-11*