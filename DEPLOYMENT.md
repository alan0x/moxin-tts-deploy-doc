# Moxin-TTS 部署指南

本指南基于实际部署经验整理，包含所有常见问题的解决方案。

## 🎯 核心功能

- **ASR**: 语音识别 (FunASR 中文/Whisper 多语言)
- **LLM**: 大语言模型对话 (Qwen/LLaMA)
- **TTS**: 文本转语音 (MoYoYo 多音色克隆)
- **语音对话**: 实时语音交互系统

## 📋 系统要求

### 最低配置

- **Python**: 3.11+ (必需)
- **内存**: 8GB RAM (推荐 16GB)
- **存储**: 15GB+ 可用空间
- **音频**: 麦克风+扬声器
- **网络**: 稳定网络连接

### 推荐配置

- **CPU**: 8 核心+
- **GPU**: NVIDIA GPU (可选，加速推理)
- **内存**: 16GB+ RAM
- **存储**: SSD 硬盘

## ⚡ 快速部署 (完整流程)

### 1. 安装 uv 包管理器

**Windows (PowerShell 管理员模式):**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 重新加载shell配置
```

### 2. 下载项目

```bash
git clone <repository_url>
cd Moxin-TTS
```

### 3. 安装依赖

```bash
# 安装核心依赖
uv sync

# 下载必需的NLTK资源 (必须执行!)
uv run python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"
```

> **⚠️ 重要**: NLTK 资源下载失败会导致系统无法启动

### 4. 模型文件准备

#### A. LLM 模型 (对话功能必需)

```bash
# 下载Qwen模型 (约6GB)
# 方法1: 从HuggingFace下载
# 需要手动下载 Qwen3-8B-Q6_K.gguf 放到 assets/models/llm/qwen 目录

# 方法2: 使用modelscope (中国用户推荐)
uv add modelscope
uv run python -c "
from modelscope import snapshot_download
snapshot_download('Qwen/Qwen2.5-7B-Instruct-GGUF',
                 cache_dir='assets/models/llm/qwen',
                 allow_file_pattern=['*q6_k.gguf'])
"
```

#### B. ASR 语音识别模型 (必需)

```bash
# 下载 FunASR 模型 (约1GB)
# 使用自动下载脚本
uv run python scripts/download_funasr_models.py
```

模型包含：

- **ASR 主模型**: speech_seaco_paraformer_large (语音识别)
- **标点模型**: punc_ct-transformer (标点恢复)

> **⚠️ 注意**: 如果下载失败，请检查网络连接或手动从 [ModelScope](https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch) 下载

#### C. TTS 语音模型 (已内置)

- MoYoYo TTS 模型已预装在 `assets/models/tts/moyoyo/`
- 包含 12 个中英文音色：罗翔、杨幂、周杰伦、马云等

### 5. 运行系统

#### 推荐: CLI 模式 (最稳定)

```bash
# 基础运行
uv run python main.py --mode cli --language zh --speaker "罗翔"

# Windows用户必需: 禁用回声消除
uv run python main.py --mode cli --language zh --speaker "罗翔" --disable-echo-cancellation
```

#### API 服务器模式

```bash
uv run python main.py --mode api --port 8000
# 访问: http://localhost:8000/docs
```

## 🔧 常见问题解决

### 1. 依赖冲突问题

**症状**: `uv sync` 失败，提示平台依赖冲突

**解决**: pyproject.toml 中的 macOS 依赖在 Windows 上冲突

```toml
# 检查 pyproject.toml 中是否有类似配置
[tool.uv.sources]
pywhispercpp = { git = "...", markers = "sys_platform == 'darwin'" }
```

### 2. NLTK 资源缺失

**症状**: 启动时报错 `Resource punkt not found`

**解决**:

```bash
uv run python -c "
import nltk
nltk.download('punkt')
nltk.download('punkt_tab')
print('NLTK resources downloaded successfully')
"
```

### 3. 回声消除错误 (Windows)

**症状**: `加载 AEC 动态库失败: argument of type 'WindowsPath' is not iterable`

**解决**: 使用禁用回声消除参数

```bash
uv run python main.py --mode cli --language zh --speaker "罗翔" --disable-echo-cancellation
```

### 4. 音频设备错误

**症状**: `[Errno -9996] Invalid input device (no default output device)`

**原因**: 系统未检测到麦克风或音响设备

**解决**:

1. 检查 Windows 音频设备设置
2. 确保麦克风权限已授予 Python 应用
3. 重启音频服务: `net stop audiosrv && net start audiosrv`

### 5. ASR 引擎注册失败

**症状**: `RuntimeError: TTS模型 'whisper' 未注册`

**原因**: API 模式默认使用 whisper，但 whisper 模块未安装

**解决**: CLI 模式使用 funasr（已预装），更稳定

```bash
# 使用CLI模式避免此问题
uv run python main.py --mode cli --language zh --speaker "罗翔" --disable-echo-cancellation
```

### 6. TTS 模型加载问题

**症状**: `Failed to import TTS module kokoro: No module named 'kokoro_onnx'`

**说明**: 这是 warning，不影响使用。MoYoYo TTS 引擎正常工作。

### 7. LLM 模型文件缺失

**症状**: 系统启动后卡住，无法进行对话

**解决**: 下载对应的 LLM 模型文件到正确目录

```bash
# 检查模型文件是否存在
ls assets/models/llm/
# 应该包含 .gguf 格式的模型文件
```

### 8. PyTorch 权重加载警告

**症状**: `torch.load` 安全警告

**解决**: 已修复，使用 `weights_only=True` 参数

## 🎨 测试 TTS 功能

如果只想测试文本转语音功能（无需 LLM 模型）:

```bash
# 创建测试脚本
cat > test_tts.py << 'EOF'
import sys
sys.path.insert(0, 'src')
from voice_dialogue.tts import tts_config_registry, tts_manager

