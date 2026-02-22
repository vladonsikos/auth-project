# Auth System — Система аутентификации и авторизации

Backend-приложение на **Django REST Framework + PostgreSQL** с собственной JWT-аутентификацией и гибкой ролевой системой доступа (RBAC).

---

## Схема базы данных

### Таблица `users` — Пользователи

| Поле           | Тип          | Описание                              |
|----------------|--------------|---------------------------------------|
| id             | BIGINT PK    | Первичный ключ                        |
| first_name     | VARCHAR(100) | Имя                                   |
| last_name      | VARCHAR(100) | Фамилия                               |
| patronymic     | VARCHAR(100) | Отчество (необязательно)              |
| email          | VARCHAR      | Уникальный email (логин)              |
| password_hash  | VARCHAR(255) | Хэш пароля (bcrypt)                   |
| is_active      | BOOLEAN      | False = мягко удалён, не может войти  |
| created_at     | TIMESTAMP    | Дата регистрации                      |
| updated_at     | TIMESTAMP    | Дата последнего обновления            |

### Таблица `sessions` — Сессии (JWT)

| Поле       | Тип       | Описание                            |
|------------|-----------|-------------------------------------|
| id         | BIGINT PK | Первичный ключ                      |
| user_id    | FK→users  | Пользователь                        |
| token      | TEXT      | JWT-токен                           |
| created_at | TIMESTAMP | Дата создания                       |
| expires_at | TIMESTAMP | Дата истечения                      |
| is_active  | BOOLEAN   | False = пользователь вышел (logout) |

### Таблица `roles` — Роли

| Поле        | Тип          | Описание               |
|-------------|--------------|------------------------|
| id          | BIGINT PK    | Первичный ключ         |
| name        | VARCHAR(50)  | Название: admin/manager/user/guest |
| description | TEXT         | Описание роли          |

### Таблица `user_roles` — Назначение ролей

| Поле        | Тип       | Описание            |
|-------------|-----------|---------------------|
| id          | BIGINT PK | Первичный ключ      |
| user_id     | FK→users  | Пользователь        |
| role_id     | FK→roles  | Роль                |
| assigned_at | TIMESTAMP | Когда назначена     |

> Один пользователь может иметь несколько ролей. Права суммируются по OR.

### Таблица `business_elements` — Бизнес-объекты

| Поле        | Тип          | Описание                             |
|-------------|--------------|--------------------------------------|
| id          | BIGINT PK    | Первичный ключ                       |
| name        | VARCHAR(100) | Кодовое имя ресурса (products и др.) |
| description | TEXT         | Описание                             |

Предопределённые объекты: `products`, `orders`, `shops`, `users`, `access_rules`.

### Таблица `access_rules` — Правила доступа

| Поле        | Тип             | Описание                                      |
|-------------|-----------------|-----------------------------------------------|
| id          | BIGINT PK       | Первичный ключ                                |
| role_id     | FK→roles        | Роль                                          |
| element_id  | FK→business_el. | Бизнес-объект                                 |
| read        | BOOLEAN         | Читать **свои** объекты (owner_id = user.id)  |
| read_all    | BOOLEAN         | Читать **все** объекты                        |
| create      | BOOLEAN         | Создавать объекты                             |
| update      | BOOLEAN         | Изменять **свои** объекты                     |
| update_all  | BOOLEAN         | Изменять **все** объекты                      |
| delete      | BOOLEAN         | Удалять **свои** объекты                      |
| delete_all  | BOOLEAN         | Удалять **все** объекты                       |

---

## Матрица прав (тестовые данные)

| Роль    | Ресурс       | read | read_all | create | update | update_all | delete | delete_all |
|---------|-------------|------|----------|--------|--------|------------|--------|------------|
| admin   | все ресурсы | ✅   | ✅       | ✅     | ✅     | ✅         | ✅     | ✅         |
| manager | products    | ✅   | ✅       | ✅     | ✅     | ✅         | ❌     | ❌         |
| manager | orders      | ✅   | ✅       | ✅     | ✅     | ✅         | ❌     | ❌         |
| manager | shops       | ✅   | ✅       | ✅     | ✅     | ❌         | ❌     | ❌         |
| manager | users       | ✅   | ✅       | ❌     | ❌     | ❌         | ❌     | ❌         |
| user    | products    | ✅   | ❌       | ✅     | ✅     | ❌         | ✅     | ❌         |
| user    | orders      | ✅   | ❌       | ✅     | ✅     | ❌         | ✅     | ❌         |
| user    | shops       | ✅   | ❌       | ❌     | ❌     | ❌         | ❌     | ❌         |
| guest   | products    | ✅   | ✅       | ❌     | ❌     | ❌         | ❌     | ❌         |
| guest   | shops       | ✅   | ✅       | ❌     | ❌     | ❌         | ❌     | ❌         |

---

## Принцип работы аутентификации

1. Пользователь отправляет `POST /api/auth/login/` с email и паролем.
2. Пароль проверяется через **bcrypt**.
3. Генерируется **JWT-токен** (библиотека PyJWT), сессия сохраняется в таблице `sessions`.
4. Клиент в каждом запросе передаёт заголовок: `Authorization: Bearer <token>`.
5. Кастомный **JWTAuthMiddleware** декодирует токен, проверяет активность сессии в БД и устанавливает `request.current_user`.
6. При `logout` — сессия помечается `is_active=False`.

