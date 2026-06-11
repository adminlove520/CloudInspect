# 操作系统支持

**CloudInspect 支持的操作系统完整列表及兼容性说明**

---

## 支持的操作系统总览

CloudInspect v1.1+ 支持以下 Linux 发行版：

### RHEL 家族 ✅

| 操作系统 | ID | 架构 | 状态 |
|---|---|---|---|
| Rocky Linux | `rocky` | x86_64, aarch64 | ✅ 完全支持 |
| AlmaLinux | `almalinux` | x86_64, aarch64 | ✅ 完全支持 |
| CentOS Linux | `centos` | x86_64 | ✅ 完全支持 |
| CentOS Stream | `centos` | x86_64 | ✅ 完全支持 |
| Oracle Linux | `ol`, `oracle` | x86_64 | ✅ 完全支持 |
| Red Hat Enterprise Linux | `rhel` | x86_64, aarch64 | ✅ 完全支持 |
| Fedora | `fedora` | x86_64 | ✅ 完全支持 |
| Amazon Linux | `amzn`, `amazon` | x86_64, aarch64 | ✅ 完全支持 |
| **华为云 EulerOS (HCE)** | `HCE` | x86_64, aarch64 | ✅ 完全支持 |
| **EulerOS** | `euler` | x86_64, aarch64 | ✅ 完全支持 |
| Anolis OS | `anolis` | x86_64, aarch64 | ✅ 完全支持 |
| TencentOS | `tencentos` | x86_64 | ✅ 完全支持 |
| Alibaba Cloud Linux | `alinux` | x86_64 | ✅ 完全支持 |

### Debian 家族 ✅

| 操作系统 | ID | 架构 | 状态 |
|---|---|---|---|
| Debian | `debian` | x86_64, aarch64 | ✅ 完全支持 |
| Ubuntu | `ubuntu` | x86_64, aarch64 | ✅ 完全支持 |
| Kali Linux | `kali` | x86_64 | ✅ 完全支持 |
| Linux Mint | `mint` | x86_64 | ✅ 完全支持 |
| Pop!_OS | `pop` | x86_64 | ✅ 完全支持 |
| Raspbian | `raspbian` | armhf, aarch64 | ✅ 完全支持 |

### SUSE 家族 ✅

| 操作系统 | ID | 架构 | 状态 |
|---|---|---|---|
| SLES | `sles`, `suse` | x86_64 | ✅ 完全支持 |
| openSUSE | `opensuse` | x86_64 | ✅ 完全支持 |

### 信创平台 ✅

| 操作系统 | ID | 架构 | 状态 |
|---|---|---|---|
| **华为云 EulerOS (HCE)** | `HCE` | x86_64, aarch64 | ✅ 完全支持 |
| **EulerOS** | `euler` | x86_64, aarch64 | ✅ 完全支持 |
| 麒麟 V10 | `kylin` | x86_64, aarch64 | ✅ 完全支持 |
| 麒麟 V10 SP1 | `kylin` | x86_64, aarch64 | ✅ 完全支持 |
| 麒麟 V10 SP2 | `kylin` | x86_64, aarch64 | ✅ 完全支持 |
| 统信 UOS | `uos` | x86_64, aarch64 | ✅ 完全支持 |
| 深度 Deepin | `deepin` | x86_64 | ✅ 完全支持 |

### 其他 ✅

| 操作系统 | ID | 架构 | 状态 |
|---|---|---|---|
| Arch Linux | `arch` | x86_64 | ✅ 完全支持 |
| Manjaro | `manjaro` | x86_64 | ✅ 完全支持 |
| Alpine Linux | `alpine` | x86_64 | ✅ 完全支持 |
| Gentoo | `gentoo` | x86_64 | ✅ 完全支持 |

---

## 华为云 EulerOS (HCE) 特别说明

### 什么是 HCE？

**Huawei Cloud EulerOS (HCE)** 是华为云基于 RHEL 社区版本开发的云服务器操作系统，专为云环境优化，提供高性能、高安全性和高可靠性。

### 特性

- 基于 RHEL 社区版本，继承 RHEL 的稳定性和兼容性
- 针对云环境进行了专项优化
- 支持 x86_64 和 aarch64 架构
- 兼容主流企业级软件和工具

### 检测方式

CloudInspect 通过以下方式检测 HCE：

```bash
# 方式1: /etc/os-release 中的 ID
cat /etc/os-release
# ID=HCE
# ID_LIKE="rhel fedora"

# 方式2: 兜底检测 /etc/hce-release
cat /etc/hce-release
```

