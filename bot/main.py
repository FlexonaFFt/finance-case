import logging
import os
from typing import Dict, List, Optional

import requests
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://api:8000")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation states
(
    CHOOSE_AUTH,
    REG_NAME,
    REG_EMAIL,
    REG_PASS,
    LOGIN_EMAIL,
    LOGIN_PASS,
    MAIN_MENU,
    SHOW_ACCOUNTS,
    DEPOSIT_CHOOSE,
    DEPOSIT_AMOUNT,
    TRANSFER_DEST,
    TRANSFER_SOURCE,
    TRANSFER_AMOUNT,
) = range(13)

# Simple in-memory store: chat_id -> token
sessions: Dict[int, str] = {}


def api_post(path: str, json: dict, token: Optional[str] = None) -> requests.Response:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.post(f"{API_BASE_URL}{path}", json=json, headers=headers, timeout=10)


def api_get(path: str, token: Optional[str] = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.get(f"{API_BASE_URL}{path}", headers=headers, timeout=10)


def fetch_accounts(token: str) -> Optional[List[dict]]:
    resp = api_get("/clients/me", token=token)
    if resp.status_code >= 400:
        return None
    data = resp.json()
    return data.get("accounts", [])


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("Пополнить"), KeyboardButton("Перевести")],
            [KeyboardButton("Мои счета")],
        ],
        resize_keyboard=True,
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Привет! Выбери действие:",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("Войти"), KeyboardButton("Зарегистрироваться")]],
            resize_keyboard=True,
        ),
    )
    return CHOOSE_AUTH


async def choose_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").lower()
    if text.startswith("зар"):
        await update.message.reply_text("Введи имя:", reply_markup=back_keyboard())
        return REG_NAME
    if text.startswith("вой") or text.startswith("лог"):
        await update.message.reply_text("Введи email:", reply_markup=back_keyboard())
        return LOGIN_EMAIL
    await update.message.reply_text("Выбери: Войти или Зарегистрироваться")
    return CHOOSE_AUTH


async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await start(update, context)
    context.user_data["reg_name"] = update.message.text.strip()
    await update.message.reply_text("Введи email:", reply_markup=back_keyboard())
    return REG_EMAIL


async def reg_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await start(update, context)
    context.user_data["reg_email"] = update.message.text.strip()
    await update.message.reply_text("Введи пароль:", reply_markup=back_keyboard())
    return REG_PASS


