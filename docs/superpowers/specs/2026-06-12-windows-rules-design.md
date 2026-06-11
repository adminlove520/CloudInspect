# CloudInspect Windows 支持增强 — 设计文档

**日期**: 2026-06-12
**状态**: 设计中

---

## 1. 目标

本次变更包含三件事：
1. 修复 Windows 4 个新模块（backdoor、history、rootkit、webshell）的 bug
2. 将 Windows 检测从硬编码改为 YAML 规则驱动，实现与 Linux 规则源共用
3. 新增独立的 GitHub Actions workflow，将 Linux 规则同步为 Windows 专用规则

---

## 2. 现有问题（需修复）

### 2.1 新模块 bug

| # | 问题 | 位置 | 严重度 |
|---|---|---|---|
| 1 | `run()` 方法缺少 try-except，`subprocess.run` 失败时整个模块崩溃 | backdoor.py, rootkit.py, webshell.py, history.py | 严重 |
| 2 | `webshell.py` 硬编码 IIS 路径 `C:\inetpub\wwwroot`，不兼容自定义路径 | webshell.py | 中等 |
| 3 | `rootkit.py` 进程白名单不完整，可能大量误报 | rootkit.py | 中等 |
| 4 | 主入口文件名在 README 和代码中不一致（cloud_inspect.py vs inspect.py） | README.md | 次要 |

---

## 3. 规则架构设计

### 3.1 格式扩展

`python/rules/` 下的规则文件（backdoor_rules.yaml、rootkit_signatures.yaml、webshell_patterns.yaml）每条规则增加 `_os_targets` 字段：

```yaml
rules:
  - id: "LD_PRELOAD_001"
    name: "LD_PRELOAD 后门"
    os_targets: ["linux"]          # 逗号分隔，不填则表示全平台
    patterns: ["LD_PRELOAD", ...]
    severity: "critical"

  - id: "WIN_REG_RUN_001"
    name: "注册表 Run 键后门"
    os_targets: ["windows"]
    patterns: ["HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"]
    severity: "high"
```

**默认值**：`os_targets` 不填的规则视为 `["linux", "windows"]`（向后兼容现有规则）。

### 3.2 Windows 规则输出目录

```
windows/rules/
├── backdoor_rules.yaml      # Windows 后门检测规则
├── rootkit_rules.yaml       # Windows Rootkit 规则
└── webshell_rules.yaml      # Windows Webshell 模式
```

每个文件只包含 `os_targets` 包含 `windows` 的规则，并按 Windows 路径格式重新组织。

### 3.3 规则同步脚本

新建 `windows/scripts/sync_rules.py`，逻辑：

1. 读取 `python/rules/*.yaml`
2. 过滤 `os_targets` 包含 `windows` 的规则
3. 转换路径格式（如 `/etc/passwd` → `C:\Windows\System32\config\SAM`）
4. 写入 `windows/rules/`
5. 若有变更，输出 diff summary

路径映射表（示例）：

| Linux | Windows |
|---|---|
| `/etc/passwd` | `C:\Windows\System32\config\SAM` |
| `/etc/shadow` | `C:\Windows\System32\config\SAM`（需 SYSTEM 权限） |
| `/etc/cron.d/` | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run` |
| `/var/www/html/` | `C:\inetpub\wwwroot\` |
| `systemctl list-units` | `Get-Service` |

---

## 4. Windows 模块改造

### 4.1 模块加载规则文件

每个 Windows 模块在 `run()` 初始化时加载对应的规则文件：

```python
import yaml
from pathlib import Path

class BackdoorModule:
    def __init__(self):
        rules_path = Path(__file__).parent.parent / "rules" / "backdoor_rules.yaml"
        with open(rules_path, encoding="utf-8") as f:
            self.rules = yaml.safe_load(f).get("rules", [])

    def run(self, os_detect, config):
        # 过滤 Windows 适用规则
        windows_rules = [r for r in self.rules if "windows" in r.get("os_targets", ["windows"])]
        # ... 用规则驱动检测
