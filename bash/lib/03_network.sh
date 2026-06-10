#!/bin/bash
###############################################################################
# 模块3: 网络状态 (network)
###############################################################################

collect_network() {
    local section_id="network" section_title="网络状态"
    log_step "检查网络状态..."
    append_section_header "$section_id" "$section_title"

    # 网卡信息
    local nic_info=""
    nic_info=$(ip -4 addr show 2>/dev/null | grep -A2 "^[0-9]" | grep -E "^[0-9]|inet " | \
        sed 's/^[0-9]*: //' | sed 's/: <UP,/:/' | grep "inet " | awk '{print $2}' | while read -r ip; do
            local iface=$(ip -4 addr show 2>/dev/null | grep -B1 "inet $ip" | head -1 | sed 's/^[0-9]*: //' | sed 's/:.*//')
            local mac=$(cat /sys/class/net/"$iface"/address 2>/dev/null || echo "未知")
            local speed=$(cat /sys/class/net/"$iface"/speed 2>/dev/null || echo "未知")
            local rx=$(cat /sys/class/net/"$iface"/statistics/rx_bytes 2>/dev/null && \
                      echo "RX: $(human_bytes $(cat /sys/class/net/"$iface"/statistics/rx_bytes 2>/dev/null))" || echo "")
            local tx=$(cat /sys/class/net/"$iface"/statistics/tx_bytes 2>/dev/null && \
                      echo "TX: $(human_bytes $(cat /sys/class/net/"$iface"/statistics/tx_bytes 2>/dev/null))" || echo "")
            echo "$iface | $ip | MAC: $mac | Speed: ${speed}Mbps | $rx | $tx"
        done || echo "无法获取网卡信息")

    # TCP 连接统计
    local tcp_stats=""
    tcp_stats=$(ss -tan 2>/dev/null | awk 'NR>1 {state[$1]++} END {for(s in state) print s": "state[s]}' | sort || \
                netstat -tan 2>/dev/null | awk 'NR>1 {state[$6]++} END {for(s in state) print s": "state[s]}' | sort || echo "无法获取")

    # 检查 CLOSE_WAIT 异常
    local close_wait=$(ss -tan 2>/dev/null | grep CLOSE-WAIT | wc -l || netstat -an 2>/dev/null | grep CLOSE-WAIT | wc -l || echo "0")
    if [[ "$close_wait" =~ ^[0-9]+$ ]] && (( close_wait > CONN_CLOSE_WAIT_THRESHOLD )); then
        log_warn "CLOSE_WAIT 连接过多: ${close_wait}"
    fi

    # 监听端口
    local listen_ports=""
    listen_ports=$(ss -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | sort -t: -k2 -n | head -30 || \
                   netstat -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | sort -t: -k2 -n | head -30 || echo "无法获取")

    # 混杂模式检测
    local promisc_found=""
    promisc_found=$(ip link show 2>/dev/null | grep -i "PROMISC" | awk -F: '{print $2}' | tr -d ' ' | while read -r iface; do
        log_warn "网卡 $iface 处于混杂模式!"
        echo "混杂模式: $iface"
    done || echo "")

    # 路由表
    local route_info=""
    route_info=$(ip route 2>/dev/null || route -n 2>/dev/null || echo "无法获取路由表")

    # DNS
    local dns_info=""
    if [[ -f /etc/resolv.conf ]]; then
        dns_info=$(grep nameserver /etc/resolv.conf 2>/dev/null | awk '{print $2}' | tr '\n' ', ' || echo "无")
    fi

    # 输出 HTML
    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#127760;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <h3>网卡信息</h3>
    $(pre_block "$nic_info" "无法获取网卡信息")
    <h3>TCP 连接统计</h3>
    $(pre_block "$tcp_stats" "无法获取连接统计")
    <h3>监听端口 (TOP 30)</h3>
    $(pre_block "$listen_ports" "无法获取监听端口")
    <h3>路由表</h3>
    $(pre_block "$route_info" "无法获取路由表")
    <h3>DNS 配置</h3>
    <p>Nameservers: $dns_info</p>
EOF

    [[ -n "$promisc_found" ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-warning">
      <strong>&#9888; 网卡混杂模式警告</strong>
      <pre>$(html_escape "$promisc_found")</pre>
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF

    json_add "network" "{}"
}