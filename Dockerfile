# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем системные зависимости для Selenium и Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Google Chrome (более простой способ)
RUN curl -sSL https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb -o chrome.deb \
    && apt-get update \
    && apt-get install -y ./chrome.deb \
    && rm chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash bot

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Меняем владельца файлов на пользователя bot
RUN chown -R bot:bot /app

# Переключаемся на пользователя bot
USER bot

# Указываем переменные окружения для Chrome
ENV DISPLAY=:99
ENV CHROME_OPTIONS="--headless --no-sandbox --disable-dev-shm-usage --disable-gpu --window-size=1920,1080"

# Открываем порт (если понадобится для вебхуков)
EXPOSE 8000

# Запускаем бота
CMD ["python", "run_bot.py"]
