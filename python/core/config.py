# coding: utf-8
"""
配置管理模块
"""

import os
import yaml
import platform


class Config:
    def __init__(self, script_dir, args=None):
        self.script_dir = script_dir
        self.args = args or {}
        self.data = {}
        self.load()

    def load(self):
        """加载默认配置"""
        config_path = os.path.join(self.script_dir, "..", "config", "default.yaml")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                self.data = yaml.safe_load(f) or {}
        else:
            self.data = self.get_default_config()

    def get_default_config(self):
        return {
            "thresholds": {
                "cpu_warn": 80, "cpu_crit": 90,
                "mem_warn": 85, "mem_crit": 95,
                "disk_warn": 85, "disk_crit": 95,
                "inode_warn": 85, "swap_warn": 50,
                "load_factor": 2, "fd_warn": 80,
                "crit_offset": 10, "conn_close_wait": 50
            },
            "scan": {
                "top_n": 10, "fd_top_n": 5, "log_lines": 20,
                "large_file_size": "100M", "recent_days": 7
            }
        }

    def get(self, key, default=None):
        keys = key.split(".")
        val = self.data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return default
        return val if val is not None else default

    def __getitem__(self, key):
        return self.get(key)