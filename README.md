# Auth System — Система аутентификации и авторизации

Backend-приложение на **Django REST Framework + PostgreSQL** с собственной JWT-аутентификацией и гибкой ролевой системой доступа (RBAC).

---

## Стек технологий

- **Python 3.11+** / **Django 4.2** / **Django REST Framework 3.14**
- **PostgreSQL** — основная база данных
- **PyJWT** — генерация и валидация JWT-токенов
- **bcrypt** — хэширование паролей
- **Docker + docker-compose** — контейнеризация

---

## Архитектура проекта

Проект следует принципу разделения ответственности:

- **Models** — описание схемы БД
- **Serializers** — валидация входящих данных
- **Services** — вся бизнес-логика (AuthService, RoleService, ProductService и др.)
- **Views** — только HTTP-слой: принять запрос → вызвать сервис → вернуть ответ
- **Permissions** — декораторы `login_required`, `permission_required`, `admin_required`
- **Middleware** — `JWTAuthMiddleware` устанавливает `request.current_user` на каждый запрос

---

## Схема базы данных

### Таблица `users` — Пользователи

| Поле          | Тип          | Описание                             |
|---------------|--------------|--------------------------------------|
| id            | BIGINT PK    | Первичный ключ                       |
| first_name    | VARCHAR(100) | Имя                                  |
| last_name     | VARCHAR(100) | Фамилия                              |
| patronymic    | VARCHAR(100) | Отчество (необязательно)             |
| email         | VARCHAR      | Уникальный email (логин)             |
| password_hash | VARCHAR(255) | Хэш пароля (bcrypt)                  |
| is_active     | BOOLEAN      | False = мягко удалён, не может войти |
| created_at    | TIMESTAMP    | Дата регистрации                     |
| updated_at    | TIMESTAMP    | Дата последнего обновления           |

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

| Поле        | Тип         | Описание                           |
|-------------|-------------|------------------------------------|
| id          | BIGINT PK   | Первичный ключ                     |
| name        | VARCHAR(50) | Название: admin/manager/user/guest |
| description | TEXT        | Описание роли                      |

### Таблица `user_roles` — Назначение ролей

| Поле        | Тип       | Описание        |
|-------------|-----------|-----------------|
| id          | BIGINT PK | Первичный ключ  |
| user_id     | FK→users  | Пользователь    |
| role_id     | FK→roles  | Роль            |
| assigned_at | TIMESTAMP | Когда назначена |

> Один пользователь может иметь несколько ролей. Права суммируются по OR.

### Таблица `business_elements` — Бизнес-объекты

| Поле        | Тип          | Описание                             |
|-------------|--------------|--------------------------------------|
| id          | BIGINT PK    | Первичный ключ                       |
| name        | VARCHAR(100) | Кодовое имя ресурса (products и др.) |
| description | TEXT         | Описание                             |

Предопределённые объекты: `products`, `orders`, `shops`, `users`, `access_rules`.

### Таблица `access_rules` — Правила доступа

| Поле       | Тип             | Описание                                     |
|------------|-----------------|----------------------------------------------|
| id         | BIGINT PK       | Первичный ключ                               |
| role_id    | FK→roles        | Роль                                         |
| element_id | FK→business_el. | Бизнес-объект                                |
| read       | BOOLEAN         | Читать **свои** объекты (owner_id = user.id) |
| read_all   | BOOLEAN         | Читать **все** объекты                       |
| create     | BOOLEAN         | Создавать объекты                            |
| update     | BOOLEAN         | Изменять **свои** объекты                    |
| update_all | BOOLEAN         | Изменять **все** объекты                     |
| delete     | BOOLEAN         | Удалять **свои** объекты                     |
| delete_all | BOOLEAN         | Удалять **все** объекты                      |

### Таблицы бизнес-объектов — `products`, `orders`, `shops`

Реальные таблицы в БД с полем `owner` (FK→users) для проверки владельца.

---

## Матрица прав (тестовые данные)

| Роль    | Ресурс      | read | read_all | create | update | update_all | delete | delete_all |
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
3. Генерируется **JWT-токен** (PyJWT), сессия сохраняется в таблице `sessions`.
4. Клиент передаёт заголовок: `Authorization: Bearer <token>`.
5. **JWTAuthMiddleware** декодирует токен, проверяет активность сессии в БД, устанавливает `request.current_user`.
6. При `logout` — сессия помечается `is_active=False`.

---

## API-эндпоинты

### Аутентификация `/api/auth/`

| Метод  | URL              | Описание                   | Аутентификация |
|--------|------------------|----------------------------|----------------|
| POST   | /register/       | Регистрация                | Нет            |
| POST   | /login/          | Вход, получение токена     | Нет            |
| POST   | /logout/         | Выход (деактивация сессии) | Да             |
| GET    | /profile/        | Просмотр профиля           | Да             |
| PATCH  | /profile/        | Обновление профиля         | Да             |
| DELETE | /profile/delete/ | Мягкое удаление аккаунта   | Да             |

