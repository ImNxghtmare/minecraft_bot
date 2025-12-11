FROM python:3.10-slim

# системные зависимости (если понадобятся)
RUN apt-get update && apt-get install -y build-essential gcc libmariadb-dev-compat libmariadb-dev curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Кэшируем установку зависимостей
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Порт uvicorn
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