```

### 4.2 异常处理

每个模块的 `run()` 和各 check 方法添加 try-except，失败时记录日志但不中断：

```python
def run(self, os_detect, config):
    issues = []
    try:
        issues.extend(self.check_startup_backdoors())
    except Exception as e:
        log_warning(f"启动项检查失败: {e}")
    return {"status": "ok", "issues": issues}
```

### 4.3 Webshell 路径动态化

用 PowerShell `Get-Website` 获取真实 IIS 路径，不再硬编码：

```python
def get_iis_paths(self):
    ps = "Import-Module WebAdministration; (Get-Website | ForEach-Object { $_.PhysicalPath })"
    result = subprocess.run(['powershell', '-Command', ps], capture_output=True, text=True, timeout=30)
    if result.returncode == 0:
        return [p.strip() for p in result.stdout.strip().split('\n') if p.strip()]
    return [r"C:\inetpub\wwwroot"]  # fallback
```

---

## 5. GitHub Actions Workflow

### 5.1 新增 workflow

文件：`.github/workflows/sync-windows-rules.yml`（放在仓库根目录，与 `update-rules.yml` 同级）

```yaml
name: Sync Windows Detection Rules

on:
  schedule:
    - cron: '0 3 * * 6'    # 比 update-rules 晚 1 小时
  workflow_dispatch:
  repository_dispatch:
    types: [sync-windows-rules]
```

触发时机比 `update-rules.yml` 晚 1 小时，确保 Linux 规则先更新完毕。

### 5.2 执行步骤

1. Checkout（windows-support 分支）
2. 运行 `windows/scripts/sync_rules.py`
3. 检查 `windows/rules/` 是否有变更
4. 若有变更，创建 PR 到 `feature/windows-support`
5. 若无变更，静默结束

**关键**：这个 workflow 只改动 `windows/rules/`，不和 main 分支的 `update-rules.yml` 竞争。

---

## 6. 文件变更清单

| 操作 | 文件 |
|---|---|
| 修改 | `windows/core/detector.py` — emergency/full 模块列表已正确，待确认 |
| 修改 | `windows/README.md` — 主入口确认、文档更新 |
| 修改 | `python/rules/backdoor_rules.yaml` — 增加 `os_targets` 字段（Windows 规则） |
| 修改 | `python/rules/rootkit_signatures.yaml` — 同上 |
| 修改 | `python/rules/webshell_patterns.yaml` — 同上 |
| 修改 | `windows/lib/backdoor.py` — 异常处理 + 规则加载 |
| 修改 | `windows/lib/history.py` — 异常处理 + 规则加载 |
| 修改 | `windows/lib/rootkit.py` — 异常处理 + 规则加载 + 白名单优化 |
| 修改 | `windows/lib/webshell.py` — 异常处理 + 规则加载 + 动态路径 |
| 新增 | `windows/scripts/sync_rules.py` — 规则同步脚本 |
| 新增 | `windows/rules/backdoor_rules.yaml` — Windows 后门规则 |
| 新增 | `windows/rules/rootkit_rules.yaml` — Windows Rootkit 规则 |
| 新增 | `windows/rules/webshell_rules.yaml` — Windows Webshell 规则 |
| 新增 | `.github/workflows/sync-windows-rules.yml` — Windows 规则同步 workflow（放在根目录，不在 windows/ 子目录） |

---

## 7. 风险与注意事项

- **规则文件格式兼容性**：现有规则没有 `os_targets` 字段，默认行为为全平台适用，需逐条审查新增的 Windows 规则不与 Linux 规则冲突
- **workflow 目录结构**：workflow 必须放在仓库根目录 `.github/workflows/`，GitHub Actions 不识别子目录中的 workflow 文件
- **Windows 分支冲突**：新增 workflow 文件在 windows-support 分支，与 main 分支独立，不会冲突
- **规则路径映射**：部分 Linux 规则（如 `/etc/shadow`）在 Windows 无等价物，映射表需完善

---

## 8. 三轮 Review

每轮 Review 聚焦：
1. **第一轮**：规则格式设计、路径映射表是否合理
2. **第二轮**：模块改造后的检测逻辑是否正确
3. **第三轮**：workflow 触发条件和自动化链路是否完整