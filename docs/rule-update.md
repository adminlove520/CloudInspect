# 规则自动更新机制

**CloudInspect 规则更新原理与使用方法**

---

## 规则文件

CloudInspect 包含以下规则文件：

| 文件 | 说明 | 更新频率 |
|---|---|---|
| `python/rules/backdoor_rules.yaml` | 后门检测规则 | 每周 |
| `python/rules/rootkit_signatures.yaml` | Rootkit 特征库 | 每周 |
| `python/rules/webshell_patterns.yaml` | Webshell 检测模式 | 每周 |

---

## 规则结构

### 示例：backdoor_rules.yaml

```yaml
_meta:
  version: "1.0.20260610"
  updated: "2026-06-10"
  total_rules: 15
  source: "custom + emerging_threats"

custom_expert_rules:
  - id: "LD_PRELOAD_001"
    name: "LD_PRELOAD 后门"
    description: "检测 LD_PRELOAD 环境变量或预加载文件"
    patterns:
      - "LD_PRELOAD"
      - "/etc/ld.so.preload"
    severity: "critical"
    reference: "GScan-L004"

  - id: "SSH_WRAPPER_001"
    name: "SSH Wrapper 后门"
    description: "检测被篡改的 sshd"
    patterns:
      - "/usr/sbin/sshd.bak"
      - "sshd.*wrapper"
    severity: "critical"
    reference: "GScan-L001"

emerging_threats:
  - source: "emerging_threats"
    name: "Malicious IP List"
    updated: "2026-06-10"
    description: "已知恶意 IP 地址列表"
    data:
      - "192.0.2.0/24"  # 示例 IP 段
```

---

## 更新机制

### GitHub Actions 自动更新

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions                            │
│                      (每周六 02:00 UTC)                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 触发条件                                                 │
│     ├── 定时: cron '0 2 * * 6' (每周六凌晨)                  │
│     ├── 手动: workflow_dispatch                              │
│     └── API: repository_dispatch                            │
│                                                             │
│  2. 执行脚本                                                 │
│     └── python .github/scripts/update_rules.py               │
│                                                             │
│  3. 数据源                                                   │
│     ├── 自定义专家规则 (本地)                                │
│     ├── Emerging Threats (可选)                             │
│     ├── AlienVault OTX (可选, 需要 API Key)                  │
│     └── AbuseIPDB (可选, 需要 API Key)                       │
│                                                             │
│  4. 合并规则                                                 │
│     ├── 去重                                                 │
│     ├── 版本控制                                             │
│     └── 格式验证                                             │
│                                                             │
│  5. 创建 PR                                                  │
│     └── feature/auto-update-rules                            │
│                                                             │
│  6. 自动合并                                                 │
│     └── 无人 Review 时自动合并到 main                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 本地更新规则

### 手动更新

```bash
# 更新所有规则
python .github/scripts/update_rules.py --source all

# 仅更新后门规则
python .github/scripts/update_rules.py --source backdoor

# 仅更新 Rootkit 规则
python .github/scripts/update_rules.py --source rootkit

# 仅更新 Webshell 规则
python .github/scripts/update_rules.py --source webshell
```

### 使用外部数据源

```bash
# 设置 API Key（可选）
export OTX_API_KEY="your_otx_api_key"
export ABUSEIPDB_API_KEY="your_abuseipdb_api_key"

# 更新规则
python .github/scripts/update_rules.py --source all
```

---

## 管理规则版本

### 查看当前规则版本

```bash
# 查看后门规则版本
grep "_meta" -A 5 python/rules/backdoor_rules.yaml

# 查看更新日期
grep "updated:" python/rules/*.yaml
```

### 回滚规则

```bash
# 查看规则提交历史
git log --oneline python/rules/

# 回滚到指定版本
git checkout abc1234 -- python/rules/

# 或回滚到上一个版本
git revert HEAD
```

---

## 自定义规则

### 添加自定义后门规则

编辑 `python/rules/backdoor_rules.yaml`:

```yaml
custom_expert_rules:
  # ... 现有规则 ...

  - id: "CUSTOM_001"
    name: "自定义后门检测"
    description: "描述此规则检测什么"
    patterns:
      - "可疑字符串1"
      - "可疑字符串2"
    severity: "warning"  # critical | warning | info
    reference: "自定义规则"
```

### 添加自定义 Webshell 模式

编辑 `python/rules/webshell_patterns.yaml`:

```yaml
php_patterns:
  # ... 现有模式 ...

  - id: "PHP_CUSTOM_001"
    name: "自定义 PHP Webshell"
    pattern: "可疑模式"
    severity: "high"
```

---

## 规则更新日志

### 查看更新历史

```bash
# 查看规则文件的变更
git log --oneline python/rules/

# 查看具体变更
git diff HEAD~1 python/rules/
```

### 规则更新通知

GitHub Actions 运行后会自动：
1. 创建 Pull Request
2. 在 PR 中说明更新内容
3. 更新 `_meta` 中的版本号

---

## API Key 配置

### GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret 名称 | 用途 | 获取地址 |
|---|---|---|
| `OTX_API_KEY` | AlienVault OTX API Key | https://otx.alienvault.com/api |
| `ABUSEIPDB_API_KEY` | AbuseIPDB API Key | https://www.abuseipdb.com/account/api |

### 本地环境变量

```bash
# 设置环境变量
export OTX_API_KEY="your_otx_api_key"
export ABUSEIPDB_API_KEY="your_abuseipdb_api_key"

# 运行更新
python .github/scripts/update_rules.py --source all
```

---

## 故障排查

### Q: 规则更新失败

```bash
# 查看错误日志
python .github/scripts/update_rules.py --source all --verbose

# 检查网络连接
curl -I https://rules.emergingthreats.net

# 检查 API Key
echo $OTX_API_KEY
echo $ABUSEIPDB_API_KEY
```

### Q: 规则格式错误

```bash
# 验证 YAML 格式
python3 -c "import yaml; yaml.safe_load(open('python/rules/backdoor_rules.yaml'))"

# 验证规则结构
python3 .github/scripts/update_rules.py --validate
```

---

*最后更新: 2026-06-11*