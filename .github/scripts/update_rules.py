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
import re
import hashlib
import argparse
from datetime import datetime, timezone
from pathlib import Path

# 添加项目路径
REPO_ROOT = Path(__file__).parent.parent.parent.resolve()
RULES_DIR = REPO_ROOT / "python" / "rules"
BACKDOOR_FILE = RULES_DIR / "backdoor_rules.yaml"
ROOTKIT_FILE = RULES_DIR / "rootkit_signatures.yaml"
WEBSHELL_FILE = RULES_DIR / "webshell_patterns.yaml"

OTX_KEY = os.environ.get("OTX_API_KEY", "")
ABUSE_KEY = os.environ.get("ABUSEIPDB_API_KEY", "")

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("[WARN] requests 未安装，外部情报源将被跳过")


# ========== 专家内置规则（基于 GScan + 安全经验）==========

CUSTOM_BACKDOOR_RULES = [
    {"name": "LD_PRELOAD后门", "env": "LD_PRELOAD", "severity": "critical",
     "desc": "LD_PRELOAD 环境变量劫持动态链接库", "check": "env",
     "files": ["/root/.bashrc", "/root/.bash_profile", "/etc/bashrc", "/etc/profile"],
     "fix": "grep LD_PRELOAD /etc/bashrc /etc/profile && vi <file> # 删除 export LD_PRELOAD",
     "mitre": "T1574.006"},
    {"name": "ld.so.preload后门", "file": "/etc/ld.so.preload", "severity": "critical",
     "desc": "动态链接器预加载文件被篡改", "check": "file_content",
     "fix": "rm -f /etc/ld.so.preload"},
    {"name": "PROMPT_COMMAND后门", "env": "PROMPT_COMMAND", "severity": "high",
     "desc": "命令提示符劫持，用于记录输入或注入命令", "check": "env",
     "files": ["/root/.bashrc", "/etc/bashrc", "/etc/profile"],
     "fix": "grep PROMPT_COMMAND /etc/bashrc /etc/profile && vi <file>"},
    {"name": "Cron后门-境外下载", "severity": "critical", "check": "cron_content",
     "patterns": ["wget.*境外", "curl.*境外", "境外ip", "nc\\s", "bash -i"],
     "paths": ["/var/spool/cron/", "/etc/cron.d/", "/etc/cron.daily/"],
     "fix": "检查 /var/spool/cron/ 和 /etc/cron.d/"},
    {"name": "SSH后门替身", "severity": "critical", "check": "binary",
     "paths": ["/tmp/su", "/tmp/sudu", "/var/tmp/su"],
     "fix": "rm -f /tmp/su && systemctl restart sshd"},
    {"name": "SSHWrapper后门", "severity": "critical", "check": "file_type",
     "path": "/usr/sbin/sshd",
     "fix": "yum -y install openssh-server && systemctl restart sshd"},
    {"name": "setuid后门", "severity": "critical", "check": "suid",
     "dirs": ["/tmp", "/var/tmp", "/dev/shm"],
     "fix": "chmod u-s <file>"},
    {"name": "启动项后门", "severity": "high", "check": "startup",
     "patterns": ["bash -i", "/dev/tcp", "nc\\s"],
     "paths": ["/etc/init.d/", "/etc/rc.local", "/etc/systemd/system/"],
     "fix": "检查 /etc/init.d/ 和 rc.local"},
    {"name": "alias后门", "severity": "medium", "check": "alias",
     "patterns": ["rm.*-rf", "wget.*境外", "curl.*境外"],
     "fix": "alias -p 查看所有 alias"},
]

CUSTOM_ROOTKIT_RULES = [
    {"name": "隐藏文件特征", "patterns": ["/tmp/...", "/tmp/..", "/var/tmp/..."], "severity": "high",
     "desc": "Rootkit 常用隐藏文件名", "mitre": "T1564.001"},
    {"name": "LKM隐藏模块", "keywords": ["hide", "sniffer", "rootkit", "backdoor"], "severity": "critical",
     "desc": "内核模块名称包含可疑关键字", "mitre": "T1014"},
    {"name": "/dev异常设备", "pattern": r"/dev/[a-z]-[a-z0-9]+", "severity": "high",
     "desc": "/dev 中存在非标准字符设备"},
    {"name": "系统命令替换", "commands": ["ps", "ls", "netstat", "ss", "find"], "severity": "critical",
     "desc": "常用系统命令被替换", "mitre": "T1562.001"},
]

