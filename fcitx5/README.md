# VoCoType Fcitx 5 版本

VoCoType 离线语音输入法的 Fcitx 5 版本实现。

## 功能特性

🎤 **语音输入** - 按住 F9 说话，松开自动识别并输入
⌨️ **Rime 拼音** - 完整的 Rime 拼音输入支持
🔒 **完全离线** - 所有识别在本地完成，零网络依赖
🚀 **轻量高效** - 纯 CPU 推理，仅需 700MB 内存
⚡ **快速响应** - 0.1 秒级识别速度

## 架构设计

```
Fcitx 5 Framework
    ↓ (C++ API)
C++ Addon (fcitx5/addon/)
    ├─ 监听 F9 按键（语音）
    ├─ 监听其他按键（Rime）
    └─ 更新 UI
    ↓ (Unix Socket IPC)
Python Backend (fcitx5/backend/)
    ├─ 语音识别（FunASR）
    └─ Rime 拼音处理（pyrime）
```

## 系统要求

### 必需依赖

- **Fcitx 5** - 输入法框架
- **Python 3.12+** - 后端运行环境
- **编译工具**:
  - CMake 3.10+
  - C++17 编译器
  - pkg-config
- **开发库**:
  - `fcitx5-devel` (或 `libfcitx5-dev`)
  - `nlohmann-json-devel` (或 `nlohmann-json3-dev`)

### 可选依赖（推荐）

- **pyrime** - Rime 拼音输入支持（完整版）
- **ibus-rime** - 共享 Rime 配置（如果已安装）
- **rime-ice** - 现代词库和配置方案

## 安装

### 快速安装

```bash
cd vocotype-cli
bash fcitx5/scripts/install-fcitx5.sh
```

安装脚本会自动完成：
1. ✅ 检查 Fcitx 5 和编译依赖
2. 🔧 编译 C++ Addon
3. 📦 安装 Python 后端
4. 🐍 配置 Python 虚拟环境
5. 🎙️ 配置音频设备（可选）
6. ⚙️ 创建 systemd 服务

### 手动安装

#### 1. 编译 C++ Addon

```bash
cd fcitx5/addon
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/.local
make -j$(nproc)
make install
```

#### 2. 安装配置文件

```bash
mkdir -p ~/.local/share/fcitx5/addon
mkdir -p ~/.local/share/fcitx5/inputmethod
cp fcitx5/data/vocotype.conf ~/.local/share/fcitx5/addon/
cp fcitx5/data/vocotype.conf.in ~/.local/share/fcitx5/inputmethod/
```

#### 3. 安装 Python 后端

```bash
INSTALL_DIR=$HOME/.local/share/vocotype-fcitx5
mkdir -p "$INSTALL_DIR"
cp -r app "$INSTALL_DIR/"
cp -r fcitx5/backend "$INSTALL_DIR/"
cp vocotype_version.py "$INSTALL_DIR/"

# 创建虚拟环境
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install -r requirements.txt

# 安装完整版（含 pyrime）
"$INSTALL_DIR/.venv/bin/pip" install -e ".[full]"
```

#### 4. 配置音频

```bash
"$INSTALL_DIR/.venv/bin/python" scripts/setup-audio.py
```

## 使用方法

### 1. 启动后台服务

**方式 A：手动启动（临时）**

```bash
vocotype-fcitx5-backend &
```

**方式 B：systemd 自动启动（推荐）**

```bash
# 启用并启动服务
systemctl --user enable vocotype-fcitx5-backend.service
systemctl --user start vocotype-fcitx5-backend.service

# 查看服务状态
systemctl --user status vocotype-fcitx5-backend.service

# 查看日志
journalctl --user -u vocotype-fcitx5-backend.service -f
```

### 2. 重启 Fcitx 5

```bash
fcitx5 -r
```

### 3. 添加输入法

1. 打开 Fcitx 5 配置工具：
   ```bash
   fcitx5-configtool
   ```

2. 在"输入法"标签中，点击"添加输入法"

3. 搜索"VoCoType"，添加到当前输入法列表

4. 切换到 VoCoType 输入法

### 4. 开始使用

- **语音输入**: 按住 F9 说话，松开后自动识别
- **拼音输入**: 正常打字，使用 Rime 拼音输入

## Rime 配置

VoCoType Fcitx 5 版本与 IBus 版本**共享 Rime 配置目录**：

```
~/.config/ibus/rime/
```

