#!/usr/bin/env python3
"""
Генератор карточек с использованием selenium (основной метод)
"""
import os
import tempfile
import time
from jinja2 import Template
from .card_generator import parse_rank_info, get_rank_image_path

async def generate_enhanced_profile_card_selenium(enhanced_stats: dict, riot_id: str, tagline: str):
    """Генерация карточки через selenium (рекомендуемый метод)"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(project_root, 'templates', 'enhanced_profile_card.html')
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)

        # Подготавливаем данные для шаблона
        rank_name, tier_level = parse_rank_info(enhanced_stats.get('current_rank', 'Unranked'))
        peak_rank_name, peak_tier_level = parse_rank_info(enhanced_stats.get('peak_rank', 'Unranked'))

        template_data = {
            'RIOT_ID': riot_id,
            'TAGLINE': tagline,
            'REGION': enhanced_stats.get('region', 'N/A'),
            'LEVEL': enhanced_stats.get('account_level', 'N/A'),
            'CURRENT_RANK': rank_name,
            'CURRENT_TIER_LEVEL': tier_level,
            'CURRENT_RR': enhanced_stats.get('current_rr', 0),
            'PEAK_RANK': peak_rank_name,
            'PEAK_TIER_LEVEL': peak_tier_level,
            'CURRENT_RANK_IMG': get_rank_image_path(enhanced_stats.get('current_rank', 'Unranked')),
            'PEAK_RANK_IMG': get_rank_image_path(enhanced_stats.get('peak_rank', 'Unranked')),
            'MATCHES': enhanced_stats.get('matches', 0),
            'WINS': enhanced_stats.get('wins', 0),
            'LOSSES': enhanced_stats.get('losses', 0),
            'WIN_RATE': enhanced_stats.get('win_rate', 0),
            'KILLS': enhanced_stats.get('kills', 0),
            'DEATHS': enhanced_stats.get('deaths', 0),
            'ASSISTS': enhanced_stats.get('assists', 0),
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
        
        # Настройки Chrome для selenium
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=900,700')
        chrome_options.add_argument('--hide-scrollbars')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--force-device-scale-factor=1')
        chrome_options.add_argument('--disable-extensions')
        
        # Создаем временный HTML файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(rendered_html)
            temp_html_path = f.name
        
        try:
            # Запускаем Chrome
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(900, 700)
            
            # Загружаем HTML файл
            driver.get(f'file://{temp_html_path.replace(os.sep, "/")}')
            
            # Ждем загрузки
            driver.implicitly_wait(5)
            time.sleep(3)
            
            # Находим элемент карточки и делаем скриншот только его
            try:
                card_element = driver.find_element("css selector", ".card")
                size = card_element.size
                print(f"📐 Размер карточки: {size['width']}x{size['height']}")
                screenshot = card_element.screenshot_as_png
                print("✅ Selenium: скриншот элемента .card")
            except Exception as e:
                print(f"⚠️ Selenium: не удалось найти элемент .card: {e}")
                screenshot = driver.get_screenshot_as_png()
                print("✅ Selenium: скриншот всей страницы")
            
            # Сохраняем изображение
            output_filename = f"{riot_id.replace(' ', '_')}_{tagline}_enhanced_selenium.png"
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
