"""唇形同步模块 - 使用 Wav2Lip"""

import os
import subprocess
import tempfile
from config import FFMPEG_PATH, MODELS_DIR


class LipSyncer:
    """唇形同步处理器"""

    def __init__(self):
        self.wav2lip_dir = os.path.join(MODELS_DIR, "Wav2Lip")
        self.model_path = os.path.join(self.wav2lip_dir, "checkpoints", "wav2lip_gan.pth")
        self.face_detection_dir = os.path.join(self.wav2lip_dir, "face_detection")

    def is_model_ready(self) -> bool:
        """检查模型是否已下载"""
        return os.path.exists(self.model_path)

    def sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        执行唇形同步

        参数:
            video_path: 输入视频路径
            audio_path: 输入音频路径
            output_path: 输出视频路径

        返回:
            输出视频路径
        """
        if not self.is_model_ready():
            raise Exception(
                f"Wav2Lip 模型未下载，请将 wav2lip_gan.pth 放到:\n"
                f"{os.path.join(self.wav2lip_dir, 'checkpoints', '')}"
            )

        # 使用 Wav2Lip 的 inference.py
        cmd = [
            "python",
            os.path.join(self.wav2lip_dir, "inference.py",
            "--checkpoint_path", self.model_path,
            "--face", video_path,
            "--audio", audio_path,
            "--outfile", output_path,
            "--nosmooth"  # 加速处理
        ]

        # 设置环境变量
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = "0"  # 使用第一块GPU

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            cwd=self.wav2lip_dir,
            env=env
        )

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
            error_msg = result.stderr[-500:] if result.stderr else "未知错误"
            raise Exception(f"唇形同步失败: {error_msg}")

        return output_path

    def sync_with_fallback(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        唇形同步，如果模型不可用则回退到音轨替换

        参数:
            video_path: 输入视频路径
            audio_path: 输入音频路径
            output_path: 输出视频路径

        返回:
            输出视频路径
        """
        if self.is_model_ready():
            try:
                return self.sync(video_path, audio_path, output_path)
            except Exception as e:
                print(f"唇形同步失败，回退到音轨替换: {e}")

        # 回退到简单的音轨替换
        return self._replace_audio(video_path, audio_path, output_path)

    def _replace_audio(self, video_path: str, audio_path: str, output_path: str) -> str:
        """简单的音轨替换（占位方案）"""
        cmd = [
            FFMPEG_PATH, "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            output_path
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding='utf-8', errors='replace'
        )

        if not os.path.exists(output_path) or os.path.getsize(output_path) < 100:
            error_msg = result.stderr[-500:] if result.stderr else "未知错误"
            raise Exception(f"音轨替换失败: {error_msg}")

        return output_path
