# 🗺️ Geosocial Network API

REST API для геосоціальної мережі, де користувачі можуть ділитися фотографіями з прив'язкою до карти та переглядати пости інших людей.

## 🚀 Швидкий старт з Docker

### Передумови

- [Docker](https://docs.docker.com/get-docker/) 20.10+
- [Docker Compose](https://docs.docker.com/compose/install/) 2.0+

### Локальне розгортання

1. **Клонуйте репозиторій:**

```bash
git clone <repository-url>
cd python-app.loc
```

2. **Створіть файл з переменними середовища:**

```bash
cp env.example .env
```

3. **Налаштуйте Cloudinary (опційно):**
   Відредагуйте `.env` файл та додайте ваші Cloudinary credentials:

```bash
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

4. **Запустіть проект:**

```bash
# Запуск всіх сервісів (API + PostgreSQL + Redis)
docker compose up -d

# Або тільки API + PostgreSQL
docker compose up -d api db
```

5. **Перевірте статус:**

```bash
docker compose ps
```

### 📍 Доступ до сервісів

- **API документація (Swagger):** http://localhost:8000/docs
- **API:** http://localhost:8000
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

### 🔧 Корисні команди

```bash
# Переглянути логи API
docker compose logs -f api

# Переглянути логи бази даних
docker compose logs -f db

# Зупинити всі сервіси
docker compose down

# Зупинити та видалити volume (УВАГА: видалить дані БД)
docker compose down -v

# Перебудувати API контейнер
docker compose build api

# Запустити команду всередині API контейнера
docker compose exec api bash

# Виконати міграції (коли будуть доступні)
docker compose exec api python -m alembic upgrade head
```

## 🛠 Розробка

### Структура проекту

```
├── app/
│   ├── api/           # API endpoints
│   ├── core/          # Конфігурація та безпека
│   ├── db/            # База даних
│   ├── models/        # SQLAlchemy моделі
│   ├── schemas/       # Pydantic схеми
│   └── services/      # Бізнес логіка
├── docker/            # Docker конфігурація
├── main.py           # Точка входу
├── pyproject.toml    # Poetry залежності
└── docker-compose.yml
```

### Локальна розробка без Docker

Якщо хочете розробляти без Docker:

1. **Встановіть Poetry:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. **Встановіть залежності:**

```bash
poetry install
```

3. **Запустіть PostgreSQL локально або використовуйте SQLite:**

```bash
# Для SQLite (за замовчуванням)
export DATABASE_URL="sqlite+aiosqlite:///./sql_app.db"

# Або для PostgreSQL
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/geosocial_app"
```

4. **Запустіть API:**

```bash
poetry run python main.py
```

## 🗄️ База даних

### Моделі даних

- **User** - користувачі системи
- **Post** - пости з фотографіями та геолокацією
- **Like** - лайки постів
- **Comment** - коментарі (планується)
- **Follow** - підписки (планується)

### Міграції

Міграції бази даних поки що виконуються автоматично при старті API через SQLAlchemy.

## 🔑 API Endpoints

### Аутентифікація

- `POST /api/v1/register` - Реєстрація
- `POST /api/v1/login` - Вхід

### Користувачі

- `GET /api/v1/me` - Поточний користувач
- `PUT /api/v1/me` - Оновити профіль
- `GET /api/v1/users/{user_id}` - Профіль користувача

### Пости

- `GET /api/v1/posts/` - Список постів (стрічка)
- `GET /api/v1/posts/map` - Пости на карті
- `POST /api/v1/posts/` - Створити пост
- `GET /api/v1/posts/{post_id}` - Деталі поста
- `PUT /api/v1/posts/{post_id}` - Оновити пост
- `DELETE /api/v1/posts/{post_id}` - Видалити пост

### Лайки

- `POST /api/v1/posts/{post_id}/like` - Лайкнути пост
- `DELETE /api/v1/posts/{post_id}/like` - Прибрати лайк
- `GET /api/v1/posts/{post_id}/likes` - Список лайків

## 🧪 Тестування

```bash
# Запуск тестів (коли будуть доступні)
docker compose exec api pytest

# Або локально
poetry run pytest
```

## 📦 Технології

- **FastAPI** - Web framework
- **SQLAlchemy** - ORM з async підтримкою
- **PostgreSQL** - Основна база даних
- **Redis** - Кешування (опційно)
- **Cloudinary** - Зберігання зображень
- **Docker** - Контейнеризація
- **Poetry** - Управління залежностями

## 🚧 Статус розробки

Проект знаходиться в активній розробці. Дивіться [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md) для детального плану.

### ✅ Реалізовано

- Базова структура API
- Аутентифікація користувачів
- CRUD операції з постами
- Система лайків
- Завантаження зображень
- Docker конфігурація

### 🚧 В розробці

- Система коментарів
- Підписки на користувачів
- Приватність постів
- Гостьовий режим

## 📄 Ліцензія

MIT License
