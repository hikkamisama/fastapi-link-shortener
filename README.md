# FastAPI URL Shortener

---

## Описание API:

| Метод | Эндпоинт              | Требует Auth        | Описание                                                                         |
| :--------- | :---------------------------- | :------------------------- | :--------------------------------------------------------------------------------------- |
| `POST`   | `/signup`                   | ❌                         | Регистрация нового пользователя                             |
| `POST`   | `/login`                    | ❌                         | Получение JWT токена                                                      |
| `POST`   | `/links/shorten`            | 🔘 (Для алиасов) | Создание короткой ссылки                                           |
| `GET`    | `/links/search`             | ❌                         | Поиск коротких ссылок по оригинальному URL             |
| `GET`    | `/links/history/deleted`    | ✅                         | Просмотр истории удаленных ссылок пользователя |
| `GET`    | `/links/{short_code}/stats` | ✅                         | Получение статистики кликов (и статуса)                 |
| `GET`    | `/links/{short_code}`       | ❌                         | Редирект на оригинальный URL                                       |
| `PUT`    | `/links/{short_code}`       | ✅                         | Обновление ссылки (смена URL, алиаса или даты)         |
| `DELETE` | `/links/{short_code}`       | ✅                         | Удаление (Soft-delete) ссылки владельцем                         |
| `DELETE` | `/links/cleanup/inactive`   | **admin**            | Принудительный Soft-delete неактивных ссылок               |
| `DELETE` | `/links/cleanup/purge`      | **admin**            | Безвозвратное удаление записей (Hard-delete) из БД       |

## Примеры запросов

### 1. Регистрация и Авторизация

Создание аккаунта:

```bash
curl -X POST "http://localhost:8000/signup"
    -H "Content-Type: application/json"
    -d '{"username": "johndoe", "password": "supersecretpassword"}'
```

Получение токена авторизации:

```bash
curl -X POST "http://localhost:8000/login"
    -H "Content-Type: application/json"
    -d '{"username": "johndoe", "password": "supersecretpassword"}'
```

### 2. Создание короткой ссылки (с кастомным алиасом)

*Замените <ТОКЕН> на токен из предыдущего шага.*

```bash
curl -X POST "http://localhost:8000/links/shorten"
    -H "Authorization: Bearer <ТОКЕН>"
    -H "Content-Type: application/json"
    -d '{"url": "https://github.com", "alias": "my-git"}'
```

### 3. Редирект (Получение оригинального сайта)

```
curl -i "http://localhost:8000/links/my-git"
```

*Сервер ответит заголовком 307 Temporary Redirect и полем Location: https://github.com/.*

### 4. Получение статистики кликов

```bash
curl -X GET "http://localhost:8000/links/my-git/stats"
    -H "Authorization: Bearer <ТОКЕН>"
```

*Пример ответа:*

```
{
  "original_url": "https://github.com/",
  "short_code": "my-git",
  "clicks": 1,
  "created_at": "2024-05-25T14:32:00Z"
}
```

## Инструкция по запуску

1. Склонируйте репозиторий и перейдите в папку:

   ```
   git clone https://github.com/hikkamisama/fastapi-link-shortener.git
   cd url-shortener
   mkdir data
   ```
2. Настройка env:

   ```
   python -m venv link-shortener
   source link-shortener/bin/activate
   python -m pip install -r requirements.txt
   ```
3. Запустите сервис:

   ```
   docker-compose up --build -d
   ```

   Сервер будет доступен по адресу: `http://localhost:8000`

   Альтренативно можно запустить сервис самостоятельно:

   ```uvicorn
   uvicorn app.main:app --reload
   ```
4. Настройте .env (пример):

   ```
   DATABASE_URL=sqlite:///./shortener.db
   REDIS_URL=redis://localhost:6379/0
   SECRET_KEY=your_super_secret_jwt_key
   DOMAIN=http://localhost:8000
   ```

## Описание БД

Проект использует реляционную базу данных (SQLite/PostgreSQL) под управлением SQLAlchemy ORM. Схема состоит из двух основных таблиц со связью «one-to-many»

### Таблица `users` (Пользователи)

| Поле            | Тип       | Описание                                                             |
| :------------------ | :----------- | :--------------------------------------------------------------------------- |
| `id`              | Integer (PK) | Уникальный идентификатор                              |
| `username`        | String       | Уникальное имя пользователя                         |
| `hashed_password` | String       | Зашифрованный пароль                                      |
| `role`            | String       | Роль (по умолчанию `user`, для админов `admin`) |
| `created_at`      | DateTime     | Дата регистрации                                              |

### Таблица `links` (Ссылки)

| Поле         | Тип       | Описание                                                                               |
| :--------------- | :----------- | :--------------------------------------------------------------------------------------------- |
| `id`           | Integer (PK) | Уникальный идентификатор                                                |
| `original_url` | String       | Исходная длинная ссылка                                                   |
| `short_id`     | String       | Сгенерированный код или кастомный алиас                     |
| `user_id`      | Integer (FK) | ID владельца (может быть `NULL` для анонимов)                   |
| `clicks`       | Integer      | Счетчик переходов                                                              |
| `is_active`    | Boolean      | Статус ссылки (Soft Delete)                                                        |
| `expires_at`   | DateTime     | Дата автоматического истечения срока (опционально) |
| `deleted_at`   | DateTime     | Дата удаления (при soft delete)                                                 |
