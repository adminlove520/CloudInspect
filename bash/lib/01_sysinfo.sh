#!/bin/bash
###############################################################################
# 模块1: 系统信息采集 (sysinfo)
###############################################################################

collect_sysinfo() {
    local section_id="sysinfo" section_title="系统信息"
    log_step "采集系统基本信息..."
    append_section_header "$section_id" "$section_title"

    local hostname hostname_fqdn ip_addr mac_addr os_version kernel arch cpu_model cpu_cores cpu_freq
    local total_mem swap_mem uptime_days selinux_status firewall_status virt_info

    # 主机名
    hostname=$(hostname 2>/dev/null || echo "未知")
    hostname_fqdn=$(hostname -f 2>/dev/null || hostname 2>/dev/null || echo "未知")

    # IP 地址（优先内网）
    ip_addr=$(ip -4 addr show 2>/dev/null | grep -oP 'inet \K[\d.]+' | grep -v '^127\.' | head -1 || \
              hostname -i 2>/dev/null || echo "未知")

    # MAC 地址
    mac_addr=$(ip link show 2>/dev/null | grep -oP 'link/ether \K[0-9a-f:]+' | head -1 || \
               cat /sys/class/net/$(ip route show default 2>/dev/null | awk '{print $5}' | head -1)/address 2>/dev/null || echo "未知")

    # 操作系统
    os_version="$OS_PRETTY"

    # 内核版本
    kernel=$(uname -r 2>/dev/null || echo "未知")

    # 架构
    arch=$(uname -m 2>/dev/null || echo "未知")

    # CPU 信息
    cpu_model=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^ *//' || \
                grep -m1 "Model" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^ *//' || echo "未知")
    cpu_cores=$(nproc 2>/dev/null || grep -c "^processor" /proc/cpuinfo 2>/dev/null || echo "未知")
    cpu_freq=$(grep -m1 "cpu MHz" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed 's/^ *//' || echo "未知")

    # 内存
    local mem_total mem_available swap_total swap_free
    mem_total=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")
    mem_available=$(grep MemAvailable /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")
    swap_total=$(grep SwapTotal /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")
    swap_free=$(grep SwapFree /proc/meminfo 2>/dev/null | awk '{print $2}' || echo "0")

    local mem_used_pct swap_used_pct
    if (( mem_total > 0 )); then
        mem_used_pct=$(( ( (mem_total - mem_available) * 100 ) / mem_total ))
    else
        mem_used_pct=0
    fi
    if (( swap_total > 0 )); then
        swap_used_pct=$(( ( (swap_total - swap_free) * 100 ) / swap_total ))
    else
        swap_used_pct=0
    fi

    total_mem=$(human_bytes $((mem_total * 1024)))
    swap_mem=$(human_bytes $((swap_total * 1024)))

    # 运行时间
    uptime_days=$(uptime -s 2>/dev/null || echo "未知")

    # SELinux
    if command -v getenforce &>/dev/null; then
        selinux_status=$(getenforce 2>/dev/null || echo "未知")
    elif [[ -f /sys/fs/selinux/enforce ]]; then
        selinux_status="启用"
    else
        selinux_status="未安装"
    fi

    # 防火墙
    if has_systemd; then
        if systemctl is-active firewalld &>/dev/null; then
            firewall_status="firewalld (active)"
        elif systemctl is-active ufw &>/dev/null; then
            firewall_status="UFW (active)"
        elif systemctl is-active iptables &>/dev/null; then
            firewall_status="iptables (active)"
        else
            firewall_status="未运行"
        fi
    else
        if command -v iptables &>/dev/null && iptables -L -n &>/dev/null; then
            firewall_status="iptables (active)"
        else
            firewall_status="未知"
        fi
    fi

    # 虚拟化
    if command -v systemd-detect-virt &>/dev/null; then
        virt_info=$(systemd-detect-virt 2>/dev/null || echo "物理机")
    elif [[ -f /sys/class/dmi/id/product_name ]]; then
        local prod=$(cat /sys/class/dmi/id/product_name 2>/dev/null | tr '[:upper:]' '[:lower:]')
        case "$prod" in
            *vmware*) virt_info="VMware" ;;
            *kvm*) virt_info="KVM" ;;
            *qemu*) virt_info="QEMU" ;;
            *virtualbox*) virt_info="VirtualBox" ;;
            *hyperv*) virt_info="Hyper-V" ;;
            *xen*) virt_info="Xen" ;;
            *) virt_info="$prod" ;;
        esac
    else
        virt_info="未知"
    fi

    # CPU 使用率（更健壮的计算）
    local cpu_idle
    cpu_idle=$(top -bn2 -d 1 2>/dev/null | tail -1 | grep -oP 'Cpu.*?\K[0-9.]+(?=.*id)' || \
               top -bn1 2>/dev/null | grep "Cpu(s)" | awk '{print $8}' | tr -d 'id,%' || echo "0")
    [[ -z "$cpu_idle" || "$cpu_idle" == "0" ]] && cpu_idle=$(awk '/^cpu / {print $5}' /proc/stat 2>/dev/null && \
        sleep 0.5 && awk '/^cpu / {print ($5 - prev)/1 * 100; exit}' prev=$(awk '/^cpu / {print $5}' /proc/stat) /proc/stat 2>/dev/null || echo "0")
    cpu_usage=$(echo "100 - $cpu_idle" | bc 2>/dev/null || echo "0")
    cpu_usage=${cpu_usage%.*}
    [[ -z "$cpu_usage" || ! "$cpu_usage" =~ ^[0-9]+$ ]] && cpu_usage=0

    # 负载
    local load_1 load_5 load_15
    if [[ -r /proc/loadavg ]]; then
        read -r load_1 load_5 load_15 _ < /proc/loadavg
    else
        load_1=$(uptime | grep -oP 'load average: \K[0-9.]+' || echo "0")
        load_5=$(uptime | grep -oP '[0-9.]+(?=, [0-9.]+, [0-9.]+$)' || echo "0")
        load_15=$(uptime | grep -oP '[0-9.]+(?=$)' || echo "0")
    fi
    [[ -z "$load_1" ]] && load_1=0
    [[ -z "$load_5" ]] && load_5=0
    [[ -z "$load_15" ]] && load_15=0

    # 告警检查
    local cpu_class mem_class
    cpu_class=$(get_color_class "$cpu_usage" "$CPU_WARN")
    mem_class=$(get_color_class "$mem_used_pct" "$MEM_WARN")

    (( cpu_usage >= CPU_WARN )) && log_warn "CPU 使用率较高: ${cpu_usage}%"
    (( mem_used_pct >= MEM_WARN )) && log_warn "内存使用率较高: ${mem_used_pct}%"

    # 输出 HTML
    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128737;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card ${cpu_class}">
        <div class="metric-label">CPU 使用率</div>
        <div class="metric-value">${cpu_usage}%</div>
        <div class="metric-sub">${cpu_model}</div>
      </div>
      <div class="metric-card ${mem_class}">
        <div class="metric-label">内存使用率</div>
        <div class="metric-value">${mem_used_pct}%</div>
        <div class="metric-sub">总计: ${total_mem}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">负载 (1/5/15)</div>
        <div class="metric-value">${load_1} / ${load_5} / ${load_15}</div>
        <div class="metric-sub">核心数: ${cpu_cores}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">运行时间</div>
        <div class="metric-value">${uptime_days}</div>
        <div class="metric-sub">${kernel}</div>
      </div>
    </div>

    <table class="info-table">
      <tr><th colspan="2">基本信息</th></tr>
      <tr><td>主机名</td><td><code>${hostname}</code></td></tr>
      <tr><td>完整域名</td><td>${hostname_fqdn}</td></tr>
      <tr><td>IP 地址</td><td><code>${ip_addr}</code></td></tr>
      <tr><td>MAC 地址</td><td><code>${mac_addr}</code></td></tr>
      <tr><td>操作系统</td><td>${os_version}</td></tr>
      <tr><td>内核版本</td><td><code>${kernel}</code></td></tr>
      <tr><td>系统架构</td><td>${arch}</td></tr>
      <tr><td>CPU 型号</td><td>${cpu_model}</td></tr>
      <tr><td>CPU 核心数</td><td>${cpu_cores} 核</td></tr>
      <tr><td>总内存</td><td>${total_mem}</td></tr>
      <tr><td>Swap</td><td>${swap_mem} (使用率: ${swap_used_pct}%)</td></tr>
      <tr><td>SELinux</td><td>${selinux_status}</td></tr>
      <tr><td>防火墙</td><td>${firewall_status}</td></tr>
      <tr><td>虚拟化</td><td>${virt_info}</td></tr>
    </table>
  </div>
