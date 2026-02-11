#!/bin/bash
# VoCoType Fcitx5 卸载脚本
#
# 用法:
#   bash fcitx5/scripts/uninstall-fcitx5.sh [--purge-config] [--dry-run]
# 选项:
#   --purge-config  同时删除 ~/.config/vocotype 下的用户配置
#   --dry-run       仅打印将执行的操作，不真正删除

set -euo pipefail

PURGE_CONFIG=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --purge-config)
            PURGE_CONFIG=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            echo "用法: $0 [--purge-config] [--dry-run]"
            exit 1
            ;;
    esac
done

run_cmd() {
    if [ "$DRY_RUN" = true ]; then
        echo "[dry-run] $*"
    else
        "$@"
    fi
}

remove_file() {
    local path="$1"
    if [ -e "$path" ] || [ -L "$path" ]; then
        run_cmd rm -f "$path"
        echo "删除: $path"
    fi
}

remove_dir() {
    local path="$1"
    if [ -d "$path" ]; then
        run_cmd rm -rf "$path"
        echo "删除目录: $path"
    fi
}

remove_dir_if_empty() {
    local path="$1"
    if [ -d "$path" ] && [ -z "$(ls -A "$path" 2>/dev/null)" ]; then
        run_cmd rmdir "$path"
        echo "删除空目录: $path"
    fi
}

echo "=== 卸载 VoCoType Fcitx5 ==="
echo ""

INSTALL_DIR="$HOME/.local/share/vocotype-fcitx5"
LAUNCHER="$HOME/.local/bin/vocotype-fcitx5-backend"
SYSTEMD_UNIT="$HOME/.config/systemd/user/vocotype-fcitx5-backend.service"
ENV_FILE="$HOME/.config/environment.d/fcitx5-vocotype.conf"

ADDON_CONF="$HOME/.local/share/fcitx5/addon/vocotype.conf"
IM_CONF="$HOME/.local/share/fcitx5/inputmethod/vocotype.conf"

LIB_SO_1="$HOME/.local/lib/fcitx5/vocotype.so"
LIB_SO_2="$HOME/.local/lib64/fcitx5/vocotype.so"
LIB_LINK_1="$HOME/.local/lib/fcitx5/libvocotype.so"
LIB_LINK_2="$HOME/.local/lib64/fcitx5/libvocotype.so"

SOCKET_FILE="/tmp/vocotype-fcitx5.sock"

echo "[1/6] 停止并禁用后台服务..."
if command -v systemctl >/dev/null 2>&1; then
    run_cmd systemctl --user disable --now vocotype-fcitx5-backend.service >/dev/null 2>&1 || true
    run_cmd systemctl --user daemon-reload >/dev/null 2>&1 || true
fi
run_cmd pkill -f "fcitx5_server.py" >/dev/null 2>&1 || true

echo ""
echo "[2/6] 删除启动器和服务文件..."
remove_file "$LAUNCHER"
remove_file "$SYSTEMD_UNIT"

echo ""
echo "[3/6] 删除 Fcitx5 插件和配置..."
remove_file "$ADDON_CONF"
remove_file "$IM_CONF"
remove_file "$LIB_SO_1"
remove_file "$LIB_SO_2"
remove_file "$LIB_LINK_1"
remove_file "$LIB_LINK_2"

echo ""
echo "[4/6] 删除 VoCoType 安装目录..."
remove_dir "$INSTALL_DIR"
remove_file "$SOCKET_FILE"

echo ""
echo "[5/6] 删除环境变量配置..."
remove_file "$ENV_FILE"

echo ""
echo "[6/6] 清理空目录..."
remove_dir_if_empty "$HOME/.local/lib/fcitx5"
remove_dir_if_empty "$HOME/.local/lib64/fcitx5"
remove_dir_if_empty "$HOME/.local/share/fcitx5/addon"
remove_dir_if_empty "$HOME/.local/share/fcitx5/inputmethod"
remove_dir_if_empty "$HOME/.config/environment.d"

if [ "$PURGE_CONFIG" = true ]; then
    echo ""
    echo "附加清理: 删除用户配置目录..."
    remove_dir "$HOME/.config/vocotype"
fi

echo ""
echo "卸载完成。"
echo "建议执行："
echo "  1) 重新登录桌面会话，或执行 fcitx5 -r"
echo "  2) 在 fcitx5-configtool 中移除 VoCoType 输入法项（如仍显示）"
