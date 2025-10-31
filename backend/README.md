# Onion Architecture FastAPI Application

Приложение с луковой (Onion) архитектурой на FastAPI с поддержкой MongoDB и PostgreSQL, включая полную систему аутентификации.

## Архитектура

```
onion_backend/
├── src/
│   ├── domain/           # Ядро - бизнес-логика (независима от всего)
│   ├── application/      # Слой приложения - use cases
│   ├── infrastructure/   # Внешний слой - реализации БД и security
│   ├── api/              # Внешний слой - HTTP endpoints
│   └── main.py          # Точка входа приложения
├── requirements.txt
├── .env.example
└── README.md
```

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Создайте `.env` файл:
```bash
cp .env.example .env
```

3. Настройте переменные окружения в `.env`

## Запуск

### С MongoDB:
```bash
# В .env установите:
DATABASE_TYPE=mongodb

# Запустите приложение (из корня проекта):
cd onion_backend
python -m src.main
```

### С PostgreSQL:
```bash
# В .env установите:
DATABASE_TYPE=postgresql

# Запустите приложение:
cd onion_backend
python -m src.main
```

## API Endpoints

### Общие
- `GET /` - Root endpoint
- `GET /health` - Health check

### Аутентификация
- `POST /auth/signup` - Регистрация нового пользователя
- `POST /auth/login` - Вход (получение JWT токена)
- `GET /auth/me` - Информация о текущем пользователе
- `GET /self` - Расширенная информация (с energy, level, xp)

### Pairs (примеры CRUD)
- `GET /api/pairs` - Получить все пары
- `GET /api/pairs/{pair_id}` - Получить пару по ID
- `POST /api/pairs` - Создать новую пару
- `PUT /api/pairs/{pair_id}` - Обновить пару
- `DELETE /api/pairs/{pair_id}` - Удалить пару
- `DELETE /api/delete_all` - Удалить все пары
- `GET /api/pairs/search?q=query` - Поиск пар через Elasticsearch

## Документация API

После запуска доступна по адресу:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Аутентификация

Приложение использует JWT токены для аутентификации.

### Пример использования:

1. **Регистрация:**
```bash
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "email": "user@example.com", "password": "secret123"}'
```

2. **Вход:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login": "user@example.com", "password": "secret123"}'
```

3. **Использование токена:**
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer <your-token>"
```

## Переключение между БД

Просто измените `DATABASE_TYPE` в `.env` файле:
- `mongodb` - для MongoDB
- `postgresql` - для PostgreSQL

Dependency Injection автоматически выберет нужную реализацию репозитория.

## Преимущества архитектуры

1. **Независимость от БД** - легко переключаться между MongoDB и PostgreSQL
2. **Тестируемость** - каждый слой можно тестировать отдельно
3. **Чистая бизнес-логика** - domain слой не зависит от frameworks
4. **SOLID принципы** - четкое разделение ответственности
5. **Безопасность** - JWT токены, хеширование паролей с солью

## Структура слоев

### Domain Layer (Ядро)
- `entities.py` - Доменные модели (Pair, User)
- `interfaces.py` - Абстракции репозиториев и сервисов

### Application Layer
- `services.py` - Бизнес-логика (PairService)
- `auth_service.py` - Логика аутентификации (AuthService)
- `dto.py` - Data Transfer Objects

### Infrastructure Layer
- `database/mongodb.py` - MongoDB реализации (Pair, User)
- `database/postgresql.py` - PostgreSQL реализации (Pair, User)
- `database/elasticsearch.py` - Elasticsearch клиент
- `security/password.py` - Хеширование паролей (SHA256 + salt)
- `security/jwt_handler.py` - JWT токены (HS256)
- `config.py` - Конфигурация приложения

### API Layer
- `main.py` - FastAPI приложение
- `routes.py` - HTTP endpoints для Pairs
- `auth_routes.py` - HTTP endpoints для аутентификации
- `self_routes.py` - HTTP endpoint /self
- `dependencies.py` - Dependency Injection

## Диаграмма зависимостей

```
API Layer
    ↓
Application Layer
    ↓
Domain Layer (Interfaces)
    ↑
Infrastructure Layer (Implementations)
```

## Особенности реализации

- **Energy система**: пользователи имеют energy, которая автоматически восстанавливается каждый день
- **Leveling**: система уровней и опыта для пользователей
- **Атомарные операции**: использование атомарных обновлений для energy
- **Асинхронность**: полностью асинхронное приложение
- **Type hints**: строгая типизация везде
