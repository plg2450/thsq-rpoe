import os
import subprocess

from config import FFMPEG_PATH
os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + ";" + os.environ.get("PATH", "")


class Recognizer:
    def __init__(self):
        from funasr import AutoModel

        self.model = AutoModel(
            model="iic/speech_paraformer-large-vad-punc_asr_nat-zh-cn-16k-common-vocab8404-pytorch",
            vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
            punc_model="iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch",
        )

    def transcribe(self, audio_path: str) -> str:
        if audio_path.endswith('.mp4'):
            audio_path = self._extract_audio(audio_path)

        import soundfile as sf
        import numpy as np
        audio, sr = sf.read(audio_path)

        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        if sr != 16000:
            import scipy.signal
            audio = scipy.signal.resample(audio, int(len(audio) * 16000 / sr))

        audio = audio.astype(np.float32)
        result = self.model.generate(input=audio)
        text = result[0]["text"] if result else ""
        return text

    def _extract_audio(self, video_path: str) -> str:
        audio_path = video_path.rsplit('.', 1)[0] + '_audio.wav'

        cmd = [
            FFMPEG_PATH,
            "-y",
            "-i", video_path,
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", "16000",
            "-ac", "1",
            audio_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 100:
            error_msg = result.stderr[-500:] if result.stderr else "未知错误"
            if "does not contain any stream" in error_msg:
                raise FileNotFoundError("视频没有音频轨道，无法提取音频")
            raise FileNotFoundError(f"音频提取失败: {error_msg}")

        return audio_path


if __name__ == "__main__":
    rec = Recognizer()
    path = input("请输入音频/视频文件路径: ")
    text = rec.transcribe(path)
    print(f"识别结果:\n{text}")
