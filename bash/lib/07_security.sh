#!/bin/bash
###############################################################################
# 模块7: 安全基线 (security)
###############################################################################

collect_security() {
    local section_id="security" section_title="安全基线"
    log_step "检查安全基线..."
    append_section_header "$section_id" "$section_title"

    local ssh_config="/etc/ssh/sshd_config"
    local issues_found=0

    # SSH 配置检查
    local ssh_permit_root="" ssh_port="" ssh_max_auth=""
    if [[ -f "$ssh_config" ]]; then
        ssh_permit_root=$(grep -i "^PermitRootLogin" "$ssh_config" 2>/dev/null | awk '{print $2}' || echo "未设置")
        ssh_port=$(grep -i "^Port" "$ssh_config" 2>/dev/null | awk '{print $2}' || echo "22")
        ssh_max_auth=$(grep -i "^MaxAuthTries" "$ssh_config" 2>/dev/null | awk '{print $2}' || echo "未设置")

        if [[ "$ssh_permit_root" == "yes" ]]; then
            log_warn "SSH 允许 root 登录: PermitRootLogin=yes"
            ((issues_found++))
        fi
        if [[ "$ssh_port" != "22" ]]; then
            log_info "SSH 使用非标准端口: $ssh_port"
        fi
    fi

    # UID=0 账户（排除 root 和系统账户）
    local uid0_users=""
    uid0_users=$(awk -F: '($3==0){print $1}' /etc/passwd 2>/dev/null | grep -v '^root$' | grep -v '^sync$' | grep -v '^shutdown$' | grep -v '^halt$' || echo "")
    if [[ -n "$uid0_users" ]]; then
        log_warn "发现非 root 的 UID=0 账户: $uid0_users"
        ((issues_found++))
    fi

    # 空密码账户
    local empty_passwd=""
    empty_passwd=$(awk -F: '($2==""){print $1}' /etc/passwd 2>/dev/null | grep -v '^#' || echo "")
    if [[ -n "$empty_passwd" ]]; then
        log_error "发现空密码账户: $empty_passwd"
        ((issues_found++))
    fi

    # 密码即将过期/已过期
    local pass_expiry=""
    pass_expiry=$(for user in $(cut -d: -f1 /etc/passwd); do
        chage -l "$user" 2>/dev/null | grep -E "密码过期|已过期|警告" | head -1 | sed "s/^/$user: /"
    done | head -10 || echo "无数据")

    # SUID 文件
    local suid_files=""
    suid_files=$(find /usr -type f -perm -4000 2>/dev/null | head -20 || echo "无法扫描")
    log_info "SUID 文件数量: $(echo "$suid_files" | wc -l)"

    # 全局可写文件（排除系统目录）
    local world_writable=""
    world_writable=$(find /var /home /opt /usr/local -type f -perm -002 2>/dev/null | head -20 || echo "无")
    if [[ -n "$world_writable" && "$world_writable" != "无" ]]; then
        log_warn "发现全局可写文件: $(echo "$world_writable" | wc -l) 个"
        ((issues_found++))
    fi

    # 最近登录失败
    local failed_logins=""
    failed_logins=$(lastb 2>/dev/null | head -10 || echo "无法读取登录失败记录")

    # 最近成功登录
    local last_logins=""
    last_logins=$(last 2>/dev/null | head -10 || echo "无法读取")

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128737;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <h3>SSH 配置</h3>
    <table class="info-table">
      <tr><td>PermitRootLogin</td><td class="$([ "$ssh_permit_root" == "yes" ] && echo "red-text" || echo "green-text")">$ssh_permit_root</td></tr>
      <tr><td>Port</td><td>$ssh_port</td></tr>
      <tr><td>MaxAuthTries</td><td>$ssh_max_auth</td></tr>
    </table>

    <h3>账户安全</h3>
    <table class="info-table">
      <tr><th>检查项</th><th>结果</th></tr>
      <tr><td>UID=0 非 root 账户</td><td class="$([ -n "$uid0_users" ] && echo "red-text" || echo "green-text")">${uid0_users:-"无"}</td></tr>
      <tr><td>空密码账户</td><td class="$([ -n "$empty_passwd" ] && echo "red-text" || echo "green-text")">${empty_passwd:-"无"}</td></tr>
    </table>

    <h3>最近登录记录（成功）</h3>
    <pre>$(html_escape "$last_logins")</pre>

    <h3>最近登录记录（失败）</h3>
    <pre>$(html_escape "$failed_logins")</pre>

    <h3>SUID 文件 (TOP 20)</h3>
    <pre>$(html_escape "$suid_files")</pre>

    <h3>全局可写文件 (TOP 20)</h3>
    <pre>$(html_escape "$world_writable")</pre>
  </div>
</div>
EOF

    json_add "security" "{\"issues_found\": $issues_found, \"uid0_users\": \"$(echo "$uid0_users" | sed 's/"/\\"/g')\"}"
}