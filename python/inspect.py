#!/usr/bin/env python3
# coding: utf-8
"""
CloudInspect - Python 版本
云主机安全巡检工具 - 功能增强版
"""

import sys
import os
import argparse
import json
import yaml
import time
from datetime import datetime

# 添加项目路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from core.config import Config
from core.detector import Detector
from core.reporter import Reporter

__version__ = "v1.0"
__author__ = "CloudInspect"


def parse_args():
    parser = argparse.ArgumentParser(
        description="CloudInspect - 云主机安全巡检工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
工作模式:
  routine    日常巡检（推荐，5-15分钟）
  emergency  应急排查（深度，30-60分钟）
  quick      快速扫描（1-3分钟）
  full       完全扫描（60分钟+）

示例:
  python inspect.py                         # 默认 HTML 报告
  python inspect.py -m emergency -f html    # 应急排查模式
  python inspect.py -f json -o /tmp/r.json  # 输出 JSON
  python inspect.py --mode quick --verbose  # 快速详细模式
        """
    )
    parser.add_argument("-o", "--output", help="报告输出路径")
    parser.add_argument("-f", "--format", default="html",
                        choices=["html", "json", "md", "docx"],
                        help="输出格式: html(默认) | json | md | docx")
    parser.add_argument("-m", "--mode", default="routine",
                        choices=["routine", "emergency", "quick", "full"],
                        help="工作模式")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")
    parser.add_argument("--version", action="version", version=f"CloudInspect {__version__}")
    return parser.parse_args()


def print_banner(mode, os_info):
    print(f"""
==============================================
  CloudInspect {__version__} - 云主机安全巡检
  Host: {os_info.get('hostname', '未知')}
  OS: {os_info.get('os', '未知')}
  Mode: {mode}
  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
==============================================
    """)


def main():
    args = parse_args()

    # 初始化配置
    config = Config(SCRIPT_DIR, args)

    # 打印横幅
    if not args.quiet:
        print_banner(args.mode, config.get("sysinfo", {}))

    # 初始化检测器
    detector = Detector(config)

    # 执行检测
    if not args.quiet:
        print("[*] 开始巡检...")

    start_time = time.time()
    results = detector.run()
    elapsed = time.time() - start_time

    # 生成报告
    reporter = Reporter(config, results)
    output_path = reporter.generate(args.format)

    # 输出结果
    if not args.quiet:
        print(f"""
==============================================
  CloudInspect {__version__} - 巡检完成
  Host: {os.uname().nodename}
  Mode: {args.mode}
  Warnings: {results.get('warnings', 0)}
  Critical: {results.get('critical', 0)}
  Elapsed: {elapsed:.1f}s
  Report: {output_path}
==============================================
    """)

    # 退出码
    if results.get("critical", 0) > 0:
        sys.exit(2)
    elif results.get("warnings", 0) > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()