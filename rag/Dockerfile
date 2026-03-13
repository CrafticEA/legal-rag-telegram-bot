# базовый образ
FROM python:3.11-slim

# рабочая директория
WORKDIR /app

# копируем код
COPY rag/ ./rag
COPY requirements.txt .

# устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# выставляем порт
EXPOSE 8001

# точка входа
CMD ["uvicorn", "rag.main:app", "--host", "0.0.0.0", "--port", "8001"]