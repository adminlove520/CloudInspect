# coding: utf-8
"""
检测调度引擎
"""

import os
import sys
import time

# 导入各检测模块
from core.os_detect import OSDetect


class Detector:
    def __init__(self, config):
        self.config = config
        self.args = config.args
        self.mode = self.args.get("mode", "routine")
        self.verbose = self.args.get("verbose", False)
        self.quiet = self.args.get("quiet", False)

        self.os_detect = OSDetect()
        self.results = {}
        self.warnings = 0
        self.critical = 0

    def log(self, msg, level="info"):
        if self.quiet and level != "error":
            return
        prefix = {"info": "[*]", "warn": "[!]", "error": "[X]", "debug": "[D]"}
        print(f"{prefix.get(level, '[*]')} {msg}")

    def run(self):
        """执行所有检测模块"""
        self.log("开始检测...")

        # 根据模式确定要执行的模块
        modules = self.get_modules()

        total = len(modules)
        for i, module_name in enumerate(modules):
            if not self.quiet:
                pct = int((i + 1) * 100 / total)
                print(f"\r[{i+1}/{total}] ({pct:3d}%) {module_name}...", end="", flush=True)

            module = self.load_module(module_name)
            if module:
                try:
                    result = module.run(self.os_detect, self.config)
                    self.results[module_name] = result
                    self.analyze_result(module_name, result)
                except Exception as e:
                    self.log(f"{module_name} 执行失败: {e}", "error")

        if not self.quiet:
            print()

        self.log(f"检测完成 - 警告: {self.warnings} | 严重: {self.critical}")

        return {
            "mode": self.mode,
            "modules": list(self.results.keys()),
            "warnings": self.warnings,
            "critical": self.critical,
            "results": self.results,
            "os_info": self.os_detect.get_info()
        }

    def get_modules(self):
        """根据模式返回要执行的模块列表"""
        all_modules = [
            "sysinfo", "disk", "network", "process",
            "service", "cron", "security",
            "backdoor", "rootkit", "log_analysis",
            "history", "webshell"
        ]

        # 各模式覆盖的模块
        mode_modules = {
            "quick": ["sysinfo", "process", "network", "security"],
            "routine": ["sysinfo", "disk", "network", "process",
                        "service", "cron", "security", "backdoor",
                        "log_analysis", "history"],
            "emergency": all_modules,
            "full": all_modules,
        }

        return mode_modules.get(self.mode, mode_modules["routine"])

    def load_module(self, module_name):
        """动态加载检测模块"""
        try:
            # 尝试从 lib 目录加载
            module_path = os.path.join(self.config.script_dir, "lib", f"{module_name}.py")
            if os.path.exists(module_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return getattr(mod, module_name.capitalize() + "Module")()
            else:
                # 使用内置模块
                return self.get_builtin_module(module_name)
        except Exception as e:
            self.log(f"加载模块 {module_name} 失败: {e}", "error")
            return None

    def get_builtin_module(self, module_name):
        """内置简化模块"""
        class BuiltinModule:
            def __init__(self, name):
                self.name = name
            def run(self, os_detect, config):
                return {"status": "skipped", "module": self.name}
        return BuiltinModule(module_name)

    def analyze_result(self, module_name, result):
        """分析模块结果，统计告警"""
        if not isinstance(result, dict):
            return

        issues = result.get("issues", [])
        for issue in issues:
            level = issue.get("level", "warning")
            if level == "critical":
                self.critical += 1
            elif level == "warning":
                self.warnings += 1