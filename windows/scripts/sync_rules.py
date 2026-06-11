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
            return path.replace(linux, win, 1)
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
    for key in ["path", "paths", "file", "check_path"]:
        if key in rule:
            val = rule[key]
            if isinstance(val, str):
                converted[key] = _convert_path(val)
            elif isinstance(val, list):
                converted[key] = [_convert_path(v) for v in val]
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

        if not src_path.exists():
            print(f"[SKIP] {src_path.name} 不存在，跳过")
            continue

        with open(src_path, encoding="utf-8") as f:
            src_data = yaml.safe_load(f) or {}

        if dst_path.exists():
            with open(dst_path, encoding="utf-8") as f:
                dst_data = yaml.safe_load(f) or {}
            stats[name]["before"] = len(dst_data.get("windows_rules", []))
        else:
            dst_data = {"windows_rules": [], "_meta": {}}

        windows_rules = _filter_os_rules(src_data)
        existing = dst_data.get("windows_rules", [])
        existing_ids = {r.get("id", "") for r in existing}
        for r in windows_rules:
            if r.get("id", "") not in existing_ids:
                existing.append(r)

        dst_data["windows_rules"] = existing
        stats[name]["after"] = len(existing)
        stats[name]["new"] = stats[name]["after"] - stats[name]["before"]

        dst_data["_meta"] = {
            "version": dst_data.get("_meta", {}).get("version", 0) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "os": "windows",
            "generated_by": "sync_rules.py",
            "total_rules": len(existing),
        }

        with open(dst_path, "w", encoding="utf-8") as f:
            yaml.dump(dst_data, f, allow_unicode=True, sort_keys=False)

        print(f"[OK] {name}: {stats[name]['before']} -> {stats[name]['after']} (+{stats[name]['new']})")

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
        return 0

    stats = sync_rules()
    total_new = sum(s["new"] for s in stats.values())
    print(f"\n✅ 同步完成，共新增 {total_new} 条规则")
    return total_new


if __name__ == "__main__":
    sys.exit(main())