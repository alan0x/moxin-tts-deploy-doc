import multiprocessing
import os
import sys
import typing
from pathlib import Path

if __name__ == '__main__':
    if hasattr(sys, '_voice_dialogue_started'):
        sys.exit(0)
    sys._voice_dialogue_started = True

    # 设置multiprocessing启动方法为spawn，避免fork问题
    if hasattr(multiprocessing, 'set_start_method'):
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            pass

    # Pyinstaller 多进程支持
    multiprocessing.freeze_support()

    # 禁用各种可能导致多进程问题的并行处理
    os.environ.update({
        "TOKENIZERS_PARALLELISM": "false",
        # "OMP_NUM_THREADS": "1",
        # "MKL_NUM_THREADS": "1", 
        # "NUMEXPR_NUM_THREADS": "1",
        # "OPENBLAS_NUM_THREADS": "1",
        # "VECLIB_MAXIMUM_THREADS": "1",
        # "BLIS_NUM_THREADS": "1",
        # # 禁用huggingface的多进程
        # "HF_HUB_DISABLE_PROGRESS_BARS": "1",
        # "TRANSFORMERS_NO_ADVISORY_WARNINGS": "1",
        # # 禁用torch的多进程
        # "TORCH_NUM_THREADS": "1",
        # "PYTORCH_JIT": "0",
        # # 禁用joblib的loky后端，使用threading
        # "JOBLIB_START_METHOD": "threading",
        # "SKLEARN_JOBLIB_START_METHOD": "threading",
    })

HERE = Path(__file__).parent
lib_path = HERE / "src"
if lib_path.exists() and lib_path.as_posix() not in sys.path:
    sys.path.insert(0, lib_path.as_posix())

from voice_dialogue.core.launcher import launch_system
from voice_dialogue.core.launcher import launch_text_mode
from voice_dialogue.core.constants import set_debug_mode
from voice_dialogue.cli.args import create_argument_parser
from voice_dialogue.api.server import launch_api_server

language: typing.Literal['zh', 'en'] = 'en'


def main():
    """
    主程序入口函数

    根据命令行参数选择启动模式：
    - cli: 启动命令行语音对话系统
    - api: 启动HTTP API服务器
    """
    parser = create_argument_parser()
    args = parser.parse_args()

    set_debug_mode(args.debug)

    print(f"""
{"=" * 80}
VoiceDialogue - 语音对话系统
{"=" * 80}
运行模式: {args.mode.upper()}
调试模式: {'启用' if args.debug else '禁用'}
{"=" * 80}
    """)

    try:
        if args.mode == 'cli':
            print(f"语言设置: {args.language}")
            print(f"说话人: {args.speaker}")
            print("正在启动命令行语音对话系统...")
            launch_system(args.language, args.speaker, args.disable_echo_cancellation)

        elif args.mode == 'api':
            launch_api_server(
                host=args.host,
                port=args.port,
                reload=args.reload
            )

        elif args.mode == 'text':
            # 新增：纯文本对话模式
            launch_text_mode(args.language, args.speaker)

    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序运行出错: {e}")
        raise


if __name__ == '__main__':
    main()
