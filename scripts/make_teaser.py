#!/usr/bin/env python3
"""Готовит тизер поста для Telegram и VK.

    python3 scripts/make_teaser.py                     # последний пост
    python3 scripts/make_teaser.py --slug zachem-blog  # конкретный пост
    python3 scripts/make_teaser.py --send              # отправить в Telegram

Для отправки нужны переменные окружения:
    TELEGRAM_BOT_TOKEN  — токен бота от @BotFather
    TELEGRAM_CHAT_ID    — id канала (например, -1001234567890)

Без --send скрипт только показывает текст и payload — ничего не отправляет.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_posts import parse_front_matter, post_date, slug_of  # noqa: E402

BASE_URL = "https://avagners.github.io"
DEFAULT_VAULT = Path.home() / "Obsidian" / "Блог"

def published(vault: Path) -> list[dict]:
    """Все посты со статусом «готово», свежие сверху."""
    posts = []
    for path in sorted(vault.glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, _ = parse_front_matter(path.read_text(encoding="utf-8"))
        if str(meta.get("status", "")).strip().lower() != "готово":
            continue
        slug = slug_of(meta, path)
        posts.append(
            {
                "slug": slug,
                "title": str(meta.get("title", "")).strip() or path.stem,
                "summary": str(meta.get("summary", "")).strip(),
                "date": post_date(meta, path).isoformat(),
                "url": f"{BASE_URL}/posts/{slug}.html",
                "source": path.name,
            }
        )
    posts.sort(key=lambda p: (p["date"], p["slug"]), reverse=True)
    return posts


def build_text(post: dict, target: str) -> str:
    """Заголовок, summary (если есть) и ссылка — через пустую строку."""
    parts = [post["title"]]
    if post["summary"]:
        parts.append(post["summary"])
    label = "Ссылка: " if target == "vk" else ""
    parts.append(f"{label}{post['url']}")
    return "\n\n".join(parts)


def send_telegram(text: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        sys.exit("Нет TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID — отправка отменена")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {"chat_id": chat, "text": text, "disable_web_page_preview": "false"}
    ).encode()
    with urllib.request.urlopen(url, data=data, timeout=20) as resp:
        payload = json.loads(resp.read().decode())
    if not payload.get("ok"):
        sys.exit(f"Telegram ответил ошибкой: {payload}")
    message = payload["result"].get("message_id")
    print(f"отправлено в Telegram, message_id={message}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Тизер поста для соцсетей")
    parser.add_argument("--vault", default=str(DEFAULT_VAULT))
    parser.add_argument("--slug", help="адрес поста; по умолчанию самый свежий")
    parser.add_argument("--target", choices=("telegram", "vk"), default="telegram")
    parser.add_argument("--send", action="store_true", help="отправить в Telegram")
    parser.add_argument("--json", action="store_true", help="показать payload запроса")
    args = parser.parse_args()

    posts = published(Path(args.vault).expanduser())
    if not posts:
        sys.exit("В хранилище нет постов со статусом «готово»")

    post = posts[0]
    if args.slug:
        matches = [p for p in posts if p["slug"] == args.slug]
        if not matches:
            sys.exit(f"Пост со slug «{args.slug}» не найден среди готовых")
        post = matches[0]

    text = build_text(post, args.target)

    print("─" * 60)
    print(text)
    print("─" * 60)
    print(f"символов: {len(text)}  ·  источник: {post['source']}  ·  цель: {args.target}")

    if args.json:
        print(json.dumps(
            {"chat_id": os.environ.get("TELEGRAM_CHAT_ID", "<TELEGRAM_CHAT_ID>"),
             "text": text,
             "disable_web_page_preview": False},
            ensure_ascii=False, indent=2))

    if args.send:
        send_telegram(text)
    else:
        print("(черновик: ничего не отправлено, добавьте --send)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
