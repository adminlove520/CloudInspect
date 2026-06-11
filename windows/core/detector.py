# coding: utf-8
"""
Windows 检测调度器
"""

import os
import time
import sys

# 添加 lib 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class Detector:
    def __init__(self, config):
        self.config = config
        self.results = {
            'warnings': 0,
            'critical': 0,
            'modules': {}
        }
        self.modules = []

    def run(self):
        """执行所有检测模块"""
        mode = getattr(self.config.args, 'mode', 'routine')

        # 根据模式决定加载哪些模块
        module_map = {
            'quick': ['sysinfo', 'disk', 'network', 'process'],
            'routine': ['sysinfo', 'disk', 'network', 'process', 'service',
                       'eventlog', 'firewall', 'user', 'update'],
            'emergency': ['sysinfo', 'disk', 'network', 'process', 'service',
                          'eventlog', 'firewall', 'user', 'update', 'registry', 'privilege'],
            'full': ['sysinfo', 'disk', 'network', 'process', 'service',
                    'eventlog', 'firewall', 'user', 'update', 'registry',
                    'privilege', 'defender']
        }

        self.modules = module_map.get(mode, module_map['routine'])

        # 导入 OS 检测
        from core.os_detect import OSDetect
        os_detect = OSDetect()

        # 执行各模块
        for module_name in self.modules:
            try:
                module_class = self.load_module(module_name)
                if module_class:
                    # 创建类实例并调用 run 方法
                    instance = module_class()
                    result = instance.run(os_detect, self.config)
                    self.results['modules'][module_name] = result

                    # 统计告警
                    if 'issues' in result:
                        for issue in result['issues']:
                            if issue.get('level') == 'warning':
                                self.results['warnings'] += 1
                            elif issue.get('level') == 'critical':
                                self.results['critical'] += 1

            except Exception as e:
                self.results['modules'][module_name] = {
                    'status': 'error',
                    'error': str(e)
                }

        return self.results

    def load_module(self, module_name):
        """动态加载模块类"""
        try:
            module_file = os.path.join(
                os.path.dirname(__file__), '..', 'lib', f'{module_name}.py'
            )
            if not os.path.exists(module_file):
                return None

            # 动态导入
            import importlib.util
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # 将模块名转为类名 (例如: sysinfo -> SysinfoModule)
            class_name = ''.join(word.capitalize() for word in module_name.split('_')) + 'Module'

            if hasattr(module, class_name):
                return getattr(module, class_name)

            return None
        except Exception:
            return None