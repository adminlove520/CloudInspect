# coding: utf-8
"""
Windows 报告生成器
"""

import os
import json
import datetime


class Reporter:
    def __init__(self, config, results):
        self.config = config
        self.results = results

    def generate(self, format='html'):
        """生成报告"""
        output_file = self.get_output_file(format)

        if format == 'json':
            return self.generate_json(output_file)
        elif format == 'md':
            return self.generate_markdown(output_file)
        else:
            return self.generate_html(output_file)

    def get_output_file(self, format):
        """获取输出文件路径"""
        output = getattr(self.config.args, 'output', None)
        if output:
            if os.path.isdir(output):
                hostname = os.environ.get('COMPUTERNAME', 'unknown')
                timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'inspect_{hostname}_{timestamp}.{format}'
                return os.path.join(output, filename)
            return output

        # 默认输出目录
        report_dir = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'cloudinspect')
        os.makedirs(report_dir, exist_ok=True)

        hostname = os.environ.get('COMPUTERNAME', 'unknown')
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'inspect_{hostname}_{timestamp}.{format}'
        return os.path.join(report_dir, filename)

    def generate_json(self, output_file):
        """生成 JSON 报告"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        return output_file

    def generate_markdown(self, output_file):
        """生成 Markdown 报告"""
        md = self.build_markdown()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(md)
        return output_file

    def generate_html(self, output_file):
        """生成 HTML 报告"""
        html = self.build_html()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        return output_file

    def build_markdown(self):
        """构建 Markdown 内容"""
        hostname = os.environ.get('COMPUTERNAME', 'unknown')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        md = f"""# CloudInspect 云主机安全巡检报告

## 基本信息

| 项目 | 值 |
|---|---|
| 主机名 | {hostname} |
| 巡检时间 | {timestamp} |
| 模式 | {getattr(self.config.args, 'mode', 'routine')} |
| 警告数 | {self.results.get('warnings', 0)} |
| 严重数 | {self.results.get('critical', 0)} |

## 检测模块

"""
        for module_name, result in self.results.get('modules', {}).items():
            status = result.get('status', 'unknown')
            issues = result.get('issues', [])

            md += f"""### {module_name.upper()}

- **状态**: {status}
- **告警数**: {len(issues)}

"""
            if issues:
                md += "| 级别 | 模块 | 描述 |\n|---|---|---|\n"
                for issue in issues:
                    md += f"| {issue.get('level', 'info')} | {issue.get('module', '')} | {issue.get('desc', '')} |\n"
                md += "\n"

        return md

    def build_html(self):
        """构建 HTML 内容"""
        hostname = os.environ.get('COMPUTERNAME', 'unknown')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        warnings = self.results.get('warnings', 0)
        critical = self.results.get('critical', 0)

        # 风险等级
        if critical > 0:
            risk_level = "严重"
            risk_color = "red"
        elif warnings > 0:
            risk_level = "警告"
            risk_color = "orange"
        else:
            risk_level = "正常"
            risk_color = "green"

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CloudInspect 巡检报告 - {hostname}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
        .header .info {{ opacity: 0.9; font-size: 14px; }}
        .summary {{ display: flex; gap: 20px; padding: 30px; background: #f8f9fa; }}
        .summary-card {{ flex: 1; padding: 20px; background: white; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .summary-card .value {{ font-size: 36px; font-weight: bold; }}
        .summary-card .label {{ color: #666; margin-top: 5px; }}
        .risk-{risk_color} {{ color: {risk_color}; }}
        .content {{ padding: 30px; }}
        .module {{ margin-bottom: 30px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; }}
        .module-header {{ background: #f8f9fa; padding: 15px 20px; font-weight: bold; font-size: 16px; border-bottom: 1px solid #e0e0e0; }}
        .module-body {{ padding: 20px; }}
        .status-ok {{ color: green; }}
        .status-warning {{ color: orange; }}
        .status-error {{ color: red; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #e0e0e0; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
        .badge-ok {{ background: #d4edda; color: #155724; }}
        .badge-warning {{ background: #fff3cd; color: #856404; }}
        .badge-critical {{ background: #f8d7da; color: #721c24; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ CloudInspect 云主机安全巡检报告</h1>
            <div class="info">
                主机: {hostname} | 时间: {timestamp} | 模式: {getattr(self.config.args, 'mode', 'routine')}
            </div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <div class="value risk-{risk_color}">{risk_level}</div>
                <div class="label">风险等级</div>
            </div>
            <div class="summary-card">
                <div class="value">{warnings}</div>
                <div class="label">警告数</div>
            </div>
            <div class="summary-card">
                <div class="value">{critical}</div>
                <div class="label">严重数</div>
            </div>
            <div class="summary-card">
                <div class="value">{len(self.results.get('modules', {}))}</div>
                <div class="label">检测模块</div>
            </div>
        </div>

        <div class="content">
"""

        for module_name, result in self.results.get('modules', {}).items():
            status = result.get('status', 'unknown')
            issues = result.get('issues', [])

            status_class = f"status-{status}" if status in ['ok', 'warning', 'error'] else ""

            html += f"""
            <div class="module">
                <div class="module-header">
                    {module_name.upper()} - 状态: <span class="{status_class}">{status}</span>
                </div>
                <div class="module-body">
"""

            if issues:
                html += """
                    <table>
                        <tr>
                            <th>级别</th>
                            <th>描述</th>
                        </tr>
"""
                for issue in issues:
                    level = issue.get('level', 'info')
                    badge_class = f"badge-{level}" if level in ['ok', 'warning', 'critical'] else 'badge-ok'
                    html += f"""
                        <tr>
                            <td><span class="badge {badge_class}">{level}</span></td>
                            <td>{issue.get('desc', '')}</td>
                        </tr>
"""
                html += """
                    </table>
"""
            else:
                html += "<p>未发现问题</p>"

            html += """
                </div>
            </div>
"""

        html += """
        </div>
    </div>
</body>
</html>
"""
        return html