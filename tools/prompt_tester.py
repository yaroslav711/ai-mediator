#!/usr/bin/env python3
"""
Автономный тестер промптов AI медиатора.
Запускает тесты без поднятия сервисов.

Установка: uv sync --extra tools
Запуск: python tools/prompt_tester.py --all
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import click
import yaml
from openai import OpenAI
from pydantic import BaseModel
from rich.console import Console
from rich.table import Table
from rich.progress import track

# Добавляем shared в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

console = Console()


class TestResult(BaseModel):
    test_name: str
    status: str  # "passed", "failed", "error"
    score: float  # 0.0 - 1.0
    details: Dict[str, Any]
    execution_time: float


class PromptTester:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.prompts_dir = Path(__file__).parent.parent / "shared" / "prompts"
        self.tests_dir = self.prompts_dir / "tests" / "cases"
        self.results_dir = self.prompts_dir / "tests" / "results"
        self.results_dir.mkdir(exist_ok=True)

    def load_current_prompt(self) -> str:
        """Загружает текущий промпт медиатора"""
        mediator_prompt = self.prompts_dir / "current" / "mediator_v1.md"
        system_rules = self.prompts_dir / "current" / "system_rules.md"

        prompt_parts = []

        if mediator_prompt.exists():
            prompt_parts.append(mediator_prompt.read_text(encoding="utf-8"))

        if system_rules.exists():
            prompt_parts.append(system_rules.read_text(encoding="utf-8"))

        return "\n\n".join(prompt_parts)

    def load_test_case(self, test_file: Path) -> Dict[str, Any]:
        """Загружает тестовый кейс"""
        with open(test_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def format_messages_for_prompt(self, messages: List[Dict]) -> str:
        """Форматирует сообщения для промпта"""
        formatted = []
        for msg in messages:
            timestamp = msg["timestamp"]
            user_id = msg["user_id"]
            content = msg["content"]
            formatted.append(f"[{timestamp}] {user_id}: {content}")

        return "\n".join(formatted)

    def run_test_case(self, test_case: Dict[str, Any]) -> TestResult:
        """Запускает один тестовый кейс"""
        start_time = datetime.now()

        try:
            # Подготавливаем промпт
            system_prompt = self.load_current_prompt()
            messages_text = self.format_messages_for_prompt(test_case["messages"])

            user_prompt = f"""
            Проанализируй следующие сообщения от пары (pair_id: {test_case["pair_id"]}):

            {messages_text}

            Предоставь персонализированные рекомендации согласно инструкциям.
            """

            # Вызываем OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=2048,
            )

            ai_response = response.choices[0].message.content

            # Анализируем качество ответа
            score = self.evaluate_response(ai_response, test_case)

            execution_time = (datetime.now() - start_time).total_seconds()

            return TestResult(
                test_name=test_case["name"],
                status="passed" if score >= 0.7 else "failed",
                score=score,
                details={
                    "ai_response": ai_response,
                    "expected": test_case.get("expected_output", {}),
                    "evaluation_notes": self.get_evaluation_notes(
                        ai_response, test_case
                    ),
                },
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_name=test_case.get("name", "Unknown"),
                status="error",
                score=0.0,
                details={"error": str(e)},
                execution_time=execution_time,
            )

    def evaluate_response(self, response: str, test_case: Dict) -> float:
        """Оценивает качество ответа (простая эвристика)"""
        score = 0.0
        expected = test_case.get("expected_output", {})

        # Проверяем наличие разделов для обоих участников
        participants = test_case.get("messages", [])
        unique_users = set(msg["user_id"] for msg in participants)

        users_mentioned = 0
        for user_id in unique_users:
            if user_id.lower() in response.lower():
                users_mentioned += 1

        if users_mentioned == len(unique_users):
            score += 0.3

        # Проверяем ключевые слова из expected
        if "participants" in expected:
            for user_data in expected["participants"].values():
                should_include = user_data.get("should_include", [])
                for keyword in should_include:
                    if keyword.lower() in response.lower():
                        score += 0.1

        # Проверяем структурированность ответа
        if "рекомендации" in response.lower() or "советы" in response.lower():
            score += 0.2

        if "понимаю" in response.lower() or "чувствуешь" in response.lower():
            score += 0.2

        # Проверяем отсутствие нежелательного контента
        if "participants" in expected:
            for user_data in expected["participants"].values():
                should_avoid = user_data.get("should_avoid", [])
                for keyword in should_avoid:
                    if keyword.lower() in response.lower():
                        score -= 0.1

        return min(1.0, max(0.0, score))

    def get_evaluation_notes(self, response: str, test_case: Dict) -> List[str]:
        """Получает заметки по оценке"""
        notes = []

        if len(response) < 200:
            notes.append("Ответ слишком короткий")

        if "рекомендации" not in response.lower():
            notes.append("Отсутствуют явные рекомендации")

        if response.count("user_") != 2:
            notes.append("Не упомянуты оба пользователя")

        return notes

    def save_results(self, results: List[TestResult]):
        """Сохраняет результаты тестов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"test_results_{timestamp}.json"

        results_data = {
            "timestamp": timestamp,
            "total_tests": len(results),
            "passed": len([r for r in results if r.status == "passed"]),
            "failed": len([r for r in results if r.status == "failed"]),
            "errors": len([r for r in results if r.status == "error"]),
            "average_score": sum(r.score for r in results) / len(results)
            if results
            else 0,
            "results": [r.dict() for r in results],
        }

        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)

        console.print(f"✅ Результаты сохранены: {results_file}")
        return results_file


