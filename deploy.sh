#!/bin/bash
# Скрипт деплоя Spike Analytics на сервер

echo "🚀 Деплой Spike Analytics..."

# Переходим в домашнюю директорию
cd /home/mark

# Клонируем репозиторий (если еще не клонировали)
if [ ! -d "spike-analytics" ]; then
    echo "📥 Клонирование репозитория..."
    git clone https://github.com/solarezz/spike-analytics.git
else
    echo "📥 Обновление репозитория..."
    cd spike-analytics
    git pull origin main
    cd ..
fi

# Переходим в директорию проекта
cd spike-analytics

# Создаем .env файл если его нет
if [ ! -f ".env" ]; then
    echo "📝 Создание .env файла..."
    cp .env.example .env
    echo "❗ ВАЖНО: Отредактируйте файл .env и добавьте ваш TG_TOKEN!"
    echo "nano .env"
    exit 1
fi

# Останавливаем старые контейнеры
echo "🛑 Остановка старых контейнеров..."
docker-compose down

# Пересобираем и запускаем
echo "🔨 Сборка и запуск..."
docker-compose up --build -d

# Показываем статус
echo "📊 Статус контейнеров:"
docker-compose ps

echo "📝 Посмотреть логи: docker-compose logs -f"
echo "🛑 Остановить: docker-compose down"
echo "✅ Деплой завершен!"
