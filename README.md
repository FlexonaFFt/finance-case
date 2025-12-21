# Finance Case

Минимальный бэкенд для счетов/транзакций с переводами и телеграм-ботом. Данные хранятся в Postgres, логи переводов — в Mongo.

## Что входит
- `api` (FastAPI): регистрация/логин, счета, транзакции, переводы.
- `telegram-bot`: пошаговая регистрация/логин, пополнение, перевод, просмотр счетов.
- `postgres`: основная БД (схема создается из `db/init` при первом старте тома).
- `mongo`: логи переводов (коллекция `transfer_events`).

## Быстрый старт (Docker)
1. Заполнить `.env` (есть пример в репо). Минимум: `BOT_TOKEN`, `JWT_SECRET` при желании поменять.
2. Поднять стек:
   ```bash
   docker compose up --build -d
   ```
3. Доступы:
   - API: http://localhost:8000
   - Postgres: localhost:5432 (postgres/postgres, БД finance)
   - Mongo: mongodb://localhost:27017/finance_logs
4. Первый запуск создаст схему и сиды в Postgres. При смене схемы — `docker compose down -v && docker compose up --build`.

## Основные эндпоинты API
- `POST /clients/register` — {name, email, password}, создает клиента и пустой счет в RUB.
- `POST /clients/login` — {email, password}, возвращает bearer.
- `GET /clients/me` — профиль и счета.
- `POST /clients/{id}/accounts` — создать счет (нужен токен владельца).
- `POST /transactions` — депозит/списание по счету (amount_minor с нужным знаком).
- `POST /transfers` — перевод между счетами (amount_minor > 0, создаются debit/credit и запись в transfers + лог в Mongo).

## Telegram-бот
- Запуск в составе compose (сервис `telegram-bot`), нужен `BOT_TOKEN` в `.env`.
- Флоу: `/start` → выбрать «Войти»/«Зарегистрироваться» → главное меню (Пополнить / Перевести / Мои счета).
- При пополнении/переводе выбирается счет из списка (до 5 штук).

## Подключения к БД
- Postgres: `psql postgresql://postgres:postgres@localhost:5432/finance`
- Mongo: `mongodb://localhost:27017/finance_logs` (auth off)

## Полезное
- Пересоздать чисто: `docker compose down -v && docker compose up --build`
- Логи: `docker compose logs api`, `docker compose logs telegram-bot`