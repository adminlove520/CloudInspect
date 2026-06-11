# coding: utf-8
"""
Windows 配置管理
"""

import os
import yaml
import argparse


class Config:
    def __init__(self, script_dir, args=None):
        self.config_dir = script_dir
        self.args = args or argparse.Namespace()
        self.data = {}
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        config_file = os.path.join(self.config_dir, 'config', 'default.yaml')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self.data = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[WARN] 配置加载失败: {e}")

        # 加载本地配置
        local_config = os.path.join(self.config_dir, 'config', 'local.yaml')
        if os.path.exists(local_config):
            try:
                with open(local_config, 'r', encoding='utf-8') as f:
                    local_data = yaml.safe_load(f) or {}
                    self.merge_config(local_data)
            except Exception:
                pass

    def merge_config(self, local_data):
        """合并本地配置"""
        for key, value in local_data.items():
            if isinstance(value, dict) and key in self.data:
                self.data[key].update(value)
            else:
                self.data[key] = value

    def get(self, key, default=None):
        """获取配置值"""
        keys = key.split('.')
        value = self.data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default

    def get_thresholds(self):
        """获取阈值配置"""
        return self.get('thresholds', {
            'cpu_warn': 80,
            'cpu_crit': 90,
            'mem_warn': 85,
            'mem_crit': 95,
            'disk_warn': 85,
            'disk_crit': 95,
        })

    def get_scan_config(self):
        """获取扫描配置"""
        return self.get('scan', {
            'top_n': 10,
            'recent_days': 7,
        })