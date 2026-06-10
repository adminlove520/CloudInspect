#!/bin/bash
###############################################################################
# 模块6: 定时任务 (cron)
###############################################################################

collect_cron() {
    local section_id="cron" section_title="定时任务"
    log_step "检查定时任务..."
    append_section_header "$section_id" "$section_title"

    local cron_output=""
    local suspicious_found=0
    local cron_entries=0

    # 系统 crontab
    if [[ -f /etc/crontab ]]; then
        cron_output+="\n--- /etc/crontab ---\n"
        cron_output+=$(cat /etc/crontab 2>/dev/null || echo "无法读取")
        ((cron_entries++)) || true
    fi

    # cron.d
    if [[ -d /etc/cron.d ]]; then
        for f in /etc/cron.d/*; do
            [[ -f "$f" ]] || continue
            cron_output+="\n--- $f ---\n"
            cron_output+=$(cat "$f" 2>/dev/null || echo "")
            ((cron_entries++)) || true

            # 可疑检测
            local content
            content=$(cat "$f" 2>/dev/null || echo "")
            if echo "$content" | grep -qiE "wget|curl.*境外|bash.*-i|nc\s|境外ip|base64"; then
                log_warn "可疑 Cron: $f"
                ((suspicious_found++)) || true
            fi
        done
    fi

    # 用户 crontab
    local user_crons_html=""
    while IFS= read -r user; do
        [[ -z "$user" ]] && continue
        local crontab
        crontab=$(crontab -l -u "$user" 2>/dev/null || echo "")
        if [[ -n "$crontab" ]]; then
            cron_output+="\n--- 用户: $user ---\n$crontab"
            ((cron_entries++)) || true

            if echo "$crontab" | grep -qiE "wget|curl.*境外|bash.*-i|nc\s|境外ip|base64"; then
                log_warn "用户 $user 定时任务可疑"
                ((suspicious_found++)) || true
                user_crons_html+="<div class=\"alert-item\">用户 $user 的 crontab 可疑</div>"
            fi
        fi
    done < <(cut -d: -f1 /etc/passwd 2>/dev/null | sort -u)

    [[ -z "$cron_output" ]] && cron_output="无定时任务"

    json_add "cron" "{\"entries\":${cron_entries},\"suspicious_count\":${suspicious_found}}"

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128340;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card green">
        <div class="metric-label">定时任务数</div>
        <div class="metric-value">${cron_entries}</div>
      </div>
      <div class="metric-card $([ "$suspicious_found" -gt 0 ] && echo red || echo green)">
        <div class="metric-label">可疑任务</div>
        <div class="metric-value">${suspicious_found}</div>
      </div>
    </div>
    <h3>定时任务内容</h3>
    <pre>$(html_escape "$cron_output")</pre>
EOF

    [[ "$suspicious_found" -gt 0 ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-warning">
      <strong>&#9888; 发现可疑定时任务，建议人工审查</strong>
      ${user_crons_html}
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF
}