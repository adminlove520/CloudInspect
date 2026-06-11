# 快速开始

**CloudInspect 云主机安全巡检工具 - 5分钟上手指南**

---

## 环境要求

| 组件 | Bash 版本 | Python 版本 |
|---|---|---|
| 操作系统 | Linux (任意发行版) | Linux (任意发行版) |
| Shell | Bash 4.0+ | - |
| Python | - | 3.8+ |
| 依赖 | 无 | pyyaml, psutil |

---

## 安装

### Bash 版本（推荐零依赖场景）

```bash
# 下载
git clone https://github.com/adminlove520/CloudInspect.git
cd CloudInspect/bash

# 直接运行
chmod +x inspect.sh
./inspect.sh
```

### Python 版本（功能完整）

```bash
# 下载
git clone https://github.com/adminlove520/CloudInspect.git
cd CloudInspect/python

# 安装依赖
pip install -r requirements.txt

# 运行
python inspect.py
```

---

## 工作模式

### routine - 日常巡检（推荐）

```bash
# Bash
./inspect.sh -m routine

# Python
python inspect.py -m routine
```

- **耗时**: 5-15 分钟
- **覆盖**: 全部核心检测模块（不含 Rootkit/Webshell）
- **适用**: 日常安全巡检、护网行动每日检查

### emergency - 应急排查

```bash
# Bash
./inspect.sh -m emergency

# Python
python inspect.py -m emergency
```

- **耗时**: 30-60 分钟
- **覆盖**: 全部 12 个检测模块
- **适用**: 确认入侵后的深度排查

### quick - 快速扫描

```bash
# Bash
./inspect.sh -m quick

# Python
python inspect.py -m quick
```

- **耗时**: 1-3 分钟
- **覆盖**: 核心系统状态（CPU/内存/磁盘/网络）
- **适用**: 快速了解主机健康状态

### full - 完全扫描

```bash
# Bash
./inspect.sh -m full

# Python
python inspect.py -m full
```

- **耗时**: 60+ 分钟
- **覆盖**: 全部模块 + 深度扫描
- **适用**: 全面体检、重大行动前检查

---

## 输出格式

### HTML 报告（默认）

```bash
./inspect.sh                    # 默认 HTML
./inspect.sh -o /tmp/report.html
```

特点：美观的卡片式设计，带图表和颜色标识，适合日常查看。

### JSON 报告

```bash
./inspect.sh -f json -o /tmp/report.json
```

特点：结构化数据，便于程序处理和自动化集成。

### Markdown 报告

```bash
./inspect.sh -f md -o /tmp/report.md
```

特点：纯文本格式，便于 Git 存档和管理。

### DOCX 报告（Python 专属）

```bash
python inspect.py -f docx -o /tmp/report.docx
```

特点：Word 格式，适合正式报告提交。

---

## 输出示例

```
==============================================
  CloudInspect v1.1 - 云主机安全巡检
  Host: web-server-01
  OS: Huawei Cloud EulerOS 2.0 (HCE)
  Mode: routine
  Time: 2026-06-11 10:30:00
==============================================

[INFO] 检测到操作系统: Huawei Cloud EulerOS 2.0 (rhel)
[INFO] 报告将保存至: /tmp/cloudinspect/inspect_web-server-01_20260611_103000.html
[INFO] CloudInspect v1.1 云主机安全巡检开始...

[ 1/12] (  8%) 采集系统基本信息...
[ 2/12] ( 16%) 检查磁盘状态...
[ 3/12] ( 25%) 检查网络状态...
[ 4/12] ( 33%) 检查进程状态...
[ 5/12] ( 41%) 检查服务状态...
[ 6/12] ( 50%) 检查定时任务...
[ 7/12] ( 58%) 检查安全基线...
[ 8/12] ( 66%) 检查后门...
[ 9/12] ( 75%) 分析系统日志...
[10/12] ( 83%) 检查历史命令...
[11/12] (100%) 生成报告...

==============================================
  CloudInspect v1.1 - 巡检完成
  Host: web-server-01
  Mode: routine
  Warnings: 3
  Critical: 0
  Elapsed: 8.5s
  Report: /tmp/cloudinspect/inspect_web-server-01_20260611_103000.html
==============================================
```

---

## 常用命令示例

### 1. 日常巡检，HTML 报告

```bash
./inspect.sh
```

### 2. 应急排查模式，JSON 输出

```bash
./inspect.sh -m emergency -f json -o /tmp/emergency_report.json
```

### 3. 静默模式，不显示进度

```bash
./inspect.sh -q
```

### 4. 详细日志模式

```bash
./inspect.sh -v
```

### 5. 组合使用

```bash
./inspect.sh -m emergency -f json -o /tmp/report.json -v
```

---

## 报告解读

### 退出码

| 退出码 | 含义 | 处理建议 |
|---|---|---|
| `0` | 正常（无警告/无严重） | 无需处理 |
| `1` | 有警告 | 关注警告内容，按需处理 |
| `2` | 有严重告警/脚本错误 | 立即处理，建议进入 emergency 模式复检 |

### 告警级别

| 级别 | 标识 | 含义 |
|---|---|---|
| **严重** | 🔴 红色 | 发现入侵痕迹或严重安全风险，需立即处理 |
| **警告** | 🟡 黄色 | 发现可疑行为或配置问题，建议关注 |
| **正常** | 🟢 绿色 | 检测项正常，无问题 |

---

## 下一步

- 查看 [命令行参数详解](command-line.md)
- 查看 [配置说明](configuration.md)
- 查看 [各检测模块文档](modules/)
- 查看 [离线安装指南](offline-install.md)

---

## 常见问题

**Q: Bash 版本提示 "权限不足"**
```bash
chmod +x inspect.sh
```

**Q: 报告生成失败**
```bash
# 检查目录权限
ls -la /tmp/cloudinspect
# 或指定其他目录
mkdir -p /tmp/myreports
./inspect.sh -o /tmp/myreports/report.html
```

**Q: 支持华为云 EulerOS 吗？**
> ✅ 完全支持。CloudInspect v1.1+ 已支持 HCE (华为云 EulerOS) 和 EulerOS，详情见 [OS 支持说明](os-support.md)。

---

*最后更新: 2026-06-11*