CUSTOM_WEBSHELL_PATTERNS = [
    {"pattern": r"eval\s*\(", "severity": "high", "desc": "动态代码执行"},
    {"pattern": r"base64_decode\s*\(", "severity": "high", "desc": "Base64 混淆"},
    {"pattern": r"system\s*\(|passthru\s*\(|exec\s*\(", "severity": "high", "desc": "系统命令执行"},
    {"pattern": r"shell_exec\s*\(|popen\s*\(|proc_open\s*\(", "severity": "high", "desc": "Shell命令执行"},
    {"pattern": r"preg_replace.*\/e", "severity": "critical", "desc": "PCRE代码执行"},
    {"pattern": r"assert\s*\(", "severity": "high", "desc": "断言执行"},
    {"pattern": r"call_user_func\s*\(|create_function\s*\(", "severity": "medium", "desc": "回调函数执行"},
    {"pattern": r"usort\s*\(", "severity": "medium", "desc": "动态函数执行"},
    {"pattern": r"ini_set.*disable_functions", "severity": "critical", "desc": "禁用安全函数"},
    {"pattern": r"\\\\x[0-9a-f]{2,}", "severity": "high", "desc": "Hex编码混淆"},
    {"pattern": r"gxz\.php|404\.php|config\.php", "severity": "medium", "desc": "可疑文件名"},
    {"pattern": r"ob_start\s*\(", "severity": "medium", "desc": "输出缓冲混淆"},
]


# ========== 外部情报源 ==========

def fetch_otx_pulses() -> list:
    """从 AlienVault OTX 获取订阅脉冲"""
    if not OTX_KEY:
        print("[SKIP] OTX_API_KEY 未设置，跳过 AlienVault OTX")
        return []

    if not HAS_REQUESTS:
        return []

    try:
        headers = {"X-OTX-API-KEY": OTX_KEY, "User-Agent": "CloudInspect/1.0"}
        resp = requests.get(
            "https://otx.alienvault.com/api/v1/pulses/subscribed",
            headers=headers, timeout=30
        )
        if resp.status_code != 200:
            print(f"[WARN] OTX API 返回 {resp.status_code}")
            return []

        data = resp.json()
        pulses = data.get("results", [])[:100]
        print(f"[OTX] 获取到 {len(pulses)} 个脉冲")

        items = []
        for pulse in pulses:
            for ind in pulse.get("indicators", []):
                itype = ind.get("type", "")
                if itype in ["IPv4", "domain", "filehash-MD5", "filehash-SHA256", "hostname"]:
                    items.append({
                        "indicator": ind.get("indicator", ""),
                        "type": itype,
                        "pulse": pulse.get("name", ""),
                        "pulse_id": pulse.get("id", ""),
                        "created": pulse.get("created", ""),
                        "source": "alienvault_otx"
                    })
        print(f"[OTX] 提取到 {len(items)} 条指标")
        return items
    except Exception as e:
        print(f"[ERROR] OTX 获取失败: {e}")
        return []


def fetch_abuseipdb() -> list:
    """从 AbuseIPDB 获取高置信度恶意 IP"""
    if not ABUSE_KEY:
        print("[SKIP] ABUSEIPDB_API_KEY 未设置，跳过 AbuseIPDB")
        return []

    if not HAS_REQUESTS:
        return []

    try:
        headers = {"Key": ABUSE_KEY, "Accept": "application/json", "User-Agent": "CloudInspect/1.0"}
        resp = requests.get(
            "https://api.abuseipdb.com/api/v2/blacklist",
            headers=headers,
            params={"confidenceMinimum": 80, "limit": 200},
            timeout=30
        )
        if resp.status_code != 200:
            print(f"[WARN] AbuseIPDB API 返回 {resp.status_code}")
            return []

        data = resp.json().get("data", [])
        ips = [{
            "indicator": d.get("ipAddress", ""),
            "confidence": d.get("abuseConfidenceScore", 0),
            "country": d.get("isoCode", ""),
            "source": "abuseipdb"
        } for d in data if d.get("abuseConfidenceScore", 0) >= 80]
        print(f"[ABUSE] 获取到 {len(ips)} 条高置信度恶意 IP")
        return ips
    except Exception as e:
        print(f"[ERROR] AbuseIPDB 获取失败: {e}")
        return []


def fetch_emerging_threats() -> list:
    """从 Emerging Threats 获取恶意 IP 列表（无需 API Key）"""
    if not HAS_REQUESTS:
        return []

    sources = [
        ("https://rules.emergingthreats.net/blockrules/compromised-ips.txt", "et_compromised"),
    ]

    all_ips = []
    for url, src_name in sources:
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "CloudInspect/1.0"})
            if resp.status_code == 200:
                lines = resp.text.splitlines()
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith("#") and re.match(r"\d+\.\d+\.\d+\.\d+", line):
                        all_ips.append({
                            "indicator": line,
                            "type": "ipv4",
                            "source": src_name,
                            "confidence": 70
                        })
                print(f"[ET] 从 {src_name} 获取到 {len([l for l in lines if re.match(r'\d+\.\d+\.\d+\.\d+', l.strip())]} 条 IP")
        except Exception as e:
            print(f"[WARN] Emerging Threats {url} 失败: {e}")

    return all_ips


