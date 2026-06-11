# CloudInspect

**云主机安全巡检工具** — 护网行动专用，支持日常巡检 + 应急排查

[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)]()
[![Bash](https://img.shields.io/badge/Shell-Bash%204.0+-green.svg)]()
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Auto%20Rules-blue.svg)](.github/workflows/update-rules.yml)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 功能概览

| 功能 | 说明 |
|---|---|
| **12 大检测模块** | 系统信息 / 磁盘 / 网络 / 进程 / 服务 / 定时任务 / 安全基线 / 后门检测 / Rootkit / 日志分析 / 历史命令 / Webshell |
| **4 种工作模式** | routine（日常）/ emergency（应急）/ quick（快速）/ full（完全） |
| **双语言版本** | Bash（零依赖）/ Python（功能完整） |
| **4 种报告格式** | HTML（美观卡片式）/ DOCX（正式交付）/ Markdown（存档）/ JSON（程序处理） |
| **跨平台支持** | RHEL 家族 (含 HCE/EulerOS) / Debian 家族 / SUSE / Kylin / UOS / Arch / Alpine / Gentoo |
| **离线安装** | download_packages.sh → install.sh，零联网依赖 |
| **自动规则更新** | GitHub Actions 每周自动更新检测规则 |

---

## 支持的操作系统

### 信创平台 ✅

| 操作系统 | 架构 | 状态 |
|---|---|---|
| **华为云 EulerOS (HCE)** | x86_64, aarch64 | ✅ 完全支持 |
| **EulerOS** | x86_64, aarch64 | ✅ 完全支持 |
| **麒麟 Kylin V10** | x86_64, aarch64 | ✅ 完全支持 |
| **统信 UOS** | x86_64, aarch64 | ✅ 完全支持 |

### 主流 Linux ✅

| 家族 | 操作系统 |
|---|---|
| **RHEL** | Rocky / AlmaLinux / CentOS / RHEL / Fedora / Amazon Linux / Oracle / Anolis |
| **Debian** | Debian / Ubuntu / Kali / Mint |
| **SUSE** | SLES / openSUSE |
| **其他** | Arch / Alpine / Gentoo |

---

## 快速开始

### Bash 版本（零依赖）

```bash
git clone https://github.com/adminlove520/CloudInspect.git
cd CloudInspect/bash
chmod +x inspect.sh
./inspect.sh                    # 默认 HTML 报告
./inspect.sh -m emergency       # 应急排查模式
./inspect.sh -f json -o /tmp/r.json  # 输出 JSON
```

### Python 版本（功能完整）

```bash
git clone https://github.com/adminlove520/CloudInspect.git
cd CloudInspect/python
pip install -r requirements.txt  # 或: pip install pyyaml psutil python-docx lxml
python inspect.py -m emergency -f html   # 应急排查 + HTML
python inspect.py -f docx -o /tmp/report.docx  # Word 报告
```

---

## 工作模式

| 模式 | 参数 | 耗时 | 说明 |
|---|---|---|---|
| **routine** | `-m routine` | 5-15 分钟 | 日常巡检（推荐），覆盖全部核心模块 |
| **emergency** | `-m emergency` | 30-60 分钟 | 应急排查，深度检测后门/Rootkit/Webshell |
| **quick** | `-m quick` | 1-3 分钟 | 快速扫描，核心系统状态 |
| **full** | `-m full` | 60+ 分钟 | 完全扫描，所有模块 |

---

## 命令行参数

| 参数 | 说明 |
|---|---|
| `-o FILE` | 指定报告输出路径 |
| `-f FORMAT` | 输出格式: `html`（默认）/ `json` / `md` / `docx` |
| `-m MODE` | 工作模式: `routine` / `emergency` / `quick` / `full` |
| `-v` | 详细日志 |
| `-q` | 静默模式 |
| `-h` | 显示帮助 |

---

## 检测模块

| # | 模块 | routine | emergency | 说明 |
|---|---|---|---|---|
| 1 | 系统信息 | ✅ | ✅ | 主机/CPU/内存/网络/虚拟化 |
| 2 | 磁盘状态 | ✅ | ✅ | 使用率/Inode/大文件 |
| 3 | 网络状态 | ✅ | ✅ | 网卡/连接/端口/混杂模式 |
| 4 | 进程状态 | ✅ | ✅ | 僵尸/隐藏进程/TOP |
| 5 | 服务状态 | ✅ | ✅ | 30+ 常见服务检测 |
| 6 | 定时任务 | ✅ | ✅ | Cron 后门检测 |
| 7 | 安全基线 | ✅ | ✅ | SSH/账户/SUID/可写文件 |
| 8 | 后门检测 | ✅ | ✅ | LD_PRELOAD/SSH wrapper/setuid 等 10+ 种 |
| 9 | Rootkit | - | ✅ | 特征库/LKM/隐藏进程 |
| 10 | 日志分析 | ✅ | ✅ | 登录失败/OOM/硬件错误 |
| 11 | 历史命令 | ✅ | ✅ | 反弹shell/境外IP/可疑下载 |
| 12 | Webshell | - | ✅ | 正则特征扫描 |

