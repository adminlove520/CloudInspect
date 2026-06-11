# 命令行参数详解

**CloudInspect 所有命令行参数完整说明**

---

## 参数概览

| 参数 | 说明 | 默认值 |
|---|---|---|
| `-o, --output FILE` | 指定报告输出路径 | 自动生成 |
| `-f, --format FORMAT` | 输出格式 | `html` |
| `-m, --mode MODE` | 工作模式 | `routine` |
| `-v, --verbose` | 详细日志 | 关闭 |
| `-q, --quiet` | 静默模式 | 关闭 |
| `-h, --help` | 显示帮助 | - |
| `--version` | 显示版本 | - |

---

## 详细说明

### `-o, --output FILE`

指定报告输出路径。

```bash
# 指定完整路径
./inspect.sh -o /tmp/my_report.html

# 指定目录（自动生成文件名）
./inspect.sh -o /tmp/
```

**注意**:
- 如果指定目录，文件名自动生成为 `inspect_<hostname>_<datetime>.<format>`
- 如果是文件路径，直接使用指定路径

**示例**:
```bash
# 输出到 /tmp 目录
./inspect.sh -o /tmp/

# 生成的文件: /tmp/inspect_web-server-01_20260611_103000.html

# 输出到指定文件
./inspect.sh -o /tmp/my_report.json
```

---

### `-f, --format FORMAT`

指定输出格式。

| 格式 | Bash | Python | 说明 |
|---|---|---|---|
| `html` | ✅ | ✅ | HTML 报告（默认） |
| `json` | ✅ | ✅ | JSON 结构化数据 |
| `md` | ✅ | ✅ | Markdown 纯文本 |
| `docx` | ❌ | ✅ | Word 文档（Python 专属） |

**示例**:
```bash
# HTML（默认）
./inspect.sh -f html

# JSON
./inspect.sh -f json -o /tmp/report.json

# Markdown
./inspect.sh -f md -o /tmp/report.md

# DOCX（仅 Python）
python inspect.py -f docx -o /tmp/report.docx
```

---

### `-m, --mode MODE`

指定工作模式。

| 模式 | 耗时 | 覆盖模块 | 适用场景 |
|---|---|---|---|
| `routine` | 5-15 分钟 | 核心模块（不含 Rootkit/Webshell） | 日常巡检 |
| `emergency` | 30-60 分钟 | 全部 12 个模块 | 应急排查 |
| `quick` | 1-3 分钟 | 核心系统状态 | 快速检查 |
| `full` | 60+ 分钟 | 全部 + 深度扫描 | 全面体检 |

**示例**:
```bash
# 日常巡检（默认）
./inspect.sh

# 等价于
./inspect.sh -m routine

# 应急排查
./inspect.sh -m emergency

# 快速扫描
./inspect.sh -m quick

# 完全扫描
./inspect.sh -m full
```

---

### `-v, --verbose`

启用详细日志输出。

**示例**:
```bash
# 显示详细的执行过程
./inspect.sh -v

# 组合使用
./inspect.sh -m emergency -v -o /tmp/emergency.json
```

**输出示例**:
```
[INFO] 检测到操作系统: Huawei Cloud EulerOS 2.0 (rhel)
[DEBUG] OS_FAMILY=rhel, OS_ID=HCE
[DEBUG] Loading config from: config/default.yaml
[INFO] 报告将保存至: /tmp/cloudinspect/inspect_20260611_103000.html
[DEBUG] CPU threshold: 80, MEM threshold: 85
[ 1/12] (  8%) 采集系统基本信息...
[DEBUG] hostname=web-server-01, ip=10.0.0.10
[DEBUG] CPU usage=45%, memory=62%
...
```

---

### `-q, --quiet`

启用静默模式，不显示进度和日志。

**示例**:
```bash
# 仅输出最终结果
./inspect.sh -q

# 适合定时任务
crontab -e
0 2 * * * /opt/cloudinspect/inspect.sh -q -o /tmp/reports/
```

**注意**: 静默模式下仍然会输出最终报告路径和退出码。

---

### `-h, --help`

显示帮助信息。

```bash
./inspect.sh -h
```

**输出**:
```
CloudInspect v1.1 - 云主机安全巡检工具

用法: inspect.sh [选项]

选项:
  -o, --output FILE   指定报告输出路径
  -f, --format FORMAT 输出格式: html (默认) | json | md
  -m, --mode MODE     工作模式: routine | emergency | quick | full
  -v, --verbose       详细日志
  -q, --quiet         静默模式
  -h, --help          显示帮助

模式说明:
  routine    日常巡检（推荐，5-15分钟）
  emergency  应急排查（深度，30-60分钟）
  quick      快速扫描（1-3分钟）
  full       完全扫描（60分钟+）

示例:
  inspect.sh                         # 默认 HTML 报告
  inspect.sh -m emergency -f html    # 应急排查模式
  inspect.sh -f json -o /tmp/r.json  # 输出 JSON
  inspect.sh --mode quick --verbose  # 快速详细模式

退出码:
  0 - 正常（无警告/无严重）
  1 - 有警告
  2 - 有严重告警/脚本错误
```

---

### `--version`

显示版本信息。

```bash
./inspect.sh --version
```

**输出**:
```
CloudInspect v1.1
```

---

## 组合使用示例

### 日常巡检（完整参数）

```bash
./inspect.sh -m routine -f html -o /tmp/report.html -v
```

### 应急排查（JSON 输出）

```bash
./inspect.sh -m emergency -f json -o /tmp/emergency.json -v
```

### 定时任务（静默模式）

```bash
# 每天凌晨2点执行
0 2 * * * /opt/cloudinspect/inspect.sh -q -o /tmp/reports/ 2>&1
```

### 快速检查（快速模式）

```bash
./inspect.sh -m quick -v
```

### 完全扫描（深夜执行）

```bash
# 深夜执行完全扫描，输出到指定目录
0 3 * * 0 /opt/cloudinspect/inspect.sh -m full -f html -o /tmp/full-scan/ -q
```

---

## 环境变量

CloudInspect 支持以下环境变量：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `REPORT_DIR` | 报告输出目录 | `/tmp/cloudinspect` |
| `MODE` | 工作模式 | `routine` |
| `OUTPUT_FORMAT` | 输出格式 | `html` |
| `VERBOSE` | 详细日志 | `0` |
| `QUIET` | 静默模式 | `0` |

**示例**:
```bash
# 使用环境变量
export REPORT_DIR="/opt/reports"
export MODE="emergency"
./inspect.sh
```

---

## 配置文件

通过 `config/default.yaml` 可以设置默认阈值和扫描参数：

```yaml
thresholds:
  cpu_warn: 80        # CPU 警告阈值
  cpu_crit: 90        # CPU 严重阈值
  mem_warn: 85        # 内存警告阈值
  mem_crit: 95        # 内存严重阈值
  disk_warn: 85       # 磁盘警告阈值

scan:
  top_n: 10           # TOP N 显示数量
  recent_days: 7      # 近期文件天数
  large_file_size: "100M"  # 大文件阈值
```

详情请查看 [配置说明](configuration.md)。

---

*最后更新: 2026-06-11*