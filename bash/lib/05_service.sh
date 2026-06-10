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
    local service_output=""

    for svc in $services; do
        local status
        status=$(service_status "$svc")
        local enabled
        enabled=$(service_enabled "$svc")

        local cls
        case "$status" in
            active)   cls="green"; ((running++)) ;;
            inactive) cls="orange"; ((stopped++)) ;;
            *)       cls="red";   ((notfound++)) ;;
        esac

        service_output+="  $svc | 状态: $status | 启用: $enabled\n"
    done

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
        <div class="metric-value">$running</div>
      </div>
      <div class="metric-card orange">
        <div class="metric-label">已停止</div>
        <div class="metric-value">$stopped</div>
      </div>
      <div class="metric-card red">
        <div class="metric-label">未找到</div>
        <div class="metric-value">$notfound</div>
      </div>
    </div>
    <pre>$(html_escape "$service_output")</pre>
  </div>
</div>
EOF

    json_add "service" "{\"running\": $running, \"stopped\": $stopped}"
}