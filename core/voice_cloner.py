import os
import base64
import json
import requests
from pathlib import Path

from config import MIMO_API_KEY, MIMO_BASE_URL, MIMO_TTS_MODEL


class VoiceCloner:
    def __init__(self):
        self.api_key = MIMO_API_KEY
        self.base_url = MIMO_BASE_URL
        self.model = MIMO_TTS_MODEL
        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _audio_to_data_url(self, audio_path: str) -> str:
        """将音频文件转换为DataURL格式"""
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        ext = Path(audio_path).suffix.lower()
        mime_type_map = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
        }
        mime_type = mime_type_map.get(ext, "audio/wav")

        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        return f"data:{mime_type};base64,{audio_base64}"

    def _decode_base64_audio(self, b64_data: str) -> bytes:
        """解码base64音频数据，支持DataURL格式"""
        if b64_data.startswith("data:"):
            _, b64_data = b64_data.split(",", 1)
        return base64.b64decode(b64_data)

    def extract_embedding(self, audio_path: str):
        """上传音频到MiMo API，获取voice_id用于后续TTS"""
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"音频文件大小: {file_size_mb:.2f} MB")

        audio_data_url = self._audio_to_data_url(audio_path)

        return {
            "voice_id": audio_data_url,
            "audio_path": audio_path
        }

    def save_embedding(self, voice_info: dict, save_path: str):
        """保存voice信息到本地文件"""
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(voice_info, f, ensure_ascii=False, indent=2)
        print(f"voice信息已保存到: {save_path}")

    def load_embedding(self, load_path: str):
        """从本地文件加载voice信息"""
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"voice信息文件不存在: {load_path}")

        with open(load_path, "r", encoding="utf-8") as f:
            voice_info = json.load(f)

        print("已加载voice信息")
        return voice_info

    def clone_voice(self, source_audio_path: str, target_voice_info: dict, output_path: str, text: str = None):
        """使用克隆的声音生成语音"""
        if text:
            return self.generate_speech_from_text(text, output_path, target_voice_info.get("voice_id"))

        result = self.extract_embedding(source_audio_path)
        return result

    def generate_speech_from_text(self, text: str, output_path: str, voice_data_url: str = None) -> str:
        """使用MiMo TTS API生成语音"""
        if not text or not text.strip():
            raise ValueError("合成文本不能为空")

        url = f"{self.base_url}/chat/completions"

        messages = [
            {"role": "user", "content": f"请用这个声音说：{text}"},
            {"role": "assistant", "content": text}
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "modalities": ["audio"],
            "audio": {
                "format": "wav"
            }
        }

        if voice_data_url:
            payload["audio"]["voice"] = voice_data_url

        try:
            print(f"正在调用MiMo TTS API...")
            print(f"文本长度: {len(text)} 字符")
            if voice_data_url:
                print("使用语音克隆")

            response = requests.post(url, json=payload, headers=self._headers, timeout=120)
            response.raise_for_status()

            result = response.json()

            if "choices" not in result or len(result["choices"]) == 0:
                raise Exception(f"API返回异常: {result}")

            choice = result["choices"][0]
            if "message" not in choice or "audio" not in choice["message"]:
                raise Exception(f"API返回的audio数据格式异常")

            audio_info = choice["message"]["audio"]
            audio_bytes = self._extract_audio_bytes(audio_info)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            print(f"语音已保存到: {output_path}")
            return output_path

        except requests.exceptions.RequestException as e:
            raise Exception(f"TTS生成失败: {e}")

    def _extract_audio_bytes(self, audio_info) -> bytes:
        """从API响应中提取音频字节数据"""
        if isinstance(audio_info, dict):
            if "data" in audio_info:
                return self._decode_base64_audio(audio_info["data"])
        elif isinstance(audio_info, str):
            return self._decode_base64_audio(audio_info)
        elif isinstance(audio_info, list) and len(audio_info) > 0:
            all_audio_data = b""
            for item in audio_info:
                if isinstance(item, dict) and "data" in item:
                    all_audio_data += self._decode_base64_audio(item["data"])
                elif isinstance(item, str):
                    all_audio_data += self._decode_base64_audio(item)
            if all_audio_data:
                return all_audio_data

        raise Exception(f"无法解析audio数据格式: {type(audio_info)}")

    def list_voices(self):
        """列出所有可用的voice"""
        print("MiMo API使用DataURL格式进行语音克隆，无需列出voice")
        return {"voices": []}
