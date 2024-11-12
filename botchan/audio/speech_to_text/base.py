from abc import ABC, abstractmethod

from botchan.utt.timed import timed
from botchan.audio.speech_to_text.data_model import AudioFormat

LANG_US = "en-US"
class SpeechToText(ABC):
    @abstractmethod
    @timed
    def transcribe(
        self,
        audio_bytes: bytes,
        audio_format: AudioFormat = AudioFormat.WAV,
        prompt: str="",
        language: str=LANG_US,
        suppress_tokens: list[int] | None = None,
    ) -> str:
        pass
