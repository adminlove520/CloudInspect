#!/bin/bash
###############################################################################
# CloudInspect - Bash 版本核心库
# 功能：OS检测 / 工具函数 / 颜色定义 / 配置加载 / 报告框架
###############################################################################

set -euo pipefail

# ========== 版本信息 ==========
VERSION="v1.0"
SCRIPT_NAME="$(basename "$0")"

# ========== 错误捕获 ==========
on_error() {
    local exit_code=$? line_no=$1
    echo -e "\n${RED}[ERROR]${NC} 脚本第 ${line_no} 行执行失败 (exit ${exit_code})" >&2
    exit 1
}
trap 'on_error $LINENO' ERR

# ========== 颜色定义 ==========
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ========== 全局变量 ==========
OS_FAMILY=""      # rhel | debian | suse | kylin | uos | arch | alpine | gentoo | other
OS_ID=""           # 原始 OS ID
OS_PRETTY=""      # 人类可读 OS 名
OS_VER_MAJOR=""    # 主版本号
OS_VER_MINOR=""
START_TIME=$(date +%s)
REPORT_DIR="${REPORT_DIR:-/tmp/cloudinspect}"
REPORT_FILE=""
OUTPUT_FORMAT="${OUTPUT_FORMAT:-html}"
VERBOSE=0
QUIET=0
MODE="${MODE:-routine}"
WARN_COUNT=0
CRITICAL_COUNT=0
TOTAL_STEPS=12
CURRENT_STEP=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ========== 配置加载（YAML 解析） ==========
load_config() {
    local config_file="${1:-${SCRIPT_DIR}/../config/default.yaml}"
    if [[ ! -f "$config_file" ]]; then
        log_warn "配置文件不存在: $config_file，使用默认配置"
        return
    fi

    # 简单的 YAML 解析（支持键值对，不支持嵌套结构）
    while IFS=': ' read -r key value; do
        [[ "$key" =~ ^# ]] && continue
        [[ -z "$key" || -z "$value" ]] && continue
        key=$(echo "$key" | tr -d ' ')
        value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

        case "$key" in
            "cpu_warn")         CPU_WARN="${value}" ;;
            "mem_warn")         MEM_WARN="${value}" ;;
            "disk_warn")        DISK_WARN="${value}" ;;
            "inode_warn")       INODE_WARN="${value}" ;;
            "swap_warn")        SWAP_WARN="${value}" ;;
            "load_factor")      LOAD_FACTOR="${value}" ;;
            "fd_warn")          FD_WARN="${value}" ;;
            "crit_offset")      CRIT_OFFSET="${value}" ;;
            "top_n")            TOP_N="${value}" ;;
            "large_file_size")  LARGE_FILE_SIZE="${value}" ;;
            "recent_days")      RECENT_DAYS="${value}" ;;
            "output_dir")       REPORT_DIR="${value}" ;;
        esac
    done < "$config_file"
}

# 默认阈值
CPU_WARN="${CPU_WARN:-80}"
MEM_WARN="${MEM_WARN:-85}"
DISK_WARN="${DISK_WARN:-85}"
INODE_WARN="${INODE_WARN:-85}"
SWAP_WARN="${SWAP_WARN:-50}"
LOAD_FACTOR="${LOAD_FACTOR:-2}"
FD_WARN="${FD_WARN:-80}"
CRIT_OFFSET="${CRIT_OFFSET:-10}"
TOP_N="${TOP_N:-10}"
LARGE_FILE_SIZE="${LARGE_FILE_SIZE:-100M}"
RECENT_DAYS="${RECENT_DAYS:-7}"

