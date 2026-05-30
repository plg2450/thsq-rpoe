from .downloader import Downloader
from .recognizer import Recognizer
from .polisher import Polisher

__all__ = ["Downloader", "Recognizer", "Polisher"]

def get_voice_cloner():
    from .voice_cloner import VoiceCloner
    return VoiceCloner()
