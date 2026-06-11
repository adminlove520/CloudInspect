# coding: utf-8
"""
Windows Webshell 检测模块
检测常见的 Webshell 后门
"""

import subprocess
import os
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

_RULES_FILE = Path(__file__).parent.parent / "rules" / "webshell_rules.yaml"

def _load_rules() -> list:
    """加载 webshell 检测规则"""
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

    def get_iis_site_count(self):
        """获取 IIS 网站数量"""
        try:
            ps_script = """
            Import-Module WebAdministration -ErrorAction SilentlyContinue
            if (Get-Command Get-Website -ErrorAction SilentlyContinue) {
                (Get-Website).Count
            } else { 0 }
            """
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return int(result.stdout.strip() or 0)
        except Exception:
            pass
        return 0

    def scan_iis(self):
        """扫描 IIS 网站目录"""
        issues = []
        try:
            ps_script = """
            Import-Module WebAdministration -ErrorAction SilentlyContinue
            if (Get-Command Get-Website -ErrorAction SilentlyContinue) {
                Get-Website | ForEach-Object {
                    $physPath = $_.PhysicalPath -replace '%SystemDrive%', $env:SystemDrive
                    [PSCustomObject]@{
                        Name = $_.Name
                        PhysicalPath = $physPath
                    }
                } | ConvertTo-Json
            }
            """
            result = subprocess.run(
                ['powershell', '-Command', ps_script],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                try:
                    data = json.loads(result.stdout)
                    sites = [data] if isinstance(data, dict) else data
                    for site in sites:
                        site_path = site.get('PhysicalPath', '')
                        if os.path.exists(site_path):
                            site_issues = self.scan_directory(site_path)
                            for issue in site_issues:
                                issue['site'] = site.get('Name', 'Unknown')
                            issues.extend(site_issues)
                except (json.JSONDecodeError, TypeError):
                    pass
        except Exception:
            pass
        return issues

    def scan_directory(self, path, max_depth=3, current_depth=0):
        """递归扫描目录查找可疑文件"""
        issues = []
        if current_depth > max_depth:
            return issues

        suspicious_extensions = ['.asp', '.aspx', '.jsp', '.php', '.htaccess']
        suspicious_patterns = [
            (r'eval\s*\(', '代码执行'),
            (r'system\s*\(', '命令执行'),
            (r'exec\s*\(', '代码执行'),
            (r'shell_exec', '命令执行'),
            (r'passthru', '命令执行'),
            (r'Process\.Start', '进程启动'),
            (r'StreamWriter', '文件写入'),
            (r'base64_decode', 'Base64编码'),
            (r'<%=.*%>', 'ASP内联代码'),
        ]

        try:
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d.lower() not in ['bin', 'app_code', 'app_data', '.git', '.svn']]
                for file in files:
                    file_lower = file.lower()
                    if not any(file_lower.endswith(ext) for ext in suspicious_extensions):
                        continue
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(50000)
                        for pattern, desc in suspicious_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                issues.append({
                                    "level": "warning",
                                    "module": "webshell",
                                    "desc": f"可疑文件: {file_path} ({desc})"
                                })
                                break
                    except Exception:
                        pass
        except Exception:
            pass
        return issues

    def scan_asp_files(self):
        """扫描 ASP/ASPX 文件"""
        issues = []
        asp_paths = [
            'C:\\inetpub\\wwwroot',
            'C:\\Inetpub\\wwwroot',
            'C:\\Windows\\System32\\inetsrv\\Config',
        ]
        for path in asp_paths:
            if os.path.exists(path):
                issues.extend(self.scan_directory(path))
        return issues

    def scan_php_files(self):
        """扫描 PHP 文件"""
        issues = []
        php_paths = [
            'C:\\wamp64\\www',
            'C:\\xampp\\htdocs',
            'C:\\phpstudy\\www',
            'C:\\phpStudy\\PHPTutorial\\WWW',
            'C:\\laragon\\www',
        ]
        for path in php_paths:
            if os.path.exists(path):
                issues.extend(self.scan_directory(path))
        return issues

    def scan_upload_dirs(self):
        """扫描上传目录"""
        issues = []
        upload_dirs = ['upload', 'uploads', 'avatar', 'avatars', 'images', 'img', 'file', 'files']
        wwwroot = 'C:\\inetpub\\wwwroot'
        if os.path.exists(wwwroot):
            try:
                for root, dirs, filenames in os.walk(wwwroot):
                    dir_name = os.path.basename(root).lower()
                    if dir_name in upload_dirs:
                        for fname in filenames:
                            ext = fname.lower()
                            if ext.endswith(('.php', '.asp', '.aspx', '.jsp', '.exe', '.bat', '.cmd', '.vbs'):
                                issues.append({
                                    "level": "warning",
                                    "module": "webshell",
                                    "desc": f"上传目录可执行文件: {os.path.join(root, fname)}"
                                })
            except Exception:
                pass
        return issues

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
                        for line in r.stdout.split('\n'):
                            if regex.search(line):
                                issues.append({
                                    "level": severity,
                                    "module": "webshell",
                                    "rule_id": rule.get("id", "?"),
                                    "desc": f"匹配规则 {rule.get('name', rule.get('id', '?'))}: {line.strip()[:80]}"
                                })
                except Exception:
                    pass
        return issues