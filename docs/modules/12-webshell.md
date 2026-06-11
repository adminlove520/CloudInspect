# 12 - Webshell 检测

**Webshell 特征扫描模块**

---

## 功能说明

Webshell 检测模块通过特征库扫描 Web 目录，发现：
- 常见 Webshell 特征
- 编码 Webshell
- 一句话木马
- 冰蝎、蚁剑等工具生成的 Webshell

**注意**: 此模块仅在 `emergency` 和 `full` 模式下运行。

---

## 检测内容

### Webshell 特征库

CloudInspect 内置以下 Webshell 特征：

#### PHP Webshell

| 特征 | 说明 | 风险 |
|---|---|---|
| `eval(` | 一句话木马核心 | 高 |
| `base64_decode` | Base64 编码隐藏 | 高 |
| `system(`, `exec(`, `passthru(` | 命令执行函数 | 中 |
| `shell_exec(`, `proc_open(` | 命令执行函数 | 中 |
| `$_POST[...](` | 动态函数调用 | 高 |
| `assert(` | 代码执行 | 高 |
| `create_function` | 动态创建函数 | 高 |

#### JSP Webshell

| 特征 | 说明 | 风险 |
|---|---|---|
| `Runtime.getRuntime()` | 命令执行 | 高 |
| `ProcessBuilder` | 进程构建 | 高 |
| `ProcessImpl` | 进程实现 | 高 |
| `java.lang.Process` | Java 进程 | 高 |

#### ASP/ASPX Webshell

| 特征 | 说明 | 风险 |
|---|---|---|
| `Execute(`, `Eval(` | 代码执行 | 高 |
| `WScript.Shell` | 命令执行 | 高 |
| `Shell.Application` | 系统命令 | 高 |

### 扫描路径

默认扫描以下 Web 目录：

| 路径 | 说明 |
|---|---|
| `/var/www` | 默认 Web 根目录 |
| `/usr/local/apache2/htdocs` | Apache 默认 |
| `/usr/share/nginx/html` | Nginx 默认 |
| `/home/*/public_html` | 用户 Web 目录 |
| `/opt` | 其他应用目录 |

---

## 输出示例

### HTML 报告

```
┌─────────────────────────────────────────┐
│  🐚 Webshell 检测                        │
├─────────────────────────────────────────┤
│  扫描路径: /var/www, /home/*/public_html │
│  扫描文件: 1,234 个                      │
│  检测时间: 45 秒                         │
│                                         │
│  ⚠️ 发现可疑文件:                         │
│                                         │
│  └─ /var/www/html/uploads/shell.php     │
│     ├─ 特征: eval(base64_decode(...))    │
│     ├─ 风险: 高                          │
│     └─ 大小: 2.3KB                        │
└─────────────────────────────────────────┘
```

### JSON 输出

```json
{
  "webshell": {
    "scanned_paths": ["/var/www", "/home/*/public_html"],
    "scanned_files": 1234,
    "scan_duration_seconds": 45,
    "detections": [
      {
        "path": "/var/www/html/uploads/shell.php",
        "matched_patterns": ["eval(base64_decode(...))"],
        "risk": "high",
        "size_bytes": 2355,
        "modified": "2026-06-10 14:00:00"
      }
    ],
    "issues": [
      {
        "level": "warning",
        "module": "webshell",
        "desc": "发现可疑 Webshell: /var/www/html/uploads/shell.php"
      }
    ]
  }
}
```

---

## 告警规则

| 规则 | 条件 | 级别 | 说明 |
|---|---|---|---|
| 高风险 Webshell | 匹配多个高风险特征 | 严重 | 立即处理 |
| 中风险 Webshell | 匹配中风险特征 | 警告 | 需人工确认 |
| 编码 Webshell | Base64 等编码 | 警告 | 需审查 |

---

## 使用场景

### 应急排查

```bash
# 包含 Webshell 检测（30-60 分钟）
./inspect.sh -m emergency

# 扫描结果会保存在报告中
```

### 完全扫描

```bash
# 最深度 Webshell 扫描（60+ 分钟）
./inspect.sh -m full

# 扫描更多目录
```

### 手动扫描

```bash
# 使用 grep 快速扫描
grep -r "eval(" /var/www/html/*.php
grep -r "base64_decode" /var/www/html/*.php

# 使用 find 查找可疑文件
find /var/www -name "*.php" -exec grep -l "eval\|base64" {} \;

# 使用 Webshell 扫描工具
# 如: https://github.com/webshell fuzz/
```

---

## 故障排查

**Q: 发现 Webshell**

```bash
# 1. 确认文件
cat /var/www/html/uploads/shell.php

# 2. 分析功能
# - 查看代码逻辑
# - 确认是否是业务代码

# 3. 如果确认是 Webshell
# - 备份（用于分析）
cp /var/www/html/uploads/shell.php /tmp/backup_shell.php
# - 删除
rm /var/www/html/uploads/shell.php

# 4. 检查是否有其他文件
find /var/www -name "*.php" -newer /tmp/backup_shell.php

# 5. 检查访问日志
grep "shell.php" /var/log/nginx/access.log

# 6. 检查是谁上传的
# - 查看 FTP 日志
# - 查看 Web 访问日志
# - 检查上传功能

# 7. 加固
# - 限制上传文件类型
# - 限制 PHP 执行权限
# - 检查漏洞来源
```

**Q: 扫描太慢**

```bash
# 编辑 config/default.yaml
scan:
  # 添加更多扫描路径
  webshell_paths:
    - /var/www
    - /home
    - /opt

  # 排除目录
  exclude_paths:
    - /var/www/cache
    - /var/www/logs

  # 限制文件大小
  max_file_size: "5M"
```

---

## 加固建议

### 防止 Webshell 上传

```nginx
# Nginx 配置
location ~* \.(php|php[3-7]|phtml)$ {
    deny all;
}

# 仅允许上传目录执行 PHP
location /uploads {
    location ~* \.php$ {
        deny all;
    }
}
```

### 目录权限

```bash
# 设置正确的目录权限
chown -R www-data:www-data /var/www/html
chmod -R 755 /var/www/html
chmod -R 644 /var/www/html/*.php

# 可写目录禁止执行
chmod 755 /var/www/html/uploads
```

---

*最后更新: 2026-06-11*