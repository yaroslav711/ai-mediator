#!/usr/bin/env python3
"""
Интерактивная песочница для экспериментов с промптами.
Позволяет быстро тестировать изменения без запуска сервисов.

Установка: uv sync --extra tools
Запуск: python tools/prompt_playground.py
"""

import sys
from pathlib import Path
from typing import List, Dict

import click
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

# Добавляем shared в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

console = Console()


class PromptPlayground:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.prompts_dir = Path(__file__).parent.parent / "shared" / "prompts"
        self.current_prompt = self.load_current_prompt()

    def load_current_prompt(self) -> str:
        """Загружает текущий промпт"""
        mediator_prompt = self.prompts_dir / "current" / "mediator_v1.md"
        system_rules = self.prompts_dir / "current" / "system_rules.md"

        prompt_parts = []

        if mediator_prompt.exists():
            prompt_parts.append(mediator_prompt.read_text(encoding="utf-8"))

        if system_rules.exists():
            prompt_parts.append(system_rules.read_text(encoding="utf-8"))

        return "\n\n".join(prompt_parts)

    def create_sample_conversation(self) -> List[Dict]:
        """Создает образец диалога для тестирования"""
        return [
            {
                "user_id": "user_alice",
                "content": "Я устала от того, что ты никогда не помогаешь по дому!",
                "timestamp": "2024-01-15T19:00:00Z",
            },
            {
                "user_id": "user_bob",
                "content": "Но я работаю больше тебя! Когда я приезжаю, хочется отдохнуть.",
                "timestamp": "2024-01-15T19:02:00Z",
            },
            {
                "user_id": "user_alice",
                "content": "А я что, не работаю? И еще дом тяну на себе!",
                "timestamp": "2024-01-15T19:03:00Z",
            },
        ]

    def format_conversation(self, messages: List[Dict]) -> str:
        """Форматирует диалог для промпта"""
        formatted = []
        for msg in messages:
            user = msg["user_id"]
            content = msg["content"]
            timestamp = msg.get("timestamp", "")
            formatted.append(f"[{timestamp}] {user}: {content}")

        return "\n".join(formatted)

    def test_prompt(self, conversation: str, custom_prompt: str = None) -> str:
        """Тестирует промпт с заданным диалогом"""
        system_prompt = custom_prompt or self.current_prompt

        user_prompt = f"""
        Проанализируй следующие сообщения от пары:

        {conversation}

        Предоставь персонализированные рекомендации согласно инструкциям.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2048,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"❌ Ошибка: {str(e)}"

    def interactive_mode(self):
        """Интерактивный режим"""
        console.print(Panel.fit("🎮 AI Mediator Prompt Playground", style="bold blue"))

        while True:
            console.print("\n📋 Выберите действие:")
            console.print("1. Тестировать с образцом диалога")
            console.print("2. Ввести свой диалог")
            console.print("3. Изменить промпт")
            console.print("4. Показать текущий промпт")
            console.print("5. Выйти")

            choice = Prompt.ask("Ваш выбор", choices=["1", "2", "3", "4", "5"])

            if choice == "1":
                self.test_with_sample()
            elif choice == "2":
                self.test_with_custom()
            elif choice == "3":
                self.edit_prompt()
            elif choice == "4":
                self.show_current_prompt()
            elif choice == "5":
                console.print("👋 До свидания!")
                break

    def test_with_sample(self):
        """Тестирование с образцом"""
        sample = self.create_sample_conversation()
        conversation = self.format_conversation(sample)

        console.print("\n💬 Образец диалога:")
        console.print(Panel(conversation, title="Диалог"))

        console.print("\n🤖 Запуск AI медиатора...")
        result = self.test_prompt(conversation)

        console.print("\n📝 Результат:")
        console.print(Panel(Markdown(result), title="Рекомендации медиатора"))

    def test_with_custom(self):
        """Тестирование с пользовательским диалогом"""
        console.print("\n✏️ Введите диалог (формат: user_id: сообщение)")
        console.print("Для завершения введите пустую строку")

        messages = []
        while True:
            line = Prompt.ask("Сообщение", default="")
            if not line:
                break

            if ":" in line:
                user_id, content = line.split(":", 1)
                messages.append(
                    {
                        "user_id": user_id.strip(),
                        "content": content.strip(),
                        "timestamp": "2024-01-15T19:00:00Z",
                    }
                )
            else:
                console.print("❌ Неверный формат. Используйте: user_id: сообщение")

        if not messages:
            console.print("❌ Диалог пуст")
            return

        conversation = self.format_conversation(messages)

        console.print("\n🤖 Запуск AI медиатора...")
        result = self.test_prompt(conversation)

        console.print("\n📝 Результат:")
        console.print(Panel(Markdown(result), title="Рекомендации медиатора"))

    def edit_prompt(self):
        """Редактирование промпта"""
        console.print("\n✏️ Редактирование промпта")
        console.print("Введите новый промпт (для сохранения текущего нажмите Enter):")

        new_prompt = console.input()
        if new_prompt.strip():
            self.current_prompt = new_prompt
            console.print("✅ Промпт обновлен!")
        else:
            console.print("ℹ️ Промпт не изменен")

    def show_current_prompt(self):
        """Показать текущий промпт"""
        console.print("\n📋 Текущий промпт:")
        console.print(Panel(self.current_prompt, title="System Prompt"))


@click.command()
@click.option(
    "--api-key", envvar="OPENAI_API_KEY", required=True, help="OpenAI API ключ"
)
@click.option("--batch", help="Файл с тестовыми диалогами для batch тестирования")
def main(api_key: str, batch: str):
    """Интерактивная песочница для промптов AI медиатора"""

    playground = PromptPlayground(api_key)

    if batch:
        # Batch режим
        console.print(f"📦 Batch тестирование из файла: {batch}")
        # TODO: реализовать batch режим
    else:
        # Интерактивный режим
        playground.interactive_mode()


if __name__ == "__main__":
    main()