# ========== OS 检测 ==========
detect_os() {
    local id id_like ver pretty
    if [[ -r /etc/os-release ]]; then
        . /etc/os-release 2>/dev/null || true
        id="${ID:-}"
        id_like="${ID_LIKE:-}"
        ver="${VERSION_ID:-}"
        pretty="${PRETTY_NAME:-}"
    fi

    # 兜底检测
    [[ -z "$id" && -f /etc/kylin-release ]] && { id="kylin"; pretty=$(head -1 /etc/kylin-release 2>/dev/null); }
    [[ -z "$id" && -f /etc/centos-release ]] && { id="centos"; pretty=$(head -1 /etc/centos-release 2>/dev/null); }
    [[ -z "$id" && -f /etc/redhat-release ]] && { id="rhel"; pretty=$(head -1 /etc/redhat-release 2>/dev/null); }
    [[ -z "$id" && -f /etc/SuSE-release ]] && { id="suse"; pretty=$(head -1 /etc/SuSE-release 2>/dev/null); }
    [[ -z "$id" && -f /etc/debian_version ]] && { id="debian"; pretty="Debian $(cat /etc/debian_version 2>/dev/null)"; }
    [[ -z "$id" && -f /etc/alpine-release ]] && { id="alpine"; pretty="Alpine $(cat /etc/alpine-release 2>/dev/null)"; }
    [[ -z "$id" && -f /etc/arch-release ]] && { id="arch"; pretty="Arch Linux"; }
    [[ -z "$id" && -f /etc/gentoo-release ]] && { id="gentoo"; pretty=$(head -1 /etc/gentoo-release 2>/dev/null); }
    [[ -z "$id" ]] && { id="unknown"; pretty=$(uname -srvm); }

    case "$id $id_like" in
        *kylin*|*neokylin*)    OS_FAMILY="kylin" ;;
        *uos*|*deepin*)        OS_FAMILY="uos" ;;
        *rhel*|*centos*|*rocky*|*almalinux*|*ol*|*oracle*|*fedora*|*amzn*|*amazon*|*anolis*|*tencentos*|*alinux*)  OS_FAMILY="rhel" ;;
        *debian*|*ubuntu*|*kali*|*mint*|*pop*|*raspbian*)  OS_FAMILY="debian" ;;
        *suse*|*sles*|*opensuse*)  OS_FAMILY="suse" ;;
        *arch*|*manjaro*)      OS_FAMILY="arch" ;;
        *alpine*)              OS_FAMILY="alpine" ;;
        *gentoo*)              OS_FAMILY="gentoo" ;;
        *)                     OS_FAMILY="other" ;;
    esac

    OS_ID="$id"
    OS_PRETTY="${pretty:-$(uname -srvm)}"
    OS_VER_MAJOR="${ver%%.*}"
    OS_VER_MINOR="${ver#*.}"

    log_info "检测到操作系统: ${OS_PRETTY} (${OS_FAMILY})"
}

# ========== systemd 检测 ==========
has_systemd() {
    command -v systemctl &>/dev/null && [[ -d /run/systemd/system ]]
}

# ========== 服务状态检测 ==========
service_status() {
    local svc="$1" s=""
    if has_systemd; then
        s=$(systemctl is-active "$svc" 2>/dev/null || true)
        [[ "$s" == "active" ]] && echo "active" && return
        if systemctl list-unit-files "${svc}.service" --no-pager --no-legend 2>/dev/null | grep -qw "${svc}.service"; then
            echo "inactive"; return
        fi
        echo "notfound"; return
    fi
    if command -v service &>/dev/null && service "$svc" status &>/dev/null 2>&1; then
        echo "active"; return
    fi
    if [[ -x "/etc/init.d/$svc" ]]; then
        "/etc/init.d/$svc" status &>/dev/null 2>&1 && echo "active" || echo "inactive"; return
    fi
    echo "notfound"
}

service_enabled() {
    local svc="$1"
    if has_systemd; then
        systemctl is-enabled "$svc" 2>/dev/null || echo "unknown"
    elif command -v chkconfig &>/dev/null; then
        chkconfig --list "$svc" 2>/dev/null | awk '{for(i=2;i<=NF;i++) if($i~/:on/){print "enabled"; exit}} END{if(!found)print "disabled"}' || echo "unknown"
    else
        echo "unknown"
    fi
}

# ========== dmesg 安全获取 ==========
safe_dmesg() {
    local out
    out=$(dmesg 2>/dev/null || true)
    if [[ -z "$out" ]] && command -v journalctl &>/dev/null; then
        out=$(journalctl -k --no-pager 2>/dev/null | tail -3000 || true)
    fi
    printf '%s' "$out"
}

# ========== 容器检测 ==========
container_cmd() {
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        echo "docker"; return
    fi
    if command -v podman &>/dev/null && podman info &>/dev/null 2>&1; then
        echo "podman"; return
    fi
    echo ""
}

# ========== 工具函数 ==========
log_info()  { (( QUIET == 1 )) && return 0; echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { (( QUIET == 1 )) || echo -e "${YELLOW}[WARN]${NC} $1"; ((WARN_COUNT++)) || true; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; ((CRITICAL_COUNT++)) || true; }
log_debug() { (( VERBOSE == 1 )) && echo -e "${CYAN}[DEBUG]${NC} $1" || true; }

log_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    (( QUIET == 1 )) && return 0
    local pct=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    printf "${GREEN}[%2d/%-2d]${NC} (%3d%%) %s\n" "$CURRENT_STEP" "$TOTAL_STEPS" "$pct" "$1"
}

html_escape() {
    local str="$1"
    str="${str//&/&amp;}"
    str="${str//</&lt;}"
    str="${str//>/&gt;}"
    str="${str//\"/&quot;}"
    str="${str//\'/&#39;}"
    echo "$str"
}

human_bytes() {
    local bytes=${1:-0}
    if (( bytes >= 1073741824 )); then
        awk "BEGIN{printf \"%.1fG\", $bytes/1073741824}"
    elif (( bytes >= 1048576 )); then
        awk "BEGIN{printf \"%.1fM\", $bytes/1048576}"
    elif (( bytes >= 1024 )); then
        awk "BEGIN{printf \"%.1fK\", $bytes/1024}"
    else
        echo "${bytes}B"
    fi
}

get_color_class() {
    local val=${1:-0} warn=${2:-80}
    if (( val >= warn + CRIT_OFFSET )); then echo "red"
    elif (( val >= warn )); then echo "orange"
    else echo "green"
    fi
}

