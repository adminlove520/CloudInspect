#!/bin/bash
###############################################################################
# 模块3: 网络状态 (network)
###############################################################################

collect_network() {
    local section_id="network" section_title="网络状态"
    log_step "检查网络状态..."
    append_section_header "$section_id" "$section_title"

    # 网卡信息
    local nic_parts=""
    ip -4 addr show 2>/dev/null | grep -A2 "^[0-9]" | grep "inet " | while read -r line; do
        local iface ip_addr mac speed rx tx
        iface=$(echo "$line" | awk -F': ' '{print $2}')
        ip_addr=$(echo "$line" | awk '{print $2}')
        mac=$(cat /sys/class/net/"$iface"/address 2>/dev/null || echo "未知")
        speed=$(cat /sys/class/net/"$iface"/speed 2>/dev/null || echo "未知")
        rx=$(cat /sys/class/net/"$iface"/statistics/rx_bytes 2>/dev/null && \
            echo "RX: $(human_bytes $(cat /sys/class/net/"$iface"/statistics/rx_bytes 2>/dev/null))" || echo "")
        tx=$(cat /sys/class/net/"$iface"/statistics/tx_bytes 2>/dev/null && \
            echo "TX: $(human_bytes $(cat /sys/class/net/"$iface"/statistics/tx_bytes 2>/dev/null))" || echo "")
        nic_parts+="  ${iface} | ${ip_addr} | MAC: ${mac} | Speed: ${speed}Mbps | ${rx} | ${tx}\n"
    done || nic_parts="无法获取网卡信息\n"

    # TCP 连接统计
    local tcp_stats
    tcp_stats=$(ss -tan 2>/dev/null | awk 'NR>1 {state[$1]++} END {for(s in state) print s": "state[s]}' | sort || \
                netstat -tan 2>/dev/null | awk 'NR>1 {state[$6]++} END {for(s in state) print s": "state[s]}' | sort || echo "无法获取")

    # CLOSE_WAIT 异常检测
    local close_wait
    close_wait=$(ss -tan 2>/dev/null | grep -c CLOSE-WAIT || netstat -an 2>/dev/null | grep -c CLOSE-WAIT || echo "0")
    [[ "$close_wait" =~ ^[0-9]+$ ]] && (( close_wait > CONN_CLOSE_WAIT_THRESHOLD )) && {
        log_warn "CLOSE_WAIT 连接过多: ${close_wait}"
    }

    # 监听端口
    local listen_ports
    listen_ports=$(ss -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | sort -t: -k2 -n | head -30 || \
                    netstat -tlnp 2>/dev/null | awk 'NR>1 {print $4}' | sort -t: -k2 -n | head -30 || echo "无法获取")

    # 混杂模式检测
    local promisc_warn=""
    ip link show 2>/dev/null | grep -i "PROMISC" | awk -F: '{print $2}' | tr -d ' ' | while read -r iface; do
        [[ -n "$iface" ]] && {
            log_warn "网卡 $iface 处于混杂模式!"
            promisc_warn+="混杂模式: $iface\n"
        }
    done || true

    # 路由表
    local route_info
    route_info=$(ip route 2>/dev/null | head -10 || route -n 2>/dev/null | head -10 || echo "无法获取路由表")

    # DNS
    local dns_info="无"
    if [[ -f /etc/resolv.conf ]]; then
        dns_info=$(grep nameserver /etc/resolv.conf 2>/dev/null | awk '{print $2}' | tr '\n' ', ' || echo "无")
    fi

    # 构建 JSON
    local close_wait_int=0
    [[ "$close_wait" =~ ^[0-9]+$ ]] && close_wait_int=$close_wait
    json_add "network" "{\"close_wait\":${close_wait_int},\"promisc_warn\":\"$promisc_warn\",\"dns\":\"$dns_info\"}"

    # 输出 HTML
    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#127760;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <h3>网卡信息</h3>
    <pre>$(html_escape "${nic_parts:-无数据}")</pre>
    <h3>TCP 连接统计</h3>
    <pre>$(html_escape "$tcp_stats")</pre>
    <h3>监听端口 (TOP 30)</h3>
    <pre>$(html_escape "${listen_ports:-无法获取}")</pre>
    <h3>路由表</h3>
    <pre>$(html_escape "${route_info:-无法获取}")</pre>
    <h3>DNS 配置</h3>
    <p>Nameservers: $(html_escape "$dns_info")</p>
EOF

    [[ -n "$promisc_warn" ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-warning">
      <strong>&#9888; 网卡混杂模式警告</strong>
      <pre>$(html_escape "$promisc_warn")</pre>
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF
}