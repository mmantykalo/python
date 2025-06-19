# 🧪 Тестування API

Швидкий посібник для тестування API ендпоінтів геосоціальної мережі.

## 🚀 Швидкий старт

1. **Запустіть API в Docker:**

```bash
docker compose up -d
```

2. **Перевірте статус:**

```bash
docker compose ps
```

3. **Відкрийте Swagger документацію:**

```
http://localhost:8000/docs
```

## 📝 Тестування через curl

### 1. Реєстрація користувача

```bash
curl -X POST "http://localhost:8000/api/v1/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpassword"
  }'
```

### 2. Вхід в систему

```bash
curl -X POST "http://localhost:8000/api/v1/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpassword"
  }'
```

Збережіть токен з відповіді для наступних запитів.

### 3. Перевірка профілю

```bash
# Замініть YOUR_TOKEN на отриманий токен
# УВАГА: Тепер використовуємо кастомний header X-Authorization
curl -X GET "http://localhost:8000/api/v1/me" \
  -H "X-Authorization: Bearer YOUR_TOKEN"
```

### 4. Створення поста (з файлом)

```bash
# Створіть тестове зображення або використовуйте існуюче
curl -X POST "http://localhost:8000/api/v1/posts/" \
  -H "X-Authorization: Bearer YOUR_TOKEN" \
  -F "image=@/path/to/your/image.jpg" \
  -F "comment=Мій перший пост!" \
  -F "latitude=50.4501" \
  -F "longitude=30.5234"
```

### 5. Отримання постів

```bash
# Всі пости (стрічка)
curl "http://localhost:8000/api/v1/posts/"

# Пости на карті (геолокація)
curl "http://localhost:8000/api/v1/posts/map?lat_min=50.0&lat_max=51.0&lon_min=30.0&lon_max=31.0"
```

### 6. Лайк поста

```bash
# Замініть POST_ID на ID реального поста
curl -X POST "http://localhost:8000/api/v1/posts/POST_ID/like" \
  -H "X-Authorization: Bearer YOUR_TOKEN"
```

## 🛠 Тестування через Swagger UI

1. **Відкрийте** http://localhost:8000/docs
2. **Натисніть "Authorize"** у правому верхньому куті
3. **Введіть токен** у форматі: `Bearer YOUR_TOKEN` в поле X-Authorization
4. **Тестуйте ендпоінти** через інтерфейс

⚠️ **ВАЖЛИВО**: Тепер для авторизації використовується кастомний header `X-Authorization` замість стандартного `Authorization`. Формат залишається такий же: `Bearer YOUR_TOKEN`

## 🗄️ Перевірка бази даних

### Підключення до PostgreSQL:

```bash
# Через Docker
docker compose exec db psql -U postgres -d geosocial_app

# Або локально (якщо встановлено psql)
psql -h localhost -p 5432 -U postgres -d geosocial_app
```

### Корисні SQL запити:

```sql
-- Переглянути всіх користувачів
SELECT * FROM users;

-- Переглянути всі пости
SELECT * FROM posts;

-- Переглянути лайки
SELECT * FROM likes;

-- Пости з інформацією про користувача
SELECT p.*, u.username
FROM posts p
JOIN users u ON p.user_id = u.id;
```

## 🐛 Відладка

### Переглянути логи:

```bash
# API логи
docker compose logs -f api

# База даних логи
docker compose logs -f db

# Всі логи
docker compose logs -f
```

### Перезапуск сервісів:

```bash
# Перезапустити API
docker compose restart api

# Повний перезапуск
docker compose down && docker compose up -d
```

### Очистка бази даних:

```bash
# УВАГА: Видалить всі дані!
docker compose down -v
docker compose up -d
```

## 📊 Приклади відповідей API

### Успішна реєстрація:

```json
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com",
  "created_at": "2024-01-01T12:00:00.000Z",
  "updated_at": "2024-01-01T12:00:00.000Z"
}
```

### Токен авторизації:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Список постів:

```json
{
  "items": [
    {
      "id": 1,
      "image_url": "https://res.cloudinary.com/...",
      "comment": "Красивий захід сонця!",
      "latitude": 50.4501,
      "longitude": 30.5234,
      "user_id": 1,
      "created_at": "2024-01-01T12:00:00.000Z",
      "likes_count": 5
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10
}
```

## ⚠️ Поширені помилки

### 401 Unauthorized

- Перевірте, чи правильно передається токен
- Перевірте, чи не закінчився термін дії токена

### 422 Validation Error

- Перевірте формат JSON
- Перевірте обов'язкові поля

### 500 Internal Server Error

- Перевірте логи API: `docker compose logs api`
- Перевірте підключення до бази даних