status_badge() {
    local val=${1:-0} warn=${2:-80}
    local crit=$((warn + CRIT_OFFSET))
    if (( val >= crit )); then
        echo '<span class="badge critical">严重</span>'
    elif (( val >= warn )); then
        echo '<span class="badge warning">警告</span>'
    else
        echo '<span class="badge ok">正常</span>'
    fi
}

elapsed_time() {
    local end=$(date +%s)
    local elapsed=$((end - START_TIME))
    local m=$((elapsed / 60))
    local s=$((elapsed % 60))
    echo "${m}m${s}s"
}

pre_block() {
    local content="$1" empty_text="${2:-无数据}"
    if [[ -z "$content" ]]; then
        echo "<pre>${empty_text}</pre>"
    else
        echo "<pre>$(html_escape "$content")</pre>"
    fi
}

# ========== 命令行参数解析 ==========
parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -o|--output)     REPORT_FILE="$2"; shift 2 ;;
            -f|--format)     OUTPUT_FORMAT="$2"; shift 2 ;;
            -m|--mode)       MODE="$2"; shift 2 ;;
            -v|--verbose)    VERBOSE=1; shift ;;
            -q|--quiet)      QUIET=1; shift ;;
            -h|--help)       show_help; exit 0 ;;
            *)               echo -e "${RED}未知参数: $1${NC}" >&2; show_help; exit 1 ;;
        esac
    done

    if [[ "$OUTPUT_FORMAT" != "html" && "$OUTPUT_FORMAT" != "json" && "$OUTPUT_FORMAT" != "md" ]]; then
        echo -e "${RED}错误: -f 仅支持 html | json | md${NC}" >&2; exit 1
    fi

    # 自动生成报告路径
    if [[ -z "$REPORT_FILE" ]]; then
        local ext="$OUTPUT_FORMAT"
        [[ "$ext" == "md" ]] && ext="md"
        REPORT_FILE="${REPORT_DIR}/inspect_$(hostname)_$(date +%Y%m%d_%H%M%S).${ext}"
    fi
}

show_help() {
    cat <<HELP
CloudInspect ${VERSION} - 云主机安全巡检工具

用法: $SCRIPT_NAME [选项]

选项:
  -o, --output FILE   指定报告输出路径
  -f, --format FORMAT 输出格式: html (默认) | json | md
  -m, --mode MODE     工作模式: routine | emergency | quick | full
  -v, --verbose       详细日志
  -q, --quiet         静默模式
  -h, --help          显示帮助

模式说明:
  routine    日常巡检（推荐，5-15分钟）
  emergency  应急排查（深度，30-60分钟）
  quick      快速扫描（1-3分钟）
  full       完全扫描（60分钟+）

示例:
  $SCRIPT_NAME                         # 默认 HTML 报告
  $SCRIPT_NAME -m emergency -f html    # 应急排查模式
  $SCRIPT_NAME -f json -o /tmp/r.json  # 输出 JSON
  $SCRIPT_NAME --mode quick --verbose  # 快速详细模式

退出码:
  0 - 正常（无警告/无严重）
  1 - 有警告
  2 - 有严重告警/脚本错误
HELP
}

# ========== 报告初始化 ==========
init_report() {
    mkdir -p "$REPORT_DIR" 2>/dev/null || {
        echo -e "${RED}错误: 无法创建报告目录 ${REPORT_DIR}${NC}" >&2; exit 1
    }

    if ! : > "$REPORT_FILE" 2>/dev/null; then
        echo -e "${RED}错误: 无法写入报告文件 ${REPORT_FILE}${NC}" >&2; exit 1
    fi

    log_info "报告将保存至: ${REPORT_FILE}"
}

# ========== 打印横幅 ==========
print_banner() {
    (( QUIET == 1 )) && return 0
    cat <<BANNER
==============================================
  CloudInspect ${VERSION} - 云主机安全巡检
  Host: $(hostname)
  OS: ${OS_PRETTY}
  Mode: ${MODE}
  Time: $(date '+%Y-%m-%d %H:%M:%S')
  Format: ${OUTPUT_FORMAT}
  Steps: ${TOTAL_STEPS}
==============================================
BANNER
}

# ========== 退出码 ==========
exit_with_code() {
    local elapsed=$(elapsed_time)
    if (( CRITICAL_COUNT > 0 )); then
        log_error "巡检完成 - 严重告警: ${CRITICAL_COUNT} | 警告: ${WARN_COUNT} | 耗时: ${elapsed}"
        exit 2
    elif (( WARN_COUNT > 0 )); then
        log_warn "巡检完成 - 警告: ${WARN_COUNT} | 耗时: ${elapsed}"
        exit 1
    else
        log_info "巡检完成 - 全部正常 | 耗时: ${elapsed}"
        exit 0
    fi
}

# ========== 初始化 ==========
init() {
    detect_os
    load_config
    parse_args "$@"
    init_report
    print_banner
}