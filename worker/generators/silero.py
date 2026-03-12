import os
import uuid
import torch

from worker.config import get_settings
from worker.generators.base import BaseTTSGenerator

settings = get_settings()


class SileroGenerator(BaseTTSGenerator):
    """
    TTS generator using Silero models (snakers4/silero-models).
    Supports Russian and other languages available in Silero.
    """

    # Cache loaded models to avoid re-downloading on every task
    _model_cache: dict[str, object] = {}

    def _load_model(self, language: str, speaker_model: str):
        cache_key = f"{language}_{speaker_model}"
        if cache_key not in self._model_cache:
            model, _ = torch.hub.load(
                "snakers4/silero-models",
                "silero_tts",
                language=language,
                speaker=speaker_model,
            )
            self._model_cache[cache_key] = model
        return self._model_cache[cache_key]

    def generate(self, text: str, settings_: dict | None = None) -> str:
        # Accept both 'settings' kwarg pattern and positional
        if settings_ is None:
            settings_ = {}
        return self._generate(text, settings_)

    # BaseTTSGenerator requires this signature
    def generate(self, text: str, settings: dict) -> str:
        language = settings.get("language", "ru")
        speaker_model = settings.get("speaker_model", "v5_ru")
        speaker = settings.get("speaker", "eugene")
        sample_rate = int(settings.get("sample_rate", 48000))

        model = self._load_model(language, speaker_model)

        filename = f"silero_{speaker}_{uuid.uuid4().hex[:8]}.mp3"
        file_path = os.path.join(settings.temp_dir, filename)

        model.save_wav(
            text=text,
            speaker=speaker,
            sample_rate=sample_rate,
            audio_path=file_path,
        )

        return file_path