### 兼容性

| 功能 | HCE 支持情况 |
|---|---|
| systemctl | ✅ 完全支持 |
| firewalld | ✅ 完全支持 |
| yum/dnf | ✅ 完全支持 |
| journalctl | ✅ 完全支持 |
| psutil (Python) | ✅ 完全支持 |
| Bash 工具 | ✅ 完全支持 |

### uname 示例

```
Linux 258.novalocal 5.10.0-60.18.0.50.hce2.x8664 #1 SMP Tue Nov 28 08:26:19 UTC 2023 x86_64 x86_64 x86_64 GNU/Linux
```

---

## EulerOS 特别说明

### 什么是 EulerOS？

**EulerOS** 是华为开发的服务器操作系统品牌，HCE (Huawei Cloud EulerOS) 是其在华为云上的发行版本。

### 检测方式

```bash
# 方式1: /etc/os-release 中的 ID
cat /etc/os-release
# ID=euler

# 方式2: 兜底检测 /etc/euler-release
cat /etc/euler-release
```

---

## 架构支持

### x86_64 (AMD64)

- ✅ 完全支持
- 所有检测模块正常工作

### aarch64 (ARM64)

- ✅ 完全支持
- 特别适配华为云 ARM 实例

| 模块 | x86_64 | aarch64 |
|---|---|---|
| 系统信息 | ✅ | ✅ |
| 磁盘检测 | ✅ | ✅ |
| 网络检测 | ✅ | ✅ |
| 进程检测 | ✅ | ✅ |
| 服务检测 | ✅ | ✅ |
| 后门检测 | ✅ | ✅ |
| Rootkit 检测 | ✅ | ✅ |

---

## 家族映射

CloudInspect 将检测到的 OS 映射到以下家族：

| 家族 | 说明 | 包含的 OS |
|---|---|---|
| `rhel` | RHEL 兼容家族 | Rocky, AlmaLinux, CentOS, RHEL, Fedora, Amazon, HCE, EulerOS, Oracle, Anolis 等 |
| `debian` | Debian 家族 | Debian, Ubuntu, Kali, Mint |
| `suse` | SUSE 家族 | SLES, openSUSE |
| `kylin` | 麒麟家族 | Kylin V10, NeoKylin |
| `uos` | UOS 家族 | 统信 UOS, Deepin |
| `arch` | Arch 家族 | Arch, Manjaro |
| `alpine` | Alpine 家族 | Alpine |
| `gentoo` | Gentoo 家族 | Gentoo |

---

## 依赖工具

### Bash 版本

零外部依赖，使用系统自带工具：

| 工具 | 用途 | 最低版本 |
|---|---|---|
| bash | 主脚本解释器 | 4.0 |
| coreutils | ls, cat, grep, awk 等 | 基础 |
| systemd | 服务管理 | 可选 |
| procps | top, ps 等进程工具 | 可选 |

### Python 版本

| 依赖 | 用途 | 最低版本 |
|---|---|---|
| Python | 解释器 | 3.8 |
| pyyaml | YAML 配置解析 | 6.0 |
| psutil | 系统信息采集 | 5.9.0 |
| python-docx | DOCX 报告生成（可选） | 0.8.10 |
| lxml | XML/HTML 解析（可选） | 4.9.0 |

---

## 已知兼容性

### ✅ 已测试环境

| 环境 | 版本 | 架构 | 结果 |
|---|---|---|---|
| 华为云 ECS (HCE) | 2.0 SP5 | x86_64 | ✅ 通过 |
| 华为云 ECS (HCE) | 2.0 SP5 | aarch64 | ✅ 通过 |
| CentOS | 7.9 | x86_64 | ✅ 通过 |
| CentOS | 8.5 | x86_64 | ✅ 通过 |
| Rocky Linux | 9.2 | x86_64 | ✅ 通过 |
| Ubuntu | 22.04 | x86_64 | ✅ 通过 |
| Debian | 12 | x86_64 | ✅ 通过 |

### ⚠️ 注意事项

1. **最小化安装**: 部分最小化安装可能缺少 `ps`, `top` 等工具，Bash 版本可正常工作
2. **特殊内核**: 部分定制内核可能影响 Rootkit 检测精度
3. **容器环境**: 容器内运行可能无法检测宿主机级别的 Rootkit

---

*最后更新: 2026-06-11*