import os
import base64
import json
import requests
import tempfile
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

        # 获取文件扩展名来确定MIME类型
        ext = Path(audio_path).suffix.lower()
        mime_type_map = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".flac": "audio/flac",
            ".ogg": "audio/ogg",
            ".m4a": "audio/mp4",
        }
        mime_type = mime_type_map.get(ext, "audio/wav")

        # 转换为DataURL
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        return f"data:{mime_type};base64,{audio_base64}"

    def extract_embedding(self, audio_path: str):
        """
        上传音频到MiMo API，获取voice_id用于后续TTS
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在: {audio_path}")

        # 检查文件大小
        file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
        print(f"音频文件大小: {file_size_mb:.2f} MB")

        # 将音频转换为DataURL
        audio_data_url = self._audio_to_data_url(audio_path)

        # 对于MiMo API，voice_id就是DataURL本身
        # 我们返回音频路径和DataURL，供后续TTS使用
        return {
            "voice_id": audio_data_url,  # DataURL作为voice_id
            "audio_path": audio_path
        }

    def save_embedding(self, voice_info: dict, save_path: str):
        """
        保存voice信息到本地文件
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(voice_info, f, ensure_ascii=False, indent=2)
        print(f"voice信息已保存到: {save_path}")

    def load_embedding(self, load_path: str):
        """
        从本地文件加载voice信息
        """
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"voice信息文件不存在: {load_path}")

        with open(load_path, "r", encoding="utf-8") as f:
            voice_info = json.load(f)

        print(f"已加载voice信息")
        return voice_info

    def clone_voice(self, source_audio_path: str, target_voice_info: dict, output_path: str, text: str = None):
        """
        使用克隆的声音生成语音

        参数:
            source_audio_path: 源音频路径（用于提取音色）
            target_voice_info: 目标voice信息（包含voice_id）
            output_path: 输出音频路径
            text: 要合成的文本（如果为None，则只提取音色不合成）
        """
        # 如果提供了文本，直接用voice_id生成TTS
        if text:
            return self.generate_speech_from_text(text, output_path, target_voice_info.get("voice_id"))

        # 否则重新上传源音频获取新的voice_id
        result = self.extract_embedding(source_audio_path)
        return result

    def generate_speech_from_text(self, text: str, output_path: str, voice_data_url: str = None) -> str:
        """
        使用MiMo TTS API生成语音

        参数:
            text: 要合成的文本
            output_path: 输出音频路径
            voice_data_url: 可选，使用指定的音频DataURL进行克隆。如果为None则使用默认声音
        """
        if not text or not text.strip():
            raise ValueError("合成文本不能为空")

        # 使用chat/completions端点
        url = f"{self.base_url}/chat/completions"

        # 构建messages
        messages = [
            {"role": "user", "content": f"请用这个声音说：{text}"},
            {"role": "assistant", "content": text}
        ]

        # 构建payload
        payload = {
            "model": self.model,
            "messages": messages,
            "modalities": ["audio"],
            "audio": {
                "format": "wav"
            }
        }

        # 如果提供了voice_data_url，添加到audio参数中
        if voice_data_url:
            payload["audio"]["voice"] = voice_data_url

        try:
            print(f"正在调用MiMo TTS API...")
            print(f"文本长度: {len(text)} 字符")
            if voice_data_url:
                print(f"使用语音克隆")

            response = requests.post(url, json=payload, headers=self._headers, timeout=120)
            response.raise_for_status()

            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "audio" in choice["message"]:
                    audio_info = choice["message"]["audio"]

                    # 检查audio_info的格式
                    if isinstance(audio_info, dict):
                        # 可能包含data字段（base64编码的音频）
                        if "data" in audio_info:
                            audio_data = audio_info["data"]
                            # 移除DataURL前缀（如果有的话）
                            if audio_data.startswith("data:"):
                                header, b64data = audio_data.split(",", 1)
                                audio_bytes = base64.b64decode(b64data)
                            else:
                                audio_bytes = base64.b64decode(audio_data)

                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "wb") as f:
                                f.write(audio_bytes)

                            print(f"语音已保存到: {output_path}")
                            return output_path

                    elif isinstance(audio_info, str):
                        # 直接是base64编码的音频
                        # 移除DataURL前缀（如果有的话）
                        if audio_info.startswith("data:"):
                            header, b64data = audio_info.split(",", 1)
                            audio_bytes = base64.b64decode(b64data)
                        else:
                            audio_bytes = base64.b64decode(audio_info)

                        os.makedirs(os.path.dirname(output_path), exist_ok=True)
                        with open(output_path, "wb") as f:
                            f.write(audio_bytes)

                        print(f"语音已保存到: {output_path}")
                        return output_path

                    elif isinstance(audio_info, list) and len(audio_info) > 0:
                        # 可能是音频片段列表
                        # 尝试合并所有片段
                        all_audio_data = b""
                        for item in audio_info:
                            if isinstance(item, dict) and "data" in item:
                                b64data = item["data"]
                                if b64data.startswith("data:"):
                                    header, b64data = b64data.split(",", 1)
                                all_audio_data += base64.b64decode(b64data)
                            elif isinstance(item, str):
                                if item.startswith("data:"):
                                    header, b64data = item.split(",", 1)
                                    all_audio_data += base64.b64decode(b64data)
                                else:
                                    all_audio_data += base64.b64decode(item)

                        if all_audio_data:
                            os.makedirs(os.path.dirname(output_path), exist_ok=True)
                            with open(output_path, "wb") as f:
                                f.write(all_audio_data)

                            print(f"语音已保存到: {output_path}")
                            return output_path

                raise Exception(f"API返回的audio数据格式异常: {type(audio_info)}")
            else:
                raise Exception(f"API返回异常: {result}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"TTS生成失败: {e}")

    def list_voices(self):
        """
        列出所有可用的voice（MiMo API可能不支持此功能）
        """
        print("MiMo API使用DataURL格式进行语音克隆，无需列出voice")
        return {"voices": []}
