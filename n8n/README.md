# legal-rag-telegram-bot

Telegram orchestration layer for the legal RAG project.

## Responsibilities

- Handle Telegram messages and file uploads
- Manage user session state (`chat_id`, `active_case_id`)
- Trigger backend API endpoints
- Send formatted responses back to users

## UI

Uses inline keyboards for interaction.

## Local run example

This is one working way to run the project locally.  
It is not the only possible setup, but it reflects a tested local flow for launching the API, n8n, and Telegram webhook.

### 1. Prerequisites

Before start, make sure you have:

- Docker Desktop running
- Tailscale installed and logged in
- a Telegram bot token
- a local file `n8n/env.n8n`

### 2. Configure `n8n/env.n8n`

Create a local file:

```text
n8n/env.n8n

Example content:
TELEGRAM_BOT_TOKEN=replace_me
N8N_HOST=replace_me.ts.net
N8N_PROTOCOL=https
WEBHOOK_URL=https://replace_me.ts.net/
N8N_API_BASE_URL=http://host.docker.internal:8000/api

