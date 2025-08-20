# Spike Analytics - VALORANT Profile Bot

🎮 Telegram бот для генерации красивых карточек профилей VALORANT игроков.

## 🚀 Быстрый запуск

### Требования
- Python 3.9+ (для локального запуска)
- **ИЛИ** Docker + Docker Compose (рекомендуется)
- Telegram Bot Token

### 🐳 Запуск через Docker (рекомендуется)

1. **Клонируйте репозиторий:**
```bash
git clone https://github.com/solarezz/spike-analytics.git
cd spike-analytics
```

2. **Создайте .env файл:**
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив ваш Telegram Bot Token
```

3. **Запустите через Docker Compose:**
```bash
docker-compose up --build
```

**Готово! 🎉** Бот запущен в контейнере и готов к работе.

### 🛠️ Локальный запуск (альтернатива)

1. **Выполните шаги 1-2 выше**

2. **Создайте виртуальное окружение:**
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

3. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

4. **Запустите бота:**
```bash
python run_bot.py
```

## 🎯 Функционал

### ✅ Готовые команды:
- `/start` - Приветствие и помощь
- `/profile valorant username#tag` - Генерация профиль-карточки

### 📊 Что показывает:
- **Визуальная карточка (1200x900px):**
  - Текущий и пиковый ранг с иконками
  - Статистика матчей и побед
  - K/D ratio и средний урон
  - Любимый агент
  
- **Текстовая сводка:**
  - Ранг и регион
  - Количество матчей и винрейт
  - Любимый агент с количеством игр
  - Стиль игры

### 🎨 Особенности:
- Обход защиты TrackerGG через CloudScraper
- Все ранги от Iron до Radiant с правильными иконками
- Поддержка всех агентов включая новых (Clove)
- Автоматическое удаление временных файлов

## � Docker

### Преимущества Docker версии:
- ✅ Все зависимости включены (Chrome, ChromeDriver)
- ✅ Одинаковая работа на любой ОС
- ✅ Легкий деплой на сервер
- ✅ Изоляция от системы

### Docker команды:
```bash
# Собрать образ
docker build -t spike-analytics .

# Запустить контейнер
docker run -d --name spike-bot --env-file .env spike-analytics

# Посмотреть логи
docker logs spike-bot

# Остановить
docker stop spike-bot

# Удалить
docker rm spike-bot
```

### Docker Compose (рекомендуется):
```bash
# Запустить в фоне
docker-compose up -d

# Посмотреть логи
docker-compose logs -f

# Остановить
docker-compose down

# Пересобрать и запустить
docker-compose up --build
```

## �🔧 Архитектура

```
spike-analytics/
├── api/clients/           # TrackerGG API клиент
├── bot/handlers/          # Telegram команды
├── static/images/ranks/   # Иконки рангов
├── templates/             # HTML шаблоны карточек
├── utils/                 # Генератор карточек
└── run_bot.py            # Точка входа
```

## 📋 Состояние альфа-версии

**✅ Работает:**
- Генерация карточек профилей
- Все ранги и агенты
- Обход защиты TrackerGG API
- Стабильная работа Selenium

**🔧 Планы:**
- Добавление команд для статистики матчей
- Поддержка других регионов
- Кэширование данных
- Улучшение дизайна карточек

## 🐛 Известные проблемы

- Selenium может быть медленным на слабых серверах
- TrackerGG иногда возвращает 403 (решается через CloudScraper)

## 📞 Поддержка

Если нашли баг или есть предложения - создайте Issue в GitHub.

---
**Статус:** 🟢 Alpha Ready
**Версия:** 1.0.0-alpha
**Дата:** Август 2025
