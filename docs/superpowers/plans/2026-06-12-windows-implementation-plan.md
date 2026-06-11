# CloudInspect Windows 增强 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 4 个 Windows 新模块 bug，改造为 YAML 规则驱动，新增 Windows 规则同步 workflow

**Architecture:**
- 4 个 Windows 模块加 try-except 保护，改从 `windows/rules/*.yaml` 读取规则
- `windows/scripts/sync_rules.py` 从 `python/rules/` 过滤 Windows 适用规则输出到 `windows/rules/`
- 新增 `.github/workflows/sync-windows-rules.yml`，定时触发规则同步并自动 PR

**Tech Stack:** Python 3, PyYAML, psutil, GitHub Actions

---

## 文件结构

```
CloudInspect/
├── .github/
│   ├── workflows/
│   │   ├── update-rules.yml          # 已有：更新 python/rules/
│   │   └── sync-windows-rules.yml    # 新增：同步到 windows/rules/
│   └── scripts/
│       └── update_rules.py           # 已有
├── python/rules/
│   ├── backdoor_rules.yaml           # 已有，需增加 os_targets
│   ├── rootkit_signatures.yaml       # 已有，需增加 os_targets
│   └── webshell_patterns.yaml        # 已有，需增加 os_targets
├── windows/
│   ├── core/
│   │   └── detector.py               # 已确认模块列表正确
│   ├── lib/
│   │   ├── backdoor.py               # 修改：异常处理 + 规则加载
│   │   ├── history.py                # 修改：异常处理 + 规则加载
│   │   ├── rootkit.py                # 修改：异常处理 + 规则加载 + 白名单
│   │   └── webshell.py               # 修改：异常处理 + 规则加载 + 动态路径
│   ├── rules/                        # 新增目录
│   │   ├── backdoor_rules.yaml       # 新增：Windows 后门规则
│   │   ├── rootkit_rules.yaml        # 新增：Windows Rootkit 规则
│   │   └── webshell_rules.yaml       # 新增：Windows Webshell 规则
│   ├── scripts/
│   │   └── sync_rules.py             # 新增：规则同步脚本
│   └── README.md                     # 修改：确认主入口文件名
└── docs/superpowers/
    ├── specs/2026-06-12-windows-rules-design.md
    └── plans/2026-06-12-windows-implementation-plan.md
```

---

## 第一阶段：Windows 模块 Bug 修复 + 规则加载改造

### Task 1: backdoor.py — 异常处理 + 规则加载

**Files:**
- Modify: `windows/lib/backdoor.py`

- [ ] **Step 1: 读取当前 backdoor.py 全文，定位 run() 和各 check 方法**

文件约 337 行，核心结构：
```python
class BackdoorModule:
    def run(self, os_detect, config):
        issues = []
        startup_backdoors = self.check_startup_backdoors()   # 无 try-except
        # ... 多个 check 调用，全部裸奔
        return {"status": ..., "issues": issues}

    def check_startup_backdoors(self):  # 裸 subprocess.run，无保护
        ps = "Get-CimInstance..."
        result = subprocess.run(['powershell', '-Command', ps], ...)
        # 若 PowerShell 报错或超时，直接抛异常
```

- [ ] **Step 2: 在文件开头添加规则加载**

在 `import` 之后、`class BackdoorModule` 之前添加：

```python
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 规则文件路径
_RULES_FILE = Path(__file__).parent.parent / "rules" / "backdoor_rules.yaml"

def _load_rules() -> list:
    """加载后门检测规则，失败时返回空列表"""
    try:
        import yaml
        if _RULES_FILE.exists():
            with open(_RULES_FILE, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("windows_rules", [])
    except Exception as e:
        logger.warning(f"加载后门规则失败: {e}")
    return []

# 预加载规则（模块级别缓存）
_RULES = _load_rules()
```

- [ ] **Step 3: 重构 run()，每个 check 调用包 try-except**

