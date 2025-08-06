import os
from jinja2 import Template
import imgkit

def get_rank_image_path(rank_name, tier_level=None):
    """
    Получает путь к изображению ранга
    
    Args:
        rank_name (str): Название ранга (Iron, Bronze, Silver, etc.)
        tier_level (int): Уровень ранга (1-3) или None для Radiant
    
    Returns:
        str: Путь к изображению
    """
    # Нормализуем название ранга (исправляем опечатки)
    rank_mapping = {
        "Iron": "iron",
        "Bronze": "bronze", 
        "Silver": "silver",
        "Gold": "gold",
        "Platinum": "platinum",
        "Diamond": "diamond",
        "Immortal": "immortal",
        "Ascendant": "ascedant",  # Исправлено с Ascendant на ascedant
        "Ascedant": "ascedant",   # Альтернативное написание
        "Radiant": "radiant"
    }
    
    # Получаем базовое имя файла
    base_name = rank_mapping.get(rank_name, rank_name.lower())
    
    # Для Radiant всегда один файл
    if base_name == "radiant":
        return "radiant.png"
    
    # Для остальных используем уровень
    if tier_level and tier_level in [1, 2, 3]:
        return f"{base_name}-{tier_level}.png"
    else:
        return f"{base_name}-1.png"

def get_rank_classes(rank_name, tier_level):
    """
    Получает CSS классы для отображения ранга
    
    Args:
        rank_name (str): Название ранга
        tier_level (int): Уровень ранга (1-3)
    
    Returns:
        tuple: (wrapper_class, rank_class)
    """
    # Нормализуем название ранга
    normalized_name = rank_name.lower()
    
    # Исправляем Ascendant -> Ascedant
    if normalized_name == "ascendant":
        normalized_name = "ascedant"
    
    # Для Radiant всегда используем один класс
    if normalized_name == "radiant":
        return "radiant-crown-wrapper", "radiant-crown"
    
    # Для остальных рангов используем уровень
    if tier_level in [1, 2, 3]:
        wrapper_class = f"{normalized_name}-rank-wrapper-{tier_level}"
        rank_class = f"{normalized_name}-rank"
        return wrapper_class, rank_class
    
    # По умолчанию для 1 уровня
    return f"{normalized_name}-rank-wrapper-1", f"{normalized_name}-rank"

def parse_rank_info(rank_string):
    """
    Разбирает строку ранга и возвращает название и уровень
    
    Args:
        rank_string (str): Строка ранга, например "Immortal 1"
    
    Returns:
        tuple: (rank_name, tier_level)
    """
    if not rank_string:
        return "Iron", 1
    
    # Разбиваем строку на части
    parts = rank_string.split()
    
    # Если только название ранга
    if len(parts) == 1:
        return parts[0], 1
    
    # Если название + уровень
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
    Генерирует карточку профиля как изображение PNG
    
    Args:
        player_data (Player): Объект игрока с данными
        
    Returns:
        bytes: Байты изображения PNG
    """
    try:
        # Получаем абсолютные пути
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(project_root, 'templates', 'profile_card.html')
        static_dir = os.path.join(project_root, 'static')
        css_dir = os.path.join(static_dir, 'css')
        images_dir = os.path.join(static_dir, 'images')
        ranks_dir = os.path.join(images_dir, 'ranks')
        
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
                'CURRENT_MMR': rr,  # В шаблоне используется CURRENT_MMR
                'RANK_WRAPPER_CLASS': get_rank_classes(rank_name, tier_level)[0],
                'RANK_CLASS': get_rank_classes(rank_name, tier_level)[1],
                'CURRENT_RANK_IMAGE': get_rank_image_path(rank_name, tier_level)
            })
        else:
            # Если нет данных о ранге
            template_data.update({
                'CURRENT_RANK': "Unranked",
                'CURRENT_MMR': 0,
                'RANK_WRAPPER_CLASS': "iron-rank-wrapper-1",
                'RANK_CLASS': "iron-rank",
                'CURRENT_RANK_IMAGE': "iron-1.png"
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
                'PEAK_RANK_WRAPPER_CLASS': get_rank_classes(peak_rank_name, peak_tier_level)[0],
                'PEAK_RANK_CLASS': get_rank_classes(peak_rank_name, peak_tier_level)[1],
                'PEAK_RANK_IMAGE': get_rank_image_path(peak_rank_name, peak_tier_level)
            })
        else:
            # Если нет данных о пиковом ранге
            template_data.update({
                'PEAK_RANK': "Unranked",
                'PEAK_EPISODE': "N/A",
                'PEAK_RANK_WRAPPER_CLASS': "iron-rank-wrapper-1",
                'PEAK_RANK_CLASS': "iron-rank",
                'PEAK_RANK_IMAGE': "iron-1.png"
            })
        
        # Статистика (пока заглушки, позже добавим реальные данные)
        template_data.update({
            'MATCHES': 0,  # Позже получим из API
            'WIN_RATE': 0,  # Позже рассчитаем
            'KD': 0.0,  # Позже рассчитаем (в шаблоне KD, не KD_RATIO)
            'AVG': 0  # Позже получим из API (в шаблоне AVG, не AVG_ACS)
        })
        
        # Рендерим HTML с данными
        html_content = template.render(**template_data)
        
        # Создаем временный HTML файл
        temp_html_path = os.path.join(project_root, 'temp_profile_card.html')
        with open(temp_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Настройки для конвертации в изображение
        options = {
            'width': '800',
            'height': '600',
            'quality': '100',  # Максимальное качество
            'enable-local-file-access': '',  # Разрешаем доступ к локальным файлам
            'allow': [project_root],  # Разрешаем доступ ко всему проекту
            'no-stop-slow-scripts': '',  # Не останавливаем медленные скрипты
        }
        
        # Конвертируем HTML в изображение PNG
        img_bytes = imgkit.from_file(
            temp_html_path,
            False,  # Не сохраняем в файл, возвращаем байты
            options=options
        )
        
        # Удаляем временный файл
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        
        return img_bytes
        
    except Exception as e:
        print(f"Ошибка генерации карточки: {e}")
        # Удаляем временный файл в случае ошибки
        temp_html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_profile_card.html')
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        raise

# Тестовая функция (для отладки)
def test_generate_card():
    """
    Тестовая функция для проверки генерации карточки
    """
    # Создаем тестовые данные (имитация объекта Player)
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