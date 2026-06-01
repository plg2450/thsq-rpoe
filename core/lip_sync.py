"""唇形同步模块 - 使用 SadTalker"""

import os
import subprocess
import sys
import glob
from config import FFMPEG_PATH, MODELS_DIR


class LipSyncer:
    """唇形同步处理器"""

    def __init__(self):
        self.sadtalker_dir = os.path.join(MODELS_DIR, "SadTalker")
        self.checkpoints_dir = os.path.join(self.sadtalker_dir, "checkpoints")
        self.model_256 = os.path.join(self.checkpoints_dir, "SadTalker_V0.0.2_256.safetensors")

    def is_model_ready(self) -> bool:
        """检查模型是否已下载"""
        return os.path.exists(self.model_256)

    def sync(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        使用 SadTalker 执行唇形同步

        参数:
            video_path: 输入视频路径（需要有人脸）
            audio_path: 输入音频路径
            output_path: 输出视频路径

        返回:
            输出视频路径
        """
        if not self.is_model_ready():
            raise Exception(
                f"SadTalker 模型未下载，请运行下载脚本或手动下载模型到:\n"
                f"{self.checkpoints_dir}"
            )

        result_dir = os.path.join(os.path.dirname(output_path), "sadtalker_results")
        os.makedirs(result_dir, exist_ok=True)

        # 使用 SadTalker 的 inference.py
        cmd = [
            sys.executable,
            os.path.join(self.sadtalker_dir, "inference.py"),
            "--driven_audio", audio_path,
            "--source_image", video_path,
            "--result_dir", result_dir,
            "--checkpoint_dir", self.checkpoints_dir,
            "--size", "256",
            "--still",
            "--preprocess", "crop",
        ]

        # 设置环境变量
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = "0"
        env["PYTHONPATH"] = self.sadtalker_dir

        print(f"开始唇形同步...")
        print(f"命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            encoding='utf-8', errors='replace',
            cwd=self.sadtalker_dir,
            env=env
        )

        if result.returncode != 0:
            print(f"SadTalker 输出: {result.stdout[-500:] if result.stdout else ''}")
            print(f"SadTalker 错误: {result.stderr[-500:] if result.stderr else ''}")

        # 查找输出的视频文件
        mp4_files = glob.glob(os.path.join(result_dir, "**/*.mp4"), recursive=True)
        if mp4_files:
            latest = max(mp4_files, key=os.path.getmtime)
            if latest != output_path:
                import shutil
                shutil.move(latest, output_path)
            return output_path

        # 也检查 result_dir 直接目录
        mp4_files = glob.glob(os.path.join(result_dir, "*.mp4"))
        if mp4_files:
            latest = max(mp4_files, key=os.path.getmtime)
            if latest != output_path:
                import shutil
                shutil.move(latest, output_path)
            return output_path

        error_msg = result.stderr[-500:] if result.stderr else "未找到输出文件"
        raise Exception(f"唇形同步失败: {error_msg}")

    def sync_with_fallback(self, video_path: str, audio_path: str, output_path: str) -> str:
        """
        唇形同步，如果模型不可用则回退到音轨替换
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