# ========== 规则加载与合并 ==========

def load_yaml(path: Path) -> dict:
    if path.exists():
        try:
            content = path.read_text(encoding="utf-8")
            # 跳过 Python 注释头
            content = re.sub(r'^#.*\n', '', content, count=1)
            return yaml.safe_load(content) or {}
        except Exception as e:
            print(f"[WARN] 加载 {path.name} 失败: {e}")
    return {"_meta": {"version": 0, "total_rules": 0}}


def save_yaml(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = data.get("_meta", {})
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header = (
        f"# coding: utf-8\n"
        f"# CloudInspect Detection Rules\n"
        f"# Auto-updated: {ts}\n"
        f"# ⚠️ 此文件由 GitHub Actions 自动更新\n\n"
    )
    # 保存元数据但不破坏规则结构
    content = yaml.dump(data, allow_unicode=True, sort_keys=False,
                        default_flow_style=False)
    path.write_text(header + content, encoding="utf-8")
    print(f"[OK] 保存 {path.name}: {meta.get('total_rules', 0)} 条规则")


def rule_hash(rule) -> str:
    s = str(rule.get("pattern", "")) + str(rule.get("name", "")) + str(rule.get("indicator", ""))
    return hashlib.md5(s.encode()).hexdigest()


def merge_rules(existing: list, new: list, source: str) -> tuple:
    """合并规则，返回 (已存在数量, 新增数量)"""
    existing_hashes = {rule_hash(r) for r in existing}
    added = 0
    for r in new:
        h = rule_hash(r)
        if h not in existing_hashes:
            r["_source"] = source
            r["_added_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            existing.append(r)
            added += 1
    return len(existing) - added, added


# ========== 更新各规则文件 ==========

def update_backdoor_rules(sources: list) -> int:
    print("\n=== 更新后门检测规则 ===")
    data = load_yaml(BACKDOOR_FILE)

    # 初始化结构
    if "custom_expert_rules" not in data:
        data["custom_expert_rules"] = []
    if "external_indicators" not in data:
        data["external_indicators"] = []

    # 内置专家规则（只增不减）
    if "custom" in sources:
        old = len(data["custom_expert_rules"])
        existing_hashes = {rule_hash(r) for r in data["custom_expert_rules"]}
        for r in CUSTOM_BACKDOOR_RULES:
            if rule_hash(r) not in existing_hashes:
                r["_source"] = "custom_expert"
                r["_added_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                data["custom_expert_rules"].append(r)
        new = len(data["custom_expert_rules"]) - old
        print(f"[OK] 专家规则: {old} → {len(data['custom_expert_rules'])} (+{new})")

    # 外部情报
    if "et" in sources or "all" in sources:
        ips = fetch_emerging_threats()
        if ips:
            _, added = merge_rules(data["external_indicators"], ips, "emerging_threats")
            print(f"[OK] ET 恶意 IP: +{added} 条")

    if "otx" in sources or "all" in sources:
        pulses = fetch_otx_pulses()
        if pulses:
            _, added = merge_rules(data["external_indicators"], pulses, "alienvault_otx")
            print(f"[OK] OTX 指标: +{added} 条")

    if "abuse" in sources or "all" in sources:
        ips = fetch_abuseipdb()
        if ips:
            _, added = merge_rules(data["external_indicators"], ips, "abuseipdb")
            print(f"[OK] AbuseIPDB IP: +{added} 条")

    # 更新元数据
    data["_meta"] = {
        "version": data["_meta"].get("version", 0) + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": "github-actions-update-rules",
        "total_rules": len(data["custom_expert_rules"]) + len(data["external_indicators"]),
        "sources": sources
    }

    save_yaml(BACKDOOR_FILE, data)
    return data["_meta"]["total_rules"]


def update_rootkit_rules(sources: list) -> int:
    print("\n=== 更新 Rootkit 特征库 ===")
    data = load_yaml(ROOTKIT_FILE)

    if "expert_rules" not in data:
        data["expert_rules"] = []
    if "external_signatures" not in data:
        data["external_signatures"] = []

    if "custom" in sources or "all" in sources:
        old = len(data["expert_rules"])
        existing_hashes = {rule_hash(r) for r in data["expert_rules"]}
        for r in CUSTOM_ROOTKIT_RULES:
            if rule_hash(r) not in existing_hashes:
                r["_source"] = "custom_expert"
                r["_added_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                data["expert_rules"].append(r)
        new = len(data["expert_rules"]) - old
        print(f"[OK] 专家规则: {old} → {len(data['expert_rules'])} (+{new})")

    # Emerging Threats 也可提供 rootkit 相关规则
    if ("et" in sources or "all" in sources) and HAS_REQUESTS:
        try:
            resp = requests.get(
                "https://rules.emergingthreats.net/blockrules/compromised-ips.txt",
                timeout=20
            )
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line and re.match(r"\d+\.\d+\.\d+\.\d+", line):
                        sigs = data["external_signatures"]
                        _, added = merge_rules(sigs, [{
                            "indicator": line, "type": "ipv4",
                            "source": "emerging_threats"
                        }], "emerging_threats")
        except Exception as e:
            print(f"[WARN] ET rootkit 更新失败: {e}")

    data["_meta"] = {
        "version": data["_meta"].get("version", 0) + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": "github-actions-update-rules",
        "total_rules": len(data["expert_rules"]) + len(data.get("external_signatures", [])),
        "sources": sources
    }

    save_yaml(ROOTKIT_FILE, data)
    return data["_meta"]["total_rules"]


def update_webshell_rules(sources: list) -> int:
    print("\n=== 更新 Webshell 检测规则 ===")
    data = load_yaml(WEBSHELL_FILE)

    if "detection_patterns" not in data:
        data["detection_patterns"] = []
    if "expert_patterns" not in data:
        data["expert_patterns"] = []

    if "custom" in sources or "all" in sources:
        old = len(data["expert_patterns"])
        existing_hashes = {rule_hash(r) for r in data["expert_patterns"]}
        for r in CUSTOM_WEBSHELL_PATTERNS:
            if rule_hash(r) not in existing_hashes:
                r["_source"] = "custom_expert"
                r["_added_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                data["expert_patterns"].append(r)
        new = len(data["expert_patterns"]) - old
        print(f"[OK] 专家规则: {old} → {len(data['expert_patterns'])} (+{new})")

    data["_meta"] = {
        "version": data["_meta"].get("version", 0) + 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": "github-actions-update-rules",
        "total_rules": len(data["expert_patterns"]) + len(data["detection_patterns"]),
        "sources": sources
    }

    save_yaml(WEBSHELL_FILE, data)
    return data["_meta"]["total_rules"]


# ========== 主入口 ==========

def main():
    parser = argparse.ArgumentParser(description="CloudInspect 规则更新工具")
    parser.add_argument("--source", default="all",
                        choices=["all", "custom", "et", "otx", "abuse"],
                        help="规则源: all/custom/et(emerging)/otx(alienvault)/abuse(abuseipdb)")
    parser.add_argument("--dry-run", action="store_true", help="仅模拟，不写入文件")
    args = parser.parse_args()

    ts = datetime.now(timezone.utc).isoformat()
    print(f"""
╔══════════════════════════════════════╗
║  CloudInspect 规则自动更新          ║
║  时间: {ts}       ║
╚══════════════════════════════════════╝
    """)

    # 解析来源
    source_map = {
        "all": ["custom", "et", "otx", "abuse"],
        "custom": ["custom"],
        "et": ["et"],
        "otx": ["otx"],
        "abuse": ["abuse"],
    }
    sources = source_map.get(args.source, ["all"])

    print(f"[INFO] 启用来源: {', '.join(sources)}")
    print(f"[INFO] OTX: {'✅ 已配置' if OTX_KEY else '❌ 未配置'}")
    print(f"[INFO] AbuseIPDB: {'✅ 已配置' if ABUSE_KEY else '❌ 未配置'}")

    if args.dry_run:
        print("[DRY-RUN] 模拟运行，不写入文件")
        return

    RULES_DIR.mkdir(parents=True, exist_ok=True)

    bd_count = update_backdoor_rules(sources)
    rk_count = update_rootkit_rules(sources)
    ws_count = update_webshell_rules(sources)

    total = bd_count + rk_count + ws_count
    print(f"""
╔══════════════════════════════════════╗
║  ✅ 规则更新完成                    ║
║  后门规则:     {bd_count:>4} 条              ║
║  Rootkit 特征: {rk_count:>4} 条              ║
║  Webshell 模式: {ws_count:>3} 条              ║
║  ──────────────────              ║
║  规则总数:     {total:>4} 条              ║
╚══════════════════════════════════════╝
    """)


if __name__ == "__main__":
    main()
