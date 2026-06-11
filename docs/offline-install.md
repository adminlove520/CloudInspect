# 离线安装指南

**内网环境零联网部署 CloudInspect**

---

## 场景说明

在无法访问互联网的内网环境中，需要先在联网主机下载依赖，然后拷贝到内网安装。

```
┌─────────────────┐      USB/内网传输      ┌─────────────────┐
│   联网主机       │ ─────────────────>   │   内网主机       │
│   (有互联网)     │                      │   (无互联网)    │
│                 │                      │                 │
│  download.sh ───┼──> packages/ ──────────│──> install.sh   │
└─────────────────┘                      └─────────────────┘
```

---

## Step 1: 联网主机下载

### 下载脚本

```bash
cd CloudInspect
chmod +x scripts/download_packages.sh
./scripts/download_packages.sh
```

### 下载内容

脚本会下载以下内容到 `packages/` 目录：

| 类型 | 内容 | 说明 |
|---|---|---|
| Bash | bash-4.4.tar.gz | Bash 4.4 预编译包 |
| Python | Python-3.11.tar.gz | Python 3.11 源码 |
| pip | get-pip.py | pip 安装脚本 |
| wheels | *.whl | Python 依赖包 |

### 下载脚本说明

```bash
# 查看下载选项
./scripts/download_packages.sh --help

# 下载 Python 3.11（默认）
./scripts/download_packages.sh --python 3.11

# 仅下载 Bash
./scripts/download_packages.sh --bash-only

# 仅下载 Python
./scripts/download_packages.sh --python-only

# 指定输出目录
./scripts/download_packages.sh --output /opt/packages
```

### 验证下载

```bash
ls -la packages/
# 应看到:
# packages/
# ├── bash/
# ├── python3/
# ├── pip/
# └── README.md
```

---

## Step 2: 拷贝到内网

### 方法 1: USB 拷贝

```bash
# 打包
tar -czvf cloudinspect-packages.tar.gz packages/

# 拷贝到 USB
cp cloudinspect-packages.tar.gz /media/usb/

# 在内网主机解压
tar -xzvf cloudinspect-packages.tar.gz
```

### 方法 2: 内网传输

```bash
# 在内网服务器之间传输
scp -r packages/ user@internal-server:/opt/
```

---

## Step 3: 内网安装

### 一键安装

```bash
cd CloudInspect
chmod +x scripts/install.sh
./scripts/install.sh
```

### 安装选项

```bash
# 查看帮助
./scripts/install.sh --help

# 安装 Bash（如果系统 Bash 版本过低）
./scripts/install.sh --bash

# 安装 Python（如果系统没有 Python）
./scripts/install.sh --python

# 安装全部
./scripts/install.sh --all

# 指定 packages 目录
./scripts/install.sh --packages /opt/packages
```

### 安装过程

```
=== CloudInspect 离线安装 ===

[1/4] 检查环境...
  OS: Huawei Cloud EulerOS 2.0
  Bash: 4.2 (满足要求)
  Python: 未安装 (需要安装)
  [PASS] 可以运行

[2/4] 安装 Python 3.11...
  [PASS] Python 安装完成

[3/4] 安装 Python 依赖...
  [PASS] pyyaml-6.0 已安装
  [PASS] psutil-5.9.0 已安装
  [PASS] python-docx-0.8.10 已安装

[4/4] 验证安装...
  [PASS] CloudInspect 已就绪

=== 安装完成 ===
  Bash 版本: ./bash/inspect.sh
  Python 版本: ./python/inspect.py

  运行示例:
    ./bash/inspect.sh -m routine
    python3 ./python/inspect.py -m routine
```

---

## 安装要求

### 最小磁盘空间

| 组件 | 空间需求 |
|---|---|
| Bash 版本 | 5 MB |
| Python 版本 | 150 MB |
| 全部（含依赖） | 300 MB |

### 操作系统支持

离线安装支持与 CloudInspect 相同的所有操作系统：
- RHEL/CentOS/Rocky/AlmaLinux
- Debian/Ubuntu
- SUSE/openSUSE
- 麒麟 Kylin
- **华为云 EulerOS (HCE)**
- **EulerOS**
- 统信 UOS
- 等

---

## 故障排查

### Q: 安装脚本失败

```bash
# 检查 packages 目录
ls -la packages/

# 检查权限
chmod +x scripts/install.sh

# 手动安装
cd packages/python3
./configure && make && make install
```

### Q: Python 依赖安装失败

```bash
# 手动安装依赖
cd packages/pip
python3 get-pip.py

pip install pyyaml psutil python-docx lxml
```

### Q: Bash 版本不兼容

```bash
# 检查当前 Bash 版本
bash --version

# 如果低于 4.0，安装预编译版本
cd packages/bash
./install-bash.sh
```

---

## 完整部署流程

### 1. 准备阶段（联网主机）

```bash
# 克隆代码
git clone https://github.com/adminlove520/CloudInspect.git
cd CloudInspect

# 下载离线包
./scripts/download_packages.sh

# 打包
tar -czvf cloudinspect-offline.tar.gz \
  packages/ \
  bash/ \
  python/ \
  config/ \
  scripts/
```

### 2. 传输阶段

```bash
# 拷贝到 USB 或内网服务器
cp cloudinspect-offline.tar.gz /media/usb/
```

### 3. 安装阶段（内网主机）

```bash
# 解压
tar -xzvf cloudinspect-offline.tar.gz
cd CloudInspect

# 安装
./scripts/install.sh

# 运行
./bash/inspect.sh -m routine
```

### 4. 验证阶段

```bash
# 运行巡检
./bash/inspect.sh -m routine

# 检查报告
ls -la /tmp/cloudinspect/

# 查看报告内容
cat /tmp/cloudinspect/inspect_*.html | head -50
```

---

## 自定义离线包

### 添加额外工具

```bash
# 在 packages 目录添加其他工具
packages/
├── bash/
├── python3/
├── pip/
├── tools/          # 自定义工具目录
│   ├── rkhunter/   # Rootkit 检测工具
│   └── chkrootkit/ # 另一种 Rootkit 检测工具
└── README.md
```

### 修改安装脚本

编辑 `scripts/install.sh` 添加自定义安装逻辑。

---

*最后更新: 2026-06-11*