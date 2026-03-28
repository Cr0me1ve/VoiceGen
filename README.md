# VoiceGenWorker

Celery-воркер для синтеза речи из текста. Принимает задачи из Redis-очереди `voice`, генерирует аудиофайлы через Silero TTS и отдаёт их через встроенный Nginx-файловый сервер внутри сети Netbird.

## Архитектура

```
GenManager ──► Redis (очередь voice) ──► VoiceGenWorker ──► Silero TTS ──► /temp/*.mp3
                                                                               │
                                                              Nginx ◄──────────┘
                                                                │
                                                         download_url (Netbird)
```

- **Брокер/бэкенд**: Redis (DB 0 — брокер, DB 1 — результаты)
- **Сеть**: Netbird VPN — файловый сервер доступен только внутри VPN
- **Конкурентность**: `--concurrency=1 --pool=solo` — последовательная обработка

## Быстрый старт

```bash
git clone <repo>
cd VoiceGenWorker
sudo bash setup.sh
```

Скрипт автоматически:
1. Установит и подключит Netbird
2. Установит Docker
3. Создаст `.env` по результатам диалога
4. Откроет порт в UFW и запустит контейнеры

## Ручная установка

### 1. Создать `.env`

```bash
cat > .env <<EOF
REDIS_HOST=<IP GenManager в Netbird>
REDIS_PORT=6379
REDIS_PASSWORD=<пароль Redis>
DEFAULT_GENERATOR=silero
DEFAULT_SPEAKER=eugene
DEFAULT_SAMPLE_RATE=48000
TEMP_DIR=temp
NETBIRD_IP=<IP этого воркера в Netbird>
FILE_SERVER_PORT=8888
EOF
chmod 600 .env
```

`CELERY_BROKER_URL` и `CELERY_RESULT_BACKEND` генерируются автоматически из `REDIS_*`, но их можно задать явно.

### 2. Запустить контейнеры

```bash
docker compose up -d --build
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
|---|---|---|
| `REDIS_HOST` | `localhost` | Хост Redis |
| `REDIS_PORT` | `6379` | Порт Redis |
| `REDIS_PASSWORD` | `` | Пароль Redis |
| `CELERY_BROKER_URL` | авто | Полный URL брокера (переопределяет REDIS_*) |
| `CELERY_RESULT_BACKEND` | авто | Полный URL бэкенда результатов |
| `DEFAULT_GENERATOR` | `silero` | Генератор TTS по умолчанию |
| `DEFAULT_SPEAKER` | `eugene` | Голос по умолчанию |
| `DEFAULT_SAMPLE_RATE` | `48000` | Частота дискретизации (Гц) |
| `TEMP_DIR` | `temp` | Директория для аудиофайлов |
| `NETBIRD_IP` | `127.0.0.1` | IP воркера в сети Netbird |
| `FILE_SERVER_PORT` | `8888` | Порт Nginx файлового сервера |

## Celery-задача

**Имя:** `voice_worker.tasks.generate`
**Очередь:** `voice`

### Параметры

| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `prompt` | str | да | Текст для синтеза |
| `request_type` | str | да | Должен быть `"voice"` |
| `model_name` | str | нет | Имя генератора (default: `DEFAULT_GENERATOR`) |
| `max_timeout` | int | нет | Информационный таймаут (воркером не используется) |
| `callback_url` | str | нет | URL для POST-уведомления по завершении |
| `**kwargs` | | нет | Параметры генератора (speaker, sample_rate и др.) |

### Возвращаемое значение

```json
{
    "download_url": "http://<NETBIRD_IP>:<FILE_SERVER_PORT>/<filename>.mp3"
}
```

### Передача параметров генератора

**Через kwargs:**
```json
{
    "prompt": "Привет, мир",
    "request_type": "voice",
    "speaker": "aidar",
    "sample_rate": 24000
}
```

**JSON-префикс в prompt:**
```json
{
    "prompt": "{\"speaker\":\"aidar\",\"sample_rate\":24000}\nПривет, мир",
    "request_type": "voice"
}
```

## Генератор Silero

### Голоса (`speaker`)

| Голос | Пол |
|---|---|
| `aidar` | мужской |
| `baya` | женский |
| `kseniya` | женский |
| `xenia` | женский |
| `eugene` | мужской (по умолчанию) |
| `random` | случайный |

### Частоты дискретизации (`sample_rate`)

`8000`, `24000`, `48000` (по умолчанию)

## Структура проекта

```
VoiceGenWorker/
├── worker/
│   ├── tasks.py              # Celery-задача generate
│   ├── celery_app.py         # Инициализация Celery
│   ├── config.py             # Настройки (Pydantic Settings)
│   └── generators/
│       ├── __init__.py       # Реестр генераторов
│       ├── base.py           # Базовый класс BaseTTSGenerator + ParamSpec
│       └── silero.py         # Реализация Silero TTS
├── nginx/
│   └── file-server.conf      # Конфигурация Nginx
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── setup.sh                  # Скрипт автодеплоя
```

## Добавление нового генератора

1. Создать `worker/generators/my_tts.py`:

```python
from worker.generators.base import BaseTTSGenerator, ParamSpec

class MyTTSGenerator(BaseTTSGenerator):
    PARAMS = {
        "voice": ParamSpec("default", str, "Голос"),
    }

    def generate(self, text: str, params: dict) -> str:
        p = self.resolve_params(params)
        # ... генерация аудио ...
        return file_path  # путь к .mp3
```

2. Зарегистрировать в `worker/generators/__init__.py`:

```python
from worker.generators.my_tts import MyTTSGenerator
_REGISTRY["my_tts"] = MyTTSGenerator
```

3. Использовать, передав `model_name="my_tts"` в задачу.

## Управление

```bash
# Логи
docker compose logs -f

# Перезапуск
docker compose restart

# Обновление
git pull && docker compose up -d --build

# Остановка
docker compose down
```
