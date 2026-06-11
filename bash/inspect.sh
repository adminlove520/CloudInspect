#!/bin/bash
###############################################################################
# CloudInspect - 云主机安全巡检工具
# 版本: v1.1
# 功能: 系统巡检 + 入侵检测 + 应急排查
# 支持: Rocky / RHEL / CentOS / EulerOS / Ubuntu / Debian / Kylin / UOS / SUSE / Arch / Alpine / Gentoo 等主流操作系统
###############################################################################

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="${SCRIPT_DIR}/lib"

# ========== 加载核心库 + 报告生成器 ==========
. "${LIB_DIR}/core.sh"
. "${LIB_DIR}/reporter.sh"

# ========== 主流程 ==========
main() {
    init "$@"

    log_info "CloudInspect ${VERSION} 云主机安全巡检开始..."

    # 初始化 HTML 报告
    generate_html_header > "$REPORT_FILE"

    # 创建临时 JSON 数据文件
    mkdir -p /tmp/cloudinspect 2>/dev/null || true
    : > /tmp/cloudinspect_tmp.json 2>/dev/null || true

    # ========== 执行各检测模块 ==========

    . "${LIB_DIR}/01_sysinfo.sh"
    collect_sysinfo

    . "${LIB_DIR}/02_disk.sh"
    collect_disk

    . "${LIB_DIR}/03_network.sh"
    collect_network

    . "${LIB_DIR}/04_process.sh"
    collect_process

    . "${LIB_DIR}/05_service.sh"
    collect_service

    . "${LIB_DIR}/06_cron.sh"
    collect_cron

    . "${LIB_DIR}/07_security.sh"
    collect_security

    . "${LIB_DIR}/08_backdoor.sh"
    collect_backdoor

    # Rootkit 仅 emergency/full 模式
    if [[ "$MODE" == "emergency" || "$MODE" == "full" ]]; then
        . "${LIB_DIR}/09_rootkit.sh"
        collect_rootkit
    fi

    . "${LIB_DIR}/10_log_analysis.sh"
    collect_log_analysis

    . "${LIB_DIR}/11_history.sh"
    collect_history

    # Webshell 仅 emergency/full 模式
    if [[ "$MODE" == "emergency" || "$MODE" == "full" ]]; then
        . "${LIB_DIR}/12_webshell.sh"
        collect_webshell
    fi

    # ========== 生成报告尾 ==========
    generate_html_footer >> "$REPORT_FILE"

    # ========== 输出其他格式 ==========
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        output_json
        log_info "JSON 报告: ${REPORT_FILE%.html}.json"
    elif [[ "$OUTPUT_FORMAT" == "md" ]]; then
        output_markdown
        log_info "Markdown 报告: ${REPORT_FILE%.html}.md"
    fi

    # ========== 清理临时文件 ==========
    rm -f /tmp/cloudinspect_tmp.json 2>/dev/null || true

    # ========== 完成 ==========
    log_info "报告已生成: ${REPORT_FILE}"
    print_banner
    exit_with_code
}

main "$@"