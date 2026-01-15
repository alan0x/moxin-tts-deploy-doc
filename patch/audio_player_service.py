import time
from multiprocessing import Queue
from queue import Empty
from typing import Optional

from voice_dialogue.audio.player import play_audio
from voice_dialogue.core.base import BaseThread
from voice_dialogue.core.constants import voice_state_manager, silence_over_threshold_event
from voice_dialogue.models.voice_task import VoiceTask, AnswerDisplayMessage
from voice_dialogue.services.mixins import TaskStatusMixin, HistoryMixin, PerformanceLogMixin
from voice_dialogue.utils.logger import logger


class AudioPlayerService(BaseThread, TaskStatusMixin, HistoryMixin, PerformanceLogMixin):
    """音频流播放器 - 负责播放生成的音频并管理播放状态"""

    def __init__(
            self, group=None, target=None, name=None, args=(), kwargs={}, *, daemon=None,
            audio_playing_queue: Queue,
            websocket_message_queue: Queue = None,
            skip_event_wait: bool = False,  # ← 新增参数
    ):
        super().__init__(group, target, name, args, kwargs, daemon=daemon)
        self.audio_playing_queue: Queue = audio_playing_queue
        self.websocket_message_queue: Queue = websocket_message_queue
        self.skip_event_wait = skip_event_wait

    def _get_task_from_queue(self) -> Optional[VoiceTask]:
        """从音频播放队列中获取任务。"""
        # 使用阻塞式获取，当队列为空时，run循环中的Empty异常会处理它
        return self.audio_playing_queue.get(block=True, timeout=1)

    def _process_task(self, voice_task: VoiceTask):
        """处理单个音频播放任务。"""
        # 这个内部循环用于等待一个外部事件（用户静音），同时检查任务是否被中断
        while not self.is_exited:
            if self.handle_user_speaking_interruption(voice_task):
                return  # 任务被中断，结束处理

            if not self.is_task_valid(voice_task):
                logger.info(f"音频播放: 任务<{voice_task.id}> 无效")
                return  # 任务无效，结束处理

            if not self.skip_event_wait:  # ← 新增判断
                if not silence_over_threshold_event.is_set():
                    time.sleep(0.05)
                    continue

            # 等待用户彻底静音的信号
            if not silence_over_threshold_event.is_set():
                time.sleep(0.05)  # 短暂等待，避免CPU空转
                continue

            # --- 开始播放逻辑 ---
            if self.websocket_message_queue:
                self.websocket_message_queue.put_nowait(
                    AnswerDisplayMessage(
                        session_id=voice_task.session_id,
                        task_id=voice_task.id,
                        answer_index=voice_task.answer_index,
                        answer=voice_task.answer_sentence,
                    )
                )

            self.log_task_performance(voice_task, "音频播放")

            self.update_chat_history(voice_task)

            voice_state_manager.set_audio_playing(voice_task.id)
            voice_state_manager.reset_task_id()

            if not self.is_stopped:
                audio_data, sample_rate = voice_task.tts_generated_sentence_audio
                play_audio(audio_data, sample_rate)

            # 任务处理完毕，跳出内部循环
            break

    def run(self):
        """
        主运行循环。
        不断从队列获取任务，并调用_process_task进行处理。
        """
        if not hasattr(self, 'is_ready'):
            logger.warning(f"{self.__class__.__name__} 中缺少 'is_ready' 属性。")

        self.is_ready = True

        while not self.is_exited:
            try:
                task = self._get_task_from_queue()
                if task:
                    self._process_task(task)

            except Empty:
                # 队列在1秒内没有新项目，这是正常现象，继续循环
                continue
            except Exception as e:
                logger.error(f"在 AudioStreamPlayer 环节发生错误: {e}")
                time.sleep(0.1)  # 发生未知错误时短暂休眠