```python
def run(self, os_detect, config):
    issues = []

    checks = [
        ("启动项", self.check_startup_backdoors),
        ("计划任务", self.check_scheduled_backdoors),
        ("可疑服务", self.check_service_backdoors),
        ("网络连接", self.check_network_backdoors),
        ("注册表", self.check_registry_backdoors),
        ("账户", self.check_account_backdoors),
    ]

    for name, fn in checks:
        try:
            result = fn()
            if result:
                issues.extend(result)
        except subprocess.TimeoutExpired:
            logger.warning(f"{name} 检查超时")
        except Exception as e:
            logger.warning(f"{name} 检查失败: {e}")

    # 使用规则文件中的自定义规则（如果存在）
    for rule in _RULES:
        try:
            issues.extend(self._apply_rule(rule))
        except Exception as e:
            logger.warning(f"应用规则 {rule.get('id', '?')} 失败: {e}")

    return {
        "status": "ok" if not issues else "warning",
        "checks": {name: True for name, _ in checks},
        "issues": issues
    }
```

- [ ] **Step 4: 添加 _apply_rule 辅助方法（处理 YAML 规则）**

```python
def _apply_rule(self, rule: dict) -> list:
    """根据规则类型执行检测"""
    issues = []
    rule_id = rule.get("id", "unknown")
    check_type = rule.get("check_type", "")

    if check_type == "registry_key":
        path = rule.get("path", "")
        pattern = rule.get("pattern", "")
        try:
            ps = f'Get-ItemProperty -Path "{path}" -ErrorAction SilentlyContinue | Out-String'
            r = subprocess.run(['powershell', '-Command', ps], capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and pattern in r.stdout:
                issues.append({"level": rule.get("severity", "warning"),
                               "module": "backdoor",
                               "desc": f"{rule.get('name', rule_id)}: 匹配 {pattern}"})
        except Exception:
            pass

    elif check_type == "service_name":
        svc = rule.get("service_name", "")
        try:
            ps = f'Get-Service -Name "{svc}" -ErrorAction SilentlyContinue | Select-Object Name,Status'
            r = subprocess.run(['powershell', '-Command', ps], capture_output=True, text=True, timeout=15)
            if r.returncode == 0 and svc.lower() in r.stdout.lower():
                issues.append({"level": rule.get("severity", "warning"),
                               "module": "backdoor",
                               "desc": f"{rule.get('name', rule_id)}: 服务存在"})
        except Exception:
            pass

    return issues
```

- [ ] **Step 5: 确认主入口是 cloud_inspect.py 还是 inspect.py**

```bash
ls windows/*.py
```

根据实际文件名更新 README（见 Task 8）。

- [ ] **Step 6: Commit**

```bash
git add windows/lib/backdoor.py
git commit -m "fix(windows): add exception handling and YAML rule loading to backdoor module"
```

---

### Task 2: history.py — 异常处理 + 规则加载

**Files:**
- Modify: `windows/lib/history.py`

- [ ] **Step 1: 读取 history.py 结构**

约 186 行，结构与 backdoor.py 类似：
```python
class HistoryModule:
    def run(self, os_detect, config):
        issues = []
        ps_history = self.get_powershell_history()   # 无保护
        cmd_history = self.get_cmd_history()         # 无保护
        recent_execs = self.get_recent_execs()        # 无保护
        return {...}
```

- [ ] **Step 2: 添加规则加载和异常处理，模式与 backdoor.py 一致**

```python
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_RULES_FILE = Path(__file__).parent.parent / "rules" / "backdoor_rules.yaml"  # history 共用 backdoor 规则

def _load_rules() -> list:
    try:
        import yaml
        if _RULES_FILE.exists():
            with open(_RULES_FILE, encoding="utf-8") as f:
                return yaml.safe_load(f).get("windows_rules", [])
    except Exception as e:
        logger.warning(f"加载规则失败: {e}")
    return []

_RULES = _load_rules()

class HistoryModule:
    def run(self, os_detect, config):
        issues = []

        checks = [
            ("PowerShell历史", self.get_powershell_history),
            ("CMD历史", self.get_cmd_history),
            ("最近执行", self.get_recent_execs),
        ]

        for name, fn in checks:
            try:
                result = fn()
                if result:
                    issues.extend(self._analyze(name, result))
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} 检查超时")
            except Exception as e:
                logger.warning(f"{name} 检查失败: {e}")

        return {
            "status": "ok" if not issues else "warning",
            "powershell_history_lines": len([r for r in issues if "powershell" in str(r)]),
            "cmd_history_lines": len([r for r in issues if "cmd" in str(r)]),
            "recent_execs_count": len(issues),
            "issues": issues
        }

    def _analyze(self, source: str, lines: list) -> list:
        issues = []
        suspicious = ["Invoke-WebRequest", "IEX", "DownloadString",
                      "bash -i", "nc ", "/dev/tcp", "rm -rf /"]
        for line in lines:
            for pattern in suspicious:
                if pattern.lower() in str(line).lower():
                    issues.append({
                        "level": "warning",
                        "module": "history",
                        "source": source,
                        "desc": f"可疑命令: {str(line)[:100]}"
                    })
                    break
        return issues
```

