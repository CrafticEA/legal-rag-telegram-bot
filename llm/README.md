# Legal LLM Service

LLM‑сервис для проекта **legal‑rag‑telegram‑bot**.\
Сервис отвечает за генерацию ответов на основе контекста,
подготовленного RAG‑модулем, и работает через локальную модель в
**Docker Model Runner**.

Поддерживаются два режима работы:

-   **POST /generate** --- ответ на пользовательский вопрос по найденным
    фрагментам документов
-   **POST /recommendations** --- генерация рекомендаций по заранее
    подготовленному `prompt_context.json`

------------------------------------------------------------------------

# Технологический стек

-   **FastAPI**
-   **Uvicorn**
-   **Docker**
-   **Docker Compose**
-   **Docker Model Runner**
-   **llama.cpp backend**
-   **Qwen LLM (локально)**

------------------------------------------------------------------------

# Роль сервиса в архитектуре

    User / Telegram / API
            │
            ▼
            RAG
            │
            ▼
       JSON Request
            │
            ▼
     Legal LLM Service
            │
            ▼
     Docker Model Runner
            │
            ▼
          Local LLM

LLM‑сервис **не выполняет**:

-   parsing документов
-   chunking
-   embeddings
-   retrieval
-   построение FAISS индекса

Все эти операции выполняет **RAG‑модуль**.

LLM‑сервис получает **готовый JSON‑контекст** и генерирует финальный
ответ.

------------------------------------------------------------------------

# Поддерживаемые сценарии

## 1. Ответ на вопрос пользователя

Endpoint:

    POST /generate

Pipeline:

    User question
         │
         ▼
    RAG retrieve(query)
         │
         ▼
    top_k chunks
         │
         ▼
    POST /generate
         │
         ▼
    LLM response

------------------------------------------------------------------------

## 2. Генерация рекомендаций по делу

Endpoint:

    POST /recommendations

Pipeline:

    Documents uploaded
            │
            ▼
    Parsing → Chunking → Embeddings
            │
            ▼
    Index build (FAISS)
            │
            ▼
    Generate prompt_context.json
            │
            ▼
    User presses "Recommendations"
            │
            ▼
    POST /recommendations
            │
            ▼
    LLM response

------------------------------------------------------------------------

# Структура модуля

    llm/
    ├── app/
    │   ├── main.py
    │   ├── model_client.py
    │   ├── prompt_builder.py
    │   └── schemas.py
    │
    ├── Dockerfile
    ├── requirements.txt
    └── README.md

------------------------------------------------------------------------

# Описание модулей

## main.py

Основное FastAPI приложение.

Endpoints:

-   `GET /status`
-   `POST /generate`
-   `POST /recommendations`

------------------------------------------------------------------------

## model_client.py

Клиент для взаимодействия с **Docker Model Runner** через
OpenAI‑совместимый API.

Основные функции:

-   получение списка доступных моделей
-   отправка chat completion запроса
-   обработка ошибок LLM

------------------------------------------------------------------------

## prompt_builder.py

Генерация prompt для модели.

Реализует:

-   system prompt
-   user prompt
-   форматирование chunks
-   подготовку prompt для рекомендаций

------------------------------------------------------------------------

## schemas.py

Pydantic схемы API.

Основные модели:

-   `GenerateRequest`
-   `RecommendationRequest`
-   `GenerateResponse`
-   `Chunk`
-   `SourceItem`

------------------------------------------------------------------------

# Переменные окружения

    DMR_BASE_URL=http://model-runner.docker.internal:12434/engines/v1
    DMR_MODEL=docker.io/ai/qwen2.5:latest
    DMR_TIMEOUT_SECONDS=120

  Переменная            Назначение
  --------------------- ---------------------------
  DMR_BASE_URL          адрес Docker Model Runner
  DMR_MODEL             модель по умолчанию
  DMR_TIMEOUT_SECONDS   timeout запроса к модели

------------------------------------------------------------------------

# Docker Compose пример

``` yaml
llm:
  build: ./llm
  container_name: legal_llm
  ports:
    - "8002:8002"
  environment:
    DMR_BASE_URL: http://model-runner.docker.internal:12434/engines/v1
    DMR_MODEL: docker.io/ai/qwen2.5:latest
    DMR_TIMEOUT_SECONDS: 120
  extra_hosts:
    - "model-runner.docker.internal:host-gateway"
  restart: unless-stopped
```

------------------------------------------------------------------------

