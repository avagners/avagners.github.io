#!/usr/bin/env python3
"""Собирает посты из хранилища Obsidian в статический HTML для avagners.github.io.

Использование:
    python3 scripts/build_posts.py                    # берёт ~/Obsidian/Блог
    python3 scripts/build_posts.py --vault /путь      # другое хранилище

Что делает:
  - читает *.md из папки блога хранилища;
  - пропускает всё, где status не «готово»;
  - конвертирует Markdown (заголовки, абзацы, списки, код, цитаты, ссылки,
    жирный и моноширинный текст) в HTML;
  - кладёт результат в posts/<slug>.html;
  - перегенерирует список постов между маркерами в posts.html.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from datetime import date
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
TEMPLATE = SITE / "scripts" / "post_template.html"
POSTS_DIR = SITE / "posts"
INDEX = SITE / "posts.html"
BASE_URL = "https://avagners.github.io"

MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)

# ---------------------------------------------------------------- front matter

def parse_front_matter(text: str) -> tuple[dict, str]:
    """Возвращает (поля, тело заметки). Ожидает YAML между --- в начале файла."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text

    meta: dict = {}
    for line in text[3:end].strip("\n").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            meta[key.strip()] = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
        else:
            meta[key.strip()] = value.strip("'\"")
    return meta, text[end + 4:].lstrip("\n")


# ------------------------------------------------------------------- markdown

def inline(text: str) -> str:
    """Разметка внутри строки: код, жирный, курсив, ссылки."""
    text = html.escape(text, quote=False)

    codes: list[str] = []
    text = re.sub(r"`([^`]+)`", lambda m: codes.append(m.group(1)) and f"\x00{len(codes) - 1}\x00", text)

    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", r'<a href="\2">\1</a>', text)
    return re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", text)


def md_to_html(md: str) -> str:
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    para: list[str] = []
    i = 0

    def flush() -> None:
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush()
            lang = stripped[3:].strip()
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            cls = f' class="language-{html.escape(lang)}"' if lang else ""
            out.append(f"<pre><code{cls}>{html.escape(chr(10).join(body))}</code></pre>")
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            flush()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", stripped):
            flush()
            out.append("<hr>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush()
            quote: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + inline(" ".join(quote)) + "</p></blockquote>")
            continue

        for pattern, tag in ((r"^[-*+]\s+", "ul"), (r"^\d+\.\s+", "ol")):
            if re.match(pattern, stripped):
                flush()
                items: list[str] = []
                while i < len(lines) and re.match(pattern, lines[i].strip()):
                    items.append(re.sub(pattern, "", lines[i].strip()))
                    i += 1
                body = "\n".join(f"  <li>{inline(x)}</li>" for x in items)
                out.append(f"<{tag}>\n{body}\n</{tag}>")
                break
        else:
            if not stripped:
                flush()
            else:
                para.append(stripped)
        i += 1

    flush()
    return "\n".join(out)


# --------------------------------------------------------------------- сборка

def post_date(meta: dict, path: Path) -> date:
    raw = str(meta.get("date", "")).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", path.name)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return date.today()


def slug_of(meta: dict, path: Path) -> str:
    slug = str(meta.get("slug", "")).strip()
    if slug:
        return re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
    m = re.match(r"\d{4}-\d{2}-\d{2}-(.+)", path.stem)
    return (m.group(1) if m else path.stem).lower()


def strip_leading_h1(body: str, title: str) -> str:
    lines = body.split("\n")
    for idx, line in enumerate(lines):
        if not line.strip():
            continue
        if re.match(r"^#\s+", line) and line.lstrip("# ").strip().lower() == title.lower():
            del lines[idx]
        break
    return "\n".join(lines).lstrip("\n")


def build(vault: Path, dry_run: bool = False) -> int:
    if not vault.is_dir():
        print(f"Нет такой папки: {vault}", file=sys.stderr)
        return 1

    template = TEMPLATE.read_text(encoding="utf-8")
    POSTS_DIR.mkdir(exist_ok=True)

    collected: list[tuple[date, str, str]] = []  # (дата, slug, html-файл)
    built: list[str] = []

    for path in sorted(vault.glob("*.md")):
        if path.name.startswith("_"):
            continue
        meta, body = parse_front_matter(path.read_text(encoding="utf-8"))
        status = str(meta.get("status", "")).strip().lower()
        if status != "готово":
            print(f"пропуск ({status or 'без статуса'}): {path.name}")
            continue

        title = str(meta.get("title", "")).strip() or path.stem
        summary = str(meta.get("summary", "")).strip()
        d = post_date(meta, path)
        slug = slug_of(meta, path)

        content = md_to_html(strip_leading_h1(body, title))
        page = (
            template.replace("{{TITLE}}", html.escape(title))
            .replace("{{SUMMARY}}", html.escape(summary))
            .replace("{{DATE_ISO}}", d.isoformat())
            .replace("{{DATE_HUMAN}}", f"{d.day} {MONTHS[d.month - 1]} {d.year}")
            .replace("{{URL}}", f"{BASE_URL}/posts/{slug}.html")
            .replace("{{CONTENT}}", content)
        )

        target = POSTS_DIR / f"{slug}.html"
        if not dry_run:
            target.write_text(page, encoding="utf-8")
        collected.append((d, slug, summary, title))
        built.append(f"posts/{slug}.html")

    collected.sort(key=lambda x: (x[0], x[1]), reverse=True)
    items = "\n".join(
        f'        <li>\n'
        f'            <time datetime="{d.isoformat()}">{d.day} {MONTHS[d.month - 1]} {d.year}</time>\n'
        f'            <a href="/posts/{slug}.html">{html.escape(title)}</a>\n'
        f'            <p>{html.escape(summary)}</p>\n'
        f'        </li>'
        for d, slug, summary, title in collected
    )
    if not items:
        items = '        <p class="muted">Пока пусто — первый пост в работе.</p>'
    else:
        items = '        <ul class="post-list">\n' + items + "\n        </ul>"

    if not dry_run:
        index = INDEX.read_text(encoding="utf-8")
        new_index = re.sub(
            r"(<!-- posts:start -->).*?(<!-- posts:end -->)",
            lambda m: f"{m.group(1)}\n{items}\n        {m.group(2)}",
            index,
            flags=re.S,
        )
        INDEX.write_text(new_index, encoding="utf-8")

    for name in built:
        print(f"собрано: {name}")
    print(f"итого постов: {len(collected)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Собрать посты из Obsidian в HTML")
    parser.add_argument("--vault", default=str(Path.home() / "Obsidian" / "Блог"))
    parser.add_argument("--dry-run", action="store_true", help="ничего не писать, только показать")
    args = parser.parse_args()
    return build(Path(args.vault).expanduser(), dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