这意味着：
- ✅ 如果您已在使用 ibus-rime，VoCoType 会自动继承您的配置
- ✅ 推荐使用 [rime-ice（雾凇拼音）](https://github.com/iDvel/rime-ice) 获得更好体验
- ✅ 所有 Rime 自定义配置都适用

详见：[RIME_CONFIG_GUIDE.md](../RIME_CONFIG_GUIDE.md)

## 故障排查

### Backend 无法启动

**问题**: `vocotype-fcitx5-backend` 启动失败

**解决方案**:
1. 检查 Python 依赖是否完整安装：
   ```bash
   ~/.local/share/vocotype-fcitx5/.venv/bin/python -c "import pyrime; print('OK')"
   ```

2. 查看详细错误日志：
   ```bash
   ~/.local/share/vocotype-fcitx5/.venv/bin/python \
       ~/.local/share/vocotype-fcitx5/backend/fcitx5_server.py --debug
   ```

### C++ Addon 无法加载

**问题**: Fcitx 5 找不到 VoCoType 插件

**解决方案**:
1. 检查插件是否安装：
   ```bash
   ls ~/.local/lib/fcitx5/vocotype.so
   ls ~/.local/share/fcitx5/addon/vocotype.conf
   ```

2. 检查 Fcitx 5 日志：
   ```bash
   fcitx5 --verbose=10
   ```

### 语音识别无响应

**问题**: F9 按键无反应或识别失败

**解决方案**:
1. 检查 Backend 是否运行：
   ```bash
   pgrep -fa fcitx5_server.py
   ```

2. 测试 IPC 连接：
   ```bash
   echo '{"type":"ping"}' | nc -U /tmp/vocotype-fcitx5.sock
   # 应返回: {"pong":true}
   ```

3. 重新配置音频设备：
   ```bash
   ~/.local/share/vocotype-fcitx5/.venv/bin/python scripts/setup-audio.py
   ```

### Rime 拼音不可用

**问题**: 只有语音输入，没有拼音功能

**解决方案**:
1. 检查 pyrime 是否安装：
   ```bash
   ~/.local/share/vocotype-fcitx5/.venv/bin/python -c "import pyrime"
   ```

2. 如果未安装，重新安装完整版：
   ```bash
   cd vocotype-cli
   ~/.local/share/vocotype-fcitx5/.venv/bin/pip install -e ".[full]"
   ```

3. 检查 Rime 数据目录：
   ```bash
   ls /usr/share/rime-data/
   ```

## 与 IBus 版本的区别

| 特性 | IBus 版本 | Fcitx 5 版本 |
|-----|----------|-------------|
| 输入法框架 | IBus | Fcitx 5 |
| 实现语言 | 纯 Python | C++ + Python (IPC) |
| Rime 配置 | `~/.config/ibus/rime/` | 共享同一目录 |
| 安装位置 | `~/.local/share/vocotype/` | `~/.local/share/vocotype-fcitx5/` |
| 后台服务 | 集成在引擎内 | 独立 Python 进程 |

两个版本**可以同时安装**，互不干扰。

## 卸载

```bash
# 停止并禁用服务
systemctl --user stop vocotype-fcitx5-backend.service
systemctl --user disable vocotype-fcitx5-backend.service

# 删除文件
rm -rf ~/.local/share/vocotype-fcitx5
rm ~/.local/lib/fcitx5/vocotype.so
rm ~/.local/share/fcitx5/addon/vocotype.conf
rm ~/.local/share/fcitx5/inputmethod/vocotype.conf.in
rm ~/.local/bin/vocotype-fcitx5-backend
rm ~/.config/systemd/user/vocotype-fcitx5-backend.service

# 重启 Fcitx 5
fcitx5 -r
```

## 技术细节

### 代码复用

Fcitx 5 版本大量复用 IBus 版本的代码：

- **语音识别**: 100% 复用 `app/funasr_server.py`
- **Rime 集成**: 90% 复用 `ibus/engine.py` 的 Rime 逻辑
- **音频采集**: 80% 复用录音逻辑

### IPC 协议

C++ Addon 与 Python Backend 通过 Unix Socket 通信，协议格式为 JSON：

**语音识别请求**:
```json
{"type": "transcribe", "audio_path": "/tmp/xxx.wav"}
```

**Rime 按键请求**:
```json
{"type": "key_event", "keyval": 97, "mask": 0}
```

详见：[fcitx5-with-rime-integration.md](../.claude/plans/fcitx5-with-rime-integration.md)

## 开发

### 重新编译 C++ Addon

```bash
cd fcitx5/addon/build
make -j$(nproc)
make install
fcitx5 -r
```

### 调试 Python Backend

```bash
# 前台运行，查看详细日志
~/.local/share/vocotype-fcitx5/.venv/bin/python \
    ~/.local/share/vocotype-fcitx5/backend/fcitx5_server.py --debug
```

### 测试 IPC 通信

```bash
# Ping 测试
echo '{"type":"ping"}' | nc -U /tmp/vocotype-fcitx5.sock

# Rime 按键测试（'a' 键）
echo '{"type":"key_event","keyval":97,"mask":0}' | nc -U /tmp/vocotype-fcitx5.sock
```

## 许可证

与主项目相同 (GPL)

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**相关文档**:
- [IBus 版本 README](../readme.md)
- [Rime 配置指南](../RIME_CONFIG_GUIDE.md)
- [实现计划](../.claude/plans/fcitx5-with-rime-integration.md)