@click.command()
@click.option("--test-case", help="Запустить конкретный тест")
@click.option("--all", "run_all", is_flag=True, help="Запустить все тесты")
@click.option("--api-key", envvar="OPENAI_API_KEY", help="OpenAI API ключ")
def main(test_case: str, run_all: bool, api_key: str):
    """Тестирование промптов AI медиатора"""

    if not api_key:
        console.print("❌ Требуется OPENAI_API_KEY", style="red")
        sys.exit(1)

    tester = PromptTester(api_key)

    # Находим тестовые файлы
    test_files = []
    if test_case:
        test_file = tester.tests_dir / f"{test_case}.yaml"
        if test_file.exists():
            test_files = [test_file]
        else:
            console.print(f"❌ Тест {test_case} не найден", style="red")
            sys.exit(1)
    elif run_all:
        test_files = list(tester.tests_dir.glob("*.yaml"))
    else:
        console.print("Укажите --test-case или --all")
        sys.exit(1)

    if not test_files:
        console.print("❌ Тестовые файлы не найдены", style="red")
        sys.exit(1)

    console.print(f"🚀 Запуск {len(test_files)} тестов...")

    # Запускаем тесты
    results = []
    for test_file in track(test_files, description="Выполнение тестов..."):
        test_case_data = tester.load_test_case(test_file)
        result = tester.run_test_case(test_case_data)
        results.append(result)

    # Выводим результаты
    table = Table(title="Результаты тестирования промптов")
    table.add_column("Тест")
    table.add_column("Статус")
    table.add_column("Оценка")
    table.add_column("Время")

    for result in results:
        status_color = (
            "green"
            if result.status == "passed"
            else "red"
            if result.status == "failed"
            else "yellow"
        )
        table.add_row(
            result.test_name,
            f"[{status_color}]{result.status}[/{status_color}]",
            f"{result.score:.2f}",
            f"{result.execution_time:.1f}s",
        )

    console.print(table)

    # Сохраняем результаты
    tester.save_results(results)

    # Итоговая статистика
    passed = len([r for r in results if r.status == "passed"])
    total = len(results)
    avg_score = sum(r.score for r in results) / total if results else 0

    console.print(
        f"\n📊 Итоги: {passed}/{total} тестов пройдено, средняя оценка: {avg_score:.2f}"
    )


if __name__ == "__main__":
    main()
