#!/bin/bash
###############################################################################
# 报告生成器 (reporter)
# 功能: HTML 报告头/尾/辅助函数 | JSON 数据聚合
###############################################################################

JSON_DATA=""
JSON_INDENT="  "

# ========== 报告头 ==========
generate_html_header() {
    cat >> "$REPORT_FILE" <<'HTML_HEADER'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CloudInspect 云主机安全巡检报告</title>
<style>
  :root {
    --c-primary: #1976d2;
    --c-primary-dark: #0d47a1;
    --c-primary-soft: #e8f1fc;
    --c-text: #1f2937;
    --c-text-2: #4b5563;
    --c-bg: #f3f5f9;
    --c-card: #ffffff;
    --c-border: #d9dee7;
    --c-ok: #16a34a;
    --c-ok-bg: #f0fdf4;
    --c-warn: #d97706;
    --c-warn-bg: #fffbeb;
    --c-crit: #dc2626;
    --c-crit-bg: #fef2f2;
    --c-side-bg: #0f172a;
    --c-side-text: #cbd5e1;
    --c-side-muted: #64748b;
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", Arial, sans-serif;
    --font-mono: ui-monospace, "SFMono-Regular", "Cascadia Code", "JetBrains Mono", Consolas, monospace;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body { font-family: var(--font-sans); font-size: 14px; background: var(--c-bg); color: var(--c-text); line-height: 1.6; }

  /* 深色侧栏导航 */
  .toc { position: fixed; left: 0; top: 0; bottom: 0; width: 220px; background: var(--c-side-bg); padding: 20px 0; overflow-y: auto; z-index: 10; }
  .toc-brand { padding: 0 20px 14px; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 12px; }
  .toc-brand .name { font-size: 14px; font-weight: 700; color: #fff; }
  .toc-brand .ver { font-size: 11px; color: var(--c-side-muted); font-family: var(--font-mono); margin-top: 2px; }
  .toc a { display: flex; align-items: center; gap: 8px; padding: 8px 20px; color: var(--c-side-text); font-size: 13px; text-decoration: none; border-left: 3px solid transparent; transition: all 0.12s; }
  .toc a:hover { background: rgba(255,255,255,0.05); color: #fff; }
  .toc a.active { background: rgba(25,118,210,0.18); border-left-color: var(--c-primary); color: #fff; font-weight: 500; }
  .toc .sec { padding: 12px 20px 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--c-side-muted); }

  /* 内容区 */
  .container { max-width: 1200px; margin: 24px auto 24px 240px; padding: 0 24px; }

  /* 蓝色 Header Banner */
  .header { background: linear-gradient(135deg, var(--c-primary) 0%, var(--c-primary-dark) 100%); color: #fff; padding: 20px 24px 16px; border-radius: 10px; margin-bottom: 18px; box-shadow: 0 2px 8px rgba(15,23,42,0.10); }
  .header h1 { font-size: 20px; font-weight: 700; }
  .header h1 .tag { display: inline-block; background: rgba(255,255,255,0.20); font-size: 11px; padding: 3px 8px; border-radius: 4px; margin-right: 8px; }
  .header-meta { display: flex; flex-wrap: wrap; gap: 16px 28px; margin-top: 10px; font-size: 13px; opacity: 0.9; }

  /* 仪表盘总览 */
  .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-bottom: 18px; }
  .dash-card { background: var(--c-card); border-radius: 10px; padding: 16px 18px; box-shadow: 0 1px 3px rgba(15,23,42,0.06); border: 1px solid var(--c-border); }
  .dash-card.green { border-left: 4px solid var(--c-ok); }
  .dash-card.orange { border-left: 4px solid var(--c-warn); }
  .dash-card.red { border-left: 4px solid var(--c-crit); }
  .dash-card.blue { border-left: 4px solid var(--c-primary); }
  .dash-label { font-size: 12px; color: var(--c-text-2); margin-bottom: 4px; }
  .dash-value { font-size: 26px; font-weight: 700; color: var(--c-text); }
  .dash-value.green { color: var(--c-ok); }
  .dash-value.orange { color: var(--c-warn); }
  .dash-value.red { color: var(--c-crit); }
  .dash-sub { font-size: 11px; color: var(--c-text-2); margin-top: 2px; }

  /* 卡片 */
  .card { background: var(--c-card); border-radius: 10px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(15,23,42,0.06); border: 1px solid var(--c-border); overflow: hidden; }
  .card-header { padding: 14px 18px; border-bottom: 1px solid var(--c-border); background: var(--c-bg); }
  .card-header h2 { font-size: 15px; font-weight: 600; color: var(--c-text); }
  .card-header .icon { margin-right: 6px; }
  .card-body { padding: 16px 18px; }
  .card-body h3 { font-size: 13px; font-weight: 600; color: var(--c-text-2); margin: 14px 0 8px; text-transform: uppercase; letter-spacing: 0.5px; }
  .card-body h3:first-child { margin-top: 0; }

  /* 指标网格 */
  .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 14px; }
  .metric-card { background: var(--c-bg); border-radius: 8px; padding: 12px 14px; text-align: center; }
  .metric-card.green { background: var(--c-ok-bg); }
  .metric-card.orange { background: var(--c-warn-bg); }
  .metric-card.red { background: var(--c-crit-bg); }
  .metric-label { font-size: 11px; color: var(--c-text-2); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
  .metric-value { font-size: 22px; font-weight: 700; color: var(--c-text); }
  .metric-card.green .metric-value { color: var(--c-ok); }
  .metric-card.orange .metric-value { color: var(--c-warn); }
  .metric-card.red .metric-value { color: var(--c-crit); }
  .metric-sub { font-size: 10px; color: var(--c-text-2); margin-top: 2px; }

  /* 信息表格 */
  .info-table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
  .info-table th { background: var(--c-bg); padding: 7px 12px; text-align: left; font-size: 12px; font-weight: 600; color: var(--c-text-2); border-bottom: 1px solid var(--c-border); }
  .info-table td { padding: 6px 12px; border-bottom: 1px solid var(--c-border-light); font-size: 13px; }
  .info-table tr:last-child td { border-bottom: none; }
  .info-table code { background: var(--c-bg); padding: 1px 5px; border-radius: 3px; font-family: var(--font-mono); font-size: 12px; }

  /* 徽章 */
  .badge { display: inline-block; padding: 2px 7px; border-radius: 10px; font-size: 11px; font-weight: 600; }
  .badge.ok { background: var(--c-ok-bg); color: var(--c-ok); }
  .badge.warning { background: var(--c-warn-bg); color: var(--c-warn); }
  .badge.critical { background: var(--c-crit-bg); color: var(--c-crit); }

  /* 告警框 */
  .alert { padding: 12px 16px; border-radius: 8px; margin-top: 12px; }
  .alert-warning { background: var(--c-warn-bg); border: 1px solid var(--c-warn); color: #92400e; }
  .alert-danger { background: var(--c-crit-bg); border: 1px solid var(--c-crit); color: #991b1b; }
  .alert-info { background: var(--c-primary-soft); border: 1px solid var(--c-primary); color: #1e40af; }
  .alert strong { font-weight: 600; }

  /* 磁盘进度条 */
  .disk-item { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--c-border-light); }
  .disk-item:last-child { border-bottom: none; }
  .disk-info { min-width: 180px; }
  .disk-mount { font-weight: 600; font-size: 12px; }
  .disk-fs { font-size: 11px; color: var(--c-text-2); display: block; }
  .disk-bar-wrap { flex: 1; height: 6px; background: var(--c-bg); border-radius: 3px; overflow: hidden; }
  .disk-bar { height: 100%; border-radius: 3px; transition: width 0.3s; }
  .disk-bar.green { background: var(--c-ok); }
  .disk-bar.orange { background: var(--c-warn); }
  .disk-bar.red { background: var(--c-crit); }
  .disk-stats { min-width: 120px; text-align: right; font-size: 12px; }

  /* 颜色文本 */
  .green-text { color: var(--c-ok); }
  .orange-text { color: var(--c-warn); }
  .red-text { color: var(--c-crit); }

  /* pre */
  pre { background: #0f172a; color: #e2e8f0; padding: 12px 14px; border-radius: 6px; font-family: var(--font-mono); font-size: 12px; line-height: 1.5; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
  pre strong { color: #f87171; }

  /* 文本颜色 */
  .text-muted { color: var(--c-text-2); font-style: italic; }
  code { background: var(--c-bg); padding: 1px 5px; border-radius: 3px; font-family: var(--font-mono); font-size: 12px; }

  /* 进度条动画 */
  @keyframes slideIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
  .card { animation: slideIn 0.3s ease-out; }
</style>
</head>
<body>

<!-- 侧栏导航 -->
<nav class="toc">
  <div class="toc-brand">
    <div class="name">&#128737; CloudInspect</div>
    <div class="ver">v1.0 云主机巡检</div>
  </div>
  <div class="sec">导航</div>
  <a href="#top" class="active" onclick="highlight(this)">&#127968; 总览仪表盘</a>
  <a href="#sysinfo" onclick="highlight(this)">&#128737; 系统信息</a>
  <a href="#disk" onclick="highlight(this)">&#128190; 磁盘状态</a>
  <a href="#network" onclick="highlight(this)">&#127760; 网络状态</a>
  <a href="#process" onclick="highlight(this)">&#128187; 进程状态</a>
  <a href="#service" onclick="highlight(this)">&#9881; 服务状态</a>
  <a href="#cron" onclick="highlight(this)">&#128340; 定时任务</a>
  <a href="#security" onclick="highlight(this)">&#128737; 安全基线</a>
  <a href="#backdoor" onclick="highlight(this)">&#128678; 后门检测</a>
  <a href="#rootkit" onclick="highlight(this)">&#128737; Rootkit</a>
  <a href="#log_analysis" onclick="highlight(this)">&#128209; 日志分析</a>
  <a href="#history" onclick="highlight(this)">&#128220; 历史命令</a>
  <a href="#webshell" onclick="highlight(this)">&#128275; Webshell</a>
</nav>

<!-- 内容区 -->
<div class="container">
HTML_HEADER

    # 动态生成 Header 横幅
    local elapsed=$(elapsed_time)
    local risk_level="正常"
    local risk_cls="green"
    if (( CRITICAL_COUNT > 0 )); then
        risk_level="严重告警"
        risk_cls="red"
    elif (( WARN_COUNT > 0 )); then
        risk_level="存在警告"
        risk_cls="orange"
    fi

    cat >> "$REPORT_FILE" <<EOF
  <!-- Header Banner -->
  <div class="header" id="top">
    <h1><span class="tag">${VERSION}</span> 云主机安全巡检报告</h1>
    <div class="header-meta">
      <span>&#128100; 主机: $(hostname)</span>
      <span>&#128197; 时间: $(date '+%Y-%m-%d %H:%M:%S')</span>
      <span>&#128737; 操作系统: ${OS_PRETTY}</span>
      <span>&#9203; 耗时: ${elapsed}</span>
      <span>&#128200; 模式: ${MODE}</span>
    </div>
  </div>

  <!-- 仪表盘总览 -->
  <div class="dashboard">
    <div class="dash-card ${risk_cls}">
      <div class="dash-label">风险等级</div>
      <div class="dash-value ${risk_cls}">${risk_level}</div>
      <div class="dash-sub">严重: ${CRITICAL_COUNT} | 警告: ${WARN_COUNT}</div>
    </div>
    <div class="dash-card green">
      <div class="dash-label">CPU</div>
      <div class="dash-value">$(grep cpu_usage /tmp/cloudinspect_tmp.json 2>/dev/null | grep -oP 'cpu_usage_pct.:\K[0-9]+' || echo 'N/A')%</div>
      <div class="dash-sub">$(nproc 2>/dev/null || echo '?') 核</div>
    </div>
    <div class="dash-card green">
      <div class="dash-label">内存</div>
      <div class="dash-value">$(grep mem_used /tmp/cloudinspect_tmp.json 2>/dev/null | grep -oP 'mem_used_pct.:\K[0-9]+' || echo 'N/A')%</div>
      <div class="dash-sub">$(grep mem_total /tmp/cloudinspect_tmp.json 2>/dev/null | head -1 || echo 'N/A')</div>
    </div>
    <div class="dash-card green">
      <div class="dash-label">磁盘</div>
      <div class="dash-value">$(df -h / 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%' || echo 'N/A')%</div>
      <div class="dash-sub">根分区使用率</div>
    </div>
    <div class="dash-card blue">
      <div class="dash-label">运行时间</div>
      <div class="dash-value">$(uptime -p 2>/dev/null | sed 's/up //' || uptime | awk '{print $3}' | sed 's/,//')</div>
      <div class="dash-sub">$(uptime -s 2>/dev/null | cut -c1-10 || echo 'N/A')</div>
    </div>
  </div>

  <script>
  function highlight(el) {
    document.querySelectorAll('.toc a').forEach(function(a){ a.classList.remove('active'); });
    el.classList.add('active');
  }
  </script>
HTML_HEADER
}

# ========== 报告尾 ==========
generate_html_footer() {
    local elapsed=$(elapsed_time)
    cat >> "$REPORT_FILE" <<EOF

  <!-- Footer -->
  <div style="text-align:center; padding: 20px 0; color: #94a3b8; font-size: 12px; border-top: 1px solid #e2e8f0; margin-top: 24px;">
    <p>CloudInspect ${VERSION} - 云主机安全巡检报告 | 生成时间: $(date '+%Y-%m-%d %H:%M:%S') | 耗时: ${elapsed}</p>
    <p>Designed for 护网行动 | 异常请联系安全团队</p>
  </div>
</div>
</body>
</html>
EOF
}

# ========== 辅助函数 ==========
append_section_header() {
    local section_id="$1" section_title="$2"
    # 动态注入到报告（模块中已直接写入，这里是备用接口）
    true
}

# ========== JSON 数据聚合 ==========
json_add() {
    local key="$1" value="$2"
    if [[ -z "$JSON_DATA" ]]; then
        JSON_DATA="{\n"
    else
        JSON_DATA+=",\n"
    fi
    JSON_DATA+="${JSON_INDENT}\"${key}\": ${value}"
}

json_finalize() {
    JSON_DATA+="\n}"
}

# ========== 输出 JSON ==========
output_json() {
    json_finalize
    echo -e "$JSON_DATA" > "${REPORT_FILE%.html}.json"
}

# ========== 输出 Markdown ==========
output_markdown() {
    local md_file="${REPORT_FILE%.html}.md"
    cat > "$md_file" <<EOF
# CloudInspect 云主机安全巡检报告

## 基本信息
- **主机**: $(hostname)
- **操作系统**: $OS_PRETTY
- **巡检时间**: $(date '+%Y-%m-%d %H:%M:%S')
- **工作模式**: $MODE
- **耗时**: $(elapsed_time)

## 巡检结果摘要
- **风险等级**: $([ "$CRITICAL_COUNT" -gt 0 ] && echo "严重告警" || ([ "$WARN_COUNT" -gt 0 ] && echo "存在警告" || echo "正常"))
- **严重告警**: $CRITICAL_COUNT
- **警告**: $WARN_COUNT

## 详细报告

> 详细检测结果请查看 HTML 格式报告。

---
*由 CloudInspect ${VERSION} 自动生成*
EOF
}