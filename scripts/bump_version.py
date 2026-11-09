#!/usr/bin/env python3
"""Меняет версию сайта: файл VERSION и подвалы страниц.

    python3 scripts/bump_version.py 1.0.1

После смены версии пересоберите посты, чтобы обновились их страницы:
    python3 scripts/build_posts.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
VERSION_FILE = SITE / "VERSION"
TEMPLATE = SITE / "scripts" / "post_template.html"


def main() -> int:
    if len(sys.argv) != 2:
        sys.exit("Использование: bump_version.py <версия, например 1.0.1>")

    new = sys.argv[1].lstrip("v")
    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        sys.exit("Версия должна быть в формате X.Y.Z (например, 1.0.1)")

    VERSION_FILE.write_text(new + "\n", encoding="utf-8")

    changed: list[str] = []
    targets = sorted(SITE.glob("*.html")) + [TEMPLATE]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        if "{{VERSION}}" in text:
            # шаблон поста подставляет версию при сборке — трогать его нельзя
            continue
        updated = re.sub(
            r'<span class="version-value">[^<]*</span>',
            f'<span class="version-value">{new}</span>',
            text,
        )
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            changed.append(path.relative_to(SITE).as_posix())

    print(f"версия: {new}")
    print("обновлено:", ", ".join(changed) if changed else "ничего")
    print("дальше: python3 scripts/build_posts.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
