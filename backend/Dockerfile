# Базовый образ с Python 3.9
FROM python:3.9

# Рабочая директория
WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект
COPY . .

# Запуск Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:9000", "foodgram_backend.wsgi"]