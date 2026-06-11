# CloudInspect for Windows Server

云主机安全巡检工具 - Windows Server 版

---

## 功能概览

| 功能 | 说明 |
|---|---|
| **12 个检测模块** | 系统信息 / 磁盘 / 网络 / 进程 / 服务 / 事件日志 / 防火墙 / 用户 / 更新 / 注册表 / 权限 / Defender |
| **4 种工作模式** | routine（日常）/ emergency（应急）/ quick（快速）/ full（完全） |
| **3 种报告格式** | HTML / JSON / Markdown |
| **PowerShell 集成** | 辅助脚本支持深度系统检测 |
| **离线安装** | Python 3.13 便携版 + 依赖包 |

---

## 支持的操作系统

| 操作系统 | 版本 | 状态 |
|---|---|---|
| Windows Server 2012 | R2 | ✅ 支持 |
| Windows Server 2016 | - | ✅ 支持 |
| Windows Server 2019 | - | ✅ 支持 |
| Windows Server 2022 | - | ✅ 支持 |
| Windows 10 | 专业版/企业版 | ✅ 支持 |
| Windows 11 | 专业版/企业版 | ✅ 支持 |

---

## 快速开始

### 前置要求

- Python 3.8+ (推荐 Python 3.13)
- Windows PowerShell 5.1+ 或 PowerShell Core

### 安装依赖

```powershell
# 克隆仓库
git clone https://github.com/adminlove520/CloudInspect.git
cd CloudInspect/windows

# 安装 Python 依赖
pip install -r requirements.txt
```

### 运行巡检

```powershell
# 日常巡检（默认 HTML 报告）
python inspect.py

# 应急排查模式
python inspect.py -m emergency

# 输出 JSON
python inspect.py -f json -o C:\Temp\report.json

# 快速扫描
python inspect.py -m quick -v
```

---

## 工作模式

| 模式 | 耗时 | 说明 |
|---|---|---|
| **routine** | 5-15 分钟 | 日常巡检（推荐） |
| **emergency** | 30-60 分钟 | 应急排查，深度检测 |
| **quick** | 1-3 分钟 | 快速扫描 |
| **full** | 60+ 分钟 | 完全扫描 |

---

## 检测模块

| # | 模块 | quick | routine | emergency | 说明 |
|---|---|---|---|---|---|
| 1 | 系统信息 | ✅ | ✅ | ✅ | 主机/CPU/内存/磁盘 |
| 2 | 磁盘状态 | ✅ | ✅ | ✅ | 使用率/大文件 |
| 3 | 网络状态 | ✅ | ✅ | ✅ | 网卡/连接 |
| 4 | 进程状态 | ✅ | ✅ | ✅ | TOP/可疑进程 |
| 5 | 服务状态 | - | ✅ | ✅ | Windows 服务 |
| 6 | 事件日志 | - | ✅ | ✅ | 安全/系统日志 |
| 7 | 防火墙 | - | ✅ | ✅ | Windows 防火墙 |
| 8 | 用户和组 | - | ✅ | ✅ | 本地用户/管理员 |
| 9 | Windows 更新 | - | ✅ | ✅ | 待安装更新 |
| 10 | 注册表 | - | - | ✅ | 自启动项/RDP |
| 11 | 权限检查 | - | - | ✅ | SeDebug/可逆加密 |
| 12 | Windows Defender | - | - | ✅ | 防病毒状态 |

---

## 命令行参数

```powershell
python inspect.py [选项]

选项:
  -o, --output FILE   指定报告输出路径
  -f, --format FORMAT 输出格式: html (默认) | json | md
  -m, --mode MODE     工作模式: routine | emergency | quick | full
  -v, --verbose       详细日志
  -q, --quiet         静默模式
  -h, --help          显示帮助
```

---

## PowerShell 辅助脚本

`scripts/` 目录包含独立的 PowerShell 脚本，可用于深度检测：

| 脚本 | 说明 |
|---|---|
| `check_eventlog.ps1` | 获取事件日志 |
| `check_firewall.ps1` | 获取防火墙状态 |
| `check_users.ps1` | 获取用户信息 |
| `check_privilege.ps1` | 权限检查 |
| `get_defender.ps1` | Windows Defender 状态 |

**使用示例**:
```powershell
# 获取安全日志中的登录失败事件
powershell -ExecutionPolicy Bypass -File scripts/check_eventlog.ps1

# 检查 Windows Defender 状态
powershell -ExecutionPolicy Bypass -File scripts/get_defender.ps1
```

---

## 离线安装

### Step 1: 下载 Python 3.13

从 https://www.python.org/downloads/ 下载 Windows 安装包

### Step 2: 安装依赖

```powershell
pip install -r requirements.txt
```

或使用离线包：
```powershell
pip install --no-index --find-links packages/wheels pyyaml psutil pywin32 wmi lxml
```

---

## 报告示例

### HTML 报告

美观的卡片式设计，包含：
- 风险等级概览
- 各模块检测结果
- 告警详情

### JSON 输出

```json
{
  "warnings": 3,
  "critical": 0,
  "modules": {
    "sysinfo": {"status": "ok", "cpu_percent": 45},
    "defender": {"status": "warning", "enabled": true, "signature_age_days": 8}
  }
}
```

---

## 故障排查

### Q: PowerShell 执行策略限制

```powershell
# 解除执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 或使用 Bypass
powershell -ExecutionPolicy Bypass -File script.ps1
```

### Q: 缺少 pywin32

```powershell
pip install pywin32
```

### Q: 权限不足

以管理员身份运行 PowerShell：
```powershell
Start-Process powershell -Verb RunAs
```

---

## 目录结构

```
windows/
├── inspect.py              # 主入口
├── requirements.txt        # Python 依赖
├── core/
│   ├── config.py          # 配置管理
│   ├── detector.py        # 检测调度
│   ├── reporter.py        # 报告生成
│   └── os_detect.py        # OS 检测
├── lib/                    # 检测模块
│   ├── sysinfo.py         # 系统信息
│   ├── disk.py            # 磁盘状态
│   ├── network.py          # 网络状态
│   ├── process.py         # 进程状态
│   ├── service.py          # 服务状态
│   ├── eventlog.py         # 事件日志
│   ├── firewall.py         # 防火墙
│   ├── user.py             # 用户和组
│   ├── update.py           # Windows 更新
│   ├── registry.py         # 注册表
│   ├── privilege.py        # 权限检查
│   └── defender.py          # Windows Defender
├── scripts/               # PowerShell 辅助脚本
│   ├── check_eventlog.ps1
│   ├── check_firewall.ps1
│   ├── check_users.ps1
│   ├── check_privilege.ps1
│   └── get_defender.ps1
├── packages/
│   └── python-3.13/        # Python 离线包（可选）
└── README.md
```

---

## License

MIT License