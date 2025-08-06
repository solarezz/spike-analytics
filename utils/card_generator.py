import os
from jinja2 import Template
from html2image import Html2Image

def get_rank_image_path(rank_name, tier_level=None):
    """
    Получает абсолютный путь к изображению ранга
    """
    # Нормализуем название ранга
    rank_mapping = {
        "Iron": "iron",
        "Bronze": "bronze", 
        "Silver": "silver",
        "Gold": "gold",
        "Platinum": "platinum",
        "Diamond": "diamond",
        "Immortal": "immortal",
        "Ascendant": "ascedant",
        "Ascedant": "ascedant",
        "Radiant": "radiant"
    }
    
    base_name = rank_mapping.get(rank_name, rank_name.lower())
    
    # Получаем абсолютный путь к проекту
    project_root = os.path.dirname(os.path.dirname(__file__))
    
    # Для Radiant всегда один файл
    if base_name == "radiant":
        return os.path.join(project_root, "static", "images", "ranks", f"{base_name}.png")
    
    # Для остальных используем уровень
    if tier_level and tier_level in [1, 2, 3]:
        return os.path.join(project_root, "static", "images", "ranks", f"{base_name}-{tier_level}.png")
    else:
        return os.path.join(project_root, "static", "images", "ranks", f"{base_name}-1.png")

def parse_rank_info(rank_string):
    """
    Разбирает строку ранга и возвращает название и уровень
    """
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

def generate_profile_card(player_data):
    """
    Генерирует карточку профиля как изображение PNG с помощью html2image
    """
    try:
        # Получаем абсолютные пути
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(project_root, 'templates', 'profile_card.html')
        static_dir = os.path.join(project_root, 'static')
        
        # Проверяем существование файлов
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")
        
        # Читаем HTML шаблон
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Создаем Jinja2 шаблон
        template = Template(template_content)
        
        # Подготавливаем данные для шаблона
        template_data = {
            'PLAYER_NAME': player_data.name,
            'PLAYER_TAG': player_data.tag,
            'REGION': player_data.region.upper() if player_data.region else "N/A",
            'LEVEL': player_data.account_level,
        }
        
        # Данные текущего ранга
        if player_data.rank_info and player_data.rank_info.current_data:
            current_rank = player_data.rank_info.current_data.currenttierpatched
            rr = player_data.rank_info.current_data.ranking_in_tier
            
            # Разбираем информацию о ранге
            rank_name, tier_level = parse_rank_info(current_rank)
            
            template_data.update({
                'CURRENT_RANK': current_rank,
                'CURRENT_MMR': rr,
                'CURRENT_RANK_IMAGE': get_rank_image_path(rank_name, tier_level)
            })
        else:
            # Если нет данных о ранге
            template_data.update({
                'CURRENT_RANK': "Unranked",
                'CURRENT_MMR': 0,
                'CURRENT_RANK_IMAGE': os.path.join(project_root, "static", "images", "ranks", "iron-1.png")
            })
        
        # Данные пикового ранга
        if player_data.rank_info and player_data.rank_info.highest_rank:
            peak_rank = player_data.rank_info.highest_rank.patched_tier
            season = player_data.rank_info.highest_rank.season
            
            # Разбираем информацию о пиковом ранге
            peak_rank_name, peak_tier_level = parse_rank_info(peak_rank)
            
            template_data.update({
                'PEAK_RANK': peak_rank,
                'PEAK_EPISODE': f"Episode 8 • {season}" if season else "N/A",
                'PEAK_RANK_IMAGE': get_rank_image_path(peak_rank_name, peak_tier_level)
            })
        else:
            # Если нет данных о пиковом ранге
            template_data.update({
                'PEAK_RANK': "Unranked",
                'PEAK_EPISODE': "N/A",
                'PEAK_RANK_IMAGE': os.path.join(project_root, "static", "images", "ranks", "iron-1.png")
            })
        
        # Статистика (пока заглушки)
        template_data.update({
            'MATCHES': 0,
            'WINRATE': 0,
            'KD': 0.0,
            'AVG': 0
        })
        
        # Рендерим HTML с данными
        html_content = template.render(**template_data)
        
        # Создаем временный HTML файл
        temp_html_path = os.path.join(project_root, 'temp_profile_card.html')
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Используем html2image для конвертации
        hti = Html2Image(
            output_path=project_root,
            custom_flags=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--headless=new'
            ]
        )
        
        # Генерируем изображение
        screenshot = hti.screenshot(
            html_file=temp_html_path,
            size=(969,696),
            save_as='temp_card_screenshot.png'
        )
        
        # Читаем сгенерированное изображение
        screenshot_path = os.path.join(project_root, 'temp_card_screenshot.png')
        with open(screenshot_path, 'rb') as f:
            img_bytes = f.read()
        
        # Удаляем временные файлы
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        
        return img_bytes
        
    except Exception as e:
        print(f"Ошибка генерации карточки: {e}")
        # Удаляем временные файлы в случае ошибки
        temp_html_path = os.path.join(project_root, 'temp_profile_card.html')
        screenshot_path = os.path.join(project_root, 'temp_card_screenshot.png')
        
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        raise

# Тестовая функция
def test_generate_card():
    """
    Тестовая функция для проверки генерации карточки
    """
    # Создаем тестовые данные
    class TestPlayer:
        def __init__(self):
            self.name = "TestPlayer"
            self.tag = "1234"
            self.region = "eu"
            self.account_level = 156
            
            class TestRankInfo:
                class TestCurrentData:
                    currenttierpatched = "Immortal 1"
                    ranking_in_tier = 67
                
                class TestHighestRank:
                    patched_tier = "Radiant"
                    season = "Act 2"
                
                current_data = TestCurrentData()
                highest_rank = TestHighestRank()
            
            self.rank_info = TestRankInfo()
    
    # Генерируем карточку
    try:
        player = TestPlayer()
        img_bytes = generate_profile_card(player)
        
        # Сохраняем для проверки
        with open("test_card.png", "wb") as f:
            f.write(img_bytes)
        
        print("Тестовая карточка сохранена как test_card.png")
        return True
    except Exception as e:
        print(f"Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    # Запуск теста
    test_generate_card()