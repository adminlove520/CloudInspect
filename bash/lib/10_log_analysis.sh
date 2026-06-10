#!/bin/bash
###############################################################################
# 模块10: 日志分析 (log_analysis)
###############################################################################

collect_log_analysis() {
    local section_id="log_analysis" section_title="日志分析"
    log_step "分析系统日志..."
    append_section_header "$section_id" "$section_title"

    local log_output=""
    local anomaly_count=0

    # 1. secure 日志分析（登录相关）
    log_output+="\n=== 安全日志分析 ===\n"
    local secure_lines=""
    for log_file in /var/log/secure /var/log/auth.log; do
        [[ -f "$log_file" ]] && secure_lines=$(tail -"$LOG_LINES" "$log_file" 2>/dev/null || echo "")
        [[ -n "$secure_lines" ]] && break
    done

    if [[ -n "$secure_lines" ]]; then
        local failed_auth=$(echo "$secure_lines" | grep -ciE "failed|password|invalid" 2>/dev/null || echo 0)
        local failed_count=0
        [[ "$failed_auth" =~ ^[0-9]+$ ]] && failed_count=$failed_auth
        if (( failed_count > 10 )); then
            log_warn "最近 $LOG_LINES 行日志中发现 $failed_count 次认证失败"
            ((anomaly_count++))
        fi

        log_output+="\n--- 最近认证记录 ---\n$secure_lines\n"
    fi

    # 2. dmesg 硬件错误
    log_output+="\n=== dmesg 硬件错误 ===\n"
    local dmesg_output=$(safe_dmesg)
    local dmesg_errors=$(echo "$dmesg_output" | grep -ciE "error|fail|ECC|IO error|硬件故障" 2>/dev/null || echo 0)
    if (( dmesg_errors > 0 )); then
        log_output+="⚠️ 发现 $dmesg_errors 条硬件错误\n"
        log_warn "dmesg 硬件错误: $dmesg_errors 条"
        ((anomaly_count++))
    fi

    # 3. OOM 事件
    log_output+="\n=== OOM 事件检测 ===\n"
    local oom_count=0
    if [[ -f /var/log/messages ]]; then
        oom_count=$(grep -c "Out of memory" /var/log/messages 2>/dev/null || echo 0)
    fi
    if (( oom_count > 0 )); then
        log_output+="⚠️ 发现 $oom_count 次 OOM 事件\n"
        log_warn "OOM 事件: $oom_count 次"
        ((anomaly_count++))
    else
        log_output+="✅ 未发现 OOM 事件\n"
    fi

    # 4. 系统日志异常（error/fail/critical）
    log_output+="\n=== 系统日志异常检测 ===\n"
    local syslog_anomaly=""
    if [[ -f /var/log/messages ]]; then
        syslog_anomaly=$(tail -"$LOG_LINES" /var/log/messages 2>/dev/null | grep -iE "error|fail|critical|panic|oom" | head -10 || echo "无异常")
    fi
    log_output+="$syslog_anomaly\n"

    # 5. NTP 时间同步
    log_output+="\n=== NTP 时间同步 ===\n"
    local ntp_status="未知"
    if command -v timedatectl &>/dev/null; then
        ntp_status=$(timedatectl 2>/dev/null | grep -i "NTP" | awk '{print $3}' || echo "未知")
    fi
    log_output+="NTP 状态: $ntp_status\n"

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128209;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card $([ "$anomaly_count" -gt 0 ] && echo orange || echo green)">
        <div class="metric-label">日志异常数</div>
        <div class="metric-value">$anomaly_count</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">OOM 次数</div>
        <div class="metric-value">${oom_count:-0}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">NTP 状态</div>
        <div class="metric-value">$ntp_status</div>
      </div>
    </div>
    <pre>$(html_escape "$log_output")</pre>
  </div>
</div>
EOF

    json_add "log_analysis" "{\"anomaly_count\": $anomaly_count, \"oom_count\": ${oom_count:-0}}"
}