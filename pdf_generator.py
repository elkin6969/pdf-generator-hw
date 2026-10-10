#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Generator CLI Tool
Генерация PDF-документов из CSV/JSON данных и HTML-шаблонов.
"""

import os
import sys
import json
import re
import warnings
import platform
import subprocess
from pathlib import Path

import pandas as pd
import weasyprint

# Подавление предупреждений
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


def init_dirs():
    """Создание необходимых директорий, если их нет."""
    dirs = ["data", "templates", "output"]
    for d in dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ Создана папка: {path}")
    print()


def get_files(directory: str, extensions: list) -> list:
    """Получение списка файлов с указанными расширениями в директории."""
    path = Path(directory)
    if not path.exists():
        return []
    files = []
    for ext in extensions:
        files.extend(path.glob(f"*{ext}"))
    return sorted(files)


def load_data(file_path: Path) -> pd.DataFrame:
    """Загрузка данных из CSV или JSON файла в DataFrame."""
    ext = file_path.suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(file_path, encoding="utf-8")
    elif ext == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list):
                    df = pd.DataFrame(value)
                    break
            else:
                df = pd.DataFrame([data])
        else:
            raise ValueError("Неподдерживаемый формат JSON")
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {ext}")
    return df


def render_pdf(template_path: Path, data: dict, output_path: Path):
    """Рендеринг PDF из HTML-шаблона с подстановкой данных."""
    with open(template_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    for key, value in data.items():
        placeholder = "{{ " + str(key) + " }}"
        html_content = html_content.replace(placeholder, str(value))

    html_content = re.sub(r"\{\{.*?\}\}", "", html_content)

    html = weasyprint.HTML(string=html_content)
    html.write_pdf(str(output_path))


def open_pdf(file_path: Path):
    """Открытие PDF-файла в системной программе просмотра."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(str(file_path))
        elif system == "Darwin":
            subprocess.run(["open", str(file_path)], check=True)
        else:
            subprocess.run(["xdg-open", str(file_path)], check=True)
    except Exception as e:
        print(f"  ⚠ Не удалось открыть файл автоматически: {e}")
        print(f"  → Файл сохранён: {file_path}")


def display_menu(items: list, label: str) -> int:
    """Отображение меню выбора и возврат индекса."""
    print(f"\n{'='*50}")
    print(f"  Доступные {label}:")
    print(f"{'='*50}")
    for i, item in enumerate(items, 1):
        print(f"  {i}. {item.name}")
    print(f"{'='*50}")

    while True:
        try:
            choice = input(f"\n  Выберите номер (1-{len(items)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(items):
                return idx
            print(f"  ✗ Введите число от 1 до {len(items)}")
        except ValueError:
            print("  ✗ Введите корректное число")
        except KeyboardInterrupt:
            print("\n  Выход...")
            sys.exit(0)


def display_records(df: pd.DataFrame) -> int:
    """Отображение записей из DataFrame и возврат индекса выбранной."""
    print(f"\n{'='*50}")
    print(f"  Записи в файле (всего: {len(df)}):")
    print(f"{'='*50}")

    # Определяем колонку для отображения ID
    id_col = None
    for col in df.columns:
        if str(col).lower() in ["invoice_id", "id", "номер", "id_заказа"]:
            id_col = str(col)
            break

    # Используем range, чтобы гарантировать, что номер строки — это целое число
    for display_num in range(len(df)):
        row = df.iloc[display_num]
        if id_col and id_col in row.index:
            second_val = row.iloc[1] if len(row) > 1 else row.iloc[0]
            print(f"  {display_num + 1}. [{row[id_col]}] — {second_val}")
        else:
            print(f"  {display_num + 1}. {row.iloc[0]}")

    print(f"{'='*50}")

    while True:
        try:
            choice = input(f"\n  Выберите номер записи (1-{len(df)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(df):
                return idx
            print(f"  ✗ Введите число от 1 до {len(df)}")
        except ValueError:
            print("  ✗ Введите корректное число")
        except KeyboardInterrupt:
            print("\n  Выход...")
            sys.exit(0)


def run():
    """Главная функция запуска CLI."""
    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║       PDF Generator — Генератор документов      ║")
    print("╚══════════════════════════════════════════════════╝")
    print()

    print("  Проверка структуры папок...")
    init_dirs()

    data_files = get_files("data", [".csv", ".json"])
    if not data_files:
        print("  ✗ Папка 'data' пуста! Добавьте CSV или JSON файлы.")
        sys.exit(1)

    template_files = get_files("templates", [".html"])
    if not template_files:
        print("  ✗ Папка 'templates' пуста! Добавьте HTML-шаблоны.")
        sys.exit(1)

    data_idx = display_menu(data_files, "файлы данных")
    selected_data = data_files[data_idx]
    print(f"\n  ✓ Выбран файл данных: {selected_data.name}")

    template_idx = display_menu(template_files, "шаблоны")
    selected_template = template_files[template_idx]
    print(f"\n  ✓ Выбран шаблон: {selected_template.name}")

    try:
        df = load_data(selected_data)
    except Exception as e:
        print(f"\n  ✗ Ошибка загрузки данных: {e}")
        sys.exit(1)

    if df.empty:
        print("\n  ✗ Файл данных пуст!")
        sys.exit(1)

    record_idx = display_records(df)
    selected_record = df.iloc[record_idx].to_dict()

    print(f"\n  Генерация PDF...")
    output_name = f"document_{record_idx + 1}.pdf"
    output_path = Path("output") / output_name

    try:
        render_pdf(selected_template, selected_record, output_path)
        print(f"  ✓ PDF успешно создан: {output_path}")
    except Exception as e:
        print(f"\n  ✗ Ошибка генерации PDF: {e}")
        sys.exit(1)

    print(f"\n  Открытие PDF...")
    open_pdf(output_path)

    print(f"\n{'='*50}")
    print("  Готово!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\n\n  Программа прервана пользователем.")
        sys.exit(0)