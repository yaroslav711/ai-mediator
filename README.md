# AI Mediator - Медиатор конфликтов в отношениях

🤖 AI агент для разрешения конфликтов в отношениях через Telegram бота

## Описание проекта

AI Mediator анализирует сообщения от двух партнеров и предоставляет персонализированные рекомендации для разрешения конфликтов. Система работает через Telegram бота и использует AI для понимания контекста и предложения конструктивных решений.

## Особенности

- 🎯 **Персонализированные рекомендации** для каждого партнера
- 🧠 **AI анализ** эмоций и паттернов общения  
- 📱 **Telegram интеграция** для удобного использования
- 🔄 **Микросервисная архитектура** для независимой разработки
- 🧪 **Автономное тестирование промптов** без запуска сервисов
- 📊 **Аналитика** отношений и эффективности медиации

## Быстрый старт

### Требования
- Python 3.11+
- Docker & Docker Compose
- OpenAI API ключ
- Telegram Bot Token

### Установка

```bash
# Клонирование
git clone <repo-url>
cd ai-mediator

# Настройка окружения
cp env.example .env
# ОБЯЗАТЕЛЬНО отредактируйте .env:
# - добавьте OPENAI_API_KEY
# - добавьте TELEGRAM_BOT_TOKEN

# Запуск всех сервисов (с uv - быстрее)
make docker-up

# Или с pip (если uv не работает)
USE_UV=false make docker-up
```

### Тестирование промптов (без запуска сервисов)
```bash
# Установка зависимостей для инструментов
uv sync --extra tools

# Запуск тестов промптов
python tools/prompt_tester.py --all

# Интерактивная песочница  
python tools/prompt_playground.py
```

## Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram Bot  │    │   API Service   │    │   Analytics     │
│   (Python)      │───▶│   (FastAPI)     │───▶│   (Future)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   Database      │
                       └─────────────────┘
```

### Сервисы
- **API Service** (`services/api/`) - Backend с бизнес-логикой и AI интеграцией
- **Bot Service** (`services/bot/`) - Telegram бот для взаимодействия с пользователями  
- **Analytics Service** (`services/analytics/`) - Будущий сервис аналитики

### Общие компоненты
- **Prompts** (`shared/prompts/`) - Централизованное управление AI промптами
- **Contracts** (`shared/contracts/`) - API схемы и контракты
- **Database** (`shared/database/`) - Модели БД и миграции
- **Tools** (`tools/`) - Инструменты для разработки и тестирования

## Разработка

### Структура проекта
Подробное описание: [docs/STRUCTURE.md](docs/STRUCTURE.md)

### Гайд для разработчиков  
Инструкции: [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

### Полезные команды

```bash
# Разработка
make dev-install     # Установка dev зависимостей
make test           # Запуск всех тестов
make lint           # Проверка кода
make format         # Форматирование

# Docker
make docker-build   # Сборка образов
make docker-up      # Запуск сервисов
make docker-logs    # Просмотр логов

# База данных
make db-upgrade     # Применить миграции
make db-migration   # Создать миграцию

# Промпты
make prompt-test    # Тестирование промптов
python tools/prompt_playground.py  # Интерактивная песочница
```

## Тестирование промптов

Уникальная особенность проекта - возможность тестировать AI промпты **без запуска сервисов**:

```bash
# Все тесты
python tools/prompt_tester.py --all

# Конкретный тест
python tools/prompt_tester.py --test-case jealousy_conflict

# Интерактивное тестирование
python tools/prompt_playground.py
```

Тестовые кейсы находятся в `shared/prompts/tests/cases/` и включают:
- Конфликты из-за ревности
- Проблемы с границами
- Коммуникационные проблемы

## API

### Основные endpoints

- `POST /api/v1/mediate` - Запрос медиации для пары
- `GET /api/v1/pairs/{pair_id}/history` - История медиаций
- `POST /api/v1/users/register` - Регистрация пользователя
- `GET /health` - Проверка состояния сервиса

Полная документация: [docs/API.md](docs/API.md)

## Telegram Bot

### Команды
- `/start` - Начало работы с ботом
- `/pair` - Привязка к партнеру
- `/help` - Справка по командам
- `/settings` - Настройки медиации

### Workflow
1. Пользователи регистрируются и связываются в пару
2. Ведут обычную переписку через бота  
3. AI автоматически определяет конфликты
4. Предоставляет персонализированные рекомендации

## Развертывание

### Production
```bash
# Сборка production образов
docker-compose -f infra/production/docker-compose.prod.yml build

# Запуск в production
docker-compose -f infra/production/docker-compose.prod.yml up -d
```

### Staging
```bash
docker-compose -f infra/staging/docker-compose.staging.yml up -d
```

## Мониторинг

- **Health checks** встроены во все сервисы
- **Логирование** в JSON формате для анализа
- **Метрики** через prometheus (планируется)

## Безопасность

- 🔒 Все API ключи в переменных окружения
- 🛡️ Валидация входных данных через Pydantic
- ⚠️ Обнаружение критических ситуаций (насилие, угрозы)
- 🚫 Автоматическое перенаправление к специалистам при необходимости

## Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Создайте Pull Request

## Команда

- **Backend разработка** - API сервис и интеграции
- **AI/ML разработка** - Промпты и логика медиации  
- **Frontend разработка** - Telegram бот и будущий веб-интерфейс
- **DevOps** - Инфраструктура и развертывание

## Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для подробностей.

## Поддержка

- 📧 Email: support@ai-mediator.com
- 💬 Telegram: @ai_mediator_support  
- 🐛 Issues: [GitHub Issues](https://github.com/your-org/ai-mediator/issues)

---

⚡ **Создано для помощи в отношениях через силу AI** ⚡