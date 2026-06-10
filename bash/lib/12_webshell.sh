#!/bin/bash
###############################################################################
# 模块12: Webshell 检测 (webshell) — 参考 GScan 设计
###############################################################################

collect_webshell() {
    local section_id="webshell" section_title="Webshell 检测"
    log_step "扫描 Webshell..."

    # Webshell 仅在 emergency/full 模式
    if [[ "$MODE" == "quick" || "$MODE" == "routine" ]]; then
        log_info "Routine/Quick 模式跳过 Webshell 检测（使用 emergency 模式启用）"
        append_section_header "$section_id" "$section_title"
        cat >> "$REPORT_FILE" <<'EOF'
<div class="card" id="webshell">
  <div class="card-header">
    <h2><span class="icon">&#128275;</span> Webshell 检测</h2>
  </div>
  <div class="card-body">
    <p class="text-muted">当前模式未启用 Webshell 深度扫描。使用 <code>--mode emergency</code> 或 <code>--mode full</code> 启用。</p>
  </div>
</div>
EOF
        json_add "webshell" "{\"mode\": \"skipped\"}"
        return 0
    fi

    append_section_header "$section_id" "$section_title"

    local webshell_found=0
    local webshell_output="=== Webshell 检测开始 ===\n"

    # Webshell 检测规则（正则特征）
    local ws_patterns="eval\(|base64_decode|system\(|passthru|exec\(|shell_exec|popen\(|proc_open|preg_replace.*\/e|assert\(|call_user_func|create_function|usort|ini_set.*disable_functions"

    local scan_paths="/var/www /home /opt"
    local scan_exts=".php .jsp .asp .aspx .py .htm .html"

    log_info "开始扫描 Webshell，请耐心等待..."

    for scan_path in $scan_paths; do
        [[ ! -d "$scan_path" ]] && continue
        webshell_output+="\n--- 扫描: $scan_path ---\n"

        for ext in $scan_exts; do
            local matches=$(find "$scan_path" -type f -name "*$ext" 2>/dev/null | head -100)
            [[ -z "$matches" ]] && continue

            while read -r file; do
                [[ ! -f "$file" ]] && continue
                local size=$(stat -c%s "$file" 2>/dev/null || echo "0")
                # 跳过大于 2MB 的文件
                (( size > 2097152 )) && continue

                local content=$(cat "$file" 2>/dev/null | head -100 || echo "")
                if echo "$content" | grep -qiE "$ws_patterns"; then
                    webshell_output+="  ⚠️ 可疑文件: $file (匹配特征)\n"
                    log_warn "Webshell 可疑: $file"
                    ((webshell_found++))
                fi
            done <<< "$matches"
        done
    done

    webshell_output+="\n=== Webshell 检测完成，发现 $webshell_found 项可疑 ===\n"

    log_info "Webshell 检测完成: $webshell_found 项可疑"

    cat >> "$REPORT_FILE" <<EOF
<div class="card" id="$section_id">
  <div class="card-header">
    <h2><span class="icon">&#128275;</span> $section_title</h2>
  </div>
  <div class="card-body">
    <div class="metrics-grid">
      <div class="metric-card $([ "$webshell_found" -gt 0 ] && echo red || echo green)">
        <div class="metric-label">Webshell 检测结果</div>
        <div class="metric-value">$([ "$webshell_found" -gt 0 ] && echo "⚠️ $webshell_found 项可疑" || echo "✅ 未发现")</div>
      </div>
    </div>
    <pre>$(html_escape "$webshell_output")</pre>
EOF

    [[ "$webshell_found" -gt 0 ]] && cat >> "$REPORT_FILE" <<EOF
    <div class="alert alert-danger">
      <strong>&#9888; 发现疑似 Webshell 文件，请立即进行人工确认和清理！</strong>
    </div>
EOF

    cat >> "$REPORT_FILE" <<'EOF'
  </div>
</div>
EOF

    json_add "webshell" "{\"found_count\": $webshell_found}"
}