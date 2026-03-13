import os
import json
from worker.celery_app import celery
from worker.config import get_settings
from worker.generators import get_generator

settings = get_settings()


@celery.task(name="voice_worker.tasks.generate", bind=True)
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
    Celery task для GenManager (multi_queue).
    Слушает очередь 'voice', обрабатывает request_type='voice'.

    Параметры генератора передаются двумя способами:
    1. Через kwargs: {"speaker": "aidar", "sample_rate": 24000}
    2. JSON-префиксом в prompt:
       '{"speaker":"aidar","sample_rate":24000}\nТекст для озвучки'
    """
    if request_type != "voice":
        raise ValueError(
            f"VoiceGenWorker handles only request_type='voice', got '{request_type}'"
        )

    text = prompt
    inline_params: dict = {}
    first_line, _, rest = prompt.partition("\n")
    if first_line.strip().startswith("{"):
        try:
            inline_params = json.loads(first_line.strip())
            text = rest.strip()
        except json.JSONDecodeError:
            pass

    raw_params = {**inline_params, **kwargs}
    generator_name = model_name or settings.default_generator

    os.makedirs(settings.temp_dir, exist_ok=True)

    generator = get_generator(generator_name)
    file_path = generator.generate(text=text, params=raw_params)

    if callback_url:
        _send_callback(callback_url, file_path)

    return file_path


def _send_callback(url: str, file_path: str) -> None:
    try:
        import httpx
        httpx.post(url, json={"result": file_path}, timeout=10)
    except Exception:
        pass
