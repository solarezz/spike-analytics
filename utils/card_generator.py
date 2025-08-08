import os
import re
from jinja2 import Template
from html2image import Html2Image
from PIL import Image, ImageOps

def get_rank_image_path(rank_name, tier_level=None):
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

def generate_profile_card(player_data):
    try:
        project_root = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(project_root, 'templates', 'profile_card.html')
        static_dir = os.path.join(project_root, 'static')

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Шаблон не найден: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        template = Template(template_content)

        template_data = {
            'PLAYER_NAME': player_data.name,
            'PLAYER_TAG': player_data.tag,
            'REGION': player_data.region.upper() if player_data.region else "N/A",
            'LEVEL': player_data.account_level,
        }

        if player_data.rank_info and player_data.rank_info.current_data:
            current_rank = player_data.rank_info.current_data.currenttierpatched
            rr = player_data.rank_info.current_data.ranking_in_tier
            
            rank_name, tier_level = parse_rank_info(current_rank)
            
            template_data.update({
                'CURRENT_RANK': current_rank,
                'CURRENT_MMR': rr,
                'CURRENT_RANK_IMAGE': get_rank_image_path(rank_name, tier_level)
            })
        else:
            template_data.update({
                'CURRENT_RANK': "Unranked",
                'CURRENT_MMR': 0,
                'CURRENT_RANK_IMAGE': os.path.join(project_root, "static", "images", "ranks", "iron-1.png")
            })
        
        if player_data.rank_info and player_data.rank_info.highest_rank:
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

        template_data.update({
            'MATCHES': 0,
            'WINRATE': 0,
            'KD': 0.0,
            'AVG': 0
        })

        html_content = template.render(**template_data)

        name = sanitize_filename(player_data.name)

        temp_html_path = os.path.join(project_root, f'temp_{name}_{player_data.tag}.html')
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
        
        
        output_filename = f'{name}-{player_data.tag}.png'
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
        temp_html_path = os.path.join(project_root, 'temp_profile_card.html')
        screenshot_path = os.path.join(project_root, 'temp_card_screenshot.png')
        
        if os.path.exists(temp_html_path):
            os.remove(temp_html_path)
        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)
        raise

def test_generate_card():

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
    try:
        player = TestPlayer()
        img_bytes = generate_profile_card(player)

        with open("test_card.png", "wb") as f:
            f.write(img_bytes)
        
        print("Тестовая карточка сохранена как test_card.png")
        return True
    except Exception as e:
        print(f"Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    test_generate_card()
