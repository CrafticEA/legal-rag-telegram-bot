FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV HF_HOME=/root/.cache/huggingface

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-base')"
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; model_name='BAAI/bge-reranker-base'; AutoTokenizer.from_pretrained(model_name); AutoModelForSequenceClassification.from_pretrained(model_name)"

COPY app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "info", "--access-log"]