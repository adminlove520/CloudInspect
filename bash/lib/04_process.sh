#!/bin/bash
###############################################################################
# 模块4: 进程检测 (process)
###############################################################################

collect_process() {
    local section_id="process" section_title="进程状态"
    log_step "检查进程状态..."
    append_section_header "$section_id" "$section_title"

    local zombie_count=0
    zombie_count=$(ps aux 2>/dev/null | grep -c ' Z ' || echo "0")
    [[ "$zombie_count" =~ ^[0-9]+$ ]] || zombie_count=0

    if (( zombie_count > 0 )); then
        log_warn "发现僵尸进程: ${zombie_count} 个"
    fi

    # CPU TOP
    local cpu_top_html=""
    local cpu_top_json=""
    ps aux --sort=-%cpu 2>/dev/null | head -$((TOP_N + 1)) | tail -$TOP_N | while read -r line; do
        local user pid cpu mem cmd
        user=$(echo "$line" | awk '{print $1}')
        pid=$(echo "$line" | awk '{print $2}')
        cpu=$(echo "$line" | awk '{print $3}')
        mem=$(echo "$line" | awk '{print $4}')
        cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i}')
        [[ -z "$cmd" ]] && continue
        cpu_top_html+="<tr><td>$(html_escape "$user")</td><td>$(html_escape "$pid")</td>"
        cpu_top_html+="<td>$(html_escape "$cpu")</td><td>$(html_escape "$mem")</td><td><code>$(html_escape "${cmd:0:60}")</code></td></tr>"
        cpu_top_json+="{\"user\":\"$(echo "$user" | sed 's/"/\\"/g')\",\"pid\":\"$pid\",\"cpu\":\"$cpu\",\"mem\":\"$mem\",\"cmd\":\"$(echo "$cmd" | sed 's/"/\\"/g' | cut -c1-60)\"},"
    done || true
    cpu_top_json="${cpu_top_json%,}"

    # MEM TOP
    local mem_top_html=""
    local mem_top_json=""
    ps aux --sort=-%mem 2>/dev/null | head -$((TOP_N + 1)) | tail -$TOP_N | while read -r line; do
        local user pid mem cmd
        user=$(echo "$line" | awk '{print $1}')
        pid=$(echo "$line" | awk '{print $2}')
        mem=$(echo "$line" | awk '{print $4}')
        cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i}')
        [[ -z "$cmd" ]] && continue
        mem_top_html+="<tr><td>$(html_escape "$user")</td><td>$(html_escape "$pid")</td>"
        mem_top_html+="<td>$(html_escape "$mem")</td><td><code>$(html_escape "${cmd:0:60}")</code></td></tr>"
        mem_top_json+="{\"user\":\"$(echo "$user" | sed 's/"/\\"/g')\",\"pid\":\"$pid\",\"mem\":\"$mem\"},"
    done || true
    mem_top_json="${mem_top_json%,}"

    # D 状态进程
    local d_procs=""
    d_procs=$(ps aux 2>/dev/null | awk '$8 ~ /D/ {print $0}' | head -10 | while read -r line; do
        echo "$(html_escape "$line")"
    done || echo "无 D 状态进程")

    # 可疑进程检测
    local suspicious_found=0
    local suspicious_html=""
    for pid_dir in /proc/[0-9]*; do
        [[ -d "$pid_dir" ]] || continue
        local pid="${pid_dir##*/}"
        local exe
        exe=$(readlink "$pid_dir/exe" 2>/dev/null || echo "")
        local cmdline
        cmdline=$(tr '\0' ' ' < "$pid_dir/cmdline" 2>/dev/null | cut -c1-100 || echo "")
        if [[ -n "$exe" && "$exe" == *tmp* ]]; then
            suspicious_html+="<div class=\"alert-item\">PID=$pid EXE=$exe CMD=$cmdline</div>"
            ((suspicious_found++)) || true
        fi
    done || true

    # 构建 JSON
    local final_json="{\"zombie_count\":${zombie_count},\"suspicious_count\":${suspicious_found},\"cpu_top\":[${cpu_top_json}],\"mem_top\":[${mem_top_json}]}"
    json_add "process" "$final_json"

    # 输出 HTML
    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128187;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card $([ "$zombie_count" -gt 0 ] && echo orange || echo green)">
        <div class="metric-label">僵尸进程</div>
        <div class="metric-value">${zombie_count}</div>
      </div>
      <div class="metric-card $([ "$suspicious_found" -gt 0 ] && echo orange || echo green)">
        <div class="metric-label">可疑进程</div>
        <div class="metric-value">${suspicious_found}</div>
      </div>
    </div>

    <h3>CPU 占用 TOP ${TOP_N}</h3>
    <table class="info-table">
      <tr><th>USER</th><th>PID</th><th>CPU%</th><th>MEM%</th><th>CMD</th></tr>
      ${cpu_top_html}
    </table>

    <h3>内存占用 TOP ${TOP_N}</h3>
    <table class="info-table">
      <tr><th>USER</th><th>PID</th><th>MEM%</th><th>CMD</th></tr>
      ${mem_top_html}
    </table>

    <h3>D 状态进程（不可中断）</h3>
    <pre>$(html_escape "$d_procs")</pre>
EOF

    [[ "$suspicious_found" -gt 0 ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-warning">
      <strong>&#9888; 发现可疑进程</strong>
      <div>${suspicious_html}</div>
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF
}