# API

## GET /status

Проверка состояния сервиса.

### Пример ответа

``` json
{
  "status": "ok",
  "dmr_base_url": "http://model-runner.docker.internal:12434/engines/v1",
  "model_configured": "docker.io/ai/qwen2.5:latest",
  "available_models": [
    "docker.io/ai/qwen2.5:latest"
  ]
}
```

------------------------------------------------------------------------

# POST /generate

Ответ на вопрос пользователя по chunks, найденным RAG.

### Пример запроса

``` json
{
  "case_id": "case-001",
  "query": "Какие риски есть в договоре аренды?",
  "context": {
    "chunks": [
      {
        "text": "Арендатор обязан вносить арендную плату не позднее 5 числа каждого месяца.",
        "source": "lease_contract.pdf",
        "page": 3,
        "chunk_id": "chunk-11",
        "score": 0.91
      },
      {
        "text": "При просрочке оплаты более 10 дней арендодатель вправе расторгнуть договор.",
        "source": "lease_contract.pdf",
        "page": 5,
        "chunk_id": "chunk-19",
        "score": 0.89
      }
    ]
  },
  "instructions": {
    "answer_only_from_context": true,
    "cite_sources": true,
    "structured_output": true
  },
  "generation": {
    "temperature": 0.2,
    "max_tokens": 250,
    "enable_thinking": false
  }
}
```

### Пример ответа

``` json
{
  "answer": "Существует риск расторжения договора аренды при длительной просрочке оплаты. Также возможен риск взыскания задолженности.",
  "sources": [
    {
      "source": "lease_contract.pdf",
      "page": 3,
      "chunk_id": "chunk-11"
    },
    {
      "source": "lease_contract.pdf",
      "page": 5,
      "chunk_id": "chunk-19"
    }
  ],
  "meta": {
    "mode": "generate",
    "case_id": "case-001",
    "model": "docker.io/ai/qwen2.5:latest",
    "generation_time_sec": 1.24
  }
}
```

------------------------------------------------------------------------

# POST /recommendations

Генерация рекомендаций по делу.

JSON формируется **RAG после загрузки документов**.

Файл хранится внутри дела:

    case_id/
    ├── documents/
    ├── embeddings/
    ├── index/
    ├── chunks.jsonl
    └── prompt_context.json

### Пример запроса

``` json
{
  "case_id": "case-001",
  "context": {
    "case_summary": "Спор связан с просрочкой арендных платежей.",
    "goal": "Подготовить рекомендации для юриста.",
    "procedural_stage": "досудебная стадия",
    "requested_output": "Сформулировать практические рекомендации.",
    "facts": [
      "Заключен договор аренды",
      "Есть просрочка платежей"
    ],
    "claimant_position": "Арендодатель может расторгнуть договор.",
    "respondent_position": "Арендатор хочет сохранить договор.",
    "risks": [
      "Расторжение договора",
      "Взыскание задолженности"
    ],
    "missing_info": [
      "Неизвестна точная сумма задолженности",
      "Нет данных о переписке сторон"
    ],
    "chunks": [
      {
        "text": "Арендатор обязан платить аренду ежемесячно.",
        "source": "lease_contract.pdf",
        "page": 3,
        "chunk_id": "chunk-11",
        "score": 0.91
      }
    ]
  }
}
```

------------------------------------------------------------------------

# Требования к chunks

``` json
{
  "text": "string",
  "source": "string",
  "page": 0,
  "chunk_id": "string",
  "score": 0.0
}
```

  Поле       Обязательное
  ---------- --------------
  text       да
  source     да
  page       нет
  chunk_id   нет
  score      нет

------------------------------------------------------------------------

# Рекомендуемые параметры RAG

  Параметр             Значение
  -------------------- -----------------
  chunks per request   3‑10
  chunk_size           \~1500 символов
  overlap              \~200
  top_k                5‑8

------------------------------------------------------------------------

# Запуск

## Сборка контейнера

    docker compose build llm

## Запуск

    docker compose up -d llm

## Проверка логов

    docker logs -f legal_llm

------------------------------------------------------------------------

# Swagger

Документация API:

    http://localhost:8002/docs

OpenAPI schema:

    http://localhost:8002/openapi.json

------------------------------------------------------------------------

# Назначение сервиса

Этот модуль является **LLM‑слоем системы** и предоставляет единый HTTP
API для генерации ответов поверх данных, подготовленных RAG.
