#!/bin/bash
###############################################################################
# CloudInspect - 下载离线安装包脚本
# 功能: 在联网主机下载 Bash4 + Python3 + pip 依赖到 packages/ 目录
# 用法: ./download_packages.sh
###############################################################################

set -euo pipefail

VERSION="v1.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGES_DIR="${SCRIPT_DIR}/../packages"
DOWNLOAD_LOG="${SCRIPT_DIR}/download.log"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }
log_done()  { echo -e "${GREEN}[DONE]${NC} $1"; }

# 创建目录
init() {
    echo "=============================================="
    echo "  CloudInspect ${VERSION} - 下载离线安装包"
    echo "=============================================="

    mkdir -p "${PACKAGES_DIR}/bash"
    mkdir -p "${PACKAGES_DIR}/python3"
    mkdir -p "${PACKAGES_DIR}/pip"
    log_info "创建目录结构完成"
}

# 下载 Bash 4 预编译包
download_bash() {
    log_info "下载 Bash 4 预编译包..."
    local bash_base="https://github.com/CloudInspect/releases/raw/main/bash"

    # Rocky/CentOS/RHEL 8
    log_info "  -> Rocky/CentOS/RHEL 8"
    curl -sfL "${bash_base}/rocky8/bash-4.4-rocky8.tar.gz" -o "${PACKAGES_DIR}/bash/bash-4.4-rocky8.tar.gz" || \
    log_warn "下载失败，将尝试通用版本"

    # Ubuntu 22.04
    log_info "  -> Ubuntu 22.04"
    curl -sfL "${bash_base}/ubuntu22/bash-4.4-ubuntu22.tar.gz" -o "${PACKAGES_DIR}/bash/bash-4.4-ubuntu22.tar.gz" || true

    # Debian
    log_info "  -> Debian"
    curl -sfL "${bash_base}/debian/bash-4.4-debian.tar.gz" -o "${PACKAGES_DIR}/bash/bash-4.4-debian.tar.gz" || true

    # Kylin
    log_info "  -> Kylin V10"
    curl -sfL "${bash_base}/kylin/bash-4.4-kylin.tar.gz" -o "${PACKAGES_DIR}/bash/bash-4.4-kylin.tar.gz" || true

    # Alpine
    log_info "  -> Alpine"
    curl -sfL "${bash_base}/alpine/bash-4.4-alpine.tar.gz" -o "${PACKAGES_DIR}/bash/bash-4.4-alpine.tar.gz" || true

    # Arch
    log_info "  -> Arch"
    curl -sfL "${bash_base}/arch/bash-4.4-arch.tar.gz" -o "${PACKAGES_DIR}/bash/bash-4.4-arch.tar.gz" || true

    log_done "Bash 下载完成: $(ls "${PACKAGES_DIR}/bash/" 2>/dev/null | wc -l) 个"
}

# 下载 Python3 预编译包
download_python() {
    log_info "下载 Python 3 预编译包..."
    local py_base="https://github.com/CloudInspect/releases/raw/main/python3"

    # Rocky 9
    log_info "  -> Rocky 9"
    curl -sfL "${py_base}/rocky9/python3-rocky9.tar.gz" -o "${PACKAGES_DIR}/python3/python3-rocky9.tar.gz" || true

    # CentOS 7
    log_info "  -> CentOS 7"
    curl -sfL "${py_base}/centos7/python3-centos7.tar.gz" -o "${PACKAGES_DIR}/python3/python3-centos7.tar.gz" || true

    # Ubuntu 22.04
    log_info "  -> Ubuntu 22.04"
    curl -sfL "${py_base}/ubuntu22/python3-ubuntu22.tar.gz" -o "${PACKAGES_DIR}/python3/python3-ubuntu22.tar.gz" || true

    # Debian
    log_info "  -> Debian"
    curl -sfL "${py_base}/debian/python3-debian.tar.gz" -o "${PACKAGES_DIR}/python3/python3-debian.tar.gz" || true

    # Kylin
    log_info "  -> Kylin"
    curl -sfL "${py_base}/kylin/python3-kylin.tar.gz" -o "${PACKAGES_DIR}/python3/python3-kylin.tar.gz" || true

    # Alpine
    log_info "  -> Alpine"
    curl -sfL "${py_base}/alpine/python3-alpine.tar.gz" -o "${PACKAGES_DIR}/python3/python3-alpine.tar.gz" || true

    log_done "Python 下载完成: $(ls "${PACKAGES_DIR}/python3/" 2>/dev/null | wc -l) 个"
}

# 下载 pip wheel 包
download_pip_deps() {
    log_info "下载 Python pip 依赖包..."

    # 如果有 requirements.txt，从 PyPI 下载 wheel
    local req_file="${SCRIPT_DIR}/../python/requirements.txt"
    if [[ -f "$req_file" ]]; then
        log_info "读取依赖列表: $req_file"
        while IFS= read -r pkg; do
            [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue
            pkg=$(echo "$pkg" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | cut -d'<' -f1 | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'[' -f1)
            [[ -z "$pkg" ]] && continue

            log_info "  -> $pkg"
            pip3 download "$pkg" --only-binary=:all: -d "${PACKAGES_DIR}/pip/" 2>/dev/null || \
            pip download "$pkg" --only-binary=:all: -d "${PACKAGES_DIR}/pip/" 2>/dev/null || \
            log_warn "  下载失败: $pkg"
        done < "$req_file"
    fi

    # 额外下载核心依赖
    local core_deps="pyyaml python-docx lxml"
    for dep in $core_deps; do
        log_info "  -> $dep"
        pip3 download "$dep" --only-binary=:all: -d "${PACKAGES_DIR}/pip/" 2>/dev/null || \
        pip download "$dep" --only-binary=:all: -d "${PACKAGES_DIR}/pip/" 2>/dev/null || \
        log_warn "  下载失败: $dep"
    done

    log_done "pip 依赖下载完成: $(ls "${PACKAGES_DIR}/pip/" 2>/dev/null | wc -l) 个包"
}

# 复制 requirements.txt
copy_requirements() {
    local req_file="${SCRIPT_DIR}/../python/requirements.txt"
    if [[ -f "$req_file" ]]; then
        cp "$req_file" "${PACKAGES_DIR}/requirements.txt"
        log_info "复制 requirements.txt 完成"
    fi
}

# 显示总结
summary() {
    echo ""
    echo "=============================================="
    echo "  下载完成总结"
    echo "=============================================="
    echo "  Bash 包: $(ls "${PACKAGES_DIR}/bash/" 2>/dev/null | wc -l) 个 ($(du -sh "${PACKAGES_DIR}/bash/" 2>/dev/null | cut -f1 || echo '?'))"
    echo "  Python 包: $(ls "${PACKAGES_DIR}/python3/" 2>/dev/null | wc -l) 个 ($(du -sh "${PACKAGES_DIR}/python3/" 2>/dev/null | cut -f1 || echo '?'))"
    echo "  pip 包: $(ls "${PACKAGES_DIR}/pip/" 2>/dev/null | wc -l) 个 ($(du -sh "${PACKAGES_DIR}/pip/" 2>/dev/null | cut -f1 || echo '?'))"
    echo ""
    echo "  下一步:"
    echo "    1. 将 packages/ 目录拷贝到内网服务器"
    echo "    2. 在内网服务器运行: ./install.sh"
    echo "=============================================="
}

main() {
    init
    download_bash
    download_python
    download_pip_deps
    copy_requirements
    summary
}

main "$@"