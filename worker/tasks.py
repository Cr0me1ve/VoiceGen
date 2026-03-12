import os
from worker.celery_app import celery
from worker.config import get_settings
from worker.generators import get_generator

settings = get_settings()


@celery.task(name="worker.tasks.generate", bind=True)
def generate(
    self,
    prompt: str,
    request_type: str,
    model_name: str | None = None,
    max_timeout: int = 180,
    callback_url: str | None = None,
    **kwargs,
):
    """
    Celery task: generate audio from text.
    Only handles request_type='audio'; ignores other types
    so this worker can coexist on the same queue without errors.
    """
    if request_type != "audio":
        raise ValueError(
            f"VoiceGen only handles request_type='audio', got '{request_type}'"
        )

    generator_name = model_name or settings.default_generator

    # Parse optional extra settings passed via kwargs
    tts_settings = {
        "speaker": kwargs.get("speaker", settings.default_speaker),
        "sample_rate": kwargs.get("sample_rate", settings.default_sample_rate),
        "language": kwargs.get("language", "ru"),
        "speaker_model": kwargs.get("speaker_model", "v5_ru"),
    }

    os.makedirs(settings.temp_dir, exist_ok=True)

    generator = get_generator(generator_name)
    file_path = generator.generate(text=prompt, settings=tts_settings)

    if callback_url:
        _send_callback(callback_url, file_path)

    return file_path


def _send_callback(url: str, file_path: str) -> None:
    try:
        import httpx
        httpx.post(url, json={"result": file_path}, timeout=10)
    except Exception:
        pass
