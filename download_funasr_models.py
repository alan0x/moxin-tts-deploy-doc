"""
下载 FunASR 模型脚本
用于自动下载 ASR 语音识别模型和标点恢复模型
"""

from pathlib import Path
from modelscope import snapshot_download


def download_funasr_models():
    """下载 FunASR 所需的所有模型"""
    
    # 创建目标目录
    base_dir = Path('assets/models/asr/funasr')
    base_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("开始下载 FunASR 模型...")
    print("=" * 70)
    
    # 1. 下载 ASR 主模型
    print("\n📥 [1/2] 下载 ASR 语音识别模型...")
    print("模型: speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch")
    
    asr_model_dir = base_dir / "speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
    
    try:
        # 只下载核心模型文件，跳过示例文件（避免Windows路径问题）
        snapshot_download(
            'iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
            cache_dir=str(asr_model_dir),
            revision='master',
            # 只下载必需的模型文件，排除示例文件
            allow_file_pattern=['*.yaml', '*.json', '*.pt', '*.mvn', 'seg_dict', 'tokens.json', 'README.md']
        )
        print(f"✅ ASR 模型下载完成: {asr_model_dir}")
    except Exception as e:
        print(f"❌ ASR 模型下载失败: {e}")
        raise
    
    # 2. 下载标点恢复模型
    print("\n📥 [2/2] 下载标点恢复模型...")
    print("模型: punc_ct-transformer_cn-en-common-vocab471067-large")
    
    punc_model_dir = base_dir / "punc_ct-transformer_cn-en-common-vocab471067-large"
    
    try:
        # 只下载核心模型文件，跳过示例文件（避免Windows路径问题）
        snapshot_download(
            'iic/punc_ct-transformer_cn-en-common-vocab471067-large',
            cache_dir=str(punc_model_dir),
            revision='master',
            # 只下载必需的模型文件，排除示例文件
            allow_file_pattern=['*.yaml', '*.json', '*.pt', '*.onnx', 'tokens.json', 'README.md', 'configuration.json']
        )
        print(f"✅ 标点模型下载完成: {punc_model_dir}")
    except Exception as e:
        print(f"❌ 标点模型下载失败: {e}")
        raise
    
    print("\n" + "=" * 70)
    print("🎉 所有 FunASR 模型下载完成！")
    print("=" * 70)
    print(f"\n模型存储位置: {base_dir.resolve()}")
    print("\n现在可以运行:")
    print("  uv run python main.py --mode cli --language zh --speaker \"罗翔\" --disable-echo-cancellation")


if __name__ == "__main__":
    download_funasr_models()
