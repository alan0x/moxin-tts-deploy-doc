"""
语音对话系统启动器

负责启动和协调语音对话系统的所有组件
"""

import time

from voice_dialogue.audio.capture import AudioCapture
from voice_dialogue.config.speaker_config import get_tts_config_by_speaker_name, get_available_speaker_names
from voice_dialogue.core.constants import (
    audio_frames_queue,
    user_voice_queue,
    transcribed_text_queue,
    text_input_queue,
    audio_output_queue,
    session_manager
)
from voice_dialogue.services import ASRService, LLMService, AudioPlayerService, SpeechStateMonitor, TTSAudioGenerator
from voice_dialogue.utils.logger import logger

import uuid
from queue import Empty
from voice_dialogue.models.voice_task import VoiceTask

from voice_dialogue.core.constants import silence_over_threshold_event


def launch_system(
        user_language: str,
        speaker: str,
        disable_echo_cancellation: bool = False,
) -> None:
    """
    启动完整的语音对话系统

    该函数负责启动并协调语音对话系统的所有组件，包括音频采集、语音识别、
    文本生成、语音合成和音频播放等功能模块。系统采用多线程架构，各组件
    通过队列进行数据传递和通信。

    系统工作流程：
    1. 音频采集：EchoCancellingAudioCapture 采集用户语音并进行回声消除
    2. 语音监测：SpeechStateMonitor 检测用户是否在说话
    3. 语音识别：ASRWorker 将用户语音转换为文本
    4. 文本生成：LLMResponseGenerator 基于用户问题生成AI回答
    5. 语音合成：TTSAudioGenerator 将AI回答转换为语音
    6. 音频播放：AudioStreamPlayer 播放生成的语音

    Args:
        user_language (str): 用户语言，支持 'zh'（中文）和 'en'（英文）
        speaker (str): 语音合成使用的说话人，支持：
                      '罗翔', '马保国', '沈逸', '杨幂', '周杰伦', '马云'

    Raises:
        ValueError: 当指定的说话人不在支持列表中时抛出异常

    Returns:
        None: 函数会一直运行直到所有线程结束

    Note:
        该函数会阻塞运行，直到系统被外部停止或发生异常
    """
    # 导入speaker配置相关功能

    threads = []

    # 语音识别
    asr_worker = ASRService(
        user_voice_queue=user_voice_queue,
        transcribed_text_queue=transcribed_text_queue,
        language=user_language
    )
    asr_worker.daemon = True
    asr_worker.start()
    threads.append(asr_worker)

    # 文本生成
    text_generator = LLMService(
        user_question_queue=transcribed_text_queue,
        generated_answer_queue=text_input_queue
    )
    text_generator.daemon = True
    text_generator.start()
    threads.append(text_generator)

    # 动态获取TTS配置
    tts_speaker_config = get_tts_config_by_speaker_name(speaker)
    if tts_speaker_config is None:
        # 如果找不到指定说话人，列出所有可用说话人并抛出异常
        available_speakers = get_available_speaker_names()
        raise ValueError(f"不支持的TTS说话人: {speaker}。可用说话人: {', '.join(available_speakers)}")

    # 语音合成
    audio_generator = TTSAudioGenerator(
        text_input_queue=text_input_queue,
        audio_output_queue=audio_output_queue,
        tts_config=tts_speaker_config
    )
    audio_generator.daemon = True
    audio_generator.start()
    threads.append(audio_generator)

    # 音频播放
    audio_player = AudioPlayerService(audio_playing_queue=audio_output_queue)
    audio_player.daemon = True
    audio_player.start()
    threads.append(audio_player)

    # 语音状态监测
    enable_vad = disable_echo_cancellation
    speech_monitor = SpeechStateMonitor(
        audio_frame_queue=audio_frames_queue,
        user_voice_queue=user_voice_queue,
        enable_vad=enable_vad
    )
    speech_monitor.daemon = True
    speech_monitor.start()
    threads.append(speech_monitor)

    # 音频采集
    enable_echo_cancellation = not disable_echo_cancellation
    audio_capture = AudioCapture(
        audio_frames_queue=audio_frames_queue,
        enable_echo_cancellation=enable_echo_cancellation
    )
    audio_capture.daemon = True
    audio_capture.start()
    threads.append(audio_capture)

    # 等待所有线程准备就绪
    while not all([thread.is_ready for thread in threads]):
        print(f"等待所有服务启动, 当前状态: " + ", ".join([f"{thread.__class__.__name__}: {'就绪' if thread.is_ready else '未就绪'}" for thread in threads]))
        time.sleep(5)

    logger.info(
        f'\n'
        f"┌──────────────────────────────────────────┐\n"
        f"│                                          │\n"
        f"│             🚀 服务启动成功 🚀             │\n"
        f"│                                          │\n"
        f"└──────────────────────────────────────────┘"
    )

    # 等待所有线程结束
    for thread in threads:
        thread.join()


