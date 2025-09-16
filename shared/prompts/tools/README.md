# Prompt Tools

Инструменты для работы с промптами AI медиатора.

## prompt_builder.py

Основной инструмент для сборки промптов с подстановкой схем контрактов.

### Использование в CLI

```bash
# Сборка основного промпта из main.md
python shared/prompts/tools/prompt_builder.py

# Сборка промпта из эксперимента
python shared/prompts/tools/prompt_builder.py --experiment 001

# Сохранение в файл
python shared/prompts/tools/prompt_builder.py --output final_prompt.txt

# Список доступных экспериментов
python shared/prompts/tools/prompt_builder.py --list
```

### Использование в коде

```python
from shared.prompts.tools.prompt_builder import PromptBuilder

# Создание строителя
builder = PromptBuilder()

# Сборка основного промпта
prompt = builder.build()

# Сборка из эксперимента
experiment_prompt = builder.build(experiment="001")

# Получение списка экспериментов
experiments = builder.list_experiments()
```

### Возможности

- ✅ Автоматическая подстановка JSON схем из `{{CONTRACT_SCHEMA:filename.json}}`
- ✅ Работа с основным промптом (`main.md`) 
- ✅ Работа с экспериментами (`experiments/001_*.md`)
- ✅ CLI и программный интерфейс
- ✅ Сохранение в файл
- ✅ Валидация файлов и JSON

### Архитектура

```
shared/prompts/
├── main.md                    # Основной промпт
├── experiments/               # Экспериментальные промпты  
│   ├── 001_fast_connect.md
│   └── 002_enhanced_empathy.md
└── tools/
    ├── prompt_builder.py      # Основной инструмент
    └── README.md             # Эта документация

shared/contracts/             # Схемы форматов
├── llm_output_format.json   # Простой формат для LLM
└── backend_*.json          # Сложные схемы для бэкенда
```