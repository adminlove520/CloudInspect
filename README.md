# CloudInspect

**云主机安全巡检工具** — 护网行动专用，支持日常巡检 + 应急排查

[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg)]()
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)]()
[![Bash](https://img.shields.io/badge/Shell-Bash%204.0+-green.svg)]()

---

## 功能概览

| 功能 | 说明 |
|---|---|
| **12 大检测模块** | 系统信息 / 磁盘 / 网络 / 进程 / 服务 / 定时任务 / 安全基线 / 后门检测 / Rootkit / 日志分析 / 历史命令 / Webshell |
| **4 种工作模式** | routine（日常）/ emergency（应急）/ quick（快速）/ full（完全） |
| **双语言版本** | Bash（零依赖）/ Python（功能完整） |
| **3 种报告格式** | HTML（美观卡片式）/ DOCX（正式交付）/ Markdown（存档） |
| **跨平台支持** | Rocky / RHEL / CentOS / Ubuntu / Debian / Kylin / SUSE / Arch / Alpine / Gentoo |
| **离线安装** | download_packages.sh → install.sh，零联网依赖 |

---

## 快速开始

### Bash 版本（零依赖）

```bash
cd CloudInspect/bash
chmod +x inspect.sh
./inspect.sh                    # 默认 HTML 报告
./inspect.sh -m emergency       # 应急排查模式
./inspect.sh -f json -o /tmp/r.json  # 输出 JSON
./inspect.sh --mode quick --verbose  # 快速详细
```

### Python 版本（功能完整）

```bash
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

## 报告示例

HTML 报告采用**分层卡片式**设计：
- 顶部仪表盘（风险等级/关键指标）
- 左侧导航目录
- 内容区按检测类别卡片展示
- 每类带统计徽章 + 可展开详情

---

## 离线安装

### Step 1：联网主机下载

```bash
cd CloudInspect/scripts
chmod +x download_packages.sh
./download_packages.sh
# 生成 packages/ 目录（包含 Bash4/Python3/pip wheel）
```

### Step 2：拷贝到内网 + 安装

```bash
# 将 packages/ 目录拷贝到内网服务器
cd CloudInspect/scripts
chmod +x install.sh
./install.sh
# 全自动安装 Bash4 + Python3 + 依赖
```

---

## 目录结构

```
CloudInspect/
├── bash/
│   ├── inspect.sh           # 主入口（Bash版）
│   └── lib/                  # 12个检测模块
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
│   ├── lib/                  # 12个检测模块（与Bash同源）
│   ├── core/                # 核心引擎
│   │   ├── config.py         # 配置管理
│   │   ├── detector.py       # 检测调度
│   │   ├── reporter.py       # 多格式报告
│   │   └── os_detect.py      # OS检测层
│   ├── rules/               # 特征规则库
│   │   ├── backdoor_rules.yaml
│   │   ├── rootkit_signatures.yaml
│   │   └── webshell_patterns.yaml
│   └── requirements.txt
│
├── config/
│   └── default.yaml         # 默认配置（Bash/Python共读）
│
├── packages/                 # 离线安装包
│   ├── bash/                 # 预编译 Bash 4
│   ├── python3/              # 预编译 Python 3
│   └── pip/                  # wheel 包
│
├── scripts/
│   ├── download_packages.sh  # 联网下载离线包
│   └── install.sh           # 内网一键安装
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

## License

MIT License