### Управление правами `/api/access/` (только admin)

| Метод            | URL               | Описание                              |
|------------------|-------------------|---------------------------------------|
| GET/POST         | /roles/           | Список/создание ролей                 |
| GET/PATCH/DELETE | /roles/\<id\>/    | Детали/редактирование/удаление роли   |
| GET/POST         | /elements/        | Список/создание бизнес-объектов       |
| GET/POST         | /rules/           | Список/создание правил доступа        |
| GET/PATCH/DELETE | /rules/\<id\>/    | Детали/редактирование правила         |
| GET/POST         | /user-roles/      | Список/назначение ролей пользователям |
| DELETE           | /user-roles/\<id\>/ | Отозвать роль у пользователя        |

### Бизнес-объекты `/api/business/`

| Метод  | URL              | Право               |
|--------|------------------|---------------------|
| GET    | /products/       | read / read_all     |
| POST   | /products/       | create              |
| GET    | /products/\<id\>/ | read / read_all    |
| PATCH  | /products/\<id\>/ | update / update_all |
| DELETE | /products/\<id\>/ | delete / delete_all |
| GET    | /orders/         | read / read_all     |
| POST   | /orders/         | create              |
| GET    | /shops/          | read_all            |
| POST   | /shops/          | create              |

---

## Запуск через Docker (рекомендуется)

### 1. Клонировать репозиторий

```bash
git clone https://github.com/vladonsikos/auth-project.git
cd auth-project
```

### 2. Запустить

```bash
docker compose up --build
```

Сервер автоматически:
- поднимет PostgreSQL
- применит миграции
- загрузит тестовые данные (`seed_data`)
- запустится на `http://localhost:8000`

### 3. Остановить

```bash
docker compose down
```

> Данные PostgreSQL сохраняются в Docker volume `postgres_data`. Для полного сброса: `docker compose down -v`

---

## Запуск локально (Ubuntu)

### 1. Установка зависимостей

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib
```

### 2. Создание базы данных

```bash
sudo -u postgres psql
```

```sql
CREATE USER auth_user WITH PASSWORD 'auth_password';
CREATE DATABASE auth_db OWNER auth_user;
GRANT ALL PRIVILEGES ON DATABASE auth_db TO auth_user;
\q
```

### 3. Виртуальное окружение и зависимости

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Переменные окружения

```bash
cp .env.example .env
nano .env
```

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

### 5. Миграции и тестовые данные

```bash
python manage.py migrate
python manage.py seed_data
```

### 6. Запуск

```bash
python manage.py runserver
```

Сервер: `http://127.0.0.1:8000`

---

## Тестовые пользователи

| Роль    | Email               | Пароль     |
|---------|---------------------|------------|
| admin   | admin@example.com   | admin123   |
| manager | manager@example.com | manager123 |
| user    | user@example.com    | user1234   |
| guest   | guest@example.com   | guest123   |

---

## Запуск тестов

```bash
python manage.py test tests --verbosity=2
```

**62 теста** покрывают:
- Регистрацию, вход, выход, профиль, удаление аккаунта
- RBAC: роли, правила доступа, назначение ролей (только admin)
- Бизнес-объекты: права read/read_all, create, update/update_all, delete/delete_all
- Граничные случаи: 401, 403, 404, 400

---

## Примеры запросов (curl)

### Регистрация

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Иван","last_name":"Иванов","email":"ivan@test.com","password":"pass1234","password_confirm":"pass1234"}'
```

### Вход

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
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt
├── .env.example
├── manage.py
├── config/
│   ├── settings.py          # Настройки Django
│   └── urls.py              # Корневые URL
├── apps/
│   ├── users/               # Аутентификация
│   │   ├── models.py        # User, Session
│   │   ├── serializers.py   # Register, Login, Profile serializers
│   │   ├── services.py      # AuthService — вся логика auth
│   │   ├── middleware.py    # JWTAuthMiddleware
│   │   ├── utils.py         # bcrypt + JWT helpers
│   │   ├── views.py         # Тонкие views, делегируют в AuthService
│   │   └── urls.py
│   ├── access/              # Авторизация (RBAC)
│   │   ├── models.py        # Role, UserRole, BusinessElement, AccessRule
│   │   ├── serializers.py
│   │   ├── services.py      # RoleService, AccessRuleService, UserRoleService
│   │   ├── permissions.py   # login_required, permission_required, admin_required
│   │   ├── views.py         # Admin API — тонкие views
│   │   ├── urls.py
│   │   └── management/commands/seed_data.py
│   └── business/            # Бизнес-объекты
│       ├── models.py        # Product, Order, Shop
│       ├── serializers.py
│       ├── services.py      # ProductService, OrderService, ShopService
│       ├── views.py         # get_object_or_404, RBAC-проверки через сервисы
│       └── urls.py
└── tests/
    ├── test_auth.py         # 16 тестов аутентификации
    ├── test_access.py       # 22 теста RBAC
    └── test_business.py     # 24 теста бизнес-объектов
```
