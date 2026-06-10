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

    if (( zombie_count > 0 )); then
        log_warn "发现僵尸进程: ${zombie_count} 个"
    fi

    # CPU TOP
    local cpu_top=""
    cpu_top=$(ps aux --sort=-%cpu 2>/dev/null | head -$((TOP_N + 1)) | tail -$TOP_N | \
        awk '{printf "%-12s %-8s %-6s %-6s %s\n", $1, $2, $3"%", $4"%", $11}' || echo "无数据")

    # MEM TOP
    local mem_top=""
    mem_top=$(ps aux --sort=-%mem 2>/dev/null | head -$((TOP_N + 1)) | tail -$TOP_N | \
        awk '{printf "%-12s %-8s %-6s %-6s %s\n", $1, $2, $3"%", $4"%", $11}' || echo "无数据")

    # 隐藏进程检测（/proc 中有但 ps 看不到）
    local hidden_procs=""
    hidden_procs=$(for pid in $(ls /proc/ 2>/dev/null | grep -E '^[0-9]+$'); do
        if [[ -f "/proc/$pid/status" ]]; then
            local name=$(grep "^Name:" /proc/$pid/status 2>/dev/null | cut -f2)
            local exe=$(readlink /proc/$pid/exe 2>/dev/null || echo "")
            local cmdline=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ')
            # 检查可疑进程
            if [[ -n "$exe" && "$exe" == *tmp* ]] || [[ -n "$cmdline" && "$cmdline" =~ python.*-c.*base64 ]]; then
                log_warn "可疑进程: PID=$pid NAME=$name EXE=$exe"
                echo "可疑: PID=$pid NAME=$name CMD=$cmdline"
            fi
        fi
    done | head -20 || echo "")

    # D 状态进程
    local d_procs=""
    d_procs=$(ps aux 2>/dev/null | awk '$8 ~ /D/ {print $0}' | head -10 || echo "无 D 状态进程")

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
    </div>

    <h3>CPU 占用 TOP ${TOP_N}</h3>
    <pre>$(html_escape "$cpu_top")</pre>

    <h3>内存占用 TOP ${TOP_N}</h3>
    <pre>$(html_escape "$mem_top")</pre>

    <h3>D 状态进程（不可中断）</h3>
    <pre>$(html_escape "$d_procs")</pre>
EOF

    [[ -n "$hidden_procs" ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-warning">
      <strong>&#9888; 可疑进程检测</strong>
      <pre>$(html_escape "$hidden_procs")</pre>
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF

    json_add "process" "{}"
}