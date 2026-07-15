# 🥤 Telegram Bot для трекера покупок напитков

Личный Telegram бот для записи покупок напитков с автоматическим расчётом пищевой ценности и использованием Google Sheets в качестве базы данных.

## ✨ Возможности

- ✅ **Добавление напитков** с составом (калории, сахар, кофеин, натрий)
- ✅ **Быстрая запись покупок** одной кнопкой
- ✅ **Автоматический расчёт** пищевой ценности на реальный объём
- ✅ **История покупок** с фильтрацией по датам
- ✅ **Статистика** (затраты, потребление, калории)
- ✅ **Хранение данных** напрямую в Google Sheets
- ✅ **Распознавание чеков и этикеток** (через OCR.space API)
- ✅ **Бесплатный хостинг** (Render.com)

---

## 🚀 Быстрый старт

### 1. Клонирование и подготовка

```bash
cd drink_tracker_bot
pip install -r requirements.txt
cp .env.example .env
```

### 2. Настройка переменных окружения

Отредактируй `.env` файл:

```env
# Telegram (получи от @BotFather в Telegram)
TELEGRAM_BOT_TOKEN=your_token_here

# Google Sheets
# Если запускаешь локально, используй JSON файл:
GOOGLE_SHEETS_CREDENTIALS_JSON=./credentials.json
# Если запускаешь на сервере, скопируй всё содержимое JSON файла в эту переменную:
GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT={"type": "service_account", ...}
GOOGLE_SHEETS_ID=your-sheet-id

# Webhook (Обязательно для защиты от сна на Render)
WEBHOOK_URL=https://your-app-name.onrender.com

# OCR (Для распознавания картинок)
OCR_API_KEY=your_ocr_key

# Твой Telegram ID (узнай у @userinfobot)
OWNER_USER_ID=123456789
```

### 3. Настройка Google Sheets

1. Создай Google Cloud проект и включи Google Sheets API и Google Drive API.
2. Создай Service Account и скачай JSON ключ (это твой `credentials.json`).
3. Создай таблицу Google Sheets и предоставь доступ (Editor) email-адресу твоего Service Account.
4. Скопируй ID таблицы (из URL) в `GOOGLE_SHEETS_ID`.
5. В таблице создай три листа: `Напитки`, `Покупки`, `Логи_Синхронизации`. Заголовки можно не указывать, бот создаст их при первом бэкапе или добавлении напитка.

### 4. Запуск локально

```bash
python main.py
```

---

## ☁️ Развёртывание на Render.com

### Подготовка

1. Залей код на GitHub.
2. Создай `render.yaml` (конфигурация) или настрой Web Service вручную.

### Настройка Web Service на Render

1. Перейди на [render.com](https://render.com)
2. Подключи GitHub аккаунт
3. Нажми "New +" → "Web Service"
4. Выбери репозиторий
5. Установи переменные окружения из `.env` (включая `WEBHOOK_URL` и `GOOGLE_SHEETS_CREDENTIALS_JSON_CONTENT`)
6. Нажми "Deploy"

**Бот будет работать 24/7 на бесплатном плане, моментально просыпаясь через Webhooks!**

---

## 🤖 Команды бота

```
/start       - 🏠 Основное меню
/buy         - 🛒 Записать новую покупку
/history     - 📋 История покупок
/stats       - 📊 Статистика потребления
/admin       - ⚙️ Управление напитками
/help        - ❓ Справка по командам
```

---

## 📊 Структура проекта

```
drink_tracker_bot/
├── main.py                          # Точка входа (Aiohttp сервер для Webhooks)
├── config.py                        # Конфиг и переменные
├── requirements.txt                 # Зависимости
├── .env.example                     # Пример .env
│
├── handlers/
│   ├── start.py        # /start, основное меню
│   ├── buy.py          # /buy, запись покупок
│   ├── history.py      # /history, история
│   ├── stats.py        # /stats, статистика
│   ├── admin.py        # /admin, управление
│   └── photo.py        # Обработка фотографий (OCR)
│
├── database/
│   └── supabase_client.py           # Работа с Google Sheets (название сохранено для совместимости)
│
└── utils/
    ├── calculations.py              # Расчёты
    ├── validators.py                # Валидация
    ├── formatters.py                # Форматирование
    └── ocr_parser.py                # Парсинг текста с изображений
```

---

## 💬 Поддержка

Если что-то не работает:
1. Проверь логи на Render
2. Убедись что Service Account добавлен в Google Sheet с правами редактора
3. Убедись что `WEBHOOK_URL` указан правильно (без слэша на конце)

---

**Приятного использования! 🚀**
