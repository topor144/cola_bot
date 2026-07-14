# 🥤 Telegram Bot для трекера покупок напитков

Личный Telegram бот для записи покупок напитков с автоматическим расчётом пищевой ценности и синхронизацией с Excel.

## ✨ Возможности

- ✅ **Добавление напитков** с составом (калории, сахар, кофеин, натрий)
- ✅ **Быстрая запись покупок** одной кнопкой
- ✅ **Автоматический расчёт** пищевой ценности на реальный объём
- ✅ **История покупок** с фильтрацией по датам
- ✅ **Статистика** (затраты, потребление, калории)
- ✅ **Синхронизация** с Google Sheets и Excel
- ✅ **Бесплатный хостинг** (Render.com / Railway.app)
- ✅ **Бесплатная база данных** (Supabase)

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

# Supabase (создай проект на supabase.com)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here

# Google Sheets (скачай credentials.json)
GOOGLE_SHEETS_CREDENTIALS_JSON=./credentials.json
GOOGLE_SHEETS_ID=your-sheet-id

# Твой Telegram ID (узнай у @userinfobot)
OWNER_USER_ID=123456789
```

### 3. Создание Telegram бота

1. Напиши @BotFather в Telegram
2. Выполни `/newbot`
3. Введи имя бота и username
4. Скопируй токен в `.env` как `TELEGRAM_BOT_TOKEN`

### 4. Создание Supabase проекта

1. Перейди на [supabase.com](https://supabase.com)
2. Создай новый проект
3. Скопируй URL и API ключ в `.env`
4. Запусти SQL скрипты из раздела "Инициализация БД" ниже

### 5. Google Sheets интеграция (опционально)

1. Создай Google Cloud проект
2. Включи Sheets API
3. Создай Service Account
4. Скачай JSON ключ как `credentials.json`
5. Создай Google Sheet и скопируй его ID в `.env`

### 6. Запуск локально

```bash
python main.py
```

---

## 🗄️ Инициализация БД

Запусти эти SQL команды в Supabase SQL editor:

```sql
-- Таблица напитков
CREATE TABLE drinks (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  user_id BIGINT NOT NULL,
  calories_per_100ml DECIMAL(5,2),
  sugar_per_100ml DECIMAL(5,2),
  caffeine_per_100ml DECIMAL(5,2),
  sodium_per_100ml DECIMAL(5,2),
  volume_default INT DEFAULT 2000,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица покупок
CREATE TABLE purchases (
  id SERIAL PRIMARY KEY,
  drink_id INT REFERENCES drinks(id),
  user_id BIGINT NOT NULL,
  purchase_date DATE NOT NULL,
  volume_ml INT NOT NULL,
  price_rub DECIMAL(10,2),
  calories_total DECIMAL(8,2),
  sugar_total DECIMAL(8,2),
  caffeine_total DECIMAL(8,2),
  sodium_total DECIMAL(8,2),
  notes VARCHAR(500),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Таблица логов синхронизации
CREATE TABLE sync_logs (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  sync_date TIMESTAMP DEFAULT NOW(),
  status VARCHAR(50),
  message TEXT
);

-- Индексы для оптимизации
CREATE INDEX idx_drinks_user_id ON drinks(user_id);
CREATE INDEX idx_purchases_user_id ON purchases(user_id);
CREATE INDEX idx_purchases_date ON purchases(purchase_date);
CREATE INDEX idx_sync_logs_user ON sync_logs(user_id);
```

---

## ☁️ Развёртывание на Render.com

### Подготовка

1. Залей код на GitHub:
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/drink-tracker-bot.git
git push -u origin main
```

2. Создай `render.yaml` (конфигурация):

```yaml
services:
  - type: web
    name: drink-tracker-bot
    env: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: OWNER_USER_ID
        sync: false
```

### Развёртывание

1. Перейди на [render.com](https://render.com)
2. Подключи GitHub аккаунт
3. Нажми "New +" → "Web Service"
4. Выбери репозиторий
5. Установи переменные окружения из `.env`
6. Нажми "Deploy"

**Бот будет работать 24/7 на бесплатном плане!**

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
├── main.py                          # Точка входа
├── config.py                        # Конфиг и переменные
├── requirements.txt                 # Зависимости
├── .env.example                     # Пример .env
│
├── handlers/
│   ├── start.py        # /start, основное меню
│   ├── buy.py          # /buy, запись покупок
│   ├── history.py      # /history, история
│   ├── stats.py        # /stats, статистика
│   └── admin.py        # /admin, управление
│
├── database/
│   ├── supabase_client.py           # Работа с БД
│   └── queries.py                   # SQL запросы
│
├── sheets/
│   └── sync.py         # Синхронизация Google Sheets
│
└── utils/
    ├── calculations.py              # Расчёты
    ├── validators.py                # Валидация
    └── formatters.py                # Форматирование
```

---

## 🛠️ Возможные проблемы

### ❌ "TELEGRAM_BOT_TOKEN не установлен"
**Решение:** Добавь токен в `.env` файл

### ❌ "Ошибка подключения к Supabase"
**Решение:** Проверь URL и ключ в `.env`, убедись что таблицы созданы

### ❌ "Синхронизация не работает"
**Решение:** 
1. Проверь `credentials.json` файл
2. Убедись что Service Account имеет доступ к Sheet
3. Проверь логи: `tail -f logs/sync.log`

### ❌ "Бот не отвечает"
**Решение:**
```bash
# Проверь логи
tail -f logs/bot.log

# Перезагрузи бот
pkill -f "python main.py"
python main.py
```

---

## 📈 Примеры использования

### Добавить напиток
```
/admin → ➕ Добавить напиток
Название: Любимая COLA
Калории на 100мл: 18
Сахар: 4.6
Кофеин: 34
Натрий: 30
```

### Записать покупку
```
/buy → Выбрать напиток → Выбрать объём → Ввести цену
```

### Посмотреть статистику
```
/stats → Выбрать период (7 дней, месяц, квартал)
```

---

## 📄 Лицензия

MIT License - используй как хочешь!

---

## 💬 Поддержка

Если что-то не работает:
1. Проверь логи
2. Убедись что все переменные в `.env` установлены
3. Проверь интернет соединение
4. Перезагрузи приложение

---

**Приятного использования! 🚀**
