# CloudInspect for Windows Server

云主机安全巡检工具 - Windows Server 版

---

## 功能概览

| 功能 | 说明 |
|---|---|
| **16 个检测模块** | 系统信息/磁盘/网络/进程/服务/事件日志/防火墙/用户/更新/注册表/权限/Defender/后门/历史/Rootkit/Webshell |
| **4 种工作模式** | routine/emergency/quick/full |
| **3 种报告格式** | HTML / JSON / Markdown |
| **PowerShell 集成** | 深度系统检测 |

---

## 检测模块

| # | 模块 | quick | routine | emergency | full | 说明 |
|---|---|---|---|---|---|---|
| 1 | 系统信息 | ✅ | ✅ | ✅ | ✅ | 主机/CPU/内存/磁盘 |
| 2 | 磁盘状态 | ✅ | ✅ | ✅ | ✅ | 使用率/大文件 |
| 3 | 网络状态 | ✅ | ✅ | ✅ | ✅ | 网卡/连接 |
| 4 | 进程状态 | ✅ | ✅ | ✅ | ✅ | TOP/可疑进程 |
| 5 | 服务状态 | - | ✅ | ✅ | ✅ | Windows 服务 |
| 6 | 事件日志 | - | ✅ | ✅ | ✅ | 安全/系统日志 |
| 7 | 防火墙 | - | ✅ | ✅ | ✅ | Windows 防火墙 |
| 8 | 用户和组 | - | ✅ | ✅ | ✅ | 本地用户/管理员 |
| 9 | Windows 更新 | - | ✅ | ✅ | ✅ | 待安装更新 |
| 10 | 注册表 | - | - | ✅ | ✅ | 自启动项/RDP |
| 11 | 权限检查 | - | - | ✅ | ✅ | SeDebug/可逆加密 |
| 12 | Windows Defender | - | - | ✅ | ✅ | 防病毒状态 |
| 13 | **后门检测** | - | - | ✅ | ✅ | 启动项/计划任务/服务/账户 |
| 14 | **历史命令** | - | - | ✅ | ✅ | PowerShell/CMD 历史 |
| 15 | **Rootkit 检测** | - | - | ✅ | ✅ | 隐藏进程/驱动/注册表 |
| 16 | **Webshell 检测** | - | - | ✅ | ✅ | IIS/PHP/上传目录 |

### 模式说明

| 模式 | 模块数 | 耗时 | 说明 |
|---|---|---|---|
| quick | 4 | 1-3分钟 | 快速检查 |
| routine | 9 | 5-15分钟 | 日常巡检 |
| **emergency** | **14** | 30-60分钟 | **入侵排查专用** |
| **full** | **16** | 60+分钟 | **全面体检** |

---

## 快速开始

### 安装依赖

```powershell
cd D:\Clade\project\CloudInspect\windows
pip install -r requirements.txt
```

### 运行巡检

```powershell
# 日常巡检
python cloud_inspect.py

# 入侵排查（包含后门/Rootkit/Webshell 检测）
python cloud_inspect.py -m emergency

# 快速扫描
python cloud_inspect.py -m quick

# 输出 JSON
python cloud_inspect.py -f json -o C:\Temp\report.json
```

---

## 报告位置

默认输出到: `%TEMP%\cloudinspect\`

---

*CloudInspect v2.0 for Windows*