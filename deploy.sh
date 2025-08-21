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

# Проверяем права доступа к Docker
if ! docker ps &>/dev/null; then
    echo "❗ Нужны права администратора для Docker..."
    echo "🔧 Добавляем пользователя в группу docker..."
    sudo usermod -aG docker $USER
    echo "🔄 Перезагружаем группы..."
    newgrp docker
    echo "✅ Права настроены!"
fi

# Останавливаем старые контейнеры
echo "🛑 Остановка старых контейнеров..."
sudo docker-compose down 2>/dev/null || true

# Пересобираем и запускаем
echo "🔨 Сборка и запуск..."
sudo docker-compose up --build -d

# Показываем статус
echo "📊 Статус контейнеров:"
sudo docker-compose ps

echo "📝 Посмотреть логи: sudo docker-compose logs -f"
echo "🛑 Остановить: sudo docker-compose down"
echo "✅ Деплой завершен!"
