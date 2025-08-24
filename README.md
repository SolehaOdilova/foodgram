
Продуктовый помощник Foodgram
Приложение, где пользователи публикуют рецепты, подписываются на авторов и добавляют рецепты в избранное.
Сервис «Список покупок» позволяет создавать список продуктов для выбранных рецептов.

🌐 Доступ
После запуска проекта он будет доступен по адресу:
http://127.0.0.1 (если развернут локально в Docker)
Документация к API после запуска:
http://127.0.0.1/api/docs/

⚙️ Настройка CI/CD и Docker
🔹 ВАЖНО: Все действия выполняются через Docker.
🔹 Убедитесь, что в GitHub Secrets добавлены все необходимые переменные:
ALLOWED_HOSTS
DB_ENGINE
DB_HOST
DB_PORT
HOST
MY_LOGIN
MY_PASS
PASSPHRASE
POSTGRES_DB
POSTGRES_PASSWORD
POSTGRES_USER
SECRET_KEY
SSH_KEY
USER

🛠 Предварительная установка на сервере
ssh username@ip
sudo apt update && sudo apt upgrade -y && sudo apt install curl -y
sudo curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo rm get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo systemctl start docker.service && sudo systemctl enable docker.service

📦 Сборка и отправка Docker-образов
Backend:
cd backend
docker build -t <your_dockerhub_username>/foodgram_backend:latest .
docker push <your_dockerhub_username>/foodgram_backend:latest
Frontend:
cd frontend
docker build -t <your_dockerhub_username>/foodgram_frontend:latest .
docker push <your_dockerhub_username>/foodgram_frontend:latest
📂 Развертывание на сервере
🔹 Перенести файлы docker-compose.yml и default.conf в папку infra на сервере:
scp infra/docker-compose.production.yml username@server_ip:/home/username/
scp infra/default.conf username@server_ip:/home/username/
🔹 Создать файл .env в папке infra на сервере и заполнить его нужными переменными.
Запуск проекта:
cd infra
docker-compose up -d --build
⚡ Первичная настройка Django
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate --noinput
docker-compose exec backend python manage.py createsuperuser
docker-compose exec backend python manage.py collectstatic --no-input
🔹 Дополнительно можно наполнить базу ингредиентами и тегами:
docker-compose exec backend python manage.py load_tags
docker-compose exec backend python manage.py load_ingrs
🖥 Локальный запуск
Для Linux и Windows (Docker Desktop):
cd infra
docker-compose up -d --build
После чего выполняем команды для базы, суперюзера и статики (см. раздел ⚡ выше).
✨ Автор: Одилова Солеха