# 获取可用音色
configs = tts_config_registry.get_all_configs()
print("可用音色:", [c.character_name for c in configs if c.is_model_complete()])

# 选择罗翔音色测试
config = next(c for c in configs if "Luo Xiang" in c.character_name)
tts = tts_manager.create_tts(config)
tts.setup()
tts.warmup()

# 生成语音
text = "你好，这是TTS测试。"
audio_data, sample_rate = tts.synthesize(text)

# 保存音频
import soundfile as sf
sf.write("test_output.wav", audio_data, sample_rate)
print("音频已保存到 test_output.wav")
EOF

# 运行测试
uv run python test_tts.py
```

## 🚀 生产部署建议

### 1. 系统优化

- 使用 SSD 存储模型文件
- 配置足够的交换内存
- 关闭不必要的后台程序

### 2. 安全配置

- API 模式下配置防火墙规则
- 使用反向代理 (nginx)
- 启用 HTTPS

### 3. 监控告警

- 监控内存使用率
- 监控模型加载状态
- 配置日志轮转

## 📁 目录结构

```
Moxin-TTS/
├── assets/
│   ├── models/
│   │   ├── tts/moyoyo/          # TTS语音模型
│   │   └── llm/                 # LLM对话模型
│   └── libraries/               # 平台相关库文件
├── src/voice_dialogue/          # 核心代码
├── tests/                       # 测试文件
├── main.py                      # 主入口
└── pyproject.toml              # 依赖配置
```

## 🆘 获取帮助

启动问题检查清单：

1. ✅ Python 3.11+ 版本
2. ✅ uv 包管理器安装成功
3. ✅ NLTK 资源下载完成
4. ✅ 音频设备正常工作
5. ✅ 防火墙允许网络访问
6. ✅ 足够的磁盘空间和内存

如果问题仍然存在，请检查终端错误日志并对照本指南中的解决方案。

## 📋 版本兼容性

- **Python**: 3.11, 3.12 (测试通过)
- **操作系统**: Windows 10/11, macOS 12+, Ubuntu 20.04+
- **依赖管理**: uv 0.1.0+ (推荐) 或 pip

## 🎯 最终说明

### 项目状态

- ✅ **TTS 功能**: 完全正常，支持 12 种音色
- ✅ **ASR 功能**: FunASR 中文识别正常
- ⚠️ **音频设备**: 需要正确配置麦克风/扬声器
- 📋 **LLM 模型**: 需要手动下载约 6GB 模型文件用于对话

### 成功运行的命令

```bash
# Windows用户推荐命令
uv run python main.py --mode cli --language zh --speaker "罗翔" --disable-echo-cancellation

# 仅测试TTS功能
uv run python test_tts.py
```

### Q&A

- llama_context: n_ctx_per_seq (2048) < n_ctx_train (40960) -- the full capacity of the model will not be utilized

  模型支持 40960 上下文，但当前设置为 2048，可能会导致性能下降。建议调整 n_ctx_per_seq 至 4096 或更高以充分利用模型能力。
  但更短的上下文更节省显存

本指南涵盖了实际部署中遇到的所有问题和解决方案，按此指南操作可确保在新机器上成功部署。
