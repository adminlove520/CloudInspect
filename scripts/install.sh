#!/bin/bash
###############################################################################
# CloudInspect - 离线安装脚本
# 功能: 在内网服务器一键安装 Bash4 + Python3 + 依赖，无需互联网
###############################################################################

set -euo pipefail

VERSION="v1.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES_DIR="${SCRIPT_DIR}/packages"
INSTALL_BASE="/opt/cloudinspect"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# ========== 检测 OS ==========
detect_os() {
    local os_id os_family ver
    if [[ -r /etc/os-release ]]; then
        . /etc/os-release 2>/dev/null || true
        os_id="${ID:-}"
        ver="${VERSION_ID:-}"
    fi
    [[ -z "$os_id" && -f /etc/kylin-release ]] && os_id="kylin"
    [[ -z "$os_id" && -f /etc/centos-release ]] && os_id="centos"
    [[ -z "$os_id" && -f /etc/redhat-release ]] && os_id="rhel"
    [[ -z "$os_id" && -f /etc/debian_version ]] && os_id="debian"
    [[ -z "$os_id" && -f /etc/alpine-release ]] && os_id="alpine"
    [[ -z "$os_id" && -f /etc/arch-release ]] && os_id="arch"
    [[ -z "$os_id" && -f /etc/gentoo-release ]] && os_id="gentoo"
    [[ -z "$os_id" ]] && os_id="unknown"

    echo "$os_id"
}

# ========== 检查依赖包 ==========
check_packages() {
    log_info "检查离线安装包..."
    local missing=""

    if [[ ! -d "$PACKAGES_DIR" ]]; then
        log_error "找不到 packages 目录: $PACKAGES_DIR"
        log_error "请先在联网机器运行: download_packages.sh"
        exit 1
    fi

    [[ ! -d "$PACKAGES_DIR/bash" ]] && missing+=" bash/" || true
    [[ ! -d "$PACKAGES_DIR/python3" ]] && missing+=" python3/" || true
    [[ ! -d "$PACKAGES_DIR/pip" ]] && missing+=" pip/" || true

    if [[ -n "$missing" ]]; then
        log_warn "部分包缺失: $missing"
        log_warn "将尝试最小化安装（可能需要系统自带工具）"
    fi

    log_info "检查完成"
}

# ========== 安装 Bash 4 ==========
install_bash() {
    local os_id="$1"
    log_info "安装 Bash 4..."

    local bash_pkg=""
    case "$os_id" in
        centos|rhel|rocky|almalinux|anolis)
            bash_pkg="$PACKAGES_DIR/bash/bash-4.4-rhel.tar.gz"
            [[ ! -f "$bash_pkg" ]] && bash_pkg="$PACKAGES_DIR/bash/bash-4.4-rocky.tar.gz"
            ;;
        ubuntu|debian|kali)
            bash_pkg="$PACKAGES_DIR/bash/bash-4.4-ubuntu.tar.gz"
            [[ ! -f "$bash_pkg" ]] && bash_pkg="$PACKAGES_DIR/bash/bash-4.4-debian.tar.gz"
            ;;
        kylin|uos)
            bash_pkg="$PACKAGES_DIR/bash/bash-4.4-kylin.tar.gz"
            ;;
        alpine)
            bash_pkg="$PACKAGES_DIR/bash/bash-4.4-alpine.tar.gz"
            ;;
        arch)
            bash_pkg="$PACKAGES_DIR/bash/bash-4.4-arch.tar.gz"
            ;;
        gentoo)
            bash_pkg="$PACKAGES_DIR/bash/bash-4.4-gentoo.tar.gz"
            ;;
        *)
            bash_pkg=$(ls "$PACKAGES_DIR/bash/"*.tar.gz 2>/dev/null | head -1 || echo "")
            ;;
    esac

    if [[ -n "$bash_pkg" && -f "$bash_pkg" ]]; then
        local tmp_dir=$(mktemp -d)
        tar -xzf "$bash_pkg" -C "$tmp_dir" 2>/dev/null || {
            log_warn "Bash 包解压失败，将使用系统自带 Bash"
            rm -rf "$tmp_dir"
            return 0
        }
        # 复制到 /usr/local/bin
        if [[ -d "$tmp_dir/usr/local/bin" ]]; then
            cp -f "$tmp_dir/usr/local/bin/bash" /usr/local/bin/bash_new 2>/dev/null && \
            chmod +x /usr/local/bin/bash_new && \
            log_info "Bash 4 安装完成（/usr/local/bin/bash_new）"
            # 创建软链接（可选）
            if [[ ! -f /usr/local/bin/bash ]] || [[ "$(/usr/local/bin/bash_new --version | head -1)" > "$(bash --version | head -1)" ]]; then
                ln -sf /usr/local/bin/bash_new /usr/local/bin/bash
                log_info "已创建软链接: /usr/local/bin/bash -> bash_new"
            fi
        fi
        rm -rf "$tmp_dir"
    else
        log_warn "未找到对应的 Bash 安装包: $bash_pkg"
        log_info "检查系统 Bash 版本: $(bash --version | head -1)"
        if [[ "${BASH_VERSION%%.*}" -ge 4 ]]; then
            log_info "系统 Bash 版本 >= 4.0，满足要求"
        else
            log_error "系统 Bash 版本过低 (< 4.0)，请手动安装 Bash 4"
        fi
    fi
}

