"""音频后处理模块 - 变速、变调、音量调节"""

import os


class AudioProcessor:
    """音频处理器"""

    @staticmethod
    def adjust_speed(audio_path: str, speed: float, output_path: str) -> str:
        """
        调整音频速度

        参数:
            audio_path: 输入音频路径
            speed: 速度倍率 (0.5 - 2.0)
            output_path: 输出音频路径
        """
        if speed == 1.0:
            return audio_path

        try:
            from pydub import AudioSegment
            from pydub.effects import speedup

            audio = AudioSegment.from_file(audio_path)

            # pydub的speedup方法
            if speed > 1.0:
                # 加速：使用chunks和crossfade
                chunk_length = int(len(audio) * 0.1)
                if chunk_length < 100:
                    chunk_length = 100
                adjusted = speedup(audio, speed, chunk_length=chunk_length)
            else:
                # 减速：通过拉伸实现
                # pydub没有直接的slowdown，使用简单的重复采样
                samples = audio.get_array_of_samples()
                new_length = int(len(samples) / speed)

                # 简单的重采样
                import numpy as np
                new_samples = np.interp(
                    np.linspace(0, len(samples) - 1, new_length),
                    np.arange(len(samples)),
                    samples
                )

                # 创建新的音频段
                from pydub import AudioSegment
                adjusted = AudioSegment(
                    new_samples.tobytes(),
                    frame_rate=audio.frame_rate,
                    sample_width=audio.sample_width,
                    channels=audio.channels
                )

            # 导出
            ext = os.path.splitext(output_path)[1].lower()
            if ext == '.mp3':
                adjusted.export(output_path, format='mp3', bitrate='192k')
            else:
                adjusted.export(output_path, format='wav')

            return output_path

        except ImportError:
            print("pydub未安装，跳过速度调整")
            return audio_path
        except Exception as e:
            print(f"速度调整失败: {e}")
            return audio_path

    @staticmethod
    def adjust_pitch(audio_path: str, semitones: int, output_path: str) -> str:
        """
        调整音频音调

        参数:
            audio_path: 输入音频路径
            semitones: 半音数 (-5 到 +5)
            output_path: 输出音频路径
        """
        if semitones == 0:
            return audio_path

        try:
            from pydub import AudioSegment
            import numpy as np

            audio = AudioSegment.from_file(audio_path)

            # 通过改变采样率来调整音调
            # 每个半音 = 2^(1/12) 的频率比
            factor = 2 ** (semitones / 12.0)

            # 改变采样率（这会同时改变速度和音调）
            new_frame_rate = int(audio.frame_rate * factor)

            # 使用numpy进行高质量重采样
            samples = np.array(audio.get_array_of_samples(), dtype=np.float64)

            # 计算新的样本数（保持时长不变）
            new_length = int(len(samples) / factor)

            # 重采样
            new_samples = np.interp(
                np.linspace(0, len(samples) - 1, new_length),
                np.arange(len(samples)),
                samples
            )

            # 创建新的音频段
            adjusted = AudioSegment(
                new_samples.astype(np.int16).tobytes(),
                frame_rate=audio.frame_rate,  # 保持原始采样率
                sample_width=audio.sample_width,
                channels=audio.channels
            )

            # 导出
            ext = os.path.splitext(output_path)[1].lower()
            if ext == '.mp3':
                adjusted.export(output_path, format='mp3', bitrate='192k')
            else:
                adjusted.export(output_path, format='wav')

            return output_path

        except ImportError:
            print("pydub未安装，跳过音调调整")
            return audio_path
        except Exception as e:
            print(f"音调调整失败: {e}")
            return audio_path

    @staticmethod
    def adjust_volume(audio_path: str, volume_percent: int, output_path: str) -> str:
        """
        调整音频音量

        参数:
            audio_path: 输入音频路径
            volume_percent: 音量百分比 (0 - 200)
            output_path: 输出音频路径
        """
        if volume_percent == 100:
            return audio_path

        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(audio_path)

            # 计算增益（dB）
            # 100% = 0dB, 50% = -6dB, 0% = -inf, 150% = +3.5dB, 200% = +6dB
            if volume_percent <= 0:
                gain_db = -100  # 静音
            else:
                gain_db = 20 * (volume_percent / 100 - 1)

            adjusted = audio + gain_db

            # 导出
            ext = os.path.splitext(output_path)[1].lower()
            if ext == '.mp3':
                adjusted.export(output_path, format='mp3', bitrate='192k')
            else:
                adjusted.export(output_path, format='wav')

            return output_path

        except ImportError:
            print("pydub未安装，跳过音量调整")
            return audio_path
        except Exception as e:
            print(f"音量调整失败: {e}")
            return audio_path

    @staticmethod
    def apply_all(audio_path: str, speed: float, pitch: int, volume: int, output_path: str) -> str:
        """
        应用所有音频处理

        参数:
            audio_path: 输入音频路径
            speed: 速度倍率 (0.5 - 2.0)
            pitch: 半音数 (-5 到 +5)
            volume: 音量百分比 (0 - 200)
            output_path: 输出音频路径
        """
        if speed == 1.0 and pitch == 0 and volume == 100:
            return audio_path

        # 创建临时文件
        temp_dir = os.path.dirname(output_path)
        temp_files = []

        current_path = audio_path

        # 处理顺序：速度 -> 音调 -> 音量
        if speed != 1.0:
            temp_path = os.path.join(temp_dir, 'temp_speed.wav')
            temp_files.append(temp_path)
            current_path = AudioProcessor.adjust_speed(current_path, speed, temp_path)

        if pitch != 0:
            temp_path = os.path.join(temp_dir, 'temp_pitch.wav')
            temp_files.append(temp_path)
            current_path = AudioProcessor.adjust_pitch(current_path, pitch, temp_path)

        if volume != 100:
            # 直接输出到最终路径
            current_path = AudioProcessor.adjust_volume(current_path, volume, output_path)
        else:
            # 复制到最终路径
            import shutil
            shutil.copy2(current_path, output_path)

        # 清理临时文件
        for temp_file in temp_files:
            if os.path.exists(temp_file) and temp_file != audio_path:
                try:
                    os.remove(temp_file)
                except OSError:
                    pass

        return output_path
