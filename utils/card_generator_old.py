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

async def generate_enhanced_profile_card_selenium(enhanced_stats: dict, riot_id: str, tagline: str, output_filename: str = None):
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

def parse_rank_info(rank_string):
    if not rank_string:
        return "Iron", 1
    
    parts = rank_string.split()
    
    if len(parts) == 1:
        return parts[0], 1
    
    rank_name = parts[0]
    try:
        tier_level = int(parts[1])
        if tier_level in [1, 2, 3]:
            return rank_name, tier_level
        else:
            return rank_name, 1
    except ValueError:
        return rank_name, 1

def sanitize_filename(name: str) -> str:
    name = name.replace(' ', '_')
    return re.sub(r'[<>:"/\\|?*\0]', '', name)

def crop_white_space(image_path, target_size=(800, 600)):
    try:
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                if img.mode == 'RGBA':
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                else:
                    img = img.convert('RGB')

            import numpy as np
            img_array = np.array(img)

            threshold = 250
            mask = np.any(img_array < threshold, axis=2)

            if np.any(mask):
                rows = np.any(mask, axis=1)
                cols = np.any(mask, axis=0)
                
                top = np.argmax(rows)
                bottom = len(rows) - np.argmax(rows[::-1]) - 1
                left = np.argmax(cols)
                right = len(cols) - np.argmax(cols[::-1]) - 1

                bbox = (left, top, right + 1, bottom + 1)
                cropped = img.crop(bbox)
 
                cropped = cropped.resize(target_size, Image.Resampling.LANCZOS)

                from PIL import ImageFilter, ImageEnhance

                enhancer = ImageEnhance.Sharpness(cropped)
                cropped = enhancer.enhance(1.2)

                enhancer = ImageEnhance.Contrast(cropped)
                cropped = enhancer.enhance(1.1)

                final_img = Image.new('RGB', target_size, (255, 255, 255))
                final_img.paste(cropped, (0, 0))
                final_img.save(image_path, 'PNG', optimize=False, compress_level=1)

                return True
            else:
                return False
            
    except Exception as e:
        print(f"Ошибка при обрезке изображения: {e}")
        import traceback
        traceback.print_exc()
        return False

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
            
        # Fallback: html2image
        print("🔄 Fallback на html2image...")
        return await generate_enhanced_profile_card_html2image_fallback(
            enhanced_stats, riot_id, tagline, output_filename
        )
    except Exception as e:
        print(f"❌ Ошибка при генерации карточки: {e}")
        return None

