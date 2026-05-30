import os

APP_NAME = "口播助手"
APP_VERSION = "1.0.0"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# MiMo API 配置
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "tp-c3ku54rswhsi1xrqqr7njfszrw4i2xvzoqvrl9kwvt0ac82w")
MIMO_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_TTS_MODEL = "mimo-v2.5-tts-voiceclone"

# 音频配置
AUDIO_SAMPLE_RATE = 24000
AUDIO_CHANNELS = 1
AUDIO_FORMAT = "wav"
