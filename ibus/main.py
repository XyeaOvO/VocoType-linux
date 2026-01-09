#!/usr/bin/env python3
"""VoCoType IBus Engine 主程序"""

from __future__ import annotations

import sys
import os
import argparse
import logging
from pathlib import Path

# 添加项目根目录到path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ========== 关键：在导入 gi 之前先初始化 pyrime ==========
# librime 是全局状态，必须在其他使用 librime 的进程（如 ibus-rime）之前初始化
_rime_api = None
_rime_traits = None
_rime_session_id = None

def _early_init_rime():
    """尽早初始化 Rime，确保使用正确的配置"""
    global _rime_api, _rime_traits, _rime_session_id
    try:
        from pyrime.api import Traits, API

        log_dir = Path.home() / ".local" / "share" / "vocotype" / "rime"
        log_dir.mkdir(parents=True, exist_ok=True)

        # 优先使用 ibus-rime 用户目录，保证配置完整可用
        vocotype_user_dir = Path.home() / ".config" / "vocotype" / "rime"
        ibus_rime_user = Path.home() / ".config" / "ibus" / "rime"
        if (ibus_rime_user / "default.yaml").exists():
            user_data_dir = ibus_rime_user
        elif (vocotype_user_dir / "default.yaml").exists():
            user_data_dir = vocotype_user_dir
        else:
            return

        if user_data_dir == vocotype_user_dir and not user_data_dir.exists():
            user_data_dir.mkdir(parents=True, exist_ok=True)

        shared_dirs = [
            Path("/usr/share/rime-data"),
            Path("/usr/local/share/rime-data"),
        ]
        shared_data_dir = next((d for d in shared_dirs if d.exists()), None)

        # 仅在使用 vocotype 目录时创建符号链接
        if user_data_dir == vocotype_user_dir:
            for subdir in ["build", "lua", "cn_dicts", "en_dicts", "opencc", "others"]:
                link_path = user_data_dir / subdir
                if link_path.exists() or link_path.is_symlink():
                    continue
                # 优先 ibus-rime 用户目录
                target_path = ibus_rime_user / subdir
                if not target_path.exists() and shared_data_dir:
                    target_path = shared_data_dir / subdir
                if target_path.exists():
                    try:
                        link_path.symlink_to(target_path)
                    except OSError:
                        pass

        if shared_data_dir:
            _rime_traits = Traits(
                shared_data_dir=str(shared_data_dir),
                user_data_dir=str(user_data_dir),
                log_dir=str(log_dir),
                distribution_name="VoCoType",
                distribution_code_name="vocotype",
                distribution_version="1.0",
                app_name="rime.vocotype",
            )
            _rime_api = API()
            _rime_api.setup(_rime_traits)
            _rime_api.initialize(_rime_traits)
            # 立即创建 session 以锁定配置
            _rime_session_id = _rime_api.create_session()
    except ImportError:
        pass  # pyrime 未安装，忽略
    except Exception:
        pass  # 初始化失败，后续会处理

_early_init_rime()
# ========== 早期 Rime 初始化结束 ==========

import gi
gi.require_version('IBus', '1.0')
from gi.repository import IBus, GLib

from ibus.factory import VoCoTypeFactory
from vocotype_version import __version__

logger = logging.getLogger(__name__)


class VoCoTypeIMApp:
    """VoCoType输入法应用"""

    def __init__(self, exec_by_ibus: bool = True):
        IBus.init()
        self._mainloop = GLib.MainLoop()
        self._bus = IBus.Bus()

        if not self._bus.is_connected():
            logger.error("无法连接到IBus守护进程")
            sys.exit(1)

        self._bus.connect("disconnected", self._on_bus_disconnected)
        self._factory = VoCoTypeFactory(self._bus)

        if exec_by_ibus:
            self._bus.request_name("org.vocotype.IBus.VoCoType", 0)
        else:
            self._register_component()

        logger.info("VoCoType IBus引擎已启动")

    def _register_component(self):
        """注册IBus组件（调试用）"""
        component = IBus.Component.new(
            "org.vocotype.IBus.VoCoType",
            "VoCoType Voice Input Method",
            __version__,
            "GPL",
            "VoCoType",
            "https://github.com/vocotype",
            "",
            "vocotype"
        )

        engine = IBus.EngineDesc.new(
            "vocotype",
            "VoCoType Voice Input",
            "Push-to-Talk Voice Input (F9)",
            "zh",
            "GPL",
            "VoCoType",
            "",  # icon
            "default"
        )

        component.add_engine(engine)
        self._bus.register_component(component)

    def run(self):
        """运行主循环"""
        self._mainloop.run()

    def quit(self):
        """退出"""
        self._mainloop.quit()

    def _on_bus_disconnected(self, bus):
        """IBus断开连接"""
        logger.info("IBus连接已断开")
        self._mainloop.quit()


def print_xml():
    """输出引擎XML描述"""
    print('''<?xml version="1.0" encoding="utf-8"?>
<component>
    <name>org.vocotype.IBus.VoCoType</name>
    <description>VoCoType Voice Input Method</description>
    <exec>{exec_path} --ibus</exec>
    <version>{version}</version>
    <author>VoCoType</author>
    <license>GPL</license>
    <homepage>https://github.com/vocotype</homepage>
    <textdomain>vocotype</textdomain>
    <engines>
        <engine>
            <name>vocotype</name>
            <language>zh</language>
            <license>GPL</license>
            <author>VoCoType</author>
            <layout>default</layout>
            <longname>VoCoType Voice Input</longname>
            <description>Push-to-Talk Voice Input (F9)</description>
            <rank>50</rank>
            <symbol>🎤</symbol>
        </engine>
    </engines>
</component>'''.format(exec_path=os.path.abspath(__file__), version=__version__))


def main():
    parser = argparse.ArgumentParser(description='VoCoType IBus Engine')
    parser.add_argument('--ibus', '-i', action='store_true',
                        help='由IBus守护进程启动')
    parser.add_argument('--xml', '-x', action='store_true',
                        help='输出引擎XML描述')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='启用调试日志')
    args = parser.parse_args()

    if args.xml:
        print_xml()
        return

    # 配置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stderr),
        ]
    )
    log_path = os.environ.get("VOCOTYPE_LOG_FILE")
    if log_path:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logging.getLogger().addHandler(file_handler)

    # 创建并运行应用
    app = VoCoTypeIMApp(exec_by_ibus=args.ibus)

    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()


if __name__ == "__main__":
    main()
