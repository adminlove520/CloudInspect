#!/bin/bash
###############################################################################
# 模块11: 历史命令分析 (history)
###############################################################################

collect_history() {
    local section_id="history" section_title="历史命令分析"
    log_step "分析历史命令..."
    append_section_header "$section_id" "$section_title"

    local history_output=""
    local suspicious_count=0

    # 境外 IP 列表（常见高危地区）
    local overseas_ips="185.220.|103.75.|103.76.|45.33.|104.238.|198.74.|192.168.10.1|10.0.0.1"

    history_output+="\n=== 历史命令分析 ===\n"

    # 检查各用户 history
    while read -r user; do
        [[ -z "$user" ]] && continue
        local home_dir=$(getent passwd "$user" 2>/dev/null | cut -d: -f6)
        [[ ! -d "$home_dir" ]] && continue

        local hist_files=".bash_history .sh_history .history"
        for hf in $hist_files; do
            local hist_file="$home_dir/$hf"
            [[ ! -f "$hist_file" ]] && continue

            local overseas_cmds=""
            local shell_cmds=""
            local download_cmds=""

            while read -r line; do
                [[ -z "$line" || "$line" =~ ^# ]] && continue

                # 境外 IP 操作
                if echo "$line" | grep -qE "ssh|scp|rsync" | grep -E "$overseas_ips" &>/dev/null; then
                    overseas_cmds+="  $user: $line\n"
                    ((suspicious_count++))
                fi

                # 反弹 shell 类
                if echo "$line" | grep -qiE "bash.*-i|/dev/tcp|nc\s.*-e|ncat|bash -c.*base64|python.*-c.*import.*socket|php.*-r.*socket"; then
                    shell_cmds+="  $user: $line\n"
                    log_warn "反弹shell命令: $user - $line"
                    ((suspicious_count++))
                fi

                # 可疑下载
                if echo "$line" | grep -qiE "wget.*境外|curl.*境外|wget\s+http|curl.*-O.*http"; then
                    download_cmds+="  $user: $line\n"
                    log_warn "可疑下载: $user - $line"
                    ((suspicious_count++))
                fi
            done < "$hist_file"

            [[ -n "$overseas_cmds" ]] && history_output+="\n--- 境外IP操作 ($user) ---\n$overseas_cmds"
            [[ -n "$shell_cmds" ]] && history_output+="\n--- 反弹shell命令 ($user) ---\n$shell_cmds"
            [[ -n "$download_cmds" ]] && history_output+="\n--- 可疑下载 ($user) ---\n$download_cmds"
        done
    done < <(cut -d: -f1 /etc/passwd 2>/dev/null | head -20)

    history_output+="\n=== 分析完成，发现 $suspicious_count 项可疑 ===\n"

    log_info "历史命令分析完成: $suspicious_count 项可疑"

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128220;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card $([ "$suspicious_count" -gt 0 ] && echo orange || echo green)">
        <div class="metric-label">可疑命令数</div>
        <div class="metric-value">$suspicious_count</div>
      </div>
    </div>
    <pre>$(html_escape "$history_output")</pre>
EOF

    [[ "$suspicious_count" -gt 0 ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-warning">
      <strong>&#9888; 发现可疑历史命令，建议人工审查！</strong>
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF

    json_add "history" "{\"suspicious_count\": $suspicious_count}"
}