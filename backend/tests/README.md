# Backend Tests for SubReverse

Комплексный набор тестов для backend части SubReverse, покрывающий работу с PostgreSQL, MongoDB и API endpoints.

## Структура тестов

```
tests/
├── conftest.py                          # Фикстуры и конфигурация тестов
├── test_postgres_user_repository.py     # Тесты PostgreSQL user repository
├── test_mongo_subtitle_repository.py    # Тесты MongoDB subtitle repository
├── test_mongo_idiom_quote_repositories.py  # Тесты MongoDB idiom/quote/stats repositories
├── test_auth_endpoints.py               # Тесты аутентификации (signup, login, me)
├── test_subtitle_endpoints.py           # Тесты subtitle API endpoints
└── test_energy_leveling_system.py       # Тесты энергии и системы уровней
```

## Покрытие тестами

### PostgreSQL (User Management)
- ✅ Создание пользователя
- ✅ Получение по ID, email, username
- ✅ Обновление пользователя
- ✅ Атомарное обновление энергии (энергия +/-)
- ✅ Проверка недостаточной энергии
- ✅ Перезарядка энергии (новый день)
- ✅ Предотвращение перезарядки в тот же день

### MongoDB (Subtitle Pairs)
- ✅ Создание пары субтитров
- ✅ Получение по ID и seq_id
- ✅ Массовое создание пар
- ✅ Обновление рейтинга
- ✅ Обновление категории (idiom, quote, wrong, null)
- ✅ Удаление пары
- ✅ Поиск (простой и с точной фразой в кавычках)
- ✅ Получение случайной пары
- ✅ Подсчет общего количества
- ✅ Удаление дубликатов
- ✅ Получение списка файлов
- ✅ Временная навигация (offset для prev/next)

### MongoDB (Idioms, Quotes, Stats)
- ✅ Создание/обновление идиом (upsert)
- ✅ Получение последних идиом
- ✅ Создание/обновление цитат (upsert)
- ✅ Получение последних цитат
- ✅ Сохранение и получение статистики
- ✅ Обновление статистики

### Authentication Endpoints
- ✅ Регистрация (POST /auth/signup)
- ✅ Дубликат email/username
- ✅ Вход с email и username (POST /auth/login)
- ✅ Неверный пароль
- ✅ Получение текущего пользователя (GET /auth/me)
- ✅ Проверка токена
- ✅ Endpoint /self с перезарядкой энергии
- ✅ Email case-insensitive

### Subtitle Endpoints
- ✅ GET /api/get_random - случайная пара
- ✅ GET /api/search/{id}/ - получение по ID
- ✅ GET /api/search/{id}/?offset=N - временная навигация
- ✅ PATCH /api/search/{id}/ - обновление рейтинга/категории (требует auth)
- ✅ GET /api/search?q=query - поиск
- ✅ GET /api/idioms - список идиом
- ✅ GET /api/quotes - список цитат
- ✅ GET /api/stats - получение статистики
- ✅ POST /api/stats - вычисление статистики
- ✅ POST /api/clear - удаление дубликатов
- ✅ POST /api/delete_all - удаление всех пар

### Energy & Leveling System
- ✅ Начальная энергия (10) и уровень (1)
- ✅ Расход энергии при обновлении рейтинга
- ✅ Расход энергии при обновлении категории
- ✅ Блокировка действий при нулевой энергии
- ✅ Перезарядка энергии в новый день
- ✅ Отсутствие перезарядки в тот же день
- ✅ Триггер перезарядки через /self endpoint
- ✅ Начисление XP за действия
- ✅ Повышение уровня при достижении порога
- ✅ Увеличение max_energy на 5 при повышении уровня
- ✅ Сброс XP в 0 после повышения уровня
- ✅ Требование XP масштабируется (level * 10)
- ✅ Автоматическое создание idiom/quote при установке категории

## Требования

### Системные требования
- Python 3.10+
- PostgreSQL 15+
- MongoDB 4.4+
- Доступ к тестовым базам данных

### Python зависимости
Установите все зависимости:

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-test.txt
```

## Настройка тестовых баз данных

### PostgreSQL

Создайте тестовую базу данных:

```bash
# Войдите в PostgreSQL
psql -U postgres

# Создайте тестовую базу
CREATE DATABASE subreverse_test;

# Создайте пользователя (если еще не создан)
CREATE USER subreverse WITH PASSWORD 'subreverse';

# Дайте права
GRANT ALL PRIVILEGES ON DATABASE subreverse_test TO subreverse;
```

### MongoDB

MongoDB не требует предварительной настройки - тестовая база данных `subreverse_test` будет создана автоматически и очищена после тестов.

### Переменные окружения (опционально)

Вы можете переопределить URL баз данных через переменные окружения:

```bash
export TEST_POSTGRES_URL="postgresql+asyncpg://subreverse:subreverse@localhost:5432/subreverse_test"
export TEST_MONGODB_URL="mongodb://localhost:27017"
```

По умолчанию используются:
- PostgreSQL: `postgresql+asyncpg://subreverse:subreverse@localhost:5432/subreverse_test`
- MongoDB: `mongodb://localhost:27017` (база: `subreverse_test`)

## Запуск тестов

### Запуск всех тестов

```bash
cd backend
pytest tests/ -v
```

### Запуск конкретного файла тестов