---

## API-эндпоинты

### Аутентификация `/api/auth/`

| Метод  | URL                    | Описание                     | Аутентификация |
|--------|------------------------|------------------------------|----------------|
| POST   | /register/             | Регистрация                  | Нет            |
| POST   | /login/                | Вход, получение токена       | Нет            |
| POST   | /logout/               | Выход (деактивация сессии)   | Да             |
| GET    | /profile/              | Просмотр профиля             | Да             |
| PATCH  | /profile/              | Обновление профиля           | Да             |
| DELETE | /profile/delete/       | Мягкое удаление аккаунта     | Да             |

### Управление правами `/api/access/` (только admin)

| Метод        | URL                   | Описание                     |
|--------------|-----------------------|------------------------------|
| GET/POST     | /roles/               | Список/создание ролей        |
| GET/PATCH/DELETE | /roles/<id>/      | Детали/редактирование/удаление роли |
| GET/POST     | /elements/            | Список/создание бизнес-объектов |
| GET/POST     | /rules/               | Список/создание правил доступа |
| GET/PATCH/DELETE | /rules/<id>/      | Детали/редактирование правила |
| GET/POST     | /user-roles/          | Список/назначение ролей пользователям |
| DELETE       | /user-roles/<id>/     | Отозвать роль у пользователя |

### Бизнес-объекты `/api/business/`

| Метод        | URL                   | Право            |
|--------------|-----------------------|------------------|
| GET          | /products/            | read_all         |
| POST         | /products/            | create           |
| GET          | /products/<id>/       | read / read_all  |
| PATCH        | /products/<id>/       | update / update_all |
| DELETE       | /products/<id>/       | delete / delete_all |
| GET          | /orders/              | read / read_all  |
| POST         | /orders/              | create           |
| GET          | /shops/               | read_all         |
| POST         | /shops/               | create           |

---

## Пошаговая инструкция по запуску (Ubuntu)

### 1. Установка зависимостей системы

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib
```

### 2. Создание базы данных PostgreSQL

```bash
sudo -u postgres psql
```

В psql выполнить:

```sql
CREATE USER auth_user WITH PASSWORD 'auth_password';
CREATE DATABASE auth_db OWNER auth_user;
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;
\q
```

### 3. Клонирование/распаковка проекта

```bash
cd ~
# Если получили архив:
unzip auth_project.zip -d auth_project
cd auth_project
```

### 4. Создание виртуального окружения и установка пакетов

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Заполнить `.env`:

```
SECRET_KEY=замените-на-случайную-строку
DEBUG=True
DB_NAME=auth_db
DB_USER=auth_user
DB_PASSWORD=auth_password
DB_HOST=localhost
DB_PORT=5432
JWT_SECRET=другая-случайная-строка-для-jwt
JWT_EXPIRATION_HOURS=24
```

### 6. Применение миграций

```bash
python manage.py makemigrations users access
python manage.py migrate
```

### 7. Загрузка тестовых данных

```bash
python manage.py seed_data
```

Будут созданы 4 тестовых пользователя:

| Роль    | Email                  | Пароль     |
|---------|------------------------|------------|
| admin   | admin@example.com      | admin123   |
| manager | manager@example.com    | manager123 |
| user    | user@example.com       | user1234   |
| guest   | guest@example.com      | guest123   |

### 8. Запуск сервера

```bash
python manage.py runserver
```

Сервер доступен по адресу: `http://127.0.0.1:8000`

---

## Примеры запросов (curl)

### Регистрация

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Иван","last_name":"Иванов","email":"ivan@test.com","password":"pass1234","password_confirm":"pass1234"}'
```

### Вход (получение токена)

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}'
```

### Использование токена

```bash
TOKEN="вставьте_токен_из_ответа_login"

# Просмотр профиля
curl http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Bearer $TOKEN"

# Список товаров
curl http://127.0.0.1:8000/api/business/products/ \
  -H "Authorization: Bearer $TOKEN"

# Список ролей (только admin)
curl http://127.0.0.1:8000/api/access/roles/ \
  -H "Authorization: Bearer $TOKEN"

# Изменить правило доступа (только admin)
curl -X PATCH http://127.0.0.1:8000/api/access/rules/1/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"create": false}'
```

### Выход

```bash
curl -X POST http://127.0.0.1:8000/api/auth/logout/ \
  -H "Authorization: Bearer $TOKEN"
```

---

## Структура проекта

```
auth_project/
├── config/
│   ├── settings.py       # Настройки Django
│   └── urls.py           # Корневые URL
├── apps/
│   ├── users/            # Аутентификация
│   │   ├── models.py     # User, Session
│   │   ├── middleware.py # JWTAuthMiddleware
│   │   ├── utils.py      # bcrypt + JWT
│   │   ├── views.py      # Register/Login/Logout/Profile
│   │   └── urls.py
│   ├── access/           # Авторизация (RBAC)
│   │   ├── models.py     # Role, UserRole, BusinessElement, AccessRule
│   │   ├── permissions.py# Декораторы: login_required, permission_required, admin_required
│   │   ├── views.py      # Admin API для ролей и правил
│   │   └── management/commands/seed_data.py
│   └── business/         # Mock бизнес-объекты
│       ├── views.py      # Products, Orders, Shops (mock data)
│       └── urls.py
├── requirements.txt
├── .env.example
└── README.md
```
