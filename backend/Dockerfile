# Базовый образ с Python 3.9
FROM python:3.9

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем и устанавливаем Python-зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=foodgram_backend.settings

# Запускаем Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "foodgram_backend.wsgi"]