</div>
EOF

    # JSON 数据收集
    json_add "sysinfo" "{
"hostname": \"$(echo "$hostname" | sed 's/"/\\"/g')\",
"ip\": \"$(echo "$ip_addr" | sed 's/"/\\"/g')\",
"os\": \"$(echo "$os_version" | sed 's/"/\\"/g')\",
"kernel\": \"$(echo "$kernel" | sed 's/"/\\"/g')\",
"cpu_model\": \"$(echo "$cpu_model" | sed 's/"/\\"/g')\",
"cpu_cores\": $cpu_cores,
"cpu_usage_pct\": $cpu_usage,
"mem_total_bytes\": $((mem_total * 1024)),
"mem_used_pct\": $mem_used_pct,
"swap_total_bytes\": $((swap_total * 1024)),
"swap_used_pct\": $swap_used_pct,
"load_1\": $load_1,
"load_5\": $load_5,
"load_15\": $load_15,
"uptime\": \"$(echo "$uptime_days" | sed 's/"/\\"/g')\",
"selinux\": \"$(echo "$selinux_status" | sed 's/"/\\"/g')\",
"firewall\": \"$(echo "$firewall_status" | sed 's/"/\\"/g')\",
"virt\": \"$(echo "$virt_info" | sed 's/"/\\"/g')\"
}"
}