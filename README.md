# Auth Project

Полнофункциональная система аутентификации и авторизации с ролевой моделью доступа (RBAC). Административная панель для управления пользователями, ролями и правами доступа к бизнес-объектам.

## Стек

| Слой | Технологии |
|------|-----------|
| **Backend** | Python 3.11, Django 4.2, Django REST Framework, PostgreSQL 15, PyJWT, bcrypt |
| **Frontend** | React 18, TypeScript, Vite, Material UI 5, TanStack Query, React Hook Form, Zod, i18next |
| **Инфраструктура** | Docker, Docker Compose, Nginx, Gunicorn |
| **Тестирование** | Django TestCase (backend), Vitest + MSW + Playwright (frontend) |
| **CI/CD** | GitHub Actions → SSH deploy на VPS |

## Быстрый старт

```bash
git clone <repo>
cd auth_project
cp .env.example .env
cp frontend/.env.example frontend/.env
docker compose up -d
```

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api |

## Тестовые учётные данные

| Роль | Email | Пароль |
|------|-------|--------|
| Admin | admin@example.com | admin123 |
| Manager | manager@example.com | manager123 |
| User | user@example.com | user1234 |
| Guest | guest@example.com | guest123 |

## Структура проекта

```
auth_project/
├── .env.example               # Переменные окружения бэкенда
├── .github/workflows/ci.yml   # GitHub Actions: lint → test → build → deploy
├── apps/
│   ├── users/                 # Пользователи, JWT-аутентификация, логи действий
│   ├── access/                # Роли, RBAC-права, бизнес-элементы
│   └── business/              # Бизнес-объекты: товары, магазины, заказы
├── config/                    # Настройки Django, URL-маршруты
├── tests/                     # Backend тесты (62 теста)
└── frontend/
    ├── .env.example           # Переменные окружения фронтенда
    └── src/
        ├── app/               # Инициализация, провайдеры, роутинг
        ├── pages/             # Login, Dashboard, Users, Roles, Profile
        ├── features/auth/     # AuthContext, useAuth, ProtectedRoute
        ├── entities/          # API-клиенты: user, role, access
        ├── shared/            # UI-компоненты, хуки, тема, i18n, axios
        ├── widgets/           # Layout, AccessRuleDialog
        └── tests/             # Unit + E2E тесты
```

## Возможности

- JWT-аутентификация (вход, выход, профиль, смена пароля)
- CRUD пользователей с поиском, фильтрацией, пагинацией, экспортом CSV
- RBAC: 4 предустановленные роли (Admin, Manager, User, Guest) с настройкой прав (`read`, `create`, `update`, `delete` и `_all`-варианты)
- Retry logic: до 3 попыток с экспоненциальной задержкой (axios + TanStack Query)
- Логирование действий: `useLogger` → `POST /api/logs/` + консоль
- Sentry: инициализируется при наличии `VITE_SENTRY_DSN`
- Тёмная/светлая тема, мультиязычность (RU/EN)
- Серверная пагинация и сортировка
- Lazy loading страниц (React.lazy + Suspense), code splitting бандла

## Переменные окружения

Проект использует два `.env` файла — по одному для каждого приложения.

### Бэкенд (`.env`)

```bash
cp .env.example .env
```

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `SECRET_KEY` | Django secret key | — |
| `DEBUG` | Режим отладки | `False` |
| `DB_NAME` | Имя базы данных | `auth_db` |
| `DB_USER` | Пользователь БД | `postgres` |
| `DB_PASSWORD` | Пароль БД | — |
| `DB_HOST` | Хост БД | `localhost` |
| `DB_PORT` | Порт БД | `5432` |
| `JWT_SECRET` | Секрет для JWT токенов | — |
| `JWT_EXPIRATION_HOURS` | Время жизни токена (часы) | `24` |

### Фронтенд (`frontend/.env`)

```bash
cp frontend/.env.example frontend/.env
```

| Переменная | Описание | По умолчанию |
|-----------|----------|-------------|
| `VITE_API_URL` | URL бэкенд API | `/api` |
| `VITE_SENTRY_DSN` | DSN для Sentry (опционально) | пусто |

> `VITE_API_URL=/api` — относительный путь, Nginx проксирует `/api` → `http://backend:8000`. При локальной разработке без Docker используй `http://localhost:8000/api`.

## Тесты

```bash
# Backend (62 теста)
docker compose exec backend python manage.py test tests --verbosity=2

# Frontend unit-тесты (Vitest + MSW)
cd frontend && npm test -- --run

# Frontend с покрытием
cd frontend && npm run test:coverage

# E2E тесты (Playwright)
cd frontend && npm run test:e2e
```

## Деплой

### Docker Compose

```bash
docker compose up -d --build
```

### GitHub Actions CI/CD

Workflow `.github/workflows/ci.yml` выполняет при пуше в `main`:
1. Lint + type-check
2. Unit-тесты
3. Сборка бандла
4. SSH-деплой на VPS

Необходимые секреты в GitHub:

| Секрет | Описание |
|--------|----------|
| `VITE_API_URL` | URL API на продакшене |
| `VITE_SENTRY_DSN` | Sentry DSN |
| `VPS_HOST` | IP/домен сервера |
| `VPS_USER` | SSH-пользователь |
| `VPS_SSH_KEY` | Приватный SSH-ключ |

## API

```
POST   /api/auth/login/           # Вход → JWT токен
POST   /api/auth/logout/          # Выход
POST   /api/auth/register/        # Регистрация
GET    /api/auth/profile/         # Профиль текущего пользователя

GET    /api/auth/users/           # Список пользователей (пагинация, фильтры)
POST   /api/auth/users/           # Создать пользователя
PATCH  /api/auth/users/{id}/      # Обновить пользователя
DELETE /api/auth/users/{id}/      # Удалить пользователя

GET    /api/access/roles/         # Список ролей
POST   /api/access/roles/         # Создать роль
PATCH  /api/access/roles/{id}/    # Обновить роль
DELETE /api/access/roles/{id}/    # Удалить роль

GET    /api/access/rules/         # Правила доступа
POST   /api/access/rules/         # Создать правило
PATCH  /api/access/rules/{id}/    # Обновить правило

GET    /api/access/elements/      # Бизнес-элементы
POST   /api/logs/                 # Лог действия пользователя
```