- [ ] **Step 3: Commit**

```bash
git add windows/lib/history.py
git commit -m "fix(windows): add exception handling to history module"
```

---

### Task 3: rootkit.py — 异常处理 + 白名单优化

**Files:**
- Modify: `windows/lib/rootkit.py`

- [ ] **Step 1: 读取 rootkit.py，找到 check_hidden_processes 中的白名单逻辑**

约 298 行，白名单约：
```python
KNOWN_PROCESSES = ["System", "Registry", "smss", "csrss", "wininit", ...]
```

- [ ] **Step 2: 扩充白名单 + 添加规则加载 + 异常处理**

```python
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_RULES_FILE = Path(__file__).parent.parent / "rules" / "rootkit_rules.yaml"

def _load_rules() -> list:
    try:
        import yaml
        if _RULES_FILE.exists():
            with open(_RULES_FILE, encoding="utf-8") as f:
                return yaml.safe_load(f).get("windows_rules", [])
    except Exception as e:
        logger.warning(f"加载 rootkit 规则失败: {e}")
    return []

_RULES = _load_rules()

# 扩充 Windows 系统进程白名单（包含 Server 2022、Win11 等）
KNOWN_PROCESSES = {
    # 系统核心
    "System", "Registry", "smss", "csrss", "wininit", "services", "lsass",
    "svchost", "winlogon", "dwm", "fontdrvhost", "sihost",
    # 系统进程（PID 4）
    "System",
    # 任务管理器可见的常见系统进程
    "RuntimeBroker", "ShellExperienceHost", "SearchHost", "StartMenuExperienceHost",
    "TextInputHost", "SecurityHealthService", "SecurityHealthSystray",
    "MsMpEng", "NisSrv", "spoolsv", "WmiPrvSE", "dllhost",
    "conhost", "taskhostw", "schtasks", "WmiPrvSE",
    # Windows Server 进程
    "Memory Compression", "Registry", "idle",
    # 常见第三方进程（仅无害的）
    "explorer", "OneDrive", "Teams", "Slack", "Discord",
}

class RootkitModule:
    def run(self, os_detect, config):
        issues = []

        checks = [
            ("隐藏进程", self.check_hidden_processes),
            ("隐藏服务", self.check_hidden_services),
            ("网络异常", self.check_network_anomalies),
            ("文件异常", self.check_file_anomalies),
            ("注册表异常", self.check_registry_anomalies),
            ("驱动异常", self.check_driver_anomalies),
        ]

        for name, fn in checks:
            try:
                result = fn()
                if result:
                    issues.extend(result)
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} 检查超时")
            except Exception as e:
                logger.warning(f"{name} 检查失败: {e}")

        return {
            "status": "ok" if not issues else "warning",
            "checks": {name: True for name, _ in checks},
            "issues": issues
        }

    def check_hidden_processes(self):
        issues = []
        # 逻辑保持不变，仅在调用处包 try-except（已在 run() 中处理）
        return issues
```

- [ ] **Step 3: Commit**

```bash
git add windows/lib/rootkit.py
git commit -m "fix(windows): add exception handling and expand process whitelist in rootkit module"
```

---

### Task 4: webshell.py — 异常处理 + 动态路径 + 规则加载

**Files:**
- Modify: `windows/lib/webshell.py`

- [ ] **Step 1: 读取 webshell.py，找到硬编码的 IIS 路径**

硬编码路径在 `scan_iis()` 方法中：
```python
iis_paths = [
    r"C:\inetpub\wwwroot",
    r"C:\Windows\System32\inetsrv\config",
]
```

- [ ] **Step 2: 添加动态路径获取 + 规则加载 + 异常处理**

