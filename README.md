# legal-rag-telegram-bot

<table>
  <tr>
    <td width="72">
      <img src="https://thumbs.dreamstime.com/b/%D0%B2%D0%B5%D1%81%D1%8B-%D0%BF%D1%80%D0%B0%D0%B2%D0%BE%D1%81%D1%83-%D0%B8%D1%8F-emblem-%D1%8F-%D0%B8%D0%B7%D0%B0%D0%B9%D0%BD%D0%B0-%D1%8E%D1%80%D0%B8-%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%BE%D0%B9-%D1%84%D0%B8%D1%80%D0%BC%D1%8B-86070496.jpg" width="56" alt="Legal RAG icon" />
    </td>
    <td>
      <b>Legal RAG Telegram Bot</b> — быстрый способ отвечать на юридические вопросы <i>только на основе ваших документов</i>.<br />
      Загружайте материалы по делу, задавайте вопросы привычным сообщением в Telegram и получайте краткий, структурированный ответ со ссылками на источники.
    </td>
  </tr>
</table>

## Архитектура (сервисы)

Всё поднимается через `docker-compose.yml`.

### `api` (Rails 8) — HTTP API и состояние дел

- **Роль**: хранение кейсов/документов, выдача API для n8n, оркестрация вызовов `rag` и `llm`.
- **Технологии**: Ruby 3.3, Rails `~> 8.0.2`, Postgres, Shrine (файлы в `public/uploads`).
- **Порт**: `8000` (в compose проброшен `8000:8000`).
- **Файлы**:
  - `api/config/routes.rb` — маршруты API.
  - `api/app/services/rag_ask_service.rb` — связка `rag /retrieve` → `llm /generate`.
- **Важные переменные окружения** (см. `docker-compose.yml`):
  - `DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`
  - `RAG_URL` (по умолчанию `http://localhost:8001`)
  - `LLM_URL` (по умолчанию `http://localhost:8002`)
- **Хранилище загрузок**:
  - Внутри контейнера: `/app/public/uploads`
  - В репозитории: `./uploads` (маунтится в контейнер)

#### API endpoints (основные)

База: `http://localhost:8000/api`

- **Cases**
  - `GET /cases?chat_id=...` — список кейсов
  - `POST /cases?chat_id=...` — создать кейс
  - `GET /cases/:id?chat_id=...` — детали кейса (`:id` может быть `case_123`)
  - `GET /cases/:id/status?chat_id=...` — статус
  - `POST /cases/:id/ask?chat_id=...&question=...` — Q&A через RAG+LLM
- **Documents**
  - `POST /cases/:case_id/documents` (multipart, поле `file`) — загрузить документ
  - `DELETE /cases/:case_id/documents/:id` — удалить документ
- **Index artifacts (загрузка/выдача индекса)**
  - `POST /cases/:id/upload_index` (multipart `faiss_index`, `chunks`) — загрузить индекс/чанки
  - `GET /cases/:id/faiss_index` — скачать `faiss.index`
  - `GET /cases/:id/chunks` — скачать `chunks.jsonl`

### `api-db` (Postgres 17) — база данных для `api`

- **Роль**: хранение кейсов/документов/метаданных.
- **Версия**: `postgres:17`
- **Хранилище**: volume `postgres_db`

### `rag` (FastAPI) — парсинг/эмбеддинги/FAISS и retrieval

- **Роль**: собрать индекс по документам и возвращать топ-K фрагментов по запросу.
- **Порт**: `8001`
- **Эндпоинты** (см. `rag/app/main.py`):
  - `GET /health`
  - `POST /build` — построить индекс
  - `POST /retrieve` — найти релевантные чанки
- **Хранилище**:
  - `./data` → `/app/data` — индексы/чанки по кейсам
  - `./uploads` → `/app/uploads` — доступ к загруженным документам (если используется)
- **Зависимости (Python 3.11)**: см. `rag/requirements.txt` (FastAPI, FAISS, sentence-transformers и т.д.).
- **Переменные окружения** (см. `docker-compose.yml`):
  - `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`

### `llm` (FastAPI) — генерация ответа по контексту из RAG

- **Роль**: принимает вопрос + чанки (контекст) и генерирует ответ через локальную модель.
- **Порт**: `8002`
- **Эндпоинты**:
  - `GET /status` — проверка доступности Docker Model Runner + список моделей
  - `POST /generate` — ответ на вопрос по чанкам
  - `POST /recommendations` — рекомендации по подготовленному контексту
