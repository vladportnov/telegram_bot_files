FROM python:3.8-slim

# Устанавливаем зависимости
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем исходный код в контейнер
COPY . /app

WORKDIR /app

CMD ["python", "app.py"]
