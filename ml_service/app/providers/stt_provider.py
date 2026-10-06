"""
KaushalTwin ML Service — Speech-to-Text Provider Interface
Module 1: Data Ingestion & ML Preprocessing

NOTE: The MVP operates on direct text input.
STT is an interface only — no STT model is required to run the service.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class SpeechToTextProvider(ABC):
    """
    Abstract STT provider interface.
    Implementations are interchangeable without changing the pipeline.
    """

    @abstractmethod
    def transcribe(self, audio: bytes, language: str = "hi") -> str:
        """
        Transcribe audio bytes to text.

        Parameters
        ----------
        audio    : raw audio bytes (WAV / FLAC / MP3 depending on implementation)
        language : BCP-47 language code (e.g. 'hi', 'en', 'te')

        Returns
        -------
        Transcribed text string.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...


class MockSTTProvider(SpeechToTextProvider):
    """
    Mock STT provider for testing and demo.
    Returns a fixed transcript — does NOT perform real transcription.
    Used when no speech model is available.
    """

    DEFAULT_TRANSCRIPT = (
        "I have been doing electrical work for seven years. "
        "I install switches and fans, do house wiring, "
        "and find faults using a line tester."
    )

    def transcribe(self, audio: bytes, language: str = "hi") -> str:
        return self.DEFAULT_TRANSCRIPT

    @property
    def provider_name(self) -> str:
        return "mock-stt-v1"


class WhisperSTTProvider(SpeechToTextProvider):
    """
    OpenAI Whisper-based STT provider (local model via whisper package).
    Falls back to MockSTTProvider if whisper is not installed.
    """

    def __init__(self, model_size: str = "base") -> None:
        self._model_size = model_size
        self._model = None
        self._fallback: Optional[MockSTTProvider] = None
        self._try_load()

    def _try_load(self) -> None:
        try:
            import whisper
            self._model = whisper.load_model(self._model_size)
        except ImportError:
            self._fallback = MockSTTProvider()

    def transcribe(self, audio: bytes, language: str = "hi") -> str:
        if self._model is None:
            return self._fallback.transcribe(audio, language)  # type: ignore
        # whisper requires a file path or numpy array
        import io
        import numpy as np
        import soundfile as sf

        audio_io = io.BytesIO(audio)
        data, sr = sf.read(audio_io)
        result = self._model.transcribe(data.astype(np.float32), language=language)
        return result.get("text", "")

    @property
    def provider_name(self) -> str:
        if self._model is None:
            return "whisper-fallback-to-mock"
        return f"whisper-{self._model_size}"
