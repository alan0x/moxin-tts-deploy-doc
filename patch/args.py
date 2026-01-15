"""
命令行参数处理模块

提供命令行参数解析和配置功能
"""

import argparse

from voice_dialogue.config.speaker_config import update_argument_parser_speaker_choices


def create_argument_parser():
    """创建命令行参数解析器"""
    # 动态获取可用说话人列表
    available_speakers = update_argument_parser_speaker_choices()

    parser = argparse.ArgumentParser(
        description="VoiceDialogue - 语音对话系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例用法:
  # 启动命令行模式（默认）
  python main.py

  # 启动命令行模式并指定参数
  python main.py --mode cli --language zh --speaker 沈逸

  # 启动API服务器
  python main.py --mode api

  # 启动API服务器并指定端口
  python main.py --mode api --port 9000

  # 启动API服务器并启用热重载（开发模式）
  python main.py --mode api --port 8000 --reload

支持的说话人:
  {', '.join(available_speakers)}
        """
    )

    # 运行模式选择
    parser.add_argument(
        '--mode', '-m',
        choices=['cli', 'api', 'text'],
        default='cli',
        help='运行模式: cli=命令行模式, api=API服务器模式, text=文本模式 (默认: cli)'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='启动debug模式'
    )

    # 命令行模式参数
    cli_group = parser.add_argument_group('命令行模式参数')
    cli_group.add_argument(
        '--language', '-l',
        choices=['zh', 'en'],
        default='zh',
        help='用户语言: zh=中文, en=英文 (默认: zh)'
    )
    cli_group.add_argument(
        '--speaker', '-s',
        choices=available_speakers,
        default='沈逸' if '沈逸' in available_speakers else (available_speakers[0] if available_speakers else '沈逸'),
        help='TTS说话人 (默认: 沈逸)'
    )
    cli_group.add_argument(
        '--disable-echo-cancellation',
        action='store_true',
        default=False,
        help='禁用回声消除功能 (默认: 不禁用)'
    )

    # API服务器模式参数
    api_group = parser.add_argument_group('API服务器模式参数')
    api_group.add_argument(
        '--host',
        default='0.0.0.0',
        help='服务器主机地址 (默认: 0.0.0.0)'
    )
    api_group.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='服务器端口 (默认: 8000)'
    )
    api_group.add_argument(
        '--reload',
        action='store_true',
        help='启用热重载（开发模式）'
    )

    # 新增文本模式参数组
    text_group = parser.add_argument_group('文本模式参数')

    return parser
