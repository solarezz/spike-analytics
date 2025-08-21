#!/bin/bash
# Скрипт подготовки сервера для Spike Analytics

echo "🚀 Подготовка сервера для Spike Analytics..."

# Обновляем систему
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y curl wget git unzip

# Устанавливаем Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Добавляем пользователя в группу docker
usermod -aG docker $USER

# Устанавливаем Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Создаем символическую ссылку
ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose

# Проверяем установку
echo "📋 Проверка установки:"
docker --version
docker-compose --version
git --version

echo "✅ Сервер готов! Перезагрузитесь: sudo reboot"