async def reg_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await start(update, context)
    password = update.message.text.strip()
    name = context.user_data.get("reg_name")
    email = context.user_data.get("reg_email")
    resp = api_post("/clients/register", json={"name": name, "email": email, "password": password})
    if resp.status_code >= 400:
        await update.message.reply_text(f"Ошибка: {resp.text}", reply_markup=back_keyboard())
        return REG_PASS
    login_resp = api_post("/clients/login", json={"email": email, "password": password})
    if login_resp.status_code >= 400:
        await update.message.reply_text("Регистрация успешна. Теперь войди.", reply_markup=back_keyboard())
        return CHOOSE_AUTH
    token = login_resp.json().get("access_token")
    sessions[update.effective_chat.id] = token
    await update.message.reply_text("Готово! Ты в системе.", reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await start(update, context)
    context.user_data["login_email"] = update.message.text.strip()
    await update.message.reply_text("Введи пароль:", reply_markup=back_keyboard())
    return LOGIN_PASS


async def login_pass(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await start(update, context)
    email = context.user_data.get("login_email")
    password = update.message.text.strip()
    resp = api_post("/clients/login", json={"email": email, "password": password})
    if resp.status_code >= 400:
        await update.message.reply_text(f"Ошибка: {resp.text}", reply_markup=back_keyboard())
        return LOGIN_PASS
    token = resp.json().get("access_token")
    sessions[update.effective_chat.id] = token
    await update.message.reply_text("Успешный вход.", reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def main_menu_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (update.message.text or "").lower()
    if text.startswith("мои"):
        return await show_accounts_menu(update, context)
    if text.startswith("попол"):
        return await deposit_start(update, context)
    if text.startswith("перев"):
        return await transfer_start(update, context)
    await update.message.reply_text("Выбери действие.", reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def show_accounts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    token = sessions.get(update.effective_chat.id)
    if not token:
        await update.message.reply_text("Нужно войти.", reply_markup=back_keyboard())
        return CHOOSE_AUTH
    accounts = fetch_accounts(token) or []
    if not accounts:
        await update.message.reply_text("Нет счетов.", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    buttons: List[List[KeyboardButton]] = []
    cache: Dict[str, dict] = {}
    for acc in accounts[:5]:
        tail = acc["id"][-4:]
        cache[tail] = acc
        buttons.append([KeyboardButton(f"Счет {tail}")])
    buttons.append([KeyboardButton("Назад")])
    context.user_data["accounts_cache"] = cache
    await update.message.reply_text("Счета:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return SHOW_ACCOUNTS


async def account_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text == "Назад":
        await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    cache: Dict[str, dict] = context.user_data.get("accounts_cache", {})
    tail = text.replace("Счет", "").strip()
    acc = cache.get(tail)
    if not acc:
        await update.message.reply_text("Не нашел счет, выбери кнопку.", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    await update.message.reply_text(
        f"Счет: {acc['id']}\nВалюта: {acc['currency']}\nБаланс: {acc['balance_minor']}",
        reply_markup=ReplyKeyboardMarkup([[KeyboardButton("Назад")]], resize_keyboard=True),
    )
    return SHOW_ACCOUNTS


async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    token = sessions.get(update.effective_chat.id)
    if not token:
        await update.message.reply_text("Нужно войти.", reply_markup=back_keyboard())
        return CHOOSE_AUTH
    accounts = fetch_accounts(token) or []
    if not accounts:
        await update.message.reply_text("Нет счетов.", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    buttons = [[KeyboardButton(acc["id"][-4:])] for acc in accounts[:5]]
    buttons.append([KeyboardButton("Назад")])
    context.user_data["accounts_cache"] = {acc["id"][-4:]: acc for acc in accounts[:5]}
    await update.message.reply_text("Выбери счет для пополнения:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return DEPOSIT_CHOOSE


async def deposit_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    tail = update.message.text.strip()
    cache: Dict[str, dict] = context.user_data.get("accounts_cache", {})
    acc = cache.get(tail)
    if not acc:
        await update.message.reply_text("Счет не найден, выбери кнопку.")
        return DEPOSIT_CHOOSE
    context.user_data["deposit_account"] = acc
    await update.message.reply_text(
        "Введи сумму и комментарий (пример: 1500 Пополнение):",
        reply_markup=back_keyboard(),
    )
    return DEPOSIT_AMOUNT


async def deposit_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        return await deposit_start(update, context)
    token = sessions.get(update.effective_chat.id)
    acc = context.user_data.get("deposit_account")
    parts = update.message.text.split(maxsplit=1)
    if not acc or not parts:
        await update.message.reply_text("Нужно ввести сумму.")
        return DEPOSIT_AMOUNT
    try:
        amount = int(parts[0])
    except ValueError:
        await update.message.reply_text("Сумма должна быть числом.")
        return DEPOSIT_AMOUNT
    desc = parts[1] if len(parts) > 1 else ""
    resp = api_post(
        "/transactions",
        json={
            "account_id": acc["id"],
            "amount_minor": amount,
            "currency": acc["currency"],
            "description": desc,
        },
        token=token,
    )
    if resp.status_code >= 400:
        await update.message.reply_text(f"Ошибка: {resp.text}", reply_markup=back_keyboard())
        return DEPOSIT_AMOUNT
    await update.message.reply_text("Пополнение проведено.", reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def transfer_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    token = sessions.get(update.effective_chat.id)
    if not token:
        await update.message.reply_text("Нужно войти.", reply_markup=back_keyboard())
        return CHOOSE_AUTH
    await update.message.reply_text("Введи счет получателя:", reply_markup=back_keyboard())
    return TRANSFER_DEST


async def transfer_dest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    context.user_data["transfer_dest"] = update.message.text.strip()
    token = sessions.get(update.effective_chat.id)
    accounts = fetch_accounts(token) or []
    if not accounts:
        await update.message.reply_text("Нет счетов.", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    buttons = [[KeyboardButton(acc["id"][-4:])] for acc in accounts[:5]]
    buttons.append([KeyboardButton("Назад")])
    context.user_data["accounts_cache"] = {acc["id"][-4:]: acc for acc in accounts[:5]}
    await update.message.reply_text("Выбери свой счет-источник:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True))
    return TRANSFER_SOURCE


async def transfer_source(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    tail = update.message.text.strip()
    cache: Dict[str, dict] = context.user_data.get("accounts_cache", {})
    acc = cache.get(tail)
    if not acc:
        await update.message.reply_text("Счет не найден, выбери кнопку.")
        return TRANSFER_SOURCE
    context.user_data["transfer_source"] = acc
    await update.message.reply_text(
        "Введи сумму и комментарий (пример: 2000 Перевод):",
        reply_markup=back_keyboard(),
    )
    return TRANSFER_AMOUNT


async def transfer_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == "Назад":
        await update.message.reply_text("Главное меню", reply_markup=main_menu_keyboard())
        return MAIN_MENU
    token = sessions.get(update.effective_chat.id)
    acc = context.user_data.get("transfer_source")
    dest = context.user_data.get("transfer_dest")
    parts = update.message.text.split(maxsplit=1)
    if not acc or not parts:
        await update.message.reply_text("Нужно ввести сумму.")
        return TRANSFER_AMOUNT
    try:
        amount = int(parts[0])
    except ValueError:
        await update.message.reply_text("Сумма должна быть числом.")
        return TRANSFER_AMOUNT
    desc_extra = parts[1] if len(parts) > 1 else ""
    desc = f"Перевод на {dest}. {desc_extra}".strip()
    resp = api_post(
        "/transactions",
        json={
            "account_id": acc["id"],
            "amount_minor": -amount,
            "currency": acc["currency"],
            "description": desc,
        },
        token=token,
    )
    if resp.status_code >= 400:
        await update.message.reply_text(f"Ошибка: {resp.text}", reply_markup=back_keyboard())
        return TRANSFER_AMOUNT
    await update.message.reply_text("Перевод проведен (списание).", reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено. Главное меню.", reply_markup=main_menu_keyboard())
    return MAIN_MENU


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Неизвестная команда. Напиши /start")
    return ConversationHandler.END


def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")
    application = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSE_AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_auth)],
            REG_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            REG_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_email)],
            REG_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_pass)],
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASS: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_pass)],
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu_router)],
            SHOW_ACCOUNTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, account_details)],
            DEPOSIT_CHOOSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_choose)],
            DEPOSIT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount)],
            TRANSFER_DEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_dest)],
            TRANSFER_SOURCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_source)],
            TRANSFER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_amount)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv)
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.run_polling()


if __name__ == "__main__":
    main()
