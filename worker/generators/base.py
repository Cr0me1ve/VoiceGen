from abc import ABC, abstractmethod


class BaseTTSGenerator(ABC):
    """
    Abstract base class for all TTS generators.

    To add a new generator:
    1. Create a file in worker/generators/
    2. Subclass BaseTTSGenerator
    3. Implement generate()
    4. Register it in worker/generators/__init__.py
    """

    @abstractmethod
    def generate(self, text: str, settings: dict) -> str:
        """
        Generate audio from text.

        Args:
            text:     Input text to synthesize.
            settings: Dict with keys:
                        speaker      (str)  - speaker name/id
                        sample_rate  (int)  - audio sample rate
                        language     (str)  - language code
                        speaker_model (str) - model variant (e.g. 'v5_ru')

        Returns:
            Path to the saved audio file, e.g. 'temp/silero_eugene_abc123.mp3'
        """
        ...