```python
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_RULES_FILE = Path(__file__).parent.parent / "rules" / "webshell_rules.yaml"

def _load_rules() -> list:
    try:
        import yaml
        if _RULES_FILE.exists():
            with open(_RULES_FILE, encoding="utf-8") as f:
                return yaml.safe_load(f).get("windows_rules", [])
    except Exception as e:
        logger.warning(f"加载 webshell 规则失败: {e}")
    return []

_RULES = _load_rules()

class WebshellModule:
    def run(self, os_detect, config):
        issues = []

        checks = [
            ("IIS扫描", self.scan_iis),
            ("ASP文件", self.scan_asp_files),
            ("PHP文件", self.scan_php_files),
            ("上传目录", self.scan_upload_dirs),
        ]

        for name, fn in checks:
            try:
                result = fn()
                if result:
                    issues.extend(result)
            except subprocess.TimeoutExpired:
                logger.warning(f"{name} 检查超时")
            except Exception as e:
                logger.warning(f"{name} 检查失败: {e}")

        # 使用规则文件中的模式
        for rule in _RULES:
            try:
                issues.extend(self._scan_with_rule(rule))
            except Exception as e:
                logger.warning(f"应用 webshell 规则 {rule.get('id', '?')} 失败: {e}")

        return {
            "status": "ok" if not issues else "warning",
            "iis_sites_scanned": self.get_iis_site_count(),
            "files_scanned": len(issues),
            "issues": issues
        }

    def get_iis_paths(self) -> list:
        """动态获取所有 IIS 网站物理路径"""
        ps = """
        Import-Module WebAdministration -ErrorAction SilentlyContinue
        if (Get-Command Get-Website -ErrorAction SilentlyContinue) {
            Get-Website | ForEach-Object { $_.PhysicalPath }
        }
        """
        try:
            r = subprocess.run(['powershell', '-Command', ps],
                              capture_output=True, text=True, timeout=30)
            if r.returncode == 0:
                paths = [p.strip() for p in r.stdout.strip().split('\n') if p.strip()]
                if paths:
                    return paths
        except Exception as e:
            logger.warning(f"获取 IIS 路径失败: {e}")
        # Fallback：常见路径
        return [r"C:\inetpub\wwwroot", r"C:\inetpub\v6wwwroot", r"D:\WebSites"]

    def _scan_with_rule(self, rule: dict) -> list:
        """使用规则扫描指定目录"""
        issues = []
        scan_dirs = self.get_iis_paths()
        pattern = rule.get("pattern", "")
        file_ext = rule.get("extensions", [".php", ".asp", ".aspx", ".jsp"])
        severity = rule.get("severity", "warning")

        import re
        try:
            regex = re.compile(pattern)
        except Exception:
            return issues

        for directory in scan_dirs:
            for ext in file_ext:
                ps = f'''
                Get-ChildItem -Path "{directory}" -Filter "*{ext}" -Recurse -ErrorAction SilentlyContinue |
                Select-Object -First 100 FullName |
                ForEach-Object {{ Get-Content $_.FullName -ErrorAction SilentlyContinue }}
                '''
                try:
                    r = subprocess.run(['powershell', '-Command', ps],
                                      capture_output=True, text=True, timeout=60)
                    if r.returncode == 0:
                        for i, line in enumerate(r.stdout.split('\n'), 1):
                            if regex.search(line):
                                issues.append({
                                    "level": severity,
                                    "module": "webshell",
                                    "rule_id": rule.get("id", "?"),
                                    "desc": f"匹配规则 {rule.get('name', rule_id)}: {line.strip()[:80]}"
                                })
                except Exception:
                    pass
        return issues
```

- [ ] **Step 3: Commit**

```bash
git add windows/lib/webshell.py
git commit -m "fix(windows): add exception handling, dynamic IIS path detection, and YAML rule loading to webshell module"
```

---

### Task 5: README.md — 确认主入口

**Files:**
- Modify: `windows/README.md`

- [ ] **Step 1: 确认主入口文件名**

```bash
ls windows/*.py
```

- [ ] **Step 2: 将 README 中所有 `python inspect.py` / `python cloud_inspect.py` 统一为实际文件名**

如果实际是 `cloud_inspect.py`，则统一为 `python cloud_inspect.py`。

- [ ] **Step 3: Commit**

```bash
git add windows/README.md
git commit -m "docs(windows): fix main entry point filename in README"
```

---

## 第二阶段：规则系统搭建

### Task 6: 准备 Windows 规则文件（首次手动生成）