# ========== 安装 Python3 ==========
install_python() {
    local os_id="$1"
    log_info "安装 Python 3..."

    local py_pkg=""
    case "$os_id" in
        centos|rhel|rocky|almalinux|anolis)
            py_pkg="$PACKAGES_DIR/python3/python3-rocky9.tar.gz"
            [[ ! -f "$py_pkg" ]] && py_pkg="$PACKAGES_DIR/python3/python3-centos7.tar.gz"
            [[ ! -f "$py_pkg" ]] && py_pkg=$(ls "$PACKAGES_DIR/python3/"*.tar.gz 2>/dev/null | head -1 || echo "")
            ;;
        ubuntu|debian)
            py_pkg="$PACKAGES_DIR/python3/python3-ubuntu22.tar.gz"
            [[ ! -f "$py_pkg" ]] && py_pkg=$(ls "$PACKAGES_DIR/python3/"*.tar.gz 2>/dev/null | head -1 || echo "")
            ;;
        kylin|uos)
            py_pkg="$PACKAGES_DIR/python3/python3-kylin.tar.gz"
            ;;
        alpine)
            py_pkg="$PACKAGES_DIR/python3/python3-alpine.tar.gz"
            ;;
        arch)
            py_pkg="$PACKAGES_DIR/python3/python3-arch.tar.gz"
            ;;
        *)
            py_pkg=$(ls "$PACKAGES_DIR/python3/"*.tar.gz 2>/dev/null | head -1 || echo "")
            ;;
    esac

    if [[ -n "$py_pkg" && -f "$py_pkg" ]]; then
        local tmp_dir=$(mktemp -d)
        tar -xzf "$py_pkg" -C "$tmp_dir" 2>/dev/null || {
            log_warn "Python 包解压失败，尝试系统安装"
            rm -rf "$tmp_dir"
            install_python_system
            return 0
        }

        # 复制到安装目录
        mkdir -p "$INSTALL_BASE"
        cp -rf "$tmp_dir"/* "$INSTALL_BASE/" 2>/dev/null || \
        cp -rf "$tmp_dir/." "$INSTALL_BASE/" 2>/dev/null

        rm -rf "$tmp_dir"

        # 验证
        if [[ -x "$INSTALL_BASE/python3/bin/python3" ]]; then
            log_info "Python 3 安装完成: $($INSTALL_BASE/python3/bin/python3 --version)"
        else
            log_warn "Python 3 安装验证失败，尝试系统安装"
            install_python_system
        fi
    else
        log_warn "未找到 Python 安装包，尝试系统安装"
        install_python_system
    fi
}

install_python_system() {
    log_info "尝试系统包管理器安装 Python 3..."
    if command -v python3 &>/dev/null; then
        log_info "系统已有 Python 3: $(python3 --version)"
    else
        case "$os_id" in
            centos|rhel|rocky|almalinux)
                yum install -y python3 python3-pip 2>/dev/null || \
                dnf install -y python3 python3-pip 2>/dev/null || \
                log_warn "yum/dnf 安装 Python 失败"
                ;;
            ubuntu|debian)
                apt-get install -y python3 python3-pip python3-venv 2>/dev/null || \
                log_warn "apt 安装 Python 失败"
                ;;
            alpine)
                apk add --no-cache python3 py3-pip 2>/dev/null || \
                log_warn "apk 安装 Python 失败"
                ;;
            arch)
                pacman -Sy --noconfirm python python-pip 2>/dev/null || \
                log_warn "pacman 安装 Python 失败"
                ;;
            *)
                log_warn "无法自动安装 Python，请手动安装"
                ;;
        esac
    fi
}

# ========== 安装 pip 依赖 ==========
install_pip_deps() {
    log_info "安装 Python 依赖包..."

    local pip_cmd=""
    local venv_python=""

    # 优先使用 venv
    if [[ -f "$INSTALL_BASE/python3/bin/python3" ]]; then
        venv_python="$INSTALL_BASE/python3/bin/python3"
        mkdir -p "$INSTALL_BASE/venv"
        "$venv_python" -m venv "$INSTALL_BASE/venv" 2>/dev/null || true
        pip_cmd="$INSTALL_BASE/venv/bin/pip"
    fi

    if [[ ! -f "$pip_cmd" ]]; then
        if command -v python3 &>/dev/null; then
            python3 -m venv "$INSTALL_BASE/venv" 2>/dev/null || true
            pip_cmd="$INSTALL_BASE/venv/bin/pip"
        fi
    fi

    if [[ ! -f "$pip_cmd" ]]; then
        log_warn "无法找到 pip，尝试直接使用 pip3"
        pip_cmd="pip3"
    fi

    # 安装 wheel 包
    if [[ -d "$PACKAGES_DIR/pip" ]]; then
        local wheel_files=$(ls "$PACKAGES_DIR/pip/"*.whl 2>/dev/null || echo "")
        if [[ -n "$wheel_files" ]]; then
            log_info "安装离线 wheel 包..."
            for whl in $wheel_files; do
                $pip_cmd install --no-index --force-reinstall "$whl" 2>/dev/null || \
                $pip_cmd install --ignore-installed "$whl" 2>/dev/null || \
                log_warn "安装失败: $(basename "$whl")"
            done
        fi
    fi

    # 也尝试从 requirements.txt 安装（如果有网络或缓存）
    if [[ -f "${PACKAGES_DIR}/requirements.txt" ]]; then
        $pip_cmd install -r "${PACKAGES_DIR}/requirements.txt" 2>/dev/null || \
        log_warn "requirements.txt 安装失败（正常，如果无网络）"
    fi

    log_info "pip 依赖安装完成"
}

# ========== 复制 CloudInspect ==========
install_cloudinspect() {
    log_info "安装 CloudInspect 脚本..."

    # 复制 Bash 版本
    mkdir -p "${INSTALL_BASE}/bash"
    cp -f "${SCRIPT_DIR}/../bash/"*.sh "${INSTALL_BASE}/bash/" 2>/dev/null || true
    cp -rf "${SCRIPT_DIR}/../bash/lib" "${INSTALL_BASE}/bash/" 2>/dev/null || true

    # 复制 Python 版本
    mkdir -p "${INSTALL_BASE}/python"
    cp -f "${SCRIPT_DIR}/../python/"*.py "${INSTALL_BASE}/python/" 2>/dev/null || true
    cp -rf "${SCRIPT_DIR}/../python/lib" "${INSTALL_BASE}/python/" 2>/dev/null || true
    cp -rf "${SCRIPT_DIR}/../python/core" "${INSTALL_BASE}/python/" 2>/dev/null || true
    cp -rf "${SCRIPT_DIR}/../python/rules" "${INSTALL_BASE}/python/" 2>/dev/null || true

    # 复制配置
    mkdir -p "${INSTALL_BASE}/config"
    cp -f "${SCRIPT_DIR}/../config/"*.yaml "${INSTALL_BASE}/config/" 2>/dev/null || true

    # 创建软链接
    ln -sf "${INSTALL_BASE}/bash/inspect.sh" /usr/local/bin/cloudinspect 2>/dev/null || \
    ln -sf "${INSTALL_BASE}/bash/inspect.sh" /usr/bin/cloudinspect 2>/dev/null || true

    chmod +x "${INSTALL_BASE}/bash/inspect.sh" 2>/dev/null || true

    log_info "CloudInspect 安装完成"
}

# ========== 验证安装 ==========
verify() {
    log_info "验证安装..."

    local success=0

    # 验证 Bash
    if bash "${INSTALL_BASE}/bash/inspect.sh" --help &>/dev/null || \
       bash "${INSTALL_BASE}/bash/inspect.sh" -h &>/dev/null; then
        log_info "✅ Bash 版本验证通过"
        ((success++))
    else
        log_warn "⚠️ Bash 版本可能有问题"
    fi

    # 验证 Python
    local py_bin="$INSTALL_BASE/venv/bin/python3"
    [[ ! -f "$py_bin" ]] && py_bin="python3"
    if command -v python3 &>/dev/null || [[ -f "$py_bin" ]]; then
        log_info "✅ Python 3 已安装: $(${py_bin} --version 2>/dev/null)"
        ((success++))
    fi

    echo ""
    echo "=============================================="
    echo "  CloudInspect ${VERSION} 安装完成"
    echo "=============================================="
    echo "  安装位置: $INSTALL_BASE"
    echo "  Bash 版本: $(bash --version | head -1)"
    echo "  Python 版本: $(${py_bin} --version 2>/dev/null || echo 'N/A')"
    echo ""
    echo "  使用方法:"
    echo "    Bash 版本: ${INSTALL_BASE}/bash/inspect.sh"
    echo "    Python 版本: ${INSTALL_BASE}/python/inspect.py"
    echo "    快捷命令: cloudinspect"
    echo "=============================================="
}

# ========== 主流程 ==========
main() {
    echo "=============================================="
    echo "  CloudInspect ${VERSION} - 离线安装程序"
    echo "=============================================="

    local os_id
    os_id=$(detect_os)
    log_info "检测到操作系统: $os_id"
    log_info "安装包目录: $PACKAGES_DIR"

    check_packages
    install_bash "$os_id"
    install_python "$os_id"
    install_pip_deps
    install_cloudinspect
    verify
}

main "$@"