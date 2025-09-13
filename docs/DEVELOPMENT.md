# Руководство разработчика

## Быстрый старт

### 1. Клонирование и настройка
```bash
git clone <repository-url>
cd ai-mediator
make setup-dev
```

### 2. Настройка переменных окружения
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими ключами
```

### 3. Запуск в development режиме
```bash
make docker-up
```

Сервисы будут доступны:
- API: http://localhost:8000
- Bot: запущен и слушает Telegram webhook
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Структура разработки

### Сервис API (`services/api/`)
```bash
# Установка зависимостей
cd services/api
pip install -e ".[dev]"

# Запуск в dev режиме
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Тесты
pytest

# Линтинг
ruff check .
ruff format .
```

### Сервис Bot (`services/bot/`)
```bash
# Установка зависимостей
cd services/bot
pip install -e ".[dev]"

# Запуск в dev режиме
python app/main.py

# Тесты
pytest
```

### Работа с промптами
```bash
# Тестирование промптов (без запуска сервисов)
python tools/prompt_tester.py --all

# Интерактивная песочница
python tools/prompt_playground.py

# Создание нового тестового кейса
cp shared/prompts/tests/cases/template.yaml shared/prompts/tests/cases/new_case.yaml
```

## База данных

### Миграции
```bash
# Создание новой миграции
make db-migration message="Add new table"

# Применение миграций
make db-upgrade

# Откат миграции
make db-downgrade
```

### Тестовые данные
```bash
# Заполнение тестовыми данными
make seed-data
```

## Тестирование

### Запуск всех тестов
```bash
make test
```

### Тестирование отдельных сервисов
```bash
make test-api    # Только API тесты
make test-bot    # Только Bot тесты
```

### Тестирование промптов
```bash
# Все тесты промптов
make prompt-test

# Конкретный тест
python tools/prompt_tester.py --test-case jealousy_conflict

# Интерактивное тестирование
python tools/prompt_playground.py
```

## Линтинг и форматирование

```bash
# Проверка кода
make lint

# Форматирование
make format

# Pre-commit хуки
pre-commit install
pre-commit run --all-files
```

## Docker разработка

### Полная сборка
```bash
make docker-build
make docker-up
```

### Логи
```bash
make docker-logs
```

### Остановка
```bash
make docker-down
```

## Добавление нового функционала

### 1. Новый API endpoint
1. Создайте роутер в `services/api/app/routers/`
2. Добавьте бизнес-логику в `services/api/app/services/`
3. Создайте тесты в `services/api/tests/`
4. Обновите документацию

### 2. Новый handler для бота
1. Создайте handler в `services/bot/app/handlers/`
2. Зарегистрируйте в `services/bot/app/main.py`
3. Создайте тесты в `services/bot/tests/`

### 3. Изменение промпта
1. Отредактируйте `shared/prompts/current/mediator_v1.md`
2. Создайте тестовый кейс в `shared/prompts/tests/cases/`
3. Запустите `make prompt-test`
4. При необходимости обновите контракты в `shared/contracts/`

### 4. Новая модель БД
1. Добавьте модель в `shared/database/models.py`
2. Создайте миграцию: `make db-migration message="Add new model"`
3. Примените: `make db-upgrade`
4. Обновите репозитории и сервисы

## CI/CD

### GitHub Actions
- **API CI**: `.github/workflows/ci-api.yml`
- **Bot CI**: `.github/workflows/ci-bot.yml`
- **Shared CI**: `.github/workflows/ci-shared.yml`

### Запуск локально
```bash
# Установка act для локального запуска GitHub Actions
brew install act  # MacOS
# или
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Запуск CI локально
act -j test
```

## Отладка

### API отладка
```bash
# Логи API
docker-compose logs -f api

# Подключение к контейнеру
docker-compose exec api bash

# Отладка в IDE
# Настройте remote debugging на localhost:5678
```

### Bot отладка
```bash
# Логи бота
docker-compose logs -f bot

# Тестирование webhook
ngrok http 8001
# Установите webhook URL в Telegram
```

### База данных
```bash
# Подключение к PostgreSQL
docker-compose exec postgres psql -U user -d ai_mediator

# GUI клиент
# pgAdmin: http://localhost:5050
```

## Полезные команды

```bash
# Очистка
make clean

# Полная перезагрузка
make docker-down
make clean
make docker-build
make docker-up

# Просмотр логов в реальном времени
make docker-logs

# Проверка состояния сервисов
docker-compose ps

# Мониторинг ресурсов
docker stats
```

## Troubleshooting

### Проблемы с Docker
```bash
# Пересборка без кэша
docker-compose build --no-cache

# Очистка Docker
docker system prune -a
```

### Проблемы с БД
```bash
# Сброс БД
docker-compose down -v
docker-compose up postgres -d
make db-upgrade
make seed-data
```

### Проблемы с промптами
```bash
# Проверка API ключа
python -c "import openai; print(openai.api_key)"

# Тест подключения
python tools/prompt_playground.py
```

## Стандарты кода

### Python
- Следуем PEP 8
- Используем type hints
- Docstrings в формате Google
- Coverage > 80%

### Коммиты
```
feat: добавить новый endpoint для медиации
fix: исправить обработку ошибок в боте
docs: обновить API документацию
test: добавить тесты для промптов
refactor: вынести общую логику в shared
```

### Branching
- `main` - стабильная версия
- `develop` - разработка
- `feature/название` - новые фичи
- `hotfix/название` - критические исправления