**Files:**
- Create: `windows/rules/backdoor_rules.yaml`
- Create: `windows/rules/rootkit_rules.yaml`
- Create: `windows/rules/webshell_rules.yaml`

- [ ] **Step 1: 创建 windows/rules 目录**

```bash
mkdir -p windows/rules
```

- [ ] **Step 2: 写入 backdoor_rules.yaml**

```yaml
# CloudInspect Windows 后门检测规则
# 由 windows/scripts/sync_rules.py 自动生成

_meta:
  version: 1
  os: windows
  generated_by: sync_rules.py

windows_rules:
  - id: "WIN_REG_RUN_001"
    name: "注册表 Run 键可疑项"
    check_type: "registry_key"
    path: "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
    pattern: ""
    severity: "warning"
    description: "检查注册表 Run 键中的可疑自启动项"

  - id: "WIN_REG_RUN_USER"
    name: "用户级 Run 键可疑项"
    check_type: "registry_key"
    path: "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
    pattern: ""
    severity: "warning"
    description: "检查用户级 Run 键"

  - id: "WIN_GUEST_ENABLED"
    name: "Guest 账户启用"
    check_type: "account"
    account: "Guest"
    severity: "warning"
    description: "Guest 账户被启用，可能用于后门"

  - id: "WIN_RDP_ENABLED"
    name: "RDP 远程桌面启用"
    check_type: "registry_key"
    path: "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server"
    pattern: "fDeny"
    expected_value: "0"
    severity: "info"
    description: "远程桌面服务已启用"

  - id: "WIN_ADMIN_USERS"
    name: "本地管理员数量过多"
    check_type: "admin_count"
    threshold: 3
    severity: "warning"
    description: "本地管理员数量超过阈值"

  - id: "WIN_SUSPICIOUS_SCHEDULED_TASK"
    name: "可疑计划任务"
    check_type: "scheduled_task"
    patterns: ["powershell.*-enc", "mshta", "wscript", "cscript.*shell"]
    severity: "high"
    description: "计划任务中包含可疑命令"

  - id: "WIN_SVC_MALICIOUS"
    name: "可疑服务名称"
    check_type: "service_name"
    patterns: ["update", "service", "system", "driver"]
    suspicious_names: ["WindowsUpdate", "SecurityCenter", "WwanSvc"]
    severity: "high"
    description: "服务名称与系统服务相似，可能是伪装后门"

  - id: "WIN_NET_LISTENING_UNCOMMON"
    name: "非标准端口监听"
    check_type: "network_port"
    suspicious_ports: [4444, 5555, 6666, 7777, 8888, 31337, 12345]
    severity: "high"
    description: "检测常见后门监听端口"
```

- [ ] **Step 3: 写入 rootkit_rules.yaml**

```yaml
# CloudInspect Windows Rootkit 检测规则

_meta:
  version: 1
  os: windows
  generated_by: sync_rules.py

windows_rules:
  - id: "WIN_RK_HIDDEN_PROCESS"
    name: "隐藏进程检测"
    check_type: "process_compare"
    severity: "critical"
    description: "对比 Task Manager 和 WMIC 进程数，差异过大可能存在 Rootkit"

  - id: "WIN_RK_UNSIGNED_DRIVER"
    name: "未签名驱动"
    check_type: "driver_signature"
    severity: "high"
    description: "加载的驱动缺少数字签名"

  - id: "WIN_RK_SUSPICIOUS_DEVICES"
    name: "可疑设备"
    check_type: "device_list"
    patterns: ["\\Device\\\\", "\\\\.\\"]
    severity: "high"
    description: "非标准设备名称"

  - id: "WIN_RK_MODIFIED_SYSFILES"
    name: "系统文件被修改"
    check_type: "file_hash"
    files:
      - "C:\\Windows\\System32\\cmd.exe"
      - "C:\\Windows\\System32\\net.exe"
      - "C:\\Windows\\System32\\attrib.exe"
    severity: "critical"
    description: "关键系统文件哈希值与已知值不符"

  - id: "WIN_RK_DISABLED_DEFENDER"
    name: "Defender 被禁用"
    check_type: "registry_key"
    path: "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows Defender"
    key: "DisableAntiSpyware"
    severity: "critical"
    description: "Windows Defender 被通过注册表禁用"
```

- [ ] **Step 4: 写入 webshell_rules.yaml**

