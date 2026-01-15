"""测试 ASR 模型路径是否正确"""
import sys
sys.path.insert(0, 'src')

from pathlib import Path
from voice_dialogue.config import paths

models_dir = paths.ASR_MODELS_PATH / "funasr"

print("=" * 70)
print("检查 FunASR 模型路径")
print("=" * 70)

print(f"\n基础目录: {models_dir}")
print(f"基础目录存在: {models_dir.exists()}")

# 检查第一个模型
asr_model_path = models_dir / "speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch" / "iic" / "speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
print(f"\nASR 模型路径: {asr_model_path}")
print(f"ASR 模型存在: {asr_model_path.exists()}")

if asr_model_path.exists():
    print(f"ASR 模型文件:")
    for file in sorted(asr_model_path.iterdir()):
        if file.is_file():
            size = file.stat().st_size / (1024 * 1024)  # MB
            print(f"  - {file.name} ({size:.2f} MB)")
else:
    print("❌ ASR 模型路径不存在!")
    # 尝试找到正确的路径
    base = models_dir / "speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
    print(f"\n尝试列出目录: {base}")
    if base.exists():
        for item in base.iterdir():
            print(f"  - {item.name}{'/' if item.is_dir() else ''}")

# 检查第二个模型
punc_model_path = models_dir / "punc_ct-transformer_cn-en-common-vocab471067-large" / "iic" / "punc_ct-transformer_cn-en-common-vocab471067-large"
print(f"\n标点模型路径: {punc_model_path}")
print(f"标点模型存在: {punc_model_path.exists()}")

if punc_model_path.exists():
    print(f"标点模型文件:")
    for file in sorted(punc_model_path.iterdir()):
        if file.is_file():
            size = file.stat().st_size / (1024 * 1024)  # MB
            print(f"  - {file.name} ({size:.2f} MB)")
else:
    print("❌ 标点模型路径不存在!")
    base = models_dir / "punc_ct-transformer_cn-en-common-vocab471067-large"
    print(f"\n尝试列出目录: {base}")
    if base.exists():
        for item in base.iterdir():
            print(f"  - {item.name}{'/' if item.is_dir() else ''}")

print("\n" + "=" * 70)
