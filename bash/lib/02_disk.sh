#!/bin/bash
###############################################################################
# 模块2: 磁盘检测 (disk)
###############################################################################

collect_disk() {
    local section_id="disk" section_title="磁盘状态"
    log_step "检查磁盘使用情况..."
    append_section_header "$section_id" "$section_title"

    local disk_output inode_output io_output large_files_output

    # 磁盘使用率
    disk_output=$(df -h 2>/dev/null | grep -v "tmpfs\|devtmpfs\|loop" | awk 'NR>1 || /^\/dev/' || echo "无数据")

    # 检查告警
    while read -r line; do
        [[ -z "$line" ]] && continue
        local usage=$(echo "$line" | awk '{print $5}' | tr -d '%')
        local mount=$(echo "$line" | awk '{print $6}')
        [[ -z "$usage" || -z "$mount" ]] && continue
        if [[ "$usage" =~ ^[0-9]+$ ]]; then
            if (( usage >= DISK_WARN + CRIT_OFFSET )); then
                log_error "磁盘使用率严重: ${mount} ${usage}%"
            elif (( usage >= DISK_WARN )); then
                log_warn "磁盘使用率告警: ${mount} ${usage}%"
            fi
        fi
    done <<< "$(df -h 2>/dev/null | grep '^/dev/')"

    # Inode 使用率
    inode_output=$(df -i 2>/dev/null | grep '^/dev/' | awk '{print $6, $5}' | while read -r mount usage; do
        usage=${usage%\%}
        local cls=$(get_color_class "$usage" "$INODE_WARN")
        echo "  $mount: $usage% $cls"
    done || echo "无数据")

    # 大文件扫描（仅在非 fast 模式）
    if [[ "$MODE" != "quick" ]]; then
        log_info "扫描大文件（>100M）..."
        large_files_output=$(find /var /home /opt /usr/local -type f -size +100M 2>/dev/null | \
            xargs ls -lhS 2>/dev/null | head -10 || echo "未发现大文件")
    fi

    # 磁盘 I/O
    if command -v iostat &>/dev/null; then
        io_output=$(iostat -x 1 2 2>/dev/null | tail -20 || echo "iostat 不可用")
    elif [[ -r /proc/diskstats ]]; then
        io_output=$(cat /proc/diskstats 2>/dev/null | head -20 || echo "无数据")
    else
        io_output="无法获取 I/O 信息"
    fi

    # 输出 HTML
    cat >> "$REPORT_FILE" <<'EOF'
<div class="card" id="disk">
  <div class="card-header">
    <h2><span class="icon">&#128190;</span> 磁盘状态</h2>
  </div>
  <div class="card-body">
    <h3>挂载点使用情况</h3>
EOF

    df -h 2>/dev/null | grep '^/dev/' | while read -r line; do
        local fs size used avail use mount
        fs=$(echo "$line" | awk '{print $1}')
        size=$(echo "$line" | awk '{print $2}')
        used=$(echo "$line" | awk '{print $3}')
        avail=$(echo "$line" | awk '{print $4}')
        use=$(echo "$line" | awk '{print $5}' | tr -d '%')
        mount=$(echo "$line" | awk '{print $6}')

        local cls=$(get_color_class "$use" "$DISK_WARN")
        local pct_bar=$((use * 2))

        cat >> "$REPORT_FILE" <<DSCEOF
    <div class="disk-item ${cls}">
      <div class="disk-info">
        <span class="disk-mount">${mount}</span>
        <span class="disk-fs">${fs}</span>
      </div>
      <div class="disk-bar-wrap">
        <div class="disk-bar ${cls}" style="width: ${pct_bar}%"></div>
      </div>
      <div class="disk-stats">
        <span>${used} / ${size} (${use}%)</span>
        <span class="badge ${cls}">$([ "$use" -ge "$((DISK_WARN + CRIT_OFFSET))" ] && echo "严重" || ([ "$use" -ge "$DISK_WARN" ] && echo "警告" || echo "正常"))</span>
      </div>
    </div>
DSCEOF
    done

    cat >> "$REPORT_FILE" <<'EOF'
    <h3>Inode 使用情况</h3>
EOF
    df -i 2>/dev/null | grep '^/dev/' | while read -r line; do
        local fs iused iavail iuse mount
        fs=$(echo "$line" | awk '{print $1}')
        iused=$(echo "$line" | awk '{print $3}')
        iavail=$(echo "$line" | awk '{print $4}')
        iuse=$(echo "$line" | awk '{print $5}' | tr -d '%')
        mount=$(echo "$line" | awk '{print $6}')
        local cls=$(get_color_class "$iuse" "$INODE_WARN")
        cat >> "$REPORT_FILE" <<INODEOF
    <div class="disk-item ${cls}">
      <div class="disk-info"><span class="disk-mount">${mount}</span><span class="disk-fs">${fs}</span></div>
      <div class="disk-stats"><span>已用: ${iused} | 可用: ${iavail}</span><span class="badge ${cls}">${iuse}%</span></div>
    </div>
INODEOF
    done

    # 大文件
    if [[ -n "$large_files_output" && "$large_files_output" != "未发现大文件" ]]; then
        cat >> "$REPORT_FILE" <<EOF
    <h3>大文件 (>100M)</h3>
    $(pre_block "$large_files_output" "未发现大于100M的文件")
EOF
    fi

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF

    # JSON
    json_add "disk" "{}"
}