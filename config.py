import os
from pathlib import Path

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass  # python-dotenv 未安装时使用系统环境变量

APP_NAME = "口播工作台"
APP_VERSION = "1.0.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
GENERATED_DIR = os.path.join(DATA_DIR, "generated")
VOICE_PROFILES_DIR = os.path.join(DATA_DIR, "voice_profiles")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
os.makedirs(VOICE_PROFILES_DIR, exist_ok=True)

# MiMo API 配置（从环境变量读取，不再硬编码）
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")
MIMO_BASE_URL = os.environ.get("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")
MIMO_TTS_MODEL = os.environ.get("MIMO_TTS_MODEL", "mimo-v2.5-tts-voiceclone")

# 音频配置
AUDIO_SAMPLE_RATE = 24000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "wav"

# FFmpeg 路径（优先从环境变量读取，否则自动发现）
def _find_ffmpeg():
    """自动查找 ffmpeg 路径"""
    # 1. 从环境变量读取
    ffmpeg_path = os.environ.get("FFMPEG_PATH", "")
    if ffmpeg_path and os.path.exists(ffmpeg_path):
        return ffmpeg_path

    # 2. 尝试从 imageio_ffmpeg 获取
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, Exception):
        pass

    # 3. 尝试从系统 PATH 查找
    import shutil
    ffmpeg_in_path = shutil.which("ffmpeg")
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # 4. 返回默认路径（可能不存在）
    return ""

FFMPEG_PATH = _find_ffmpeg()