def launch_text_mode(user_language: str, speaker: str):
    """
    启动纯文本对话模式（无需麦克风）
    
    工作流程：
    1. 启动 LLMService - 生成AI回答
    2. 启动 TTSAudioGenerator - 文本转语音
    3. 启动 AudioPlayerService - 播放音频
    4. 主线程循环：等待用户输入 → 显示回答 → 播放语音
    """
    silence_over_threshold_event.set()  # 立即设置为 True
    
    # 1. 启动 LLMService
    text_generator = LLMService(
        user_question_queue=transcribed_text_queue,
        generated_answer_queue=text_input_queue
    )
    text_generator.daemon = True
    text_generator.start()
    
    # 2. 获取 TTS 配置
    tts_config = get_tts_config_by_speaker_name(speaker)
    
    # 3. 启动 TTS 服务
    audio_generator = TTSAudioGenerator(
        text_input_queue=text_input_queue,
        audio_output_queue=audio_output_queue,
        tts_config=tts_config
    )
    audio_generator.daemon = True
    audio_generator.start()
    
    # 4. 启动音频播放服务
    audio_player = AudioPlayerService(audio_playing_queue=audio_output_queue, skip_event_wait=True)  # ← 新增参数：纯文本模式跳过事件等待
    audio_player.daemon = True
    audio_player.start()

    # 启动 SpeechStateMonitor（不需要麦克风，只需要设置 silence_over_threshold_event）
    speech_monitor = SpeechStateMonitor(
        audio_frame_queue=audio_frames_queue,  # 虽然不用，但需要传入
        user_voice_queue=user_voice_queue,     # 虽然不用，但需要传入
        enable_vad=False
    )
    speech_monitor.daemon = True
    speech_monitor.start()
    
    # 5. 等待服务就绪
    while not all([text_generator.is_ready, audio_generator.is_ready, audio_player.is_ready]):
        time.sleep(1)
    
    # 6. 主线程交互循环
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║              🚀 VoiceDialogue - 纯文本对话模式 🚀                 ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    while True:
        user_input = input("\n请输入文字（输入 quit 退出）:\n> ").strip()
        
        if user_input.lower() == 'quit':
            print("再见！")
            break
        
        if not user_input:
            continue
        
        # 创建任务
        voice_task = VoiceTask(
            id=str(uuid.uuid4()),
            session_id=session_manager.current_id,
            language=user_language,
            transcribed_text=user_input
        )
        
        # 放入队列
        transcribed_text_queue.put(voice_task.model_copy())
        
        # 等待 LLM 生成回答
        try:
            result_task = text_input_queue.get(timeout=30)
            print(f"\n{'='*60}")
            print(f"AI 回复:")
            print(f"{'='*60}")
            print(result_task.answer_sentence)
            print(f"{'='*60}\n")
        except Empty:
            print("生成回答超时")