---

## 文档

完整文档见 [docs/](docs/) 目录：

| 文档 | 说明 |
|---|---|
| [快速开始](docs/getting-started.md) | 5分钟上手指南 |
| [OS 支持说明](docs/os-support.md) | 支持的 OS 完整列表（含 HCE/EulerOS） |
| [命令行参数](docs/command-line.md) | 所有参数详解 |
| [配置说明](docs/configuration.md) | config/default.yaml 详解 |
| [离线安装](docs/offline-install.md) | 内网环境安装指南 |
| [报告解读](docs/report-guide.md) | 如何阅读巡检报告 |
| [故障排查](docs/troubleshooting.md) | 常见问题与解决方案 |
| [模块文档](docs/modules/) | 12 个检测模块详细说明 |

---

## 目录结构

```
CloudInspect/
├── bash/
│   ├── inspect.sh           # 主入口（Bash版）
│   └── lib/                # 12个检测模块
│       ├── core.sh          # 核心：OS检测/工具函数
│       ├── 01_sysinfo.sh    # 系统信息
│       ├── 02_disk.sh       # 磁盘
│       ├── 03_network.sh     # 网络
│       ├── 04_process.sh     # 进程
│       ├── 05_service.sh     # 服务
│       ├── 06_cron.sh         # 定时任务
│       ├── 07_security.sh     # 安全基线
│       ├── 08_backdoor.sh    # 后门检测
│       ├── 09_rootkit.sh      # Rootkit
│       ├── 10_log_analysis.sh  # 日志分析
│       ├── 11_history.sh     # 历史命令
│       ├── 12_webshell.sh     # Webshell
│       └── reporter.sh        # 报告生成
│
├── python/
│   ├── inspect.py           # 主入口（Python版）
│   ├── lib/                # 12个检测模块（与Bash同源）
│   ├── core/               # 核心引擎
│   │   ├── config.py        # 配置管理
│   │   ├── detector.py      # 检测调度
│   │   ├── reporter.py      # 多格式报告
│   │   └── os_detect.py     # OS检测层
│   ├── rules/              # 特征规则库
│   │   ├── backdoor_rules.yaml
│   │   ├── rootkit_signatures.yaml
│   │   └── webshell_patterns.yaml
│   └── requirements.txt
│
├── config/
│   └── default.yaml         # 默认配置（Bash/Python共读）
│
├── packages/                # 离线安装包
│   ├── bash/                # 预编译 Bash 4
│   ├── python3/             # 预编译 Python 3
│   └── pip/                 # wheel 包
│
├── scripts/
│   ├── download_packages.sh # 联网下载离线包
│   └── install.sh          # 内网一键安装
│
├── docs/                    # 完整文档
│   ├── README.md           # 文档索引
│   ├── getting-started.md   # 快速开始
│   ├── os-support.md        # OS 支持说明
│   ├── command-line.md      # 命令行参数
│   ├── configuration.md     # 配置说明
│   ├── offline-install.md   # 离线安装
│   ├── report-guide.md      # 报告解读
│   ├── troubleshooting.md   # 故障排查
│   ├── rule-update.md       # 规则更新
│   └── modules/             # 模块文档
│       ├── 01-sysinfo.md
│       ├── 02-disk.md
│       ├── 03-network.md
│       ├── 04-process.md
│       ├── 05-service.md
│       ├── 06-cron.md
│       ├── 07-security.md
│       ├── 08-backdoor.md
│       ├── 09-rootkit.md
│       ├── 10-log-analysis.md
│       ├── 11-history.md
│       └── 12-webshell.md
│
└── README.md
```

---

## 退出码

| 退出码 | 含义 |
|---|---|
| `0` | 正常（无警告/无严重） |
| `1` | 有警告 |
| `2` | 有严重告警/脚本错误 |

---

## 规则自动更新

CloudInspect 通过 GitHub Actions 定时自动更新检测规则，确保能检测到最新的入侵手法。

### 触发方式

| 方式 | 说明 |
|---|---|
| **自动** | 每周六凌晨 2:00 UTC 自动执行 |
| **手动** | GitHub Actions 页面点击 "Run workflow" |
| **API** | `POST /repos/owner/repo/dispatches` with `repository_dispatch` |
| **本地** | `python .github/scripts/update_rules.py --source all` |

### 设置 API Key（可选）

| Secret 名称 | 用途 |
|---|---|
| `OTX_API_KEY` | AlienVault OTX API Key |
| `ABUSEIPDB_API_KEY` | AbuseIPDB API Key |

---

## License

MIT License