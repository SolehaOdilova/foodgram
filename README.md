# Продуктовый помощник Foodgram

## Описание проекта
Foodgram - это онлайн-платформа для любителей кулинарии. Здесь пользователи могут делиться рецептами, находить вдохновение и организовывать свой процесс приготовления пищи.

### Основные возможности:
- 📝 Публикация собственных рецептов
- ❤️ Добавление рецептов в избранное
- 🛒 Формирование списка покупок
- 👥 Подписка на других авторов
- 🔍 Поиск рецептов по тегам и ингредиентам

## Технологический стек
- **Backend**: Django REST Framework
- **Frontend**: React
- **База данных**: PostgreSQL
- **Веб-сервер**: Nginx
- **Контейнеризация**: Docker

---

## Быстрый старт

### 1. Установка Docker
```bash
sudo apt update && sudo apt install -y curl
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo rm get-docker.sh

2. Клонирование проекта

bash
git clone <URL-репозитория>
cd foodgram-project-react
3. Настройка переменных окружения

Создайте файл infra/.env:

env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
4. Запуск проекта

bash
cd infra
docker-compose up -d --build
5. Настройка базы данных

bash
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py createsuperuser
6. Заполнение базы данными (опционально)

bash
docker-compose exec backend python manage.py load_tags
docker-compose exec backend python manage.py load_ingrs
Доступ к проекту

После запуска проект будет доступен по адресам:

🚀 Основное приложение: http://localhost
📚 API документация: http://localhost/api/docs/
⚙️ Админ-панель: http://localhost/admin/

Автор: Одилова Солоха