async def generate_enhanced_profile_card_html2image_fallback(enhanced_stats: dict, riot_id: str, tagline: str, output_filename: str = None):
            
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(project_root, 'templates', 'enhanced_profile_card.html')
        
        # Fallback на обычный шаблон если расширенного нет
        if not os.path.exists(template_path):
            template_path = os.path.join(project_root, 'templates', 'profile_card.html')

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)

        # Подготавливаем данные для шаблона
        rank_name, tier_level = parse_rank_info(enhanced_stats.get('current_rank', 'Unranked'))
        peak_rank_name, peak_tier_level = parse_rank_info(enhanced_stats.get('peak_rank', 'Unranked'))
        
        template_data = {
            # Основная информация
            'PLAYER_NAME': f"{riot_id}#{tagline}",
            'RIOT_ID': riot_id,
            'TAGLINE': tagline,
            'REGION': 'N/A',  # Нет в API
            'LEVEL': 'N/A',   # Нет в API
            
            # Текущий ранг
            'CURRENT_RANK': enhanced_stats.get('current_rank', 'Unranked'),
            'CURRENT_MMR': enhanced_stats.get('current_rr', 0),
            'CURRENT_RANK_IMAGE': get_rank_image_path(rank_name, tier_level),
            
            # Пиковый ранг
            'PEAK_RANK': enhanced_stats.get('peak_rank', 'Unranked'),
            'PEAK_RR': enhanced_stats.get('peak_rr', 0),
            'PEAK_RANK_IMAGE': get_rank_image_path(peak_rank_name, peak_tier_level),
            'PEAK_EPISODE': 'E9A1',  # Пока статично
            
            # Основная статистика
            'MATCHES': enhanced_stats.get('matches_played', 0),
            'MATCHES_WON': enhanced_stats.get('matches_won', 0),
            'MATCHES_LOST': enhanced_stats.get('matches_lost', 0),
            'WINRATE': str(enhanced_stats.get('win_rate', '0%')).replace('%', ''),
            'KD': enhanced_stats.get('kd_ratio', 0.0),
            'KILLS': enhanced_stats.get('kills', 0),
            'DEATHS': enhanced_stats.get('deaths', 0),
            'ASSISTS': enhanced_stats.get('assists', 0),
            'DAMAGE_PER_ROUND': enhanced_stats.get('damage_per_round', 0),
            'HEADSHOT_PCT': enhanced_stats.get('headshot_pct', 0),
            
            # Достижения
            'MVPS': enhanced_stats.get('mvps', 0),
            'MATCH_MVPS': enhanced_stats.get('match_mvps', 0),
            'TEAM_MVPS': enhanced_stats.get('team_mvps', 0),
            
            # Любимый агент
            'FAVORITE_AGENT': enhanced_stats.get('favorite_agent', 'Unknown'),
            'FAVORITE_AGENT_ROLE': enhanced_stats.get('favorite_agent_role', 'Unknown'),
            'AGENT_MATCHES': enhanced_stats.get('agent_matches', 0),
            
            # Время игры
            'TIME_PLAYED': enhanced_stats.get('time_played', '0h'),
            'MATCHES_DURATION': enhanced_stats.get('matches_duration', 'N/A'),
        }

        # Рендерим HTML
        rendered_html = template.render(**template_data)
        
        # Генерируем имя файла
        if not output_filename:
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', f"{riot_id}_{tagline}")
            output_filename = f"{safe_name}_enhanced.png"
        
        # Путь к выходному файлу
        output_path = os.path.join(project_root, output_filename)
        
        # Настраиваем Html2Image с улучшенными параметрами
        hti = Html2Image(
            output_path=project_root,
            size=(800, 534),
            browser_executable=None,
            temp_path=None,
            custom_flags=['--virtual-time-budget=10000']  # Больше времени на рендеринг
        )
        
        # Улучшенные флаги Chrome для стабильного рендеринга
        chrome_flags = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--hide-scrollbars',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--run-all-compositor-stages-before-draw',
            '--disable-new-content-rendering-timeout',
            '--force-device-scale-factor=1.0',
            '--window-size=800,534',
            '--virtual-time-budget=10000'
        ]
        
        hti.browser.flags = chrome_flags
        
        # Генерируем изображение
        print(f"🎨 Генерация enhanced карточки для {riot_id}#{tagline}...")
        hti.screenshot(
            html_str=rendered_html,
            save_as=output_filename,
            size=(800, 534)
        )
        
        # Простое улучшение качества БЕЗ замены белых пикселей
        try:
            with Image.open(output_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode != 'RGB':
                    if img.mode == 'RGBA':
                        # Создаем фон с темным цветом вместо белого
                        background = Image.new('RGB', img.size, (15, 20, 25))
                        background.paste(img, mask=img.split()[-1])
                        img = background
                    else:
                        img = img.convert('RGB')
                
                # Улучшаем качество
                from PIL import ImageEnhance
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)
                
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(1.05)
                
                # Сохраняем с лучшим качеством
                img.save(output_path, 'PNG', optimize=False, compress_level=1)
                
            print(f"✅ Enhanced карточка создана: {output_path}")
            return output_path
        except Exception as enhance_error:
            print(f"⚠️ Ошибка при улучшении качества: {enhance_error}")
            import traceback
            traceback.print_exc()
            return output_path  # Возвращаем исходный файл
            
    except Exception as e:
        print(f"💥 Ошибка при генерации enhanced карточки: {e}")
        import traceback
        traceback.print_exc()
        return None

def generate_profile_card(player_data, enhanced_stats: Optional[Dict] = None):
    """
    Генерация карточки профиля с поддержкой расширенной статистики
    
    Args:
        player_data: Базовые данные игрока
        enhanced_stats: Расширенная статистика из Tracker.gg (опционально)
    """
    try:
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(project_root, 'templates', 'enhanced_profile_card.html')
        static_dir = os.path.join(project_root, 'static')

        # Fallback на обычный шаблон если расширенного нет
        if not os.path.exists(template_path):
            template_path = os.path.join(project_root, 'templates', 'profile_card.html')

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)

        # Базовая информация игрока
        template_data = {
            'PLAYER_NAME': player_data.get('riot_id') if isinstance(player_data, dict) else player_data.riot_id,
            'REGION': (player_data.get('region') or 'N/A').upper() if isinstance(player_data, dict) else (player_data.region or 'N/A').upper(),
            'LEVEL': player_data.get('account_level', 0) if isinstance(player_data, dict) else getattr(player_data, 'account_level', 0),
        }

        # Обработка ранговой информации
        if isinstance(player_data, dict):
            # Если player_data - словарь (из enhanced_stats)
            rank_info = player_data.get('current_season', {})
            current_rank = rank_info.get('rank', 'Unranked')
            current_rr = rank_info.get('current_rr', 0)
        else:
            # Если player_data - объект
            if player_data.rank_info and player_data.rank_info.current_data:
                current_rank = player_data.rank_info.current_data.currenttierpatched
                current_rr = player_data.rank_info.current_data.ranking_in_tier
            else:
                current_rank = "Unranked"
                current_rr = 0

        rank_name, tier_level = parse_rank_info(current_rank)
        
        template_data.update({
            'CURRENT_RANK': current_rank,
            'CURRENT_MMR': current_rr,
            'CURRENT_RANK_IMAGE': get_rank_image_path(rank_name, tier_level)
        })

        # Peak ранг (пока оставляем из базовых данных)
        if not isinstance(player_data, dict) and player_data.rank_info and player_data.rank_info.highest_rank:
            peak_rank = player_data.rank_info.highest_rank.patched_tier
            season = player_data.rank_info.highest_rank.season
            peak_rank_name, peak_tier_level = parse_rank_info(peak_rank)
            
            template_data.update({
                'PEAK_RANK': peak_rank,
                'PEAK_EPISODE': f"{season}" if season else "N/A",
                'PEAK_RANK_IMAGE': get_rank_image_path(peak_rank_name, peak_tier_level)
            })
        else:
            template_data.update({
                'PEAK_RANK': "Unranked",
                'PEAK_EPISODE': "N/A",
                'PEAK_RANK_IMAGE': os.path.join(project_root, "static", "images", "ranks", "iron-1.png")
            })

        # Расширенная статистика из Tracker.gg
        if enhanced_stats:
            current_season = enhanced_stats.get('current_season', {})
            clutch_master = enhanced_stats.get('clutch_master', {})
            top_agents = enhanced_stats.get('top_agents', [])
            
            template_data.update({
                # Основная статистика
                'MATCHES': current_season.get('matches_played', 0),
                'WINRATE': round(current_season.get('win_rate', 0), 1),
                'KD': round(current_season.get('kd_ratio', 0.0), 2),
                'AVG_SCORE': round(current_season.get('average_score', 0)),
                'HEADSHOT_PCT': round(current_season.get('headshot_percentage', 0), 1),
                
                # Клатч статистика
                'CLUTCHES_WON': clutch_master.get('total_clutches', 0),
                'CLUTCH_PCT': round(clutch_master.get('clutch_percentage', 0), 1),
                'CLUTCHES_1V1': clutch_master.get('clutches_1v1', 0),
                'CLUTCHES_1V2': clutch_master.get('clutches_1v2', 0),
                'CLUTCHES_1V3': clutch_master.get('clutches_1v3', 0),
                'CLUTCHES_1V4': clutch_master.get('clutches_1v4', 0),
                'CLUTCHES_1V5': clutch_master.get('clutches_1v5', 0),
                
                # Attack vs Defense
                'ATTACK_KD': round(current_season.get('attack_kd', 0.0), 2),
                'DEFENSE_KD': round(current_season.get('defense_kd', 0.0), 2),
                'ATTACK_BETTER': current_season.get('attack_kd', 0) > current_season.get('defense_kd', 0),
                
                # Экономика
                'ECON_RATING': round(current_season.get('econ_rating', 0)),
                
                # Стиль игры
                'PLAY_STYLE': enhanced_stats.get('play_style', '🎮 Balanced Player'),
                'MAIN_ROLE': enhanced_stats.get('main_role', 'Unknown'),
                'IS_CLUTCH_GOD': enhanced_stats.get('is_clutch_god', False),
                
                # Профиль активность
                'PROFILE_VIEWS': enhanced_stats.get('profile_views', 0),
                'BADGES_COUNT': enhanced_stats.get('badges_count', 0),
                'SEASON_NAME': current_season.get('season_name', '').replace('Season ', 'S').replace(' Act ', 'A'),
            })
            
            # Топ агенты (до 3 агентов)
            for i in range(3):
                if i < len(top_agents):
                    agent = top_agents[i]
                    template_data[f'AGENT_{i+1}_NAME'] = agent.get('name', '')
                    template_data[f'AGENT_{i+1}_ROLE'] = agent.get('role', '')
                    template_data[f'AGENT_{i+1}_GAMES'] = agent.get('matches_played', 0)
                    template_data[f'AGENT_{i+1}_WINRATE'] = round(agent.get('win_rate', 0), 1)
                    template_data[f'AGENT_{i+1}_KD'] = round(agent.get('kd_ratio', 0.0), 2)
                else:
                    template_data[f'AGENT_{i+1}_NAME'] = ''
                    template_data[f'AGENT_{i+1}_ROLE'] = ''
                    template_data[f'AGENT_{i+1}_GAMES'] = 0
                    template_data[f'AGENT_{i+1}_WINRATE'] = 0
                    template_data[f'AGENT_{i+1}_KD'] = 0.0
        else:
            # Базовые значения если расширенной статистики нет
            template_data.update({
                'MATCHES': 0,
                'WINRATE': 0,
                'KD': 0.0,
                'AVG_SCORE': 0,
                'HEADSHOT_PCT': 0,
                'CLUTCHES_WON': 0,
                'CLUTCH_PCT': 0,
                'PLAY_STYLE': '🎮 Player',
                'MAIN_ROLE': 'Unknown',
                'IS_CLUTCH_GOD': False,
                'SEASON_NAME': 'Current Season'
            })

        html_content = template.render(**template_data)

        # Получение имени для файла
        if isinstance(player_data, dict):
            name = sanitize_filename(player_data.get('riot_id', 'unknown').split('#')[0])
            tag = player_data.get('riot_id', '#0000').split('#')[1] if '#' in player_data.get('riot_id', '') else '0000'
        else:
            name = sanitize_filename(player_data.name)
            tag = player_data.tag

        temp_html_path = os.path.join(project_root, f'temp_{name}_{tag}.html')
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        hti = Html2Image(
            output_path=project_root,
            browser='chrome',
            custom_flags=[
                '--no-sandbox', 
                '--disable-dev-shm-usage', 
                '--hide-scrollbars',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--force-device-scale-factor=3',
                '--disable-gpu-sandbox',
                '--disable-extensions',
                '--no-first-run',
                '--headless'
            ]
        )
        
        output_filename = f'{name}-{tag}.png'
        output_path = os.path.join(project_root, output_filename)

        screenshot = hti.screenshot(
            html_file=temp_html_path,
            size=(2400, 1800),
            save_as=output_filename
        )

        crop_success = crop_white_space(output_path, (800, 600))
        
        if not crop_success:
            print("Предупреждение: не удалось обрезать белое пространство")

        with open(output_path, 'rb') as f:
            img_bytes = f.read()

        os.remove(temp_html_path)
        
        return img_bytes
        
    except Exception as e:
        print(f"Ошибка генерации карточки: {e}")
        import traceback
        traceback.print_exc()
        
        # Очистка временных файлов
        project_root = os.path.dirname(os.path.dirname(__file__))
        temp_html_path = os.path.join(project_root, f'temp_{name}_{tag}.html')
        
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
            
        raise

def generate_enhanced_card(riot_id: str, tagline: str, enhanced_stats: Dict):
    """
    Генерация карточки только с расширенной статистикой (без базового player_data)
    """
    # Создаем базовый объект player_data из enhanced_stats
    player_data = {
        'riot_id': f"{riot_id}#{tagline}",
        'region': enhanced_stats.get('region', 'unknown'),
        'account_level': enhanced_stats.get('account_level', 0)
    }
    
    return generate_profile_card(player_data, enhanced_stats)

def test_generate_enhanced_card():
    """Тестирование с расширенной статистикой"""
    
    # Мок данные для тестирования
    enhanced_stats = {
        'riot_id': 'TestPlayer#1234',
        'account_level': 156,
        'region': 'eu',
        'current_season': {
            'season_name': 'Season 25 Act 4',
            'matches_played': 127,
            'win_rate': 67.5,
            'kd_ratio': 1.23,
            'average_score': 245,
            'headshot_percentage': 28.4,
            'attack_kd': 1.31,
            'defense_kd': 1.15,
            'econ_rating': 2150,
            'rank': 'Immortal 1'
        },
        'clutch_master': {
            'total_clutches': 23,
            'clutch_percentage': 58.5,
            'clutches_1v1': 15,
            'clutches_1v2': 6,
            'clutches_1v3': 2,
            'clutches_1v4': 0,
            'clutches_1v5': 0
        },
        'top_agents': [
            {'name': 'Jett', 'role': 'Duelist', 'matches_played': 45, 'win_rate': 71.1, 'kd_ratio': 1.34},
            {'name': 'Omen', 'role': 'Controller', 'matches_played': 32, 'win_rate': 65.6, 'kd_ratio': 1.18},
            {'name': 'Sova', 'role': 'Initiator', 'matches_played': 28, 'win_rate': 64.3, 'kd_ratio': 1.15}
        ],
        'play_style': '🔥 Clutch God',
        'main_role': 'Duelist',
        'is_clutch_god': True,
        'profile_views': 1337,
        'badges_count': 12
    }

    try:
        img_bytes = generate_enhanced_card('TestPlayer', '1234', enhanced_stats)

        with open("test_enhanced_card.png", "wb") as f:
            f.write(img_bytes)
        
        print("✅ Расширенная тестовая карточка сохранена как test_enhanced_card.png")
        return True
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Тестирование генератора карточек...")
    test_generate_enhanced_card()