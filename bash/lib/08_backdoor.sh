#!/bin/bash
###############################################################################
# 模块8: 后门检测 (backdoor) — 参考 GScan 设计
###############################################################################

collect_backdoor() {
    local section_id="backdoor" section_title="后门检测"
    log_step "检测后门痕迹..."
    append_section_header "$section_id" "$section_title"

    local backdoor_found=0
    local backdoor_output="=== 后门检测开始 ===\n"

    # 1. LD_PRELOAD 后门
    backdoor_output+="\n[1] LD_PRELOAD 检测\n"
    local ld_preload=$(grep -r "LD_PRELOAD" /root/.bashrc /root/.bash_profile /etc/bashrc /etc/profile 2>/dev/null | grep -v "^#" || echo "")
    if [[ -n "$ld_preload" ]]; then
        backdoor_output+="  ⚠️ 发现 LD_PRELOAD 配置: $ld_preload\n"
        log_warn "LD_PRELOAD 后门: $ld_preload"
        ((backdoor_found++))
    fi

    # 2. ld.so.preload 后门
    backdoor_output+="\n[2] ld.so.preload 检测\n"
    if [[ -f /etc/ld.so.preload ]]; then
        local ld_preload_content=$(cat /etc/ld.so.preload 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "")
        if [[ -n "$ld_preload_content" ]]; then
            backdoor_output+="  ⚠️ /etc/ld.so.preload 存在: $ld_preload_content\n"
            log_error "ld.so.preload 后门: $ld_preload_content"
            ((backdoor_found++))
        fi
    fi

    # 3. PROMPT_COMMAND 后门
    backdoor_output+="\n[3] PROMPT_COMMAND 检测\n"
    local prompt_cmd=$(grep -r "PROMPT_COMMAND" /root/.bashrc /etc/bashrc /etc/profile 2>/dev/null | grep -v "^#" || echo "")
    if [[ -n "$prompt_cmd" ]]; then
        backdoor_output+="  ⚠️ 发现 PROMPT_COMMAND: $prompt_cmd\n"
        log_warn "PROMPT_COMMAND 后门: $prompt_cmd"
        ((backdoor_found++))
    fi

    # 4. Cron 后门检测
    backdoor_output+="\n[4] Cron 后门检测\n"
    local cron_dirs="/var/spool/cron/ /etc/cron.d/ /etc/cron.daily/ /etc/cron.weekly/ /etc/cron.hourly/"
    for cron_dir in $cron_dirs; do
        [[ ! -d "$cron_dir" ]] && continue
        while read -r cron_file; do
            [[ -f "$cron_file" ]] || continue
            local content=$(cat "$cron_file" 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "")
            if [[ -n "$content" ]]; then
                # 检测可疑 cron
                if echo "$content" | grep -qiE "wget.*境外|curl.*境外|境外ip|nc\s|bash.*-i|/dev/tcp|base64.*解码"; then
                    backdoor_output+="  ⚠️ 可疑 Cron 文件: $cron_file\n  内容: $content\n"
                    log_error "Cron 后门: $cron_file"
                    ((backdoor_found++))
                fi
            fi
        done < <(find "$cron_dir" -type f 2>/dev/null)
    done

    # 5. SSH 后门检测 (ln -sf /usr/sbin/sshd /tmp/su)
    backdoor_output+="\n[5] SSH 后门检测\n"
    local suspicious_sshd=$(find /tmp -name "su" -type f 2>/dev/null || echo "")
    if [[ -n "$suspicious_sshd" ]]; then
        backdoor_output+="  ⚠️ 发现可疑 sshd 替身: $suspicious_sshd\n"
        log_error "SSH 后门: 发现替身程序 $suspicious_sshd"
        ((backdoor_found++))
    fi

    # 6. SSH wrapper 后门（/usr/sbin/sshd 被替换）
    backdoor_output+="\n[6] SSH wrapper 后门检测\n"
    if command -v file &>/dev/null; then
        local sshd_type=$(file /usr/sbin/sshd 2>/dev/null || echo "")
        if echo "$sshd_type" | grep -qvE "ELF|executable"; then
            backdoor_output+="  ⚠️ /usr/sbin/sshd 疑似被 wrapper 脚本替换\n"
            log_error "SSH wrapper 后门: /usr/sbin/sshd 被篡改"
            ((backdoor_found++))
        fi
    fi

    # 7. setuid 后门（异常 SUID 文件）
    backdoor_output+="\n[7] setuid 后门检测\n"
    local suspicious_suid=$(find / ! -path '/proc/*' -type f -perm -4000 2>/dev/null | \
        grep -vE "pam_timestamp_check|unix_chkpwd|ping|mount|su|pt_chown|ssh-keysign|at|passwd|chsh|crontab|chfn|usernetctl|staprun|newgrp|chage|dhcp|helper|pkexec|top|Xorg|nvidia-modprobe|quota|login" | \
        grep -E "/tmp/|/var/tmp/|/dev/shm/" || echo "")
    if [[ -n "$suspicious_suid" ]]; then
        backdoor_output+="  ⚠️ 发现可疑 SUID 文件:\n$suspicious_suid\n"
        log_error "setuid 后门: $suspicious_suid"
        ((backdoor_found++))
    fi

    # 8. 启动项后门检测
    backdoor_output+="\n[8] 启动项后门检测\n"
    local init_paths="/etc/init.d/ /etc/rc.d/ /etc/rc.local /usr/local/etc/rc.d/"
    for init_path in $init_paths; do
        [[ ! -e "$init_path" ]] && continue
        while read -r f; do
            [[ -f "$f" ]] || continue
            local content=$(cat "$f" 2>/dev/null || echo "")
            if echo "$content" | grep -qiE "wget.*境外|curl.*境外|nc\s|境外ip|/dev/tcp|base64"; then
                backdoor_output+="  ⚠️ 可疑启动项: $f\n"
                log_warn "启动项后门: $f"
                ((backdoor_found++))
            fi
        done < <(find "$init_path" -type f 2>/dev/null)
    done

    # 9. alias 后门
    backdoor_output+="\n[9] Alias 后门检测\n"
    local alias_output=$(alias 2>/dev/null | grep -v "^#" || echo "")
    if echo "$alias_output" | grep -qiE "rm\s+-rf|curl.*境外|wget.*境外"; then
        backdoor_output+="  ⚠️ 发现可疑 alias: $alias_output\n"
        log_warn "Alias 后门: $alias_output"
        ((backdoor_found++))
    fi

    backdoor_output+="\n=== 后门检测完成，发现 $backdoor_found 项异常 ===\n"

    log_info "后门检测完成: 发现 $backdoor_found 项异常"

    local alert_cls=""
    [[ "$backdoor_found" -gt 0 ]] && alert_cls="alert-danger" || alert_cls="alert-info"

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128678;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card $([ "$backdoor_found" -gt 0 ] && echo red || echo green)">
        <div class="metric-label">后门检测结果</div>
        <div class="metric-value">$([ "$backdoor_found" -gt 0 ] && echo "⚠️ $backdoor_found 项异常" || echo "✅ 未发现")</div>
      </div>
    </div>
    <pre>$(html_escape "$backdoor_output")</pre>
EOF

    [[ "$backdoor_found" -gt 0 ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-danger">
      <strong>&#9888; 发现后门痕迹，请立即进行人工排查！</strong>
      <p>检测到 $backdoor_found 项可疑后门/入侵痕迹，建议：</p>
      <ol>
        <li>检查上述可疑文件的完整路径和内容</li>
        <li>查看相关日志确认入侵时间线</li>
        <li>隔离主机并进行深度取证</li>
        <li>联系安全团队进行应急响应</li>
      </ol>
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF

    json_add "backdoor" "{\"found_count\": $backdoor_found}"
}