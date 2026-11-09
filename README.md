# avagners.github.io

Сайт-визитка и блог: <https://avagners.github.io>

Статический сайт без сборщика — обычный HTML, CSS и Markdown-источники постов.

## Структура

| Путь | Что это |
| --- | --- |
| `index.html` | Главная: обо мне, стек |
| `posts.html` | Список постов (генерируется) |
| `posts/*.html` | Страницы постов (генерируются) |
| `now.html` | Страница «Сейчас» |
| `contacts.html` | Сотрудничество и контакты |
| `styles.css` | Общие стили |
| `scripts/` | Скрипты сборки и версионирования |
| `VERSION` | Текущая версия сайта |
| `CHANGELOG.md` | История изменений |

## Посты

Исходники живут в хранилище Obsidian: `~/Obsidian/Блог/*.md`.
У каждой заметки в начале файла служебные поля: `title`, `date`, `slug`,
`summary`, `tags`, `status`. На сайт попадают только `status: готово`.

```bash
python3 scripts/build_posts.py            # Markdown → posts/*.html + список
python3 scripts/build_posts.py --dry-run  # показать, что попадёт
python3 scripts/make_teaser.py            # текст тизера для Telegram
python3 scripts/make_teaser.py --target vk
python3 scripts/make_teaser.py --send     # нужны TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
```

## Версии

Версия хранится в `VERSION` и выводится в подвале всех страниц.

```bash
python3 scripts/bump_version.py 1.1.0     # меняет VERSION и подвалы страниц
python3 scripts/build_posts.py            # пересобрать посты с новой версией
```

Правила нумерации: `MAJOR` — несовместимые изменения структуры или адресов,
`MINOR` — новые разделы и возможности, `PATCH` — правки текстов и исправления.
Каждая версия описывается в [CHANGELOG.md](CHANGELOG.md).

## Локальный просмотр

```bash
python3 -m http.server 8080 --bind 127.0.0.1
```

Затем открыть <http://127.0.0.1:8080>. Открывать `index.html` двойным кликом
бесполезно: в навигации абсолютные пути, им нужен HTTP-сервер.
