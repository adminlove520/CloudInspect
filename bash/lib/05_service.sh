#!/bin/bash
###############################################################################
# 模块5: 服务状态 (service)
###############################################################################

collect_service() {
    local section_id="service" section_title="服务状态"
    log_step "检查服务状态..."
    append_section_header "$section_id" "$section_title"

    local services="sshd crond firewalld ufw docker podman containerd nginx httpd mysqld mariadb postgresql redis mongod elasticsearch php-fpm tomcat kubelet zabbix-agent prometheus grafana-server haproxy keepalived postfix smbd vsftpd named ntp chronyd snmpd rsyncd rpcbind autofs"

    local running=0 stopped=0 notfound=0
    local service_rows=""
    local service_json_parts=""

    for svc in $services; do
        local status enabled cls
        status=$(service_status "$svc")
        enabled=$(service_enabled "$svc")

        case "$status" in
            active)   cls="green"; ((running++)) || true ;;
            inactive) cls="orange"; ((stopped++)) || true ;;
            *)        cls="red";   ((notfound++)) || true ;;
        esac

        local badge_cls
        case "$status" in
            active)   badge_cls="ok" ;;
            inactive) badge_cls="warning" ;;
            *)        badge_cls="critical" ;;
        esac

        service_rows+="<tr>"
        service_rows+="<td>$(html_escape "$svc")</td>"
        service_rows+="<td class=\"$cls\">$(html_escape "$status")</td>"
        service_rows+="<td>$(html_escape "$enabled")</td>"
        service_rows+="<td><span class=\"badge $badge_cls\">$(html_escape "$status")</span></td>"
        service_rows+="</tr>"

        service_json_parts+="\"$svc\":{\"status\":\"$(echo "$status" | sed 's/"/\\"/g')\",\"enabled\":\"$(echo "$enabled" | sed 's/"/\\"/g')\"},"
    done

    service_json_parts="${service_json_parts%,}"
    json_add "service" "{\"running\":${running},\"stopped\":${stopped},\"notfound\":${notfound},\"services\":{${service_json_parts}}}"

    log_info "服务状态: 运行中=$running 已停止=$stopped 未找到=$notfound"

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#9881;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card green">
        <div class="metric-label">运行中</div>
        <div class="metric-value green">$running</div>
      </div>
      <div class="metric-card orange">
        <div class="metric-label">已停止</div>
        <div class="metric-value orange">$stopped</div>
      </div>
      <div class="metric-card red">
        <div class="metric-label">未找到</div>
        <div class="metric-value red">$notfound</div>
      </div>
    </div>
    <table class="info-table">
      <tr><th>服务名</th><th>状态</th><th>开机启用</th><th>状态</th></tr>
      ${service_rows}
    </table>
  </div>
</div>
EOF
}