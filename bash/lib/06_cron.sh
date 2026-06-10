#!/bin/bash
###############################################################################
# 模块6: 定时任务 (cron)
###############################################################################

collect_cron() {
    local section_id="cron" section_title="定时任务"
    log_step "检查定时任务..."
    append_section_header "$section_id" "$section_title"

    local cron_output="=== 系统 Crontab ===\n"
    local suspicious_found=0

    # 系统 crontab
    if [[ -f /etc/crontab ]]; then
        cron_output+="\n--- /etc/crontab ---\n"
        cron_output+=$(cat /etc/crontab 2>/dev/null || echo "无法读取")
    fi

    # cron.d
    if [[ -d /etc/cron.d ]]; then
        cron_output+="\n\n--- /etc/cron.d/ ---\n"
        for f in /etc/cron.d/*; do
            [[ -f "$f" ]] && cron_output+="\n--- $f ---\n$(cat "$f" 2>/dev/null)"
        done
    fi

    # 用户 crontab
    local user_crons=""
    while read -r user; do
        [[ -z "$user" ]] && continue
        local crontab=$(crontab -l -u "$user" 2>/dev/null || echo "")
        if [[ -n "$crontab" ]]; then
            user_crons+="\n--- $user ---\n$crontab"
            # 可疑检测
            if echo "$crontab" | grep -qiE "wget|curl.*境外|bash.*-i|nc\s|境外ip|base64"; then
                log_warn "用户 $user 定时任务可疑"
                ((suspicious_found++))
            fi
        fi
    done < <(cut -d: -f1 /etc/passwd 2>/dev/null | sort -u)

    [[ -n "$user_crons" ]] && cron_output+="\n\n=== 用户 Crontab ===$user_crons"

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128340;</span> $section_title</h2>
  </div>
  <div class="card-body">
    $(pre_block "$cron_output" "无定时任务")
EOF

    if (( suspicious_found > 0 )); then
        cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-warning">
      <strong>&#9888; 发现可疑定时任务，建议人工审查</strong>
    </div>
EOF
    fi

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF

    json_add "cron" "{\"suspicious_count\": $suspicious_found}"
}