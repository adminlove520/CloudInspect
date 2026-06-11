# coding: utf-8
"""
CloudInspect for Windows
云主机安全巡检工具 - Windows Server 版
版本: v2.0
"""

import sys
import os
import argparse
import json
import yaml
import time
import platform
from datetime import datetime

__version__ = "v2.0"
__author__ = "CloudInspect"
__os_version__ = "Windows"


def parse_args():
    parser = argparse.ArgumentParser(
        description="CloudInspect - 云主机安全巡检工具 (Windows Server)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
工作模式:
  routine    日常巡检（推荐，5-15分钟）
  emergency  应急排查（深度，30-60分钟）
  quick      快速扫描（1-3分钟）
  full       完全扫描（60分钟+）

示例:
  python cloud_inspect.py                         # 默认 HTML 报告
  python cloud_inspect.py -m emergency -f html    # 应急排查模式
  python cloud_inspect.py -f json -o C:\\Temp\\r.json  # 输出 JSON
  python cloud_inspect.py --mode quick --verbose  # 快速详细模式

支持的操作系统:
  Windows Server 2012 / 2016 / 2019 / 2022
  Windows 10 / 11 (专业版/企业版)
"""
    )
    parser.add_argument("-o", "--output", help="报告输出路径")
    parser.add_argument("-f", "--format", default="html",
                        choices=["html", "json", "md"],
                        help="输出格式: html(默认) | json | md")
    parser.add_argument("-m", "--mode", default="routine",
                        choices=["routine", "emergency", "quick", "full"],
                        help="工作模式")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细日志")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")
    parser.add_argument("--version", action="version", version=f"CloudInspect {__version__} (Windows)")
    return parser.parse_args()


def main():
    args = parse_args()

    # 添加项目路径
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, SCRIPT_DIR)

    # 导入核心模块
    try:
        from core.config import Config
        from core.detector import Detector
        from core.reporter import Reporter
    except ImportError as e:
        print(f"[ERROR] 模块导入失败: {e}")
        print("请确保所有依赖已安装: pip install -r requirements.txt")
        sys.exit(1)

    # 打印初始横幅
    if not args.quiet:
        print(f"""
===================================================================
  CloudInspect {__version__} - 云主机安全巡检工具 (Windows)
  Host: {platform.node()}
  Mode: {args.mode}
  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
===================================================================
    """)

    # 初始化配置
    config = Config(SCRIPT_DIR, args)

    # 初始化检测器
    detector = Detector(config)

    # 执行检测
    if not args.quiet:
        print("[*] 开始巡检...")

    start_time = time.time()
    results = detector.run()
    elapsed = time.time() - start_time

    # 从检测结果中获取 sysinfo
    sysinfo_data = results.get('modules', {}).get('sysinfo', {})
    hostname = sysinfo_data.get('hostname', platform.node())
    os_name = sysinfo_data.get('os', platform.platform())

    # 生成报告
    reporter = Reporter(config, results)
    output_path = reporter.generate(args.format)

    # 输出结果
    if not args.quiet:
        print(f"""
===================================================================
  CloudInspect {__version__} - 巡检完成
  Host: {hostname}
  OS: {os_name}
  Warnings: {results.get('warnings', 0)}
  Critical: {results.get('critical', 0)}
  Elapsed: {elapsed:.1f}s
  Report: {output_path}
===================================================================
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