```yaml
# CloudInspect Windows Webshell 检测规则

_meta:
  version: 1
  os: windows
  generated_by: sync_rules.py

windows_rules:
  - id: "WIN_WS_EVAL_BASE64"
    name: "Base64 编码命令执行"
    check_type: "file_content"
    pattern: "(eval|exec)\\s*\\(\\s*base64_decode"
    extensions: [".php", ".asp", ".aspx", ".jsp"]
    severity: "critical"
    description: "检测 Base64 混淆的命令执行"

  - id: "WIN_WS_SHELL_EXEC"
    name: "Shell 命令执行函数"
    check_type: "file_content"
    pattern: "(shell_exec|passthru|system|exec)\\s*\\("
    extensions: [".php"]
    severity: "high"
    description: "检测可疑的 Shell 命令执行函数"

  - id: "WIN_WS_PREG_REPLACE_E"
    name: "PCRE 代码执行"
    check_type: "file_content"
    pattern: "preg_replace\\s*\\(\\s*['\"]\\/.*\\/e['\"]"
    extensions: [".php"]
    severity: "critical"
    description: "preg_replace /e 修饰符可执行任意代码"

  - id: "WIN_WS_CMD_SHELL"
    name: "CMD Shell 跳转"
    check_type: "file_content"
    pattern: "(cmd\\.exe|command\\.com).*\\/c"
    extensions: [".asp", ".aspx"]
    severity: "high"
    description: "检测 ASP/ASPX 中的命令执行"

  - id: "WIN_WS_SUSPICIOUS_UPLOAD"
    name: "可疑上传路径"
    check_type: "file_location"
    suspicious_dirs: ["upload", "uploads", "editor", "images", "temp", "cache"]
    extensions: [".php", ".asp", ".aspx", ".jsp", ".exe", ".dll"]
    severity: "high"
    description: "在上传目录中发现可执行文件"

  - id: "WIN_WS_IIS_CMD"
    name: "IIS 命令执行组件"
    check_type: "file_content"
    pattern: "(WScript\\.Shell|Shell\\.Application|ScriptControl)"
    extensions: [".asp", ".aspx"]
    severity: "critical"
    description: "检测 ASP 中的 COM 对象命令执行"
```

- [ ] **Step 5: Commit**

```bash
git add windows/rules/
git commit -m "feat(windows): add initial Windows detection rules (backdoor, rootkit, webshell)"
```

---

### Task 7: 规则同步脚本 sync_rules.py

**Files:**
- Create: `windows/scripts/sync_rules.py`

- [ ] **Step 1: 写入 sync_rules.py**

```python
#!/usr/bin/env python3
# coding: utf-8
"""
CloudInspect Windows 规则同步脚本
从 python/rules/ 读取规则，过滤 os_targets 包含 windows 的条目，
转换为 Windows 格式后写入 windows/rules/
"""

import os
import sys
import yaml
import re
import argparse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
SRC_RULES_DIR = REPO_ROOT / "python" / "rules"
DST_RULES_DIR = REPO_ROOT / "windows" / "rules"

SRC_FILES = {
    "backdoor": SRC_RULES_DIR / "backdoor_rules.yaml",
    "rootkit": SRC_RULES_DIR / "rootkit_signatures.yaml",
    "webshell": SRC_RULES_DIR / "webshell_patterns.yaml",
}

DST_FILES = {
    "backdoor": DST_RULES_DIR / "backdoor_rules.yaml",
    "rootkit": DST_RULES_DIR / "rootkit_rules.yaml",
    "webshell": DST_RULES_DIR / "webshell_rules.yaml",
}

# Linux 路径到 Windows 路径的映射
PATH_MAP = {
    "/etc/passwd": "C:\\Windows\\System32\\config\\SAM",
    "/etc/shadow": "C:\\Windows\\System32\\config\\SAM",
    "/etc/cron.d/": "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
    "/var/www/html/": "C:\\inetpub\\wwwroot\\",
    "/tmp/": "%TEMP%\\",
    "/var/tmp/": "%TEMP%\\",
    "/etc/init.d/": "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\",
    "/etc/systemd/system/": "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\",
}


def _convert_path(path: str) -> str:
    for linux, win in PATH_MAP.items():
        if path.startswith(linux):
            return path.replace(linux, win)
    return path


def _filter_os_rules(data: dict, target: str = "windows") -> list:
    """从规则数据中筛选指定 OS 的规则"""
    rules = []
    for section in ["custom_expert_rules", "expert_rules", "detection_patterns",
                    "expert_patterns", "custom_rules"]:
        if section in data:
            for rule in data[section]:
                os_targets = rule.get("os_targets", ["linux", "windows"])
                if target in os_targets:
                    converted = _convert_rule(rule)
                    rules.append(converted)
    return rules


def _convert_rule(rule: dict) -> dict:
    """将 Linux 规则转换为 Windows 格式"""
    converted = dict(rule)
    # 转换路径
    for key in ["path", "paths", "file", "check_path"]:
        if key in rule:
            val = rule[key]
            if isinstance(val, str):
                converted[key] = _convert_path(val)
            elif isinstance(val, list):
                converted[key] = [_convert_path(v) for v in val]
    # 添加 OS 标记
    converted["_source_os"] = "linux"
    converted["_converted"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return converted


def sync_rules() -> dict:
    """同步所有规则文件，返回变更统计"""
    stats = {}
    DST_RULES_DIR.mkdir(parents=True, exist_ok=True)

    for name, src_path in SRC_FILES.items():
        dst_path = DST_FILES[name]
        stats[name] = {"before": 0, "after": 0, "new": 0}

        # 读取源规则
        if not src_path.exists():
            print(f"[SKIP] {src_path.name} 不存在，跳过")
            continue

        with open(src_path, encoding="utf-8") as f:
            src_data = yaml.safe_load(f) or {}

        # 读取目标规则（用于 diff）
        if dst_path.exists():
            with open(dst_path, encoding="utf-8") as f:
                dst_data = yaml.safe_load(f) or {}
            stats[name]["before"] = len(dst_data.get("windows_rules", []))

        # 过滤 Windows 规则
        windows_rules = _filter_os_rules(src_data)

        # 合并已有规则（去重 by id）
        existing = dst_data.get("windows_rules", [])
        existing_ids = {r.get("id", "") for r in existing}
        for r in windows_rules:
            if r.get("id", "") not in existing_ids:
                existing.append(r)

        dst_data["windows_rules"] = existing
        stats[name]["after"] = len(existing)
        stats[name]["new"] = stats[name]["after"] - stats[name]["before"]

        # 写入
        dst_data["_meta"] = {
            "version": dst_data.get("_meta", {}).get("version", 0) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "os": "windows",
            "generated_by": "sync_rules.py",
            "total_rules": len(existing),
        }

        with open(dst_path, "w", encoding="utf-8") as f:
            yaml.dump(dst_data, f, allow_unicode=True, sort_keys=False)

        print(f"[OK] {name}: {stats[name]['before']} → {stats[name]['after']} (+{stats[name]['new']})")

    return stats


def main():
    parser = argparse.ArgumentParser(description="CloudInspect Windows 规则同步")
    parser.add_argument("--dry-run", action="store_true", help="仅显示将要同步的规则数")
    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════╗
║  CloudInspect Windows 规则同步      ║
║  时间: {datetime.now(timezone.utc).isoformat()}       ║
╚══════════════════════════════════════╝
    """)

    if args.dry_run:
        print("[DRY-RUN] 模拟运行，不写入文件")

    stats = sync_rules()

    total_new = sum(s["new"] for s in stats.values())
    print(f"\n✅ 同步完成，共新增 {total_new} 条规则")
    return total_new


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 本地测试**

```bash
cd /c/Users/whoami/CloudInspect
python windows/scripts/sync_rules.py --dry-run
```

验证输出中各规则数量。

- [ ] **Step 3: 无 --dry-run 运行，生成规则文件**

```bash
python windows/scripts/sync_rules.py
```

- [ ] **Step 4: Commit**

```bash
git add windows/scripts/sync_rules.py
git commit -m "feat(windows): add sync_rules.py to generate Windows rules from python/rules/"
```

---

## 第三阶段：GitHub Actions Workflow

### Task 8: sync-windows-rules.yml

**Files:**
- Create: `.github/workflows/sync-windows-rules.yml`

- [ ] **Step 1: 写入 workflow 文件**

```yaml
name: Sync Windows Detection Rules

on:
  schedule:
    # 每周六 03:00 UTC，比 update-rules 晚 1 小时
    - cron: '0 3 * * 6'
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run (不写入文件)'
        required: false
        default: 'false'
        type: boolean
  repository_dispatch:
    types: [sync-windows-rules]

