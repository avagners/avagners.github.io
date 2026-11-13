#!/usr/bin/env python3
"""Создаёт заготовку поста в хранилище Obsidian по шаблону.

    python3 scripts/new_post.py "Как мы строили MCP-хаб"
    python3 scripts/new_post.py "Заметка" --summary "О чём это" --tags код,жизнь
    python3 scripts/new_post.py "Заметка" --status готово --open

Имя файла — дата и латинский адрес: 2026-11-13-kak-my-stroili-mcp-hab.md
Дата, slug, summary и status подставляются автоматически; текст пишете вы.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

VAULT = Path.home() / "Obsidian" / "Блог"

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

BODY = """# {title}

Первый абзац: о чём пост и зачем его читать.

## Подзаголовок

Основной текст.

## Что осталось за кадром

Чего не сказал, что стоит проверить дальше.
"""


def translit(text: str) -> str:
    out = []
    for ch in text.lower():
        if ch in TRANSLIT:
            out.append(TRANSLIT[ch])
        elif ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def main() -> int:
    parser = argparse.ArgumentParser(description="Новый пост по шаблону")
    parser.add_argument("title", help="заголовок поста")
    parser.add_argument("--summary", default="", help="одна строка о посте")
    parser.add_argument("--tags", default="", help="теги через запятую")
    parser.add_argument("--status", default="черновик", choices=("идея", "черновик", "готово"))
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--slug", help="адрес латиницей; по умолчанию из заголовка")
    parser.add_argument("--vault", default=str(VAULT))
    parser.add_argument("--open", action="store_true", help="открыть в Obsidian")
    parser.add_argument("--dry-run", action="store_true", help="только показать путь")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser()
    if not vault.is_dir():
        sys.exit(f"Нет папки хранилища: {vault}")

    slug = args.slug or translit(args.title)
    if not slug:
        sys.exit("Не удалось построить адрес из заголовка — задайте --slug вручную")

    tags = ", ".join(t.strip() for t in args.tags.split(",") if t.strip())
    path = vault / f"{args.date}-{slug}.md"

    if path.exists():
        sys.exit(f"Такой файл уже есть: {path}")

    front = [
        "---",
        f"title: {args.title}",
        f"date: {args.date}",
        f"slug: {slug}",
        f"summary: {args.summary}",
        f"tags: [{tags}]",
        f"status: {args.status}",
        "---",
        "",
    ]
    content = "\n".join(front) + BODY.format(title=args.title)

    if args.dry_run:
        print(f"был бы создан: {path}")
        print(content)
        return 0

    path.write_text(content, encoding="utf-8")
    print(f"создан: {path}")

    if args.open:
        subprocess.run(["open", f"obsidian://open?path={quote(str(path))}"], check=False)

    print(f"дальше: откройте заметку, напишите текст и поставьте status: готово")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