```bash
# Тесты PostgreSQL
pytest tests/test_postgres_user_repository.py -v

# Тесты MongoDB
pytest tests/test_mongo_subtitle_repository.py -v

# Тесты аутентификации
pytest tests/test_auth_endpoints.py -v

# Тесты subtitle endpoints
pytest tests/test_subtitle_endpoints.py -v

# Тесты энергии и уровней
pytest tests/test_energy_leveling_system.py -v
```

### Запуск конкретного теста

```bash
pytest tests/test_auth_endpoints.py::TestAuthEndpoints::test_signup_success -v
```

### Запуск с покрытием кода

```bash
# Запуск с отчетом о покрытии
pytest tests/ --cov=src --cov-report=html --cov-report=term

# Просмотр HTML отчета
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Запуск с различными уровнями вывода

```bash
# Краткий вывод
pytest tests/

# Подробный вывод
pytest tests/ -v

# Очень подробный вывод (с print)
pytest tests/ -vv -s

# Показывать только упавшие тесты
pytest tests/ --tb=short

# Остановиться на первом падении
pytest tests/ -x

# Запустить только упавшие тесты
pytest tests/ --lf
```

### Параллельный запуск (опционально)

Для ускорения можно использовать pytest-xdist:

```bash
pip install pytest-xdist
pytest tests/ -n auto  # Автоматически определяет количество процессов
```

## Структура фикстур

### Базы данных
- `postgres_engine` - PostgreSQL engine
- `postgres_session` - PostgreSQL session (автоматический rollback)
- `postgres_user_repo` - PostgreSQL user repository
- `mongodb_client` - MongoDB client
- `mongodb_db` - MongoDB database (автоочистка после каждого теста)
- `mongo_subtitle_repo` - MongoDB subtitle repository
- `mongo_idiom_repo` - MongoDB idiom repository
- `mongo_quote_repo` - MongoDB quote repository
- `mongo_stats_repo` - MongoDB stats repository

### Безопасность
- `password_handler` - SHA256 password handler
- `jwt_handler` - JWT handler с тестовым секретом

### Сервисы
- `auth_service` - Authentication service
- `subtitle_service` - Subtitle service

### HTTP клиенты
- `async_client` - Асинхронный HTTP клиент для API
- `test_user` - Созданный тестовый пользователь
- `test_user_token` - JWT токен тестового пользователя
- `authenticated_client` - HTTP клиент с авторизацией

## Примеры использования фикстур

```python
@pytest.mark.asyncio
async def test_my_feature(postgres_user_repo, mongo_subtitle_repo):
    """Тест с использованием обоих репозиториев."""
    # Используйте репозитории напрямую
    user = await postgres_user_repo.get_by_id("some-id")
    pair = await mongo_subtitle_repo.get_random()

    assert user is not None
    assert pair is not None

@pytest.mark.asyncio
async def test_api_endpoint(authenticated_client):
    """Тест API endpoint с авторизацией."""
    response = await authenticated_client.get("/api/get_random")
    assert response.status_code == 200
```

## Очистка данных

Тесты автоматически очищают данные после выполнения:

- **PostgreSQL**: Использует транзакции с rollback после каждого теста
- **MongoDB**: Удаляет все документы из коллекций после каждого теста
- **Тестовая база**: PostgreSQL таблицы удаляются после завершения всех тестов

## Отладка тестов

### Просмотр print statements

```bash
pytest tests/ -s  # Показывает print() вывод
```

### Использование pdb

```python
import pdb; pdb.set_trace()  # Добавьте в тест для отладки
```

```bash
pytest tests/ -s  # Запуск с pdb
```

### Просмотр логов

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Известные проблемы

### PostgreSQL connection refused
Убедитесь, что PostgreSQL запущен:
```bash
# macOS
brew services start postgresql@15

# Linux
sudo systemctl start postgresql
```

### MongoDB connection refused
Убедитесь, что MongoDB запущен:
```bash
# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod

# Docker
docker run -d -p 27017:27017 mongo:4.4.18
```

### Ошибка "database does not exist"
Создайте тестовую базу данных вручную (см. раздел "Настройка тестовых баз данных").

## CI/CD Integration

Пример GitHub Actions workflow:

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: subreverse_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      mongodb:
        image: mongo:4.4.18
        ports:
          - 27017:27017

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run tests
        run: |
          cd backend
          pytest tests/ --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./backend/coverage.xml
```

## Метрики покрытия

Целевые показатели покрытия кода:
- **Overall**: 80%+
- **Repositories**: 90%+
- **Services**: 85%+
- **API endpoints**: 80%+

Для проверки текущего покрытия:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## Вклад в тесты

При добавлении новых функций:
1. Напишите тесты для новых repository методов
2. Напишите тесты для новых service методов
3. Напишите тесты для новых API endpoints
4. Убедитесь, что все тесты проходят
5. Проверьте покрытие кода

## Полезные команды

```bash
# Запуск только быстрых тестов (без медленных интеграционных)
pytest tests/ -m "not slow"

# Запуск только интеграционных тестов
pytest tests/ -m "integration"

# Генерация отчета в разных форматах
pytest tests/ --cov=src --cov-report=html --cov-report=xml --cov-report=term

# Профилирование тестов (найти медленные тесты)
pytest tests/ --durations=10
```

## Контакты и поддержка

Если возникли проблемы с запуском тестов:
1. Проверьте версии зависимостей
2. Убедитесь, что базы данных запущены
3. Проверьте переменные окружения
4. Создайте issue в репозитории проекта
