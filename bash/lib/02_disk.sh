#!/bin/bash
###############################################################################
# 模块2: 磁盘检测 (disk)
###############################################################################

collect_disk() {
    local section_id="disk" section_title="磁盘状态"
    log_step "检查磁盘使用情况..."
    append_section_header "$section_id" "$section_title"

    # 收集数据
    local disk_json_parts=""
    local disk_items_html=""
    local disk_issues=0

    # 遍历所有挂载点
    df -h 2>/dev/null | grep '^/dev/' | while read -r line; do
        local fs size used avail use mount
        fs=$(echo "$line" | awk '{print $1}')
        size=$(echo "$line" | awk '{print $2}')
        used=$(echo "$line" | awk '{print $3}')
        avail=$(echo "$line" | awk '{print $4}')
        use=$(echo "$line" | awk '{print $5}' | tr -d '%')
        mount=$(echo "$line" | awk '{print $6}')

        [[ -z "$use" || -z "$mount" ]] && continue

        local cls color_cls badge_label
        if [[ "$use" =~ ^[0-9]+$ ]]; then
            if (( use >= DISK_WARN + CRIT_OFFSET )); then
                cls="red"; color_cls="critical"; badge_label="严重"
                log_error "磁盘使用率严重: ${mount} ${use}%"
                ((disk_issues++)) || true
            elif (( use >= DISK_WARN )); then
                cls="orange"; color_cls="warning"; badge_label="警告"
                log_warn "磁盘使用率告警: ${mount} ${use}%"
                ((disk_issues++)) || true
            else
                cls="green"; color_cls="ok"; badge_label="正常"
            fi
        else
            cls="green"; color_cls="ok"; badge_label="正常"
        fi

        local pct_bar=$((use * 2))
        [[ "$pct_bar" -gt 100 ]] && pct_bar=100

        disk_items_html+="<div class=\"disk-item ${cls}\">"
        disk_items_html+="<div class=\"disk-info\"><span class=\"disk-mount\">$(html_escape "$mount")</span>"
        disk_items_html+="<span class=\"disk-fs\">$(html_escape "$fs")</span></div>"
        disk_items_html+="<div class=\"disk-bar-wrap\"><div class=\"disk-bar ${cls}\" style=\"width:${pct_bar}%\"></div></div>"
        disk_items_html+="<div class=\"disk-stats\">"
        disk_items_html+="<span>$(html_escape "$used") / $(html_escape "$size") (${use}%)</span>"
        disk_items_html+="<span class=\"badge ${color_cls}\">${badge_label}</span>"
        disk_items_html+="</div></div>"

        # JSON 数据
        disk_json_parts+="\"$(html_escape "$mount")\":{\"fs\":\"$(html_escape "$fs")\",\"size\":\"$(html_escape "$size")\",\"used\":\"$(html_escape "$used")\",\"use_pct\":${use}},"
    done

    # Inode 数据
    local inode_html=""
    df -i 2>/dev/null | grep '^/dev/' | while read -r line; do
        local fs iused iavail iuse mount
        fs=$(echo "$line" | awk '{print $1}')
        iused=$(echo "$line" | awk '{print $3}')
        iavail=$(echo "$line" | awk '{print $4}')
        iuse=$(echo "$line" | awk '{print $5}' | tr -d '%')
        mount=$(echo "$line" | awk '{print $6}')
        [[ -z "$iuse" ]] && continue

        local cls="green"
        [[ "$iuse" =~ ^[0-9]+$ ]] && (( iuse >= INODE_WARN )) && cls="orange"
        [[ "$iuse" =~ ^[0-9]+$ ]] && (( iuse >= INODE_WARN + CRIT_OFFSET )) && cls="red"

        inode_html+="<div class=\"disk-item ${cls}\">"
        inode_html+="<div class=\"disk-info\"><span class=\"disk-mount\">$(html_escape "$mount")</span>"
        inode_html+="<span class=\"disk-fs\">$(html_escape "$fs")</span></div>"
        inode_html+="<div class=\"disk-stats\">"
        inode_html+="<span>已用: $(html_escape "$iused") | 可用: $(html_escape "$iavail")</span>"
        inode_html+="<span class=\"badge ${cls}\">${iuse}%</span>"
        inode_html+="</div></div>"
    done

    # 大文件扫描（仅在非 quick 模式）
    local large_files_html=""
    if [[ "$MODE" != "quick" ]]; then
        log_info "扫描大文件（>100M）..."
        local large_output
        large_output=$(find /var /home /opt /usr/local -type f -size +100M 2>/dev/null | \
            xargs ls -lhS 2>/dev/null | head -10 || echo "未发现大于100M的文件")
        if [[ -n "$large_output" && "$large_output" != "未发现大于100M的文件" ]]; then
            large_files_html="<h3>大文件 (&gt;100M)</h3><pre>$(html_escape "$large_output")</pre>"
        fi
    fi

    # 构建最终 JSON
    disk_json_parts="${disk_json_parts%,}"
    local final_json="{\"disk_issues\":${disk_issues},\"partitions\":{${disk_json_parts}}}"

    # 输出 HTML
    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="disk">
  <div class="card-header">
    <h2><span class="icon">&#128190;</span> 磁盘状态</h2>
  </div>
  <div class="card-body">
    <h3>挂载点使用情况</h3>
    ${disk_items_html}
    <h3>Inode 使用情况</h3>
    ${inode_html}
    ${large_files_html}
  </div>
</div>
EOF

    json_add "disk" "$final_json"
}