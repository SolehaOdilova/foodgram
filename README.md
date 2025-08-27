# Foodgram

## Описание проекта
Foodgram — это социальная сеть для публикации рецептов, добавления их в избранное и подписки на других авторов.

### Возможности проекта
- Регистрация и авторизация пользователей
- Публикация рецептов с описанием, ингредиентами и тегами
- Добавление рецептов в избранное и в список покупок
- Подписка на других авторов
- Просмотр рецептов авторов, на которых подписан пользователь

## Стек технологий
- **Backend**: Django REST Framework
- **Frontend**: React
- **База данных**: PostgreSQL
- **Сервер**: Nginx
- **Контейнеризация**: Docker

## Запуск проекта локально

### 1. Установка Docker
```bash
sudo apt update && sudo apt install -y curl
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo rm get-docker.sh

2. Клонирование репозитория
git clone <URL репозитория>
cd foodgram-project-react


3. Настройка переменных окружения
Создать файл infra/.env со следующим содержимым:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1


4. Запуск Docker контейнеров
cd infra
docker-compose up -d --build


5. Выполнение миграций и создание суперпользователя
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py createsuperuser


6. Загрузка начальных данных
docker-compose exec backend python manage.py load_tags
docker-compose exec backend python manage.py load_ingrs


Доступные адреса
Приложение: http://localhost
Документация API: http://localhost/api/docs/
Админ-панель: http://localhost/admin/
