#!/usr/bin/env python3
# coding: utf-8
"""
CloudInspect 规则自动更新脚本
功能: 从多个威胁情报源自动更新检测规则
触发: GitHub Actions (schedule/dispatch) 或手动运行
"""

import os
import sys
import json
import yaml
import argparse
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
RULES_DIR = REPO_ROOT / "python" / "rules"
BACKDOOR_RULE_FILE = RULES_DIR / "backdoor_rules.yaml"
ROOTKIT_RULE_FILE = RULES_DIR / "rootkit_signatures.yaml"
WEBSHELL_RULE_FILE = RULES_DIR / "webshell_patterns.yaml"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


# ========== 规则源定义 ==========

class RuleSource:
    """规则源基类"""

    def fetch(self) -> dict:
        """获取规则数据，返回 {"rules": [...], "metadata": {...}}"""
        raise NotImplementedError


class AlienVaultOTX(RuleSource):
    """AlienVault OTX 威胁情报"""

    def fetch(self) -> dict:
        """获取 AlienVault OTX 脉冲（需要 API Key）"""
        api_key = os.environ.get("OTX_API_KEY", "")
        if not api_key:
            print("[WARN] OTX_API_KEY not set, skipping AlienVault")
            return {"rules": [], "source": "alienvault", "note": "API key not set"}

        try:
            import requests
            headers = {"X-OTX-API-KEY": api_key}
            # 获取最近的脉冲
            resp = requests.get(
                "https://otx.alienvault.com/api/v1/pulses/subscribed",
                headers=headers, timeout=30
            )
            pulses = resp.json().get("results", [])[:50]

            indicators = []
            for pulse in pulses:
                for ind in pulse.get("indicators", []):
                    if ind["type"] in ["IPv4", "domain", "filehash"]:
                        indicators.append({
                            "indicator": ind["indicator"],
                            "type": ind["type"],
                            "source": f"OTX:{pulse['name']}",
                            "id": pulse["id"]
                        })

            return {
                "rules": indicators,
                "source": "alienvault",
                "count": len(indicators),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            print(f"[WARN] AlienVault fetch failed: {e}")
            return {"rules": [], "source": "alienvault", "error": str(e)}


class EmergingThreats(RuleSource):
    """Emerging Threats 规则（ET Open）"""

    def fetch(self) -> dict:
        """从 Emerging Threats 获取 Suricata/Snort 规则"""
        rules = []
        sources = [
            ("https://rules.emergingthreats.net/blockrules/compromised-ips.txt", "ipv4"),
            ("https://rules.emergingthreats.net/open/ruleset/10.0.0/emergingcompromised.rules", "suricata"),
        ]

        try:
            import requests
            for url, rtype in sources:
                try:
                    resp = requests.get(url, timeout=20, headers={"User-Agent": "CloudInspect/1.0"})
                    if resp.status_code == 200:
                        for line in resp.text.splitlines():
                            line = line.strip()
                            if not line or line.startswith("#"):
                                continue
                            if rtype == "ipv4" and re.match(r"\d+\.\d+\.\d+\.\d+", line):
                                rules.append({
                                    "type": "ipv4",
                                    "indicator": line,
                                    "source": "ET-compromised",
                                    "severity": "high"
                                })
                            elif rtype == "suricata":
                                # 解析 Suricata 规则
                                match = re.search(r'content:"([^"]+)"', line)
                                if match:
                                    rules.append({
                                        "type": "pattern",
                                        "indicator": match.group(1),
                                        "raw": line[:200],
                                        "source": "ET-suricata",
                                        "severity": "medium"
                                    })
                except Exception as e:
                    print(f"[WARN] Failed to fetch {url}: {e}")

            return {
                "rules": rules[:500],  # 限制数量
                "source": "emerging_threats",
                "count": len(rules),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            print(f"[WARN] Emerging Threats fetch failed: {e}")
            return {"rules": [], "source": "emerging_threats", "error": str(e)}


class CustomRules(RuleSource):
    """项目维护的自定义规则 — 包含 GScan 核心检测逻辑"""

    def fetch(self) -> dict:
        """加载内置的专家规则（不依赖外部网络）"""
        rules = {
            "backdoor": [
                {"name": "LD_PRELOAD后门", "env": "LD_PRELOAD", "severity": "critical",
                 "desc": "LD_PRELOAD 环境变量劫持", "fix": "检查 /etc/ld.so.preload 和 bashrc 配置"},
                {"name": "ld.so.preload后门", "file": "/etc/ld.so.preload", "severity": "critical",
                 "desc": "动态链接器预加载劫持", "fix": "删除 /etc/ld.so.preload 或检查内容"},
                {"name": "PROMPT_COMMAND后门", "env": "PROMPT_COMMAND", "severity": "high",
                 "desc": "命令提示符劫持", "fix": "检查 /etc/bashrc 和用户 .bashrc"},
                {"name": "Cron后门-境外IP", "pattern": "wget.*境外|curl.*境外", "severity": "critical",
                 "desc": "定时任务下载境外恶意文件", "fix": "检查 /var/spool/cron/ 和 /etc/cron.d/"},
                {"name": "SSH后门替身", "pattern": "/tmp/su|/tmp/sudu", "severity": "critical",
                 "desc": "SSH 服务替换后门", "fix": "检查 /tmp 下可疑的 sshd 替身文件"},
                {"name": "SSHWrapper后门", "check": "file /usr/sbin/sshd", "severity": "critical",
                 "desc": "SSH 服务被 wrapper 脚本替换", "fix": "重新安装 openssh-server"},
                {"name": "setuid后门", "pattern": "/tmp/.*-4000|/var/tmp/.*-4000", "severity": "critical",
                 "desc": "可疑 SUID 文件位于临时目录", "fix": "chmod u-s 移除异常 SUID"},
                {"name": "启动项后门", "pattern": "bash.*-i|/dev/tcp", "severity": "high",
                 "desc": "启动脚本包含反弹shell", "fix": "检查 /etc/init.d/ 和 rc.local"},
                {"name": "alias后门", "pattern": "rm.*-rf|curl.*境外", "severity": "medium",
                 "desc": "alias 命令被篡改", "fix": "检查所有用户的 alias 配置"},
            ],
            "rootkit": [
                {"name": "隐藏文件特征", "pattern": "/tmp/...|/tmp/..", "severity": "high",
                 "desc": "Rootkit 常用隐藏文件名", "fix": "find /tmp /var/tmp -name '.*' -ls"},
                {"name": "LKM隐藏模块", "pattern": "hide|sniffer|rootkit", "severity": "critical",
                 "desc": "内核模块名称包含可疑关键字", "fix": "lsmod | grep -E 'hide|sniffer'"},
                {"name": "/dev异常设备", "pattern": "/dev/[a-z]-[a-z0-9]+", "severity": "high",
                 "desc": "/dev 中存在非标准字符设备", "fix": "find /dev -type c -o -type b | grep -v tty|sda"},
            ],
            "webshell": [
                {"pattern": r"eval\s*\(", "severity": "high", "desc": "动态代码执行"},
                {"pattern": r"base64_decode\s*\(", "severity": "high", "desc": "Base64 混淆"},
                {"pattern": r"system\s*\(|passthru\s*\(|exec\s*\(", "severity": "high", "desc": "系统命令执行"},
                {"pattern": r"shell_exec\s*\(|popen\s*\(|proc_open\s*\(", "severity": "high", "desc": "Shell 命令执行"},
                {"pattern": r"preg_replace.*\/e", "severity": "critical", "desc": "代码执行 (PCRE /e)"},
                {"pattern": r"assert\s*\(", "severity": "high", "desc": "断言执行"},
                {"pattern": r"call_user_func\s*\(|create_function\s*\(", "severity": "medium", "desc": "回调函数执行"},
                {"pattern": r"ini_set.*disable_functions", "severity": "critical", "desc": "禁用安全函数"},
                {"pattern": r"\\\\x[0-9a-f]{2,}", "severity": "high", "desc": "Hex 编码混淆"},
                {"pattern": r"gxz\.php|404\.php|config\.php", "severity": "medium", "desc": "可疑文件名"},
            ]
        }

        return {
            "rules": rules,
            "source": "custom_expert",
            "count": sum(len(v) for v in rules.values()),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "note": "基于 GScan 和安全专家经验的规则库"
        }


class AbuseIPDB(RuleSource):
    """AbuseIPDB 恶意 IP 数据库"""

    def fetch(self) -> dict:
        """获取 AbuseIPDB 高置信度恶意 IP"""
        api_key = os.environ.get("ABUSEIPDB_API_KEY", "")
        if not api_key:
            print("[WARN] ABUSEIPDB_API_KEY not set, skipping")
            return {"rules": [], "source": "abuseipdb", "note": "API key not set"}

        try:
            import requests
            resp = requests.get(
                "https://api.abuseipdb.com/api/v2/blacklist",
                headers={"Key": api_key, "Accept": "application/json"},
                params={"confidenceMinimum": 80},
                timeout=30
            )
            data = resp.json().get("data", {})[:200]
            ips = [{"indicator": d["ipAddress"], "confidence": d["abuseConfidenceScore"],
                    "source": "abuseipdb"} for d in data if d.get("abuseConfidenceScore", 0) >= 80]

            return {
                "rules": ips,
                "source": "abuseipdb",
                "count": len(ips),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            print(f"[WARN] AbuseIPDB fetch failed: {e}")
            return {"rules": [], "source": "abuseipdb", "error": str(e)}


# ========== 规则合并器 ==========

class RuleMerger:
    """规则合并与版本管理"""

    def __init__(self, rule_file: Path):
        self.rule_file = rule_file
        self.data = self._load_existing()

    def _load_existing(self) -> dict:
        if self.rule_file.exists():
            with open(self.rule_file, "r", encoding="utf-8") as f:
                content = f.read()
                # 去掉 Python 注释头
                content = re.sub(r'^#.*\n', '', content, count=1)
                return yaml.safe_load(content) or {}
        return {}

    def merge(self, new_data: dict, source: str):
        """合并新规则到现有规则"""
        if "rules" not in self.data:
            self.data["rules"] = []

        existing_hashes = {
            hashlib.md5(str(r).encode()).hexdigest()
            for r in self.data["rules"]
        }

        added = 0
        for rule in new_data.get("rules", []):
            rule_hash = hashlib.md5(str(rule).encode()).hexdigest()
            if rule_hash not in existing_hashes:
                rule["_source"] = source
                rule["_added_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                self.data["rules"].append(rule)
                added += 1

        return added

    def update_metadata(self, sources_used: list):
        """更新规则元数据"""
        self.data["_meta"] = {
            "version": self.data.get("_meta", {}).get("version", 1) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": "github-actions-update-rules",
            "sources": sources_used,
            "total_rules": len(self.data.get("rules", []))
        }

    def save(self):
        """保存规则文件"""
        content = yaml.dump(self.data, allow_unicode=True, sort_keys=False,
                            default_flow_style=False)
        # 添加文件头
        header = f'''# coding: utf-8
# CloudInspect Detection Rules
# Auto-updated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
# ⚠️ 此文件由 GitHub Actions 自动更新，请勿手动修改
# 如需编辑规则，请在 rules_schema.json 中定义格式

'''
        with open(self.rule_file, "w", encoding="utf-8") as f:
            f.write(header + content)

        print(f"[OK] Updated {self.rule_file.name}: {self.data['_meta']['total_rules']} rules")


# ========== 主更新逻辑 ==========

def update_backdoor_rules(sources: list) -> int:
    """更新后门检测规则"""
    merger = RuleMerger(BACKDOOR_RULE_FILE)

    for src_name in sources:
        try:
            src = {
                "custom": CustomRules,
                "alienvault": AlienVaultOTX,
                "emerging": EmergingThreats,
                "abuseipdb": AbuseIPDB,
            }.get(src_name, CustomRules)()

            data = src.fetch()
            if data.get("rules"):
                added = merger.merge(data, src_name)
                print(f"[OK] {src_name}: fetched {len(data['rules'])}, added {added}")
        except Exception as e:
            print(f"[WARN] {src_name} failed: {e}")

    merger.update_metadata(sources)
    merger.save()
    return merger.data["_meta"]["total_rules"]


def update_rootkit_rules(sources: list) -> int:
    """更新 Rootkit 特征库"""
    merger = RuleMerger(ROOTKIT_RULE_FILE)

    for src_name in sources:
        try:
            src = {
                "custom": CustomRules,
                "emerging": EmergingThreats,
            }.get(src_name, CustomRules)()
            data = src.fetch()
            if data.get("rules"):
                # Rootkit 数据在 nested rules dict 中
                if "rules" in data and "rootkit" in data["rules"]:
                    added = merger.merge(data["rules"]["rootkit"], src_name)
                    print(f"[OK] {src_name} rootkit: added {added}")
        except Exception as e:
            print(f"[WARN] {src_name} failed: {e}")

    merger.update_metadata(sources)
    merger.save()
    return merger.data["_meta"]["total_rules"]


def update_webshell_rules(sources: list) -> int:
    """更新 Webshell 检测规则"""
    merger = RuleMerger(WEBSHELL_RULE_FILE)

    for src_name in sources:
        try:
            src = {
                "custom": CustomRules,
                "emerging": EmergingThreats,
            }.get(src_name, CustomRules)()
            data = src.fetch()
            if data.get("rules"):
                if "rules" in data and "webshell" in data["rules"]:
                    added = merger.merge(data["rules"]["webshell"], src_name)
                    print(f"[OK] {src_name} webshell: added {added}")
        except Exception as e:
            print(f"[WARN] {src_name} failed: {e}")

    merger.update_metadata(sources)
    merger.save()
    return merger.data["_meta"]["total_rules"]


def main():
    parser = argparse.ArgumentParser(description="CloudInspect 规则更新工具")
    parser.add_argument("--source", default="all",
                        choices=["all", "custom", "alienvault", "emerging", "abuseipdb"],
                        help="规则源")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟，不写入文件")
    args = parser.parse_args()

    print(f"[INFO] CloudInspect 规则更新开始 — {datetime.now(timezone.utc).isoformat()}")

    if args.source == "all":
        sources = ["custom", "emerging"]
    else:
        sources = [args.source]

    print(f"[INFO] 使用规则源: {', '.join(sources)}")

    if args.dry_run:
        print("[DRY-RUN] 仅模拟运行，不写入文件")
        return

    RULES_DIR.mkdir(parents=True, exist_ok=True)

    bd_count = update_backdoor_rules(sources)
    rk_count = update_rootkit_rules(sources)
    ws_count = update_webshell_rules(sources)

    print(f"""
[OK] 规则更新完成
  - 后门规则: {bd_count} 条
  - Rootkit 特征: {rk_count} 条
  - Webshell 模式: {ws_count} 条
  - 时间: {datetime.now(timezone.utc).isoformat()}
    """)


if __name__ == "__main__":
    main()