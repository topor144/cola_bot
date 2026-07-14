-- Инициализация базы данных Supabase для бота трекера напитков
-- Запусти эти команды в SQL editor на Supabase

-- ============ Таблица DRINKS ============
CREATE TABLE IF NOT EXISTS drinks (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  user_id BIGINT NOT NULL,
  calories_per_100ml DECIMAL(5,2) NOT NULL,
  sugar_per_100ml DECIMAL(5,2) NOT NULL,
  caffeine_per_100ml DECIMAL(5,2) NOT NULL,
  sodium_per_100ml DECIMAL(5,2) NOT NULL,
  volume_default INT DEFAULT 2000,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Комментарий таблицы
COMMENT ON TABLE drinks IS 'Справочник напитков с составом на 100мл';
COMMENT ON COLUMN drinks.user_id IS 'ID владельца бота (фильтр доступа)';
COMMENT ON COLUMN drinks.calories_per_100ml IS 'Калории на 100мл (ккал)';
COMMENT ON COLUMN drinks.caffeine_per_100ml IS 'Кофеин на 100мл (мг)';

-- ============ Таблица PURCHASES ============
CREATE TABLE IF NOT EXISTS purchases (
  id SERIAL PRIMARY KEY,
  drink_id INT REFERENCES drinks(id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL,
  purchase_date DATE NOT NULL,
  volume_ml INT NOT NULL,
  price_rub DECIMAL(10,2),
  calories_total DECIMAL(8,2),
  sugar_total DECIMAL(8,2),
  caffeine_total DECIMAL(8,2),
  sodium_total DECIMAL(8,2),
  notes VARCHAR(500),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE purchases IS 'История покупок напитков';
COMMENT ON COLUMN purchases.user_id IS 'ID владельца (фильтр доступа)';
COMMENT ON COLUMN purchases.volume_ml IS 'Реальный объём покупки в мл';
COMMENT ON COLUMN purchases.calories_total IS 'Общие калории на весь объём';

-- ============ Таблица SYNC_LOGS ============
CREATE TABLE IF NOT EXISTS sync_logs (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  status VARCHAR(50) CHECK (status IN ('success', 'failed', 'pending')),
  message TEXT,
  synced_count INT DEFAULT 0
);

COMMENT ON TABLE sync_logs IS 'Логирование синхронизации с Google Sheets';

-- ============ ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ ============
CREATE INDEX IF NOT EXISTS idx_drinks_user_id ON drinks(user_id);
CREATE INDEX IF NOT EXISTS idx_drinks_name ON drinks(name);

CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_drink_id ON purchases(drink_id);
CREATE INDEX IF NOT EXISTS idx_purchases_date ON purchases(purchase_date);
CREATE INDEX IF NOT EXISTS idx_purchases_created ON purchases(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sync_logs_user ON sync_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_sync_logs_date ON sync_logs(sync_date DESC);

-- ============ ПРЕДСТАВЛЕНИЯ (Views) ============

-- Статистика за период
CREATE OR REPLACE VIEW v_purchase_stats AS
SELECT 
  user_id,
  DATE_TRUNC('month', purchase_date)::DATE as month,
  COUNT(*) as total_purchases,
  SUM(price_rub) as total_spent,
  AVG(price_rub) as avg_price,
  SUM(volume_ml) as total_volume,
  SUM(calories_total) as total_calories,
  SUM(sugar_total) as total_sugar,
  SUM(caffeine_total) as total_caffeine,
  SUM(sodium_total) as total_sodium
FROM purchases
GROUP BY user_id, DATE_TRUNC('month', purchase_date);

-- Популярные напитки
CREATE OR REPLACE VIEW v_popular_drinks AS
SELECT 
  user_id,
  drink_id,
  d.name,
  COUNT(*) as purchase_count,
  SUM(volume_ml) as total_volume,
  AVG(price_rub) as avg_price
FROM purchases p
JOIN drinks d ON p.drink_id = d.id
GROUP BY user_id, drink_id, d.name
ORDER BY purchase_count DESC;

-- ============ ФУНКЦИИ ============

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_drinks_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггер для updated_at
CREATE OR REPLACE TRIGGER trigger_drinks_updated
BEFORE UPDATE ON drinks
FOR EACH ROW
EXECUTE FUNCTION update_drinks_timestamp();

-- ============ RLS (Row Level Security) - ОПЦИОНАЛЬНО ============
-- Раскомментируй если нужна дополнительная безопасность

/*
ALTER TABLE drinks ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_logs ENABLE ROW LEVEL SECURITY;

-- Политика для drinks: пользователь видит только свои напитки
CREATE POLICY drinks_own_drinks ON drinks
  FOR ALL USING (user_id = (SELECT auth.uid()::BIGINT))
  WITH CHECK (user_id = (SELECT auth.uid()::BIGINT));

-- Политика для purchases
CREATE POLICY purchases_own_purchases ON purchases
  FOR ALL USING (user_id = (SELECT auth.uid()::BIGINT))
  WITH CHECK (user_id = (SELECT auth.uid()::BIGINT));

-- Политика для sync_logs
CREATE POLICY sync_logs_own_logs ON sync_logs
  FOR ALL USING (user_id = (SELECT auth.uid()::BIGINT))
  WITH CHECK (user_id = (SELECT auth.uid()::BIGINT));
*/

-- ============ ДАННЫЕ ДЛЯ ТЕСТИРОВАНИЯ ============
-- Раскомментируй для быстрого тестирования

/*
INSERT INTO drinks (name, user_id, calories_per_100ml, sugar_per_100ml, caffeine_per_100ml, sodium_per_100ml, volume_default)
VALUES 
  ('Любимая COLA', 123456789, 18, 4.6, 34, 30, 2000),
  ('Pepsi Original', 123456789, 41, 10, 38, 30, 2000),
  ('Sprite', 123456789, 42, 10.6, 0, 28, 2000)
ON CONFLICT DO NOTHING;
*/

-- ============ ПРОВЕРКА ============
-- Выполни это для проверки:
/*
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
SELECT * FROM drinks;
SELECT * FROM purchases;
*/

-- ✅ Инициализация завершена!
