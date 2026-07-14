# 🗄️ Настройка Supabase

Supabase - это бесплатная и открытая альтернатива Firebase на основе PostgreSQL.

---

## 📝 Шаг 1: Создание аккаунта

1. Перейди на [supabase.com](https://supabase.com)
2. Нажми "Start your project"
3. Зарегистрируйся через GitHub или Email
4. Подтверди почту

---

## 🏗️ Шаг 2: Создание проекта

1. В левом меню нажми "New project"
2. Введи:
   - **Project name:** `drink-tracker`
   - **Database password:** Придумай надёжный пароль (сохрани где-то!)
   - **Region:** Europe (франкфурт или ирландия - ближе к России)
3. Нажми "Create new project"
4. Дождись инициализации (~2-3 минуты)

---

## 🔐 Шаг 3: Получение учётных данных

1. Перейди в "Settings" → "API"
2. Найди **Project URL** - это твой `SUPABASE_URL`
   ```
   https://your-project.supabase.co
   ```
3. Найди **API Key** (anon/public) - это твой `SUPABASE_KEY`
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
4. Скопируй обе строки в `.env` файл:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📊 Шаг 4: Создание таблиц

1. Перейди в "SQL Editor"
2. Нажми "New query"
3. Скопируй содержимое файла `database/init_db.sql`
4. Вставь в редактор
5. Нажми "Run"

Должны создаться таблицы:
- ✅ `drinks` - справочник напитков
- ✅ `purchases` - история покупок
- ✅ `sync_logs` - логи синхронизации

---

## 🔍 Шаг 5: Проверка

1. Перейди в "Table Editor"
2. Убедись что видишь таблицы `drinks`, `purchases`, `sync_logs`
3. Они должны быть пусты (это нормально)

---

## 🔑 Получение User ID

Бот по-умолчанию разрешён только для одного пользователя. Нужно указать его ID:

1. Напиши любому Telegram боту: `@userinfobot`
2. Он ответит с твоим ID
3. Скопируй ID в `.env`:

```env
OWNER_USER_ID=123456789
```

---

## 🧪 Тестирование подключения

Запусти этот Python скрипт для проверки:

```python
import asyncio
from database.supabase_client import db
from config import OWNER_USER_ID

async def test():
    # Добавить тестовый напиток
    drink = await db.add_drink(
        name="Test Drink",
        user_id=OWNER_USER_ID,
        calories=10,
        sugar=2,
        caffeine=20,
        sodium=10
    )
    print("✅ Тестовый напиток добавлен:", drink)
    
    # Получить все напитки
    drinks = await db.get_all_drinks(OWNER_USER_ID)
    print("✅ Полученные напитки:", drinks)

asyncio.run(test())
```

Если нет ошибок - всё работает! 🎉

---

## 📈 Мониторинг

Ты можешь смотреть свои данные в любой момент:

1. Перейди в "Table Editor"
2. Выбери таблицу (drinks, purchases, sync_logs)
3. Вид все записи в реальном времени

---

## 🔒 Безопасность

### ✅ Правильно:
- Используй `SUPABASE_KEY` (public/anon)
- Ключ в `.env` файле (не в коде)
- `.env` в `.gitignore`

### ❌ Неправильно:
- Не используй Service Role Key в фронтенде
- Не загружай `.env` на GitHub
- Не делись ключами с кем-то ещё

---

## 🐛 Решение проблем

### ❌ "Failed to connect to database"
- Проверь что `SUPABASE_URL` и `SUPABASE_KEY` правильные
- Убедись что интернет соединение работает
- Проверь что проект в Supabase активен

### ❌ "Table doesn't exist"
- Запусти SQL скрипт из Шага 4 заново
- Убедись что нет ошибок при запуске

### ❌ "Permission denied"
- Проверь что `SUPABASE_KEY` это public key, а не service role key

---

## 💡 Советы

1. **Резервные копии:** Supabase автоматически создаёт резервные копии
2. **Масштабирование:** На бесплатном плане хватит для личного трекера
3. **Производительность:** Индексы уже созданы для быстрого поиска

---

## 📞 Помощь

Если что-то не работает:
1. Проверь статус Supabase: [status.supabase.com](https://status.supabase.com)
2. Посмотри в "Database" → "Logs"
3. Проверь консоль на ошибки

---

**Готово! 🎉 Теперь у тебя есть бесплатная база данных!**