- **Важно**: сам `llm` не запускает модель; он ходит в **Docker Model Runner** по OpenAI‑совместимому API.
- **Переменные окружения** (см. `docker-compose.yml` и `llm/app/model_client.py`):
  - `DMR_BASE_URL` (пример: `http://model-runner.docker.internal:12434/engines/v1` или `/v1`)
  - `DMR_MODEL` (пример в compose: `hf.co/Qwen/Qwen2.5-7B-Instruct-GGUF:Q4_K_M`)
  - `DMR_TIMEOUT_SECONDS`

### `n8n` — Telegram/webhook оркестрация

- **Роль**: принимает события Telegram, хранит состояние сессии (в static data workflow), дергает `api`, отправляет ответы пользователю.
- **Порт**: `5678`
- **Файлы**:
  - `n8n/n8n_legal_rag_api.json` — workflow (Telegram Trigger + логика роутинга/загрузки файлов/вызовов API)
- **Переменные окружения**:
  - Загружаются из `./n8n/env.n8n` (локальный файл, создаётся вручную)
  - Плюс дополнительные переменные из `docker-compose.yml` (`N8N_SECURE_COOKIE=false`, etc.)
- **Хранилище**:
  - `./n8n_data` → `/home/node/.n8n` — данные n8n
  - `./n8n` → `/files` — доступ к файлам проекта (например, для импорта workflow)

## Зависимости

### Рекомендуемый способ (через Docker)

- **Docker Desktop** (или Docker Engine) + **Docker Compose**
- **Docker Model Runner** (локально, на хосте) — для работы `llm`
  - Должен быть доступен контейнеру по адресу `model-runner.docker.internal:12434`
- Для Telegram webhook (если нужен https‑домен):
  - **Tailscale** (как один из рабочих вариантов), либо любой другой способ дать n8n публичный HTTPS URL

### Запуск без Docker (необязательно)

Если запускать сервисы локально, вам понадобятся:

- **Ruby 3.3** + Bundler (для `api`)
- **PostgreSQL 17**
- **Python 3.11** (для `rag` и `llm`)

## Быстрый старт (Docker Compose)

### 1) Подготовить `n8n/env.n8n`

Создайте файл `n8n/env.n8n` (он не в репозитории) со значениями под вашу среду:

```text
TELEGRAM_BOT_TOKEN=replace_me
N8N_HOST=replace_me.ts.net
N8N_PROTOCOL=https
WEBHOOK_URL=https://replace_me.ts.net/
N8N_API_BASE_URL=http://host.docker.internal:8000/api
```

### 2) Убедиться, что работает Docker Model Runner

`llm` ожидает, что на хосте доступен Docker Model Runner, и из контейнера он виден как:

- `http://model-runner.docker.internal:12434/...`

Проверьте готовность после старта `llm`:

```bash
curl -sS http://localhost:8002/status | jq
```

### 3) Запустить сервисы

Из корня репозитория:

```bash
docker compose build
docker compose up -d
```

Проверка:

- `api`: `http://localhost:8000/api/cases?chat_id=123`
- `rag`: `http://localhost:8001/health`
- `llm`: `http://localhost:8002/status`
- `n8n`: `http://localhost:5678`

### 4) Импортировать workflow в n8n

Импортируйте `n8n/n8n_legal_rag_api.json` в UI n8n:

- **Import workflow** → выбрать файл `n8n_legal_rag_api.json`
- Настроить/проверить credential “Telegram account” (токен берётся из `TELEGRAM_BOT_TOKEN`)
- Активировать workflow

## Полезные команды

### Логи

```bash
docker compose logs -f api
docker compose logs -f rag
docker compose logs -f llm
docker compose logs -f n8n
```

### Пересборка одного сервиса

```bash
docker compose build rag && docker compose up -d rag
```

## Структура репозитория

- `api/` — Rails API (кейсы, документы, оркестрация)
- `rag/` — FastAPI retrieval/indexing сервис
- `llm/` — FastAPI LLM gateway к Docker Model Runner
- `n8n/` — workflow и документация по Telegram-оркестрации
- `uploads/` — загруженные документы и артефакты Shrine (маунтится в `api`/`rag`)
- `data/` — индексы/чанки RAG (маунтится в `rag`)
