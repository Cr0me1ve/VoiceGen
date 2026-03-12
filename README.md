# VoiceGen

TTS worker service compatible with [GeminiBApiServer](https://github.com/Cr0me1ve/GeminiBApiServer).

## Architecture

```
GeminiBApiServer  →  Redis (Celery)  →  VoiceGen worker
                                            │
                                     generators/
                                       ├── base.py       (abstract)
                                       ├── silero.py     (Silero TTS)
                                       └── ... (add more)
```

The worker listens for tasks of `request_type=audio`. Each generator is a separate module in `worker/generators/`.
The result is a file path like `temp/<name>.mp3`.

## Quick Start

```bash
cp .env.example .env
# edit .env
docker compose up -d
```

## Adding a New TTS Generator

1. Create `worker/generators/my_tts.py` inheriting from `BaseTTSGenerator`
2. Implement `generate(text, settings) -> str` — return path to saved file
3. Register it in `worker/generators/__init__.py`

## API

Send a task via GeminiBApiServer with `request_type=audio` and `model_name=silero`.

**Extra settings** can be passed as JSON in `prompt` field or via future `settings` field (see models).

### Request body (GeminiBApiServer)
```json
{
  "prompt": "Привет мир",
  "request_type": "audio",
  "model_name": "silero"
}
```

### Result
```json
{
  "status": "completed",
  "result": "temp/silero_eugene_a1b2c3.mp3"
}
```
