# CloudInspect 文档中心

**云主机安全巡检工具 - 完整使用文档**

---

## 📚 文档目录

### 快速入门
| 文档 | 说明 |
|---|---|
| [快速开始](getting-started.md) | 5分钟上手指南 |
| [操作系统支持](os-support.md) | 支持的 OS 列表及兼容性说明 |
| [命令行参数](command-line.md) | 所有参数详解 |

### 检测模块
| 文档 | 说明 |
|---|---|
| [01-系统信息](modules/01-sysinfo.md) | 主机/CPU/内存/网络采集 |
| [02-磁盘状态](modules/02-disk.md) | 使用率/Inode/大文件检测 |
| [03-网络状态](modules/03-network.md) | 网卡/端口/连接/混杂模式 |
| [04-进程状态](modules/04-process.md) | 僵尸/隐藏进程/TOP分析 |
| [05-服务状态](modules/05-service.md) | 30+服务监控 |
| [06-定时任务](modules/06-cron.md) | Cron后门检测 |
| [07-安全基线](modules/07-security.md) | SSH/账户/SUID检查 |
| [08-后门检测](modules/08-backdoor.md) | LD_PRELOAD/SSH wrapper等 |
| [09-Rootkit检测](modules/09-rootkit.md) | 特征库/LKM检测 |
| [10-日志分析](modules/10-log-analysis.md) | 登录失败/OOM分析 |
| [11-历史命令](modules/11-history.md) | 反弹shell/境外IP检测 |
| [12-Webshell检测](modules/12-webshell.md) | Webshell特征扫描 |

### 配置与进阶
| 文档 | 说明 |
|---|---|
| [配置说明](configuration.md) | config/default.yaml 详解 |
| [离线安装](offline-install.md) | 内网环境安装指南 |
| [报告解读](report-guide.md) | 如何阅读巡检报告 |
| [故障排查](troubleshooting.md) | 常见问题与解决方案 |
| [规则更新](rule-update.md) | 规则自动更新机制 |

### 部署场景
| 场景 | 文档 |
|---|---|
| 日常巡检 | [快速开始](getting-started.md) + routine 模式 |
| 护网行动 | [护网行动指南](scenarios/competition.md) |
| 应急响应 | [emergency 模式使用](getting-started.md#工作模式) |
| 批量部署 | [批量部署指南](deployment/batch-deploy.md) |

---

## 🔧 版本选择

| 版本 | 适用场景 | 依赖 |
|---|---|---|
| **Bash** | 零依赖环境、快速部署、兼容性好 | 无 |
| **Python** | 功能完整、需要 DOCX 报告 | pyyaml, psutil |

---

## 📋 检测模块概览

CloudInspect 包含 **12 大检测模块**，覆盖云主机安全巡检的方方面面：

```
┌─────────────────────────────────────────────────────────────┐
│                      CloudInspect                           │
├─────────────────────────────────────────────────────────────┤
│  日常巡检 (routine)  │  应急排查 (emergency)  │  快速 (quick) │
│  ━━━━━━━━━━━━━━━     │  ━━━━━━━━━━━━━━━━━     │  ━━━━━━━━━  │
│  ✓ 01 系统信息        │  ✓ 01-11 全部模块       │  ✓ 核心系统  │
│  ✓ 02 磁盘状态        │  ✓ 09 Rootkit 检测      │  ✓ 快速报告  │
│  ✓ 03 网络状态        │  ✓ 12 Webshell 检测     │             │
│  ✓ 04 进程状态        │  ✓ 深度后门分析         │             │
│  ✓ 05 服务状态        │                        │             │
│  ✓ 06 定时任务        │                        │             │
│  ✓ 07 安全基线        │                        │             │
│  ✓ 08 后门检测        │                        │             │
│  ✓ 10 日志分析        │                        │             │
│  ✓ 11 历史命令        │                        │             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🐧 支持的操作系统

**主流 Linux 发行版全覆盖**

| 家族 | 操作系统 | 版本 |
|---|---|---|
| **RHEL** | Rocky Linux, AlmaLinux, CentOS, Oracle Linux, Fedora, Amazon Linux, **EulerOS (HCE)**, **EulerOS** | 7.x - 9.x |
| **Debian** | Debian, Ubuntu, Kali, Mint | 10+ |
| **SUSE** | SLES, openSUSE | 15+ |
| **Kylin** | 麒麟 V10, 麒麟 V10 SP1/SP2 | - |
| **UOS** | 统信 UOS | - |
| **Arch** | Arch Linux, Manjaro | - |
| **Alpine** | Alpine Linux | 3.x |
| **Gentoo** | Gentoo | - |

### 信创平台支持

| 平台 | 架构 | 状态 |
|---|---|---|
| **华为云 EulerOS (HCE)** | x86_64, aarch64 | ✅ 完全支持 |
| **华为云 EulerOS** | x86_64, aarch64 | ✅ 完全支持 |
| **麒麟 Kylin** | x86_64, aarch64 | ✅ 完全支持 |
| **统信 UOS** | x86_64, aarch64 | ✅ 完全支持 |

---

## 📊 报告格式

| 格式 | 用途 | 特点 |
|---|---|---|
| **HTML** | 日常查看 | 美观的卡片式设计，支持图表 |
| **JSON** | 程序处理 | 结构化数据，便于集成 |
| **Markdown** | 存档/归档 | 纯文本，便于 Git 管理 |
| **DOCX** | 正式交付 | Word 格式，适合报告提交 |

---

*最后更新: 2026-06-11*