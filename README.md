# PoliglotAi

Сайт для изучения английского с нуля до A2 для казахоязычных учеников: таблица глагола 3×3, карточки слов с интервальным повторением, тренажёр «клетка + слово» и AI-чат. Интерфейс на казахском.

Стек: **Angular 20** (фронтенд), **Django 5.1 + DRF** (бэкенд), **PostgreSQL 16**, Redis (кэш, лимиты), nginx.

## Быстрый старт (Docker)

```bash
cp .env.example .env          # при необходимости впишите ANTHROPIC_API_KEY
docker compose up -d --build --wait
open http://localhost:8080
```

Админка для методиста (слова, переводы, примеры, сценарии диалогов): http://localhost:8080/admin/

```bash
docker compose exec backend python manage.py createsuperuser
```

После регистрации на почту приходит 6-значный код подтверждения (10 минут, 5 попыток, повтор через 60 с). С `EMAIL_BACKEND=console` коды и письма для сброса пароля печатаются в лог: `docker compose logs backend`. Для реальных пользователей нужен SMTP (`EMAIL_*` в `.env`); отключить подтверждение: `REQUIRE_EMAIL_VERIFICATION=0`.

## Деплой на Render

В корне лежат `Dockerfile` (один образ: сборка Angular + Django, который отдаёт и API, и сайт) и `render.yaml` (Blueprint).

1. Render Dashboard → **New → Blueprint** → подключить GitLab-репозиторий `poliglot-group/poliglot`, выбрать ветку.
2. Render создаст веб-сервис `poliglot` и базу `poliglot-db`, сам сгенерирует `DJANGO_SECRET_KEY`.
3. Ввести `ANTHROPIC_API_KEY` (без него работает офлайн-заглушка чата).
4. Сайт откроется на `https://poliglot-<...>.onrender.com`; миграции и начальные данные применяются при старте.

Админ: в Render Shell выполнить `python manage.py createsuperuser`.

Бесплатный план: сервис засыпает после 15 минут простоя (первый запрос ~50 с), бесплатная база удаляется через 30 дней — для реальных учеников перейти на платные планы. Тот же образ подходит для Railway и Fly.io (нужны `DATABASE_URL` и `PORT`).

## Разработка

```bash
# база
docker compose up -d db                      # Postgres на localhost:5454

# бэкенд
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export POSTGRES_PORT=5454
python manage.py migrate                     # создаёт схему и загружает 40 глаголов, 16 шагов, 5 сценариев
python manage.py runserver 8000

# для e2e-тестов бэкенд можно запустить с фиксированным кодом подтверждения (работает только при DEBUG):
# EMAIL_CODE_OVERRIDE=246810 python manage.py runserver 8000

# фронтенд (проксирует /api на :8000)
cd frontend
npm ci
npx ng serve --port 4300
```

## Тесты

| Что | Команда | Что проверяет |
| --- | --- | --- |
| Бэкенд | `cd backend && POSTGRES_PORT=5454 pytest` | Код подтверждения почты (неверный, просроченный, 5 попыток, повтор), все 54 формы (6 местоимений × 9 клеток) для каждого из 40 глаголов, этапы SRS, лимит новых слов, авторизация (httpOnly, блокировка после 5 ошибок, ссылка сброса на 1 час и 1 раз), тренажёр, AI-чат |
| Линтер | `cd backend && ruff check . && ruff format --check .` | |
| Фронтенд | `cd frontend && npx ng test --watch=false --browsers=ChromeHeadless` | Компоненты таблицы, guards, разбор ошибок API |
| E2E | `cd frontend && npx playwright test` (`E2E_BASE_URL=http://localhost:8080` для Docker) | Регистрация → таблица → слова → тренажёр → чат → выход, на 1440 px и 360 px без горизонтальной прокрутки |

CI (`.github/workflows/ci.yml`) запускает всё это на каждый pull request.

## Устройство

```
backend/
  config/        настройки, URL
  users/         регистрация, вход, JWT в httpOnly-cookie, сброс пароля, профиль
  vocabulary/    слова, шаги курса, forms.py — сборка 9 форм (один источник для таблицы и тренажёра)
  srs/           этапы повторения 1-2-4-7-14-30 дней, лимит новых слов
  trainer/       задания «кто · время · форма · глагол» и проверка ответа
  chat/          диалоги, сообщения, llm.py — запросы к Claude со структурированным ответом
  progress/      журнал активности, цель дня, серия дней, сброс прогресса
frontend/src/app/
  core/          API, авторизация, interceptor обновления токена, озвучка (Web Speech, en-GB), темы
  layout/        боковое меню (десктоп), нижнее меню (телефон), строка статистики
  features/      auth, home, table, words, trainer, chat, course — каждый экран грузится лениво
```

Основные эндпоинты: `/api/auth/*`, `GET /api/verbs/{id}/forms/?pronoun=she`, `GET /api/srs/today/`, `POST /api/srs/{word_id}/answer/`, `GET /api/trainer/task/`, `POST /api/trainer/check/`, `GET /api/progress/`, `/api/chat/conversations/*`.

## Ошибки

- Бэкенд отвечает на любую ошибку API в одном формате JSON: `{"detail": "...", "code": "..."}` плюс ошибки полей (`config/exceptions.py`), в том числе на 500 и неизвестные адреса `/api/…`.
- Фронтенд: ошибки полей формы показываются у поля; общие проблемы — всплывающими уведомлениями (`core/error.interceptor.ts`, `shared/toast-container.component.ts`): нет интернета, ошибка сервера, слишком много запросов, «сервер просыпается» (запрос дольше 5 с). Одинаковые сообщения не дублируются.
- Блоки, которые не загрузились, показывают «Жүктеу мүмкін болмады» и кнопку «Қайталау» (`core/api-resource.ts`).
- Уход со страницы с незавершённой работой (тренажёр, урок слов, диалог, заполненная форма) и выход из аккаунта спрашивают подтверждение.

## AI-чат

- Запросы к LLM идут только через Django; ключ `ANTHROPIC_API_KEY` лежит в окружении сервера и в браузер не попадает.
- Модель задаётся `CHAT_MODEL` (по умолчанию `claude-opus-5`, `CHAT_EFFORT=low` для скорости). Включён серверный fallback: если модель отказывает, запрос выполняет резервная.
- Ответ структурированный: реплика, перевод на казахский, шаблон ответа, исправления с привязкой к клетке таблицы, новые слова.
- Дневной лимит сообщений — `CHAT_DAILY_LIMIT` (throttling DRF). Неуместные сообщения отсекаются до модели.
- Без ключа отвечает офлайн-заглушка: сценарные вопросы и поиск типичных ошибок (`buyed` → `bought`). Её хватает для разработки и тестов.

## Локализация

Тексты интерфейса размечены Angular i18n, исходный язык — казахский (`kk`). Добавить русский: `npx ng extract-i18n`, перевести `messages.xlf`, добавить локаль в `angular.json`. Казахские тексты, переводы и примеры в `backend/vocabulary/seed.py` должен проверить носитель языка.

## Переменные окружения

См. `.env.example`. В продакшене обязательно: свой `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `AUTH_COOKIE_SECURE=1` за HTTPS, реальный SMTP.