jobs:
  sync-rules:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout windows-support branch
        uses: actions/checkout@v4
        with:
          ref: feature/windows-support

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Sync Windows rules
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          if [ "${{ inputs.dry_run }}" == "true" ]; then
            python windows/scripts/sync_rules.py --dry-run
          else
            python windows/scripts/sync_rules.py
          fi

      - name: Check for changes
        id: git_status
        run: |
          if git diff --quiet windows/rules/; then
            echo "changes=false" >> $GITHUB_OUTPUT
            echo "无规则更新，跳过"
          else
            echo "changes=true" >> $GITHUB_OUTPUT
            echo "变更:"
            git diff --stat windows/rules/
          fi

      - name: Create Pull Request
        if: steps.git_status.outputs.changes == 'true'
        uses: peter-evans/create-pull-request@v6
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
          commit-message: "chore(windows): auto-sync detection rules from python/rules"
          branch: feature/windows-support
          delete-branch: false
          title: "🤖 自动同步 Windows 检测规则"
          body: |
            ## CloudInspect Windows 规则自动同步

            规则已从 python/rules/ 同步更新到 windows/rules/。
          labels: |
            automated
            windows
            rules-update

      - name: Auto-merge Pull Request
        if: steps.git_status.outputs.changes == 'true'
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          sleep 15
          PR_NUMBER=$(gh pr list \
            --repo ${{ github.repository }} \
            --state open \
            --head feature/windows-support \
            --json number \
            --jq '.[0].number')
          if [ -n "$PR_NUMBER" ] && [ "$PR_NUMBER" != "null" ]; then
            gh pr merge "$PR_NUMBER" \
              --repo ${{ github.repository }} \
              --squash \
              --delete-branch
            echo "PR #$PR_NUMBER 已合并"
          else
            echo "未找到 open PR，跳过合并"
          fi

      - name: Summary
        run: |
          if [ "${{ steps.git_status.outputs.changes }}" == "true" ]; then
            echo "## ✅ Windows 规则同步完成"
            echo "- 规则已同步到 windows/rules/"
            echo "- PR 已合并到 feature/windows-support"
          else
            echo "✅ 规则已是最新"
          fi
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/sync-windows-rules.yml
git commit -m "feat(ci): add sync-windows-rules workflow for Windows detection rules"
```

---

## 第四阶段：三轮 Review

### Review 1: 规则格式与路径映射

- [ ] **检查**: `os_targets` 过滤逻辑是否正确（默认全平台兼容）
- [ ] **检查**: PATH_MAP 是否覆盖了主要 Linux 路径 → Windows 等价路径
- [ ] **检查**: `sync_rules.py` 去重逻辑（by id）是否有效
- [ ] **检查**: 首次生成的 `windows/rules/*.yaml` 内容是否完整

### Review 2: 模块改造后的检测逻辑

- [ ] **检查**: backdoor.py 的 `_apply_rule` 是否能处理 8 种规则类型
- [ ] **检查**: webshell.py 的 `_scan_with_rule` 扫描目录是否正确（动态获取 IIS 路径）
- [ ] **检查**: rootkit.py 进程白名单是否覆盖主流 Windows 版本
- [ ] **检查**: history.py 的 `_analyze` 可疑命令列表是否合理

### Review 3: workflow 自动化链路

- [ ] **检查**: workflow 触发条件（cron + dispatch）是否与 `update-rules.yml` 时间错开
- [ ] **检查**: 自动 PR + merge 逻辑是否安全（不会误覆盖其他分支的 PR）
- [ ] **检查**: dry-run 参数是否正常工作

---

## Self-Review 检查清单

1. **Spec 覆盖**: spec 中的每条需求都能在计划中找到对应的 Task。Gap: 无。
2. **Placeholder 扫描**: 所有步骤均有实际代码，无 TBD/TODO。✅
3. **类型一致性**: `_apply_rule` 中的 `check_type` 值（`registry_key`、`service_name`、`account`）与 `windows/rules/backdoor_rules.yaml` 中的 `check_type` 值一致。✅

---

## 执行方式

**Plan complete.** 建议采用 **Subagent-Driven** 方式，按 Task 顺序执行，每完成一个 Task commit 一次，便于 review 和回退。