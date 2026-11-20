FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080

CMD ["sh", "-c", "uvicorn app_orquestrador_master:app --host 0.0.0.0 --port ${PORT}"]