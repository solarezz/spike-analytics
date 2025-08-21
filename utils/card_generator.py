import os
import re
import time
import tempfile
from jinja2 import Template
from html2image import Html2Image
from PIL import Image, ImageOps
from typing import Dict, Any, Optional
import asyncio
from api.clients.trackerggapi import TrackerGGAPI

def get_rank_image_path(rank_name, tier_level=None):
    rank_mapping = {
        "Iron": "iron",
        "Bronze": "bronze", 
        "Silver": "silver",
        "Gold": "gold",
        "Platinum": "platinum",
        "Diamond": "diamond",
        "Immortal": "immortal",
        "Ascendant": "ascendant",
        "Ascedant": "ascendant",  # Исправляем опечатку
        "Radiant": "radiant"
    }
    
    base_name = rank_mapping.get(rank_name, rank_name.lower())
    project_root = os.path.dirname(os.path.dirname(__file__))

    if base_name == "radiant":
        return os.path.join(project_root, "static", "images", "ranks", f"{base_name}.png")

    if tier_level and tier_level in [1, 2, 3]:
        return os.path.join(project_root, "static", "images", "ranks", f"{base_name}-{tier_level}.png")
    else:
        return os.path.join(project_root, "static", "images", "ranks", f"{base_name}-1.png")

def parse_rank_info(rank_str):
    # Проверяем на None и пустые значения
    if not rank_str or rank_str == "Unranked" or rank_str is None:
        return "Unranked", 1
    
    try:
        # Дополнительная проверка на тип
        if not isinstance(rank_str, str):
            return "Unranked", 1
            
        parts = rank_str.split()
        if len(parts) >= 2 and parts[-1].isdigit():
            tier_level = int(parts[-1])
            rank_name = " ".join(parts[:-1])
            return rank_name, tier_level
        else:
            return rank_str, 1
    except (ValueError, AttributeError, TypeError) as e:
        print(f"⚠️ Ошибка парсинга ранга '{rank_str}': {e}")
        return "Unranked", 1

def sanitize_filename(name: str) -> str:
    name = name.replace(' ', '_')
    return re.sub(r'[<>:"/\\|?*\0]', '', name)

async def generate_enhanced_profile_card_selenium(enhanced_stats: dict, riot_id: str, tagline: str, output_filename: str = None):
    """Генерация карточки через selenium (рекомендуемый метод)"""
    try:
        # Проверяем входные данные
        if not enhanced_stats or not isinstance(enhanced_stats, dict):
            print(f"❌ Неверные данные enhanced_stats: {enhanced_stats}")
            return None
            
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(project_root, 'templates', 'enhanced_profile_card.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)

        # Подготавливаем данные для шаблона с безопасным извлечением
        current_rank = enhanced_stats.get('current_rank') if enhanced_stats else None
        peak_rank = enhanced_stats.get('peak_rank') if enhanced_stats else None
        
        rank_name, tier_level = parse_rank_info(current_rank)
        peak_rank_name, peak_tier_level = parse_rank_info(peak_rank)
        
        # Отладочная информация
        current_rank_image = get_rank_image_path(rank_name, tier_level)
        peak_rank_image = get_rank_image_path(peak_rank_name, peak_tier_level)
        
        print(f"🔍 Current rank: {rank_name} (tier {tier_level}) -> {current_rank_image}")
        print(f"🔍 Peak rank: {peak_rank_name} (tier {peak_tier_level}) -> {peak_rank_image}")
        print(f"🔍 Files exist: current={os.path.exists(current_rank_image)}, peak={os.path.exists(peak_rank_image)}")
        print(f"🔍 Player name: {riot_id}#{tagline}")
        print(f"🔍 Stats: Matches={enhanced_stats.get('matches_played', 0)}, Win Rate={enhanced_stats.get('win_rate', '0%')}")
        print(f"🔍 Combat: K/D={enhanced_stats.get('kd_ratio', 0.0)}, Kills={enhanced_stats.get('kills', 0)}")

        # Формируем полные названия рангов с номерами
        full_current_rank = f"{rank_name} {tier_level}" if tier_level and rank_name != "Unranked" else rank_name
        full_peak_rank = f"{peak_rank_name} {peak_tier_level}" if peak_tier_level and peak_rank_name != "Unranked" else peak_rank_name
        
        template_data = {
            'PLAYER_NAME': f"{riot_id}#{tagline}",  # Добавляем имя игрока
            'RIOT_ID': riot_id,
            'TAGLINE': tagline,
            'REGION': enhanced_stats.get('region', 'N/A'),
            'LEVEL': enhanced_stats.get('account_level', 'N/A'),
            'CURRENT_RANK': full_current_rank,  # Теперь включает номер
            'CURRENT_TIER_LEVEL': tier_level,
            'CURRENT_RR': enhanced_stats.get('current_rr', 0),
            'CURRENT_MMR': enhanced_stats.get('current_rr', 0),  # Добавляем для совместимости с шаблоном
            'PEAK_RANK': full_peak_rank,  # Теперь включает номер
            'PEAK_TIER_LEVEL': peak_tier_level,
            'CURRENT_RANK_IMAGE': current_rank_image,  # Используем переменную
            'PEAK_RANK_IMAGE': peak_rank_image,  # Используем переменную
            'MATCHES': enhanced_stats.get('matches_played', 0),  # Исправлено имя поля
            'WINS': enhanced_stats.get('matches_won', 0),  # Исправлено имя поля
            'LOSSES': enhanced_stats.get('matches_lost', 0),  # Исправлено имя поля
            'WIN_RATE': enhanced_stats.get('win_rate', '0%').replace('%', ''),  # Убираем % для числового значения
            'WINRATE': enhanced_stats.get('win_rate', '0%').replace('%', ''),  # Добавляем для совместимости с шаблоном
            'KILLS': enhanced_stats.get('kills', 0),
            'DEATHS': enhanced_stats.get('deaths', 0),
            'ASSISTS': enhanced_stats.get('assists', 0),
            'KD': enhanced_stats.get('kd_ratio', 0.0),  # Исправлено имя поля
            'DAMAGE_PER_ROUND': enhanced_stats.get('damage_per_round', 0),
            'HEADSHOT_PCT': enhanced_stats.get('headshot_pct', 0),
            'MVPS': enhanced_stats.get('mvps', 0),
            'MATCH_MVPS': enhanced_stats.get('match_mvps', 0),
            'TEAM_MVPS': enhanced_stats.get('team_mvps', 0),
            'FAVORITE_AGENT': enhanced_stats.get('favorite_agent', 'Unknown'),
            'FAVORITE_AGENT_ROLE': enhanced_stats.get('favorite_agent_role', 'Unknown'),
            'AGENT_MATCHES': enhanced_stats.get('agent_matches', 0),
            'TIME_PLAYED': enhanced_stats.get('time_played', '0h'),
            'MATCHES_DURATION': enhanced_stats.get('matches_duration', 'N/A'),
        }

        # Рендерим HTML
        rendered_html = template.render(**template_data)
        
        # Генерируем имя файла
        if not output_filename:
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{riot_id}_{tagline}")
            output_filename = f"{safe_name}_enhanced.png"
        
        # Настройки Chrome для selenium
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1300,1000')  # Увеличиваем для 1200x900 карточки
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--force-device-scale-factor=1')
        chrome_options.add_argument('--disable-extensions')
        
        # Дополнительные опции для Docker
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--disable-default-apps')
        
        # Если в Docker, используем переменные окружения
        if os.getenv('CHROME_OPTIONS'):
            for option in os.getenv('CHROME_OPTIONS').split():
                chrome_options.add_argument(option)
        
        # Создаем временный HTML файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(rendered_html)
            temp_html_path = f.name
        
        try:
            # Запускаем Chrome
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(1300, 1000)  # Увеличиваем для 1200x900 карточки
            
            # Загружаем HTML файл
            driver.get(f'file://{temp_html_path.replace(os.sep, "/")}')
            
            # Ждем загрузки
            driver.implicitly_wait(5)
            time.sleep(3)
            
            # Находим элемент карточки и делаем скриншот только его
            try:
                card_element = driver.find_element("css selector", ".card")
                screenshot = card_element.screenshot_as_png
                print(f"✅ Selenium: карточка {riot_id}#{tagline}")
            except Exception as e:
                print(f"⚠️ Selenium: не удалось найти элемент .card: {e}")
                screenshot = driver.get_screenshot_as_png()
                print("✅ Selenium: скриншот всей страницы")
            
            # Сохраняем изображение
            output_path = os.path.join(project_root, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(screenshot)
            
            print(f"✅ Selenium карточка создана: {output_path}")
            return output_path
            
        finally:
            if 'driver' in locals():
                driver.quit()
            # Удаляем временный файл
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)
                
    except ImportError:
        print("❌ selenium не установлен. Используйте: pip install selenium")
        return None
    except Exception as e:
        print(f"❌ Ошибка selenium: {e}")
        return None

async def generate_enhanced_profile_card(riot_id: str, tagline: str, output_filename: str = None):
    """
    Генерация расширенной карточки профиля с данными из Tracker.gg
    Сначала пытается использовать selenium, затем html2image как fallback
    
    Args:
        riot_id: Riot ID игрока
        tagline: Тег игрока 
        output_filename: Имя выходного файла (опционально)
    
    Returns:
        str: Путь к созданной карточке или None в случае ошибки
    """
    try:
        # Получаем расширенную статистику
        api = TrackerGGAPI()
        enhanced_stats = await api.get_enhanced_player_stats(riot_id, tagline)
        
        if not enhanced_stats:
            print(f"❌ Не удалось получить статистику для {riot_id}#{tagline}")
            return None
            
        # Первый приоритет: selenium (более стабильный)
        print("🔄 Попытка генерации через selenium...")
        selenium_result = await generate_enhanced_profile_card_selenium(
            enhanced_stats, riot_id, tagline, output_filename
        )
        
        if selenium_result:
            print("✅ Карточка создана через selenium!")
            return selenium_result
            
        # Fallback: если selenium не сработал
        print("❌ Selenium не сработал, fallback недоступен")
        return None
        
    except Exception as e:
        print(f"❌ Ошибка при генерации карточки: {e}")
        return None
