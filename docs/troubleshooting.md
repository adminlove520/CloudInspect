# 故障排查

**常见问题与解决方案**

---

## 常见问题

### 1. 权限问题

#### Q: Bash 版本提示 "权限不足"

```
bash: ./inspect.sh: Permission denied
```

**解决方案**:
```bash
chmod +x inspect.sh
./inspect.sh
```

#### Q: Python 版本提示 "Permission denied"

```
PermissionError: [Errno 13] Permission denied: '/tmp/cloudinspect'
```

**解决方案**:
```bash
# 使用 sudo 运行（如果需要）
sudo python3 inspect.py

# 或修改目录权限
mkdir -p /tmp/cloudinspect
chmod 777 /tmp/cloudinspect
```

---

### 2. 依赖问题

#### Q: Python 版本缺少模块

```
ModuleNotFoundError: No module named 'yaml'
```

**解决方案**:
```bash
# 安装依赖
pip install pyyaml psutil python-docx lxml

# 或使用 requirements.txt
pip install -r requirements.txt
```

#### Q: psutil 安装失败

```
error: Microsoft Visual C++ 14.0 is required
```

**解决方案**:
```bash
# Windows: 安装 Visual Studio Build Tools
# 或使用预编译 wheel
pip install --only-binary :all: psutil

# Linux: 安装开发包
yum install python3-devel  # RHEL/CentOS
apt install python3-dev     # Debian/Ubuntu
pip install psutil
```

---

### 3. 执行问题

#### Q: 脚本执行卡住

```
[ 1/12] (  8%) 采集系统基本信息...
```

**解决方案**:
```bash
# 1. 检查是否有挂起的进程
# Ctrl+C 中断

# 2. 使用 verbose 模式查看卡住位置
./inspect.sh -v

# 3. 手动测试每个步骤
hostname
df -h
free -m
ps aux | head -5
```

#### Q: 报告生成失败

```
Error: 无法创建报告目录
```

**解决方案**:
```bash
# 检查目录权限
ls -la /tmp/cloudinspect

# 创建目录并设置权限
mkdir -p /tmp/cloudinspect
chmod 777 /tmp/cloudinspect

# 或使用其他目录
export REPORT_DIR=/var/log/cloudinspect
./inspect.sh -o /var/log/cloudinspect/report.html
```

---

### 4. OS 检测问题

#### Q: 检测到 "unknown" OS

```
[INFO] 检测到操作系统: unknown (other)
```

**解决方案**:
```bash
# 1. 检查 /etc/os-release
cat /etc/os-release

# 2. 检查释放文件
ls -la /etc/*release
cat /etc/centos-release 2>/dev/null
cat /etc/redhat-release 2>/dev/null

# 3. 如果是 EulerOS/HCE 但检测不到
# 手动创建 /etc/hce-release 文件
echo "Huawei Cloud EulerOS 2.0" | sudo tee /etc/hce-release
```

#### Q: EulerOS/HCE 识别为其他 OS

**问题**: 华为云 EulerOS 显示为 "rocky" 或 "centos"

**原因**: EulerOS 基于 RHEL，ID_LIKE 可能包含这些值

**解决方案**:
CloudInspect v1.1+ 已修复，优先检测 `ID=HCE` 或 `ID=euler`

```bash
# 手动验证
cat /etc/os-release | grep -E "^ID=|^ID_LIKE="
```

---

### 5. 报告问题

#### Q: HTML 报告空白

```
报告文件大小: 0 字节
```

**解决方案**:
```bash
# 1. 检查脚本是否正常执行
./inspect.sh -v

# 2. 检查临时文件
ls -la /tmp/cloudinspect*

# 3. 使用 JSON 格式测试
./inspect.sh -f json -o /tmp/test.json
cat /tmp/test.json

# 4. 检查磁盘空间
df -h /tmp
```

#### Q: JSON 报告格式错误

**解决方案**:
```bash
# 验证 JSON 格式
python3 -c "import json; json.load(open('/tmp/report.json'))"

# 查看错误
python3 -c "import json; json.load(open('/tmp/report.json'))" 2>&1
```

---

### 6. 性能问题

#### Q: 巡检太慢

```
耗时: 15 分钟 (正常应该 5-8 分钟)
```

**解决方案**:
```bash
# 1. 使用 quick 模式
./inspect.sh -m quick

# 2. 排除大目录
# 编辑 config/default.yaml
scan:
  exclude_paths:
    - /var/cache
    - /tmp
    - /opt/large_data

# 3. 减少 TOP N
scan:
  top_n: 5
```

#### Q: 内存占用过高

**解决方案**:
```bash
# 1. 使用 Bash 版本（内存占用更小）
./bash/inspect.sh -m routine

# 2. 减少扫描范围
scan:
  search_paths:
    - /var/log
    - /home
```

---

### 7. 特殊环境问题

#### Q: Docker 容器内运行

**问题**: 检测到的是容器信息而非宿主机

**解决方案**:
```bash
# 使用 --host 参数（如果支持）
./inspect.sh --host

# 或直接在宿主机运行
docker exec -it container_name /opt/cloudinspect/inspect.sh
```

#### Q: 华为云 EulerOS (HCE) aarch64 兼容

**确认**:
```bash
# 检查架构
uname -m
# 输出应为: aarch64

# 检查 Python psutil
python3 -c "import psutil; print(psutil.cpu_count())"
```

**问题**: 如果 psutil 在 aarch64 上安装失败

**解决方案**:
```bash
# 使用 Bash 版本（Bash 版本零依赖，完全兼容）
./bash/inspect.sh -m routine

# 或手动编译 psutil
pip install --no-binary :all: psutil
```

---

## 调试技巧

### 1. 查看详细日志

```bash
# 启用 verbose 模式
./inspect.sh -v

# 保存完整日志
./inspect.sh -v 2>&1 | tee /tmp/inspect.log
```

### 2. 分步执行

```bash
# 只执行系统信息采集
source bash/lib/core.sh
detect_os
echo "OS_FAMILY=$OS_FAMILY, OS_ID=$OS_ID"
```

### 3. 测试特定模块

```bash
# 测试 OS 检测
bash -c 'source bash/lib/core.sh && detect_os && echo $OS_ID'

# 测试服务检测
bash -c 'source bash/lib/core.sh && service_status sshd'
```

### 4. 检查配置文件

```bash
# 验证 YAML 格式
python3 -c "import yaml; yaml.safe_load(open('config/default.yaml'))"

# 检查配置值
cat config/default.yaml | grep -E "cpu_warn|mem_warn|disk_warn"
```

---

## 获取帮助

### 查看帮助

```bash
./inspect.sh -h
python3 inspect.py -h
```

### 查看版本

```bash
./inspect.sh --version
python3 inspect.py --version
```

### 提交问题

如遇到无法解决的问题，请提交 Issue：
- https://github.com/adminlove520/CloudInspect/issues
- https://git.nxwysoft.com/zhangz/CloudInspect/issues

请提供以下信息：
1. 操作系统版本 (`cat /etc/os-release`)
2. 架构 (`uname -m`)
3. CloudInspect 版本
4. 错误信息
5. 完整日志 (`./inspect.sh -v 2>&1 | tee debug.log`)

---

*最后更新: 2026-06-11*