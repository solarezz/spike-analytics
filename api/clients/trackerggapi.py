import httpx
import asyncio
from typing import Dict, List, Optional, Any
import json
import cloudscraper
import time
import random
import urllib.parse

class TrackerGGAPI:
    """Интеграция с Tracker.gg API для получения расширенной статистики"""
    
    BASE_URL = "https://api.tracker.gg/api/v2/valorant/standard"
    
    def __init__(self):
        # Обычный httpx клиент
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
                "Accept": "application/json",
            },
            timeout=30.0
        )
        
        # CloudScraper для обхода Cloudflare
        self.cloud_scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'android',
                'mobile': True
            }
        )
        
        # Настройки CloudScraper
        self.cloud_scraper.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "DNT": "1",
            "Origin": "https://tracker.gg",
            "Pragma": "no-cache",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
    
    async def get_enhanced_player_stats(self, riot_id: str, tagline: str) -> Optional[Dict]:
        """Получить обработанную статистику игрока для карточки"""
        
        raw_data = await self.get_player_profile(riot_id, tagline)
        if not raw_data or 'data' not in raw_data:
            return None
            
        segments = raw_data['data'].get('segments', [])
        if not segments:
            return None
            
        # Ищем текущий сезонный сегмент competitive
        current_season = None
        peak_rating = None
        all_agents = []  # Собираем всех агентов для поиска самого играемого
        
        for segment in segments:
            seg_type = segment.get('type', '')
            attributes = segment.get('attributes', {})
            
            # Текущий сезон competitive
            if seg_type == 'season' and attributes.get('playlist') == 'competitive':
                if current_season is None:  # Берем первый (обычно текущий)
                    current_season = segment
                    
            # Пиковый рейтинг
            elif seg_type == 'peak-rating' and attributes.get('playlist') == 'competitive':
                peak_rating = segment
                
            # Собираем всех агентов для поиска самого играемого
            elif seg_type == 'agent' and attributes.get('playlist') == 'competitive':
                all_agents.append(segment)
        
        if not current_season:
            print("❌ Не найден current_season сегмент")
            print(f"🔍 Доступные сегменты: {[s.get('type') for s in segments]}")
            # Возвращаем базовую структуру с минимальными данными
            return {
                'riot_id': riot_id,
                'tagline': tagline,
                'region': 'N/A',
                'account_level': 'N/A',
                'current_rank': 'Unranked',
                'matches_played': 0,
                'matches_won': 0,
                'win_rate': 0,
                'kills': 0,
                'deaths': 0,
                'assists': 0,
                'kd_ratio': 0,
                'damage_per_round': 0,
                'headshot_pct': 0,
                'favorite_agent': 'Unknown'
            }
            
        # Находим агента с наибольшим количеством матчей
        favorite_agent = None
        max_matches = 0
        
        for agent_segment in all_agents:
            agent_stats = agent_segment.get('stats', {})
            if 'matchesPlayed' in agent_stats:
                matches_played = agent_stats['matchesPlayed'].get('value', 0)
                if isinstance(matches_played, (int, float)) and matches_played > max_matches:
                    max_matches = matches_played
                    favorite_agent = agent_segment
        
        # Извлекаем основную статистику
        stats = current_season.get('stats', {})
        
        def get_stat_value(stat_name: str, default=None):
            """Получить значение статистики"""
            if stat_name in stats:
                stat_info = stats[stat_name]
                return stat_info.get('displayValue', stat_info.get('value', default))
            return default
            
        def get_rank_info(stat_name: str):
            """Получить информацию о ранге с metadata"""
            if stat_name in stats:
                rank_info = stats[stat_name]
                metadata = rank_info.get('metadata', {})
                tier_name = metadata.get('tierName')
                
                if tier_name:
                    return tier_name
                # Fallback на displayValue или value
                display_value = rank_info.get('displayValue')
                if display_value and display_value != "Unranked":
                    return display_value
                return rank_info.get('value')
            return None
        
        # Формируем результат
        result = {
            # Основная информация
            'riot_id': riot_id,
            'tagline': tagline,
            'region': raw_data['data'].get('metadata', {}).get('activeShard', 'N/A'),  # Добавляем регион из metadata
            'account_level': raw_data['data'].get('metadata', {}).get('accountLevel', 'N/A'),  # Добавляем уровень из metadata
            
            # Статистика матчей
            'matches_played': get_stat_value('matchesPlayed', 0),
            'matches_won': get_stat_value('matchesWon', 0),
            'matches_lost': get_stat_value('matchesLost', 0),
            'win_rate': get_stat_value('matchesWinPct', 0),
            
            # Статистика киллов/смертей
            'kills': get_stat_value('kills', 0),
            'deaths': get_stat_value('deaths', 0),
            'assists': get_stat_value('assists', 0),
            'kd_ratio': get_stat_value('kDRatio', 0),
            'damage_per_round': get_stat_value('damagePerRound', 0),
            'headshot_pct': get_stat_value('headshotPct', 0),
            
            # Рейтинг
            'current_rank': get_rank_info('rank'),
            'current_rr': get_stat_value('rr', 0),
            'peak_rank': None,
            'peak_rr': None,
            
            # Время игры  
            'time_played': get_stat_value('timePlayed'),
            'matches_duration': get_stat_value('matchesDuration'),
            
            # Достижения
            'mvps': get_stat_value('mVPs', 0),
            'match_mvps': get_stat_value('matchMvps', 0),
            'team_mvps': get_stat_value('teamMVPs', 0),
            
            # Агент
            'favorite_agent': None,
            'favorite_agent_role': None,
            'agent_matches': 0,
        }
        
        # Добавляем пиковый рейтинг
        if peak_rating:
            peak_stats = peak_rating.get('stats', {})
            if 'peakRating' in peak_stats:
                peak_info = peak_stats['peakRating']
                result['peak_rank'] = peak_info.get('metadata', {}).get('tierName')
                result['peak_rr'] = peak_info.get('value', 0)
        
        # Добавляем информацию о любимом агенте
        if favorite_agent:
            agent_stats = favorite_agent.get('stats', {})
            agent_attrs = favorite_agent.get('attributes', {})
            agent_id = agent_attrs.get('key')
            
            try:
                from ..models.agents import get_agent_name, get_agent_role
                agent_name = get_agent_name(agent_id) if agent_id else "Unknown"
                agent_role = get_agent_role(agent_id) if agent_id else "Unknown"
            except ImportError as e:
                print(f"❌ Ошибка импорта: {e}")
                agent_name = "Unknown"
                agent_role = "Unknown"
            except Exception as e:
                print(f"❌ Ошибка получения имени агента: {e}")
                agent_name = agent_attrs.get('name', 'Unknown')  # Fallback на имя из атрибутов
                agent_role = "Unknown"
            
            matches_played = agent_stats.get('matchesPlayed', {}).get('displayValue', 0) if agent_stats else 0
            
            result['favorite_agent'] = agent_name
            result['favorite_agent_role'] = agent_role
            result['agent_matches'] = matches_played
            
            print(f"🎭 Любимый агент: {agent_name} ({matches_played} матчей)")
        else:
            print("🎭 Любимый агент не найден")
        
        return result

    async def get_player_profile(self, riot_id: str, tagline: str) -> Optional[Dict]:
        """Получить полную статистику игрока через CloudScraper"""
        
        print(f"🌩️ Попытка получения через CloudScraper: {riot_id}#{tagline}")
        
        # Сначала пробуем обычный httpx
        httpx_result = await self._try_httpx(riot_id, tagline)
        if httpx_result:
            print("✅ Успех через обычный httpx!")
            return httpx_result
        
        # Если httpx не работает, пробуем CloudScraper
        print("🔄 Переключение на CloudScraper...")
        cloudscraper_result = await self._try_cloudscraper(riot_id, tagline)
        if cloudscraper_result:
            print("✅ Успех через CloudScraper!")
            return cloudscraper_result
        
        print("❌ Все методы не удались")
        return None
    
    async def _try_httpx(self, riot_id: str, tagline: str) -> Optional[Dict]:
        """Попытка через обычный httpx"""
        try:
            # URL-кодируем riot_id и tagline для поддержки кириллицы
            encoded_riot_id = urllib.parse.quote(riot_id, safe='')
            encoded_tagline = urllib.parse.quote(tagline, safe='')
            url = f"{self.BASE_URL}/profile/riot/{encoded_riot_id}%23{encoded_tagline}"
            print(f"📡 httpx запрос: {url}")
            
            response = await self.client.get(url)
            print(f"📊 httpx ответ: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ httpx ошибка: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"💥 httpx исключение: {e}")
            return None
    
    async def _try_cloudscraper(self, riot_id: str, tagline: str) -> Optional[Dict]:
        """Попытка через CloudScraper в отдельном потоке"""
        import threading
        import asyncio
        
        def cloudscraper_sync(riot_id: str, tagline: str) -> Optional[Dict]:
            """Синхронная функция для CloudScraper"""
            try:
                # URL-кодируем для поддержки кириллицы
                encoded_riot_id = urllib.parse.quote(riot_id, safe='')
                encoded_tagline = urllib.parse.quote(tagline, safe='')
                
                # Сначала посещаем главную страницу для получения cookies
                main_url = f"https://tracker.gg/valorant/profile/riot/{encoded_riot_id}%23{encoded_tagline}/overview"
                print(f"🌐 CloudScraper: посещение главной страницы")
                
                main_response = self.cloud_scraper.get(main_url)
                print(f"📄 CloudScraper главная страница: {main_response.status_code}")
                
                if main_response.status_code != 200:
                    print(f"❌ Не удалось загрузить главную страницу: {main_response.status_code}")
                    return None
                
                # Небольшая задержка как настоящий пользователь
                time.sleep(random.uniform(1, 3))
                
                # Обновляем заголовки для API запроса
                self.cloud_scraper.headers.update({
                    "Referer": main_url,
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Encoding": "gzip, deflate, br"  # Важно для правильной декомпрессии
                })
                
                # Теперь API запрос
                api_url = f"{self.BASE_URL}/profile/riot/{encoded_riot_id}%23{encoded_tagline}"
                print(f"🔗 CloudScraper API: {api_url}")
                
                api_response = self.cloud_scraper.get(api_url)
                print(f"📡 CloudScraper API ответ: {api_response.status_code}")
                print(f"📋 Content-Type: {api_response.headers.get('content-type', 'unknown')}")
                print(f"🔧 Content-Encoding: {api_response.headers.get('content-encoding', 'none')}")
                print(f"📦 Content-Length: {api_response.headers.get('content-length', 'unknown')}")
                
                if api_response.status_code == 200:
                    try:
                        # Проверяем, что содержимое действительно JSON
                        content_type = api_response.headers.get('content-type', '').lower()
                        
                        if 'application/json' in content_type:
                            print("✅ Контент определен как JSON")
                            
                            # Пробуем несколько способов декодирования
                            try:
                                # Способ 1: Стандартный .json()
                                data = api_response.json()
                                print("✅ CloudScraper JSON декодирован (метод 1)")
                                return data
                            except:
                                print("❌ Метод 1 не сработал, пробуем метод 2")
                                
                                try:
                                    # Способ 2: Ручное декодирование
                                    import json
                                    text_content = api_response.text
                                    print(f"📄 Длина текста: {len(text_content)} символов")
                                    print(f"📄 Первые 100 символов: {repr(text_content[:100])}")
                                    
                                    if text_content.strip():
                                        data = json.loads(text_content)
                                        print("✅ CloudScraper JSON декодирован (метод 2)")
                                        return data
                                    else:
                                        print("❌ Пустой ответ")
                                        
                                except Exception as e2:
                                    print(f"❌ Метод 2 не сработал: {e2}")
                                    
                                    try:
                                        # Способ 3: Работа с сырыми байтами
                                        raw_content = api_response.content
                                        print(f"📦 Сырой контент: {len(raw_content)} байт")
                                        print(f"📦 Первые 50 байт: {raw_content[:50]}")
                                        
                                        # Пробуем декомпрессию
                                        import gzip
                                        import brotli
                                        
                                        encoding = api_response.headers.get('content-encoding', '').lower()
                                        
                                        if encoding == 'gzip':
                                            print("🔧 Пробуем gzip декомпрессию")
                                            decompressed = gzip.decompress(raw_content)
                                            data = json.loads(decompressed.decode('utf-8'))
                                            print("✅ CloudScraper JSON декодирован (gzip)")
                                            return data
                                        elif encoding == 'br':
                                            print("🔧 Пробуем brotli декомпрессию")
                                            decompressed = brotli.decompress(raw_content)
                                            data = json.loads(decompressed.decode('utf-8'))
                                            print("✅ CloudScraper JSON декодирован (brotli)")
                                            return data
                                        else:
                                            print("🔧 Пробуем без декомпрессии")
                                            data = json.loads(raw_content.decode('utf-8'))
                                            print("✅ CloudScraper JSON декодирован (raw)")
                                            return data
                                            
                                    except Exception as e3:
                                        print(f"❌ Метод 3 не сработал: {e3}")
                                        print(f"📄 Первые 200 байт как текст: {repr(raw_content[:200])}")
                        else:
                            print(f"❌ Неожиданный content-type: {content_type}")
                            print(f"📄 Первые 200 символов: {api_response.text[:200]}")
                            
                        return None
                        
                    except Exception as e:
                        print(f"❌ Общая ошибка декодирования: {e}")
                        return None
                else:
                    print(f"❌ CloudScraper API ошибка: {api_response.status_code}")
                    
                    # Выводим заголовки ответа для диагностики
                    print("📋 Заголовки ответа:")
                    for key, value in api_response.headers.items():
                        if key.lower() in ['cf-ray', 'server', 'cf-cache-status', 'content-type', 'content-encoding']:
                            print(f"   {key}: {value}")
                    
                    print(f"📄 Ответ: {api_response.text[:300]}")
                    return None
                    
            except Exception as e:
                print(f"💥 CloudScraper исключение: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        # Запускаем CloudScraper в отдельном потоке
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cloudscraper_sync, riot_id, tagline)
    
    def extract_current_season_stats(self, profile_data: Dict, current_rank: str = None) -> Dict:
        """Извлечь статистику текущего сезона"""
        if not profile_data or 'data' not in profile_data:
            return {}
            
        segments = profile_data['data'].get('segments', [])
        current_season = None
        rank_segment = None
        
        print(f"🔍 extract_current_season_stats: найдено {len(segments)} сегментов")
        
        # Найти сегмент текущего сезона и сегмент с рангом
        for i, segment in enumerate(segments):
            segment_type = segment.get('type')
            metadata = segment.get('metadata', {})
            
            print(f"🔍 Сегмент {i}: type={segment_type}, metadata_keys={list(metadata.keys())}")
            
            if segment_type == 'season' and segment.get('attributes', {}).get('playlist') == 'competitive':
                current_season = segment
                print(f"🔍 Найден current_season (season)")
            
            # Ищем ЛЮБОЙ сегмент с рангом (не только season)
            if 'tierName' in metadata and not rank_segment:
                rank_segment = segment
                print(f"🔍 Найден rank_segment типа {segment_type} с tierName: {metadata.get('tierName')}")
                
        # Если не нашли season сегмент, попробуем overview
        if not current_season:
            for segment in segments:
                if segment.get('type') == 'overview':
                    current_season = segment
                    print(f"🔍 Используем overview сегмент как current_season")
                    break
        
        if not current_season:
            print("❌ Не найден сегмент текущего сезона для extract_current_season_stats")
            return {}
            
        stats = current_season.get('stats', {})
        metadata = current_season.get('metadata', {})
        
        print(f"🔍 extract_current_season_stats metadata: {metadata}")
        
        # Получаем ранг из разных источников
        rank = None
        
        # Если ранг передан как параметр (из get_enhanced_player_stats), используем его
        if current_rank:
            rank = current_rank
            print(f"🔍 Ранг получен как параметр: {rank}")
        
        # Если есть отдельный сегмент с рангом, используем его
        elif rank_segment:
            rank_metadata = rank_segment.get('metadata', {})
            if 'tierName' in rank_metadata:
                rank = rank_metadata['tierName']
                print(f"🔍 Ранг из rank_segment.metadata.tierName: {rank}")
        
        # Если не нашли в отдельном сегменте, пробуем текущий сегмент
        elif not rank:
            # Сначала пробуем metadata.tierName
            if 'tierName' in metadata:
                rank = metadata['tierName']
                print(f"🔍 Ранг из current_season.metadata.tierName: {rank}")
            # Потом пробуем stats.rank
            elif 'rank' in stats:
                rank_stat = stats['rank']
                if isinstance(rank_stat, dict):
                    rank = rank_stat.get('displayValue') or rank_stat.get('value')
                else:
                    rank = str(rank_stat)
                print(f"🔍 Ранг из stats.rank: {rank}")
        
        if not rank or rank == "Unranked":
            rank = "Не определен"
            
        print(f"🔍 Финальный ранг в extract_current_season_stats: {rank}")
            
        result = {
            'season_name': metadata.get('name', ''),
            'matches_played': self._get_stat_value(stats, 'matchesPlayed'),
            'matches_won': self._get_stat_value(stats, 'matchesWon'),
            'win_rate': self._get_stat_value(stats, 'matchesWinPct'),
            'kd_ratio': self._get_stat_value(stats, 'kDRatio'),
            'average_score': self._get_stat_value(stats, 'scorePerMatch'),
            'headshot_percentage': self._get_stat_value(stats, 'headshotsPercentage'),
            'clutches_won': self._get_stat_value(stats, 'clutches'),
            'clutch_percentage': self._get_stat_value(stats, 'clutchesPercentage'),
            'aces': self._get_stat_value(stats, 'aces'),
            'rank': rank,  # Добавляем ранг
            'attack_kd': self._get_stat_value(stats, 'attackKDRatio'),
            'defense_kd': self._get_stat_value(stats, 'defenseKDRatio'),
            'econ_rating': self._get_stat_value(stats, 'econRating')
        }
        
        print(f"🔍 extract_current_season_stats результат: rank={result['rank']}")
        return result
    
    def extract_agent_stats(self, profile_data: Dict) -> List[Dict]:
        """Извлечь статистику по агентам"""
        if not profile_data or 'data' not in profile_data:
            return []
            
        segments = profile_data['data'].get('segments', [])
        agents = []
        
        for segment in segments:
            if segment.get('type') == 'agent':
                metadata = segment.get('metadata', {})
                stats = segment.get('stats', {})
                
                agent_data = {
                    'name': metadata.get('name', ''),
                    'role': metadata.get('role', ''),
                    'color': metadata.get('color', ''),
                    'image_url': metadata.get('imageUrl', ''),
                    'matches_played': self._get_stat_value(stats, 'matchesPlayed'),
                    'win_rate': self._get_stat_value(stats, 'matchesWinPct'),
                    'kd_ratio': self._get_stat_value(stats, 'kDRatio'),
                    'average_score': self._get_stat_value(stats, 'scorePerMatch'),
                    'headshot_percentage': self._get_stat_value(stats, 'headshotsPercentage'),
                    'ability1_kills': self._get_stat_value(stats, 'ability1Kills'),
                    'ability2_kills': self._get_stat_value(stats, 'ability2Kills'),
                    'ultimate_kills': self._get_stat_value(stats, 'ultimateKills')
                }
                agents.append(agent_data)
        
        # Сортировать по количеству игр
        return sorted(agents, key=lambda x: x['matches_played'] or 0, reverse=True)
    
    def extract_clutch_stats(self, profile_data: Dict) -> Dict:
        """Извлечь детальную клатч статистику"""
        if not profile_data or 'data' not in profile_data:
            return {}
            
        segments = profile_data['data'].get('segments', [])
        season_segment = None
        
        for segment in segments:
            if segment.get('type') == 'season':
                season_segment = segment
                break
                
        if not season_segment:
            return {}
            
        stats = season_segment.get('stats', {})
        
        return {
            'total_clutches': self._get_stat_value(stats, 'clutches'),
            'clutch_percentage': self._get_stat_value(stats, 'clutchesPercentage'),
            'clutches_1v1': self._get_stat_value(stats, 'clutches1v1'),
            'clutches_1v2': self._get_stat_value(stats, 'clutches1v2'),
            'clutches_1v3': self._get_stat_value(stats, 'clutches1v3'),
            'clutches_1v4': self._get_stat_value(stats, 'clutches1v4'),
            'clutches_1v5': self._get_stat_value(stats, 'clutches1v5'),
            'clutches_lost': self._get_stat_value(stats, 'clutchesLost'),
            'clutches_lost_1v1': self._get_stat_value(stats, 'clutchesLost1v1'),
            'clutches_lost_1v2': self._get_stat_value(stats, 'clutchesLost1v2'),
            'clutches_lost_1v3': self._get_stat_value(stats, 'clutchesLost1v3'),
            'clutches_lost_1v4': self._get_stat_value(stats, 'clutchesLost4'),
            'clutches_lost_1v5': self._get_stat_value(stats, 'clutchesLost1v5')
        }
    
    def get_player_summary(self, profile_data: Dict) -> Dict:
        """Создать краткую сводку игрока"""
        if not profile_data or 'data' not in profile_data:
            return {}
            
        data = profile_data['data']
        platform_info = data.get('platformInfo', {})
        user_info = data.get('userInfo', {})
        metadata = data.get('metadata', {})
        
        # Получить ранг из того же места что и в get_enhanced_player_stats
        current_rank = None
        segments = data.get('segments', [])
        
        for segment in segments:
            if segment.get('type') == 'season' and segment.get('attributes', {}).get('playlist') == 'competitive':
                stats = segment.get('stats', {})
                if 'rank' in stats:
                    rank_info = stats['rank']
                    metadata = rank_info.get('metadata', {})
                    tier_name = metadata.get('tierName')
                    if tier_name:
                        current_rank = tier_name
                        break
        
        # Получить основные статы
        current_stats = self.extract_current_season_stats(profile_data, current_rank)
        top_agents = self.extract_agent_stats(profile_data)[:3]  # Топ 3 агента
        clutch_stats = self.extract_clutch_stats(profile_data)
        
        return {
            'riot_id': platform_info.get('platformUserHandle', ''),
            'avatar_url': platform_info.get('avatarUrl', ''),
            'account_level': metadata.get('accountLevel', 0),
            'region': metadata.get('activeShard', ''),
            'profile_views': user_info.get('pageviews', 0),
            'badges_count': len(user_info.get('badges', [])),
            'current_season': current_stats,
            'top_agents': top_agents,
            'clutch_master': clutch_stats,
            'is_clutch_god': (clutch_stats.get('clutch_percentage', 0) or 0) > 50,
            'main_role': self._determine_main_role(top_agents),
            'play_style': self._analyze_play_style(current_stats, clutch_stats)
        }
    
    def _get_stat_value(self, stats: Dict, key: str, is_string: bool = False) -> Any:
        """Безопасно получить значение статистики"""
        if key not in stats:
            return None if is_string else 0
            
        stat = stats[key]
        if isinstance(stat, dict):
            return stat.get('value')
        return stat
    
    def _determine_main_role(self, agents: List[Dict]) -> str:
        """Определить основную роль игрока"""
        if not agents:
            return "Unknown"
            
        role_games = {}
        for agent in agents:
            role = agent.get('role', 'Unknown')
            games = agent.get('matches_played', 0)
            role_games[role] = role_games.get(role, 0) + games
            
        return max(role_games, key=role_games.get) if role_games else "Unknown"
    
    def _analyze_play_style(self, season_stats: Dict, clutch_stats: Dict) -> str:
        """Анализ стиля игры"""
        if not season_stats:
            return "Unknown"
            
        kd = season_stats.get('kd_ratio', 0) or 0
        clutch_rate = clutch_stats.get('clutch_percentage', 0) or 0
        headshot_pct = season_stats.get('headshot_percentage', 0) or 0
        
        if clutch_rate > 60:
            return "🔥 Clutch God"
        elif kd > 1.3 and headshot_pct > 25:
            return "🎯 Precision Killer"  
        elif kd > 1.1:
            return "⚔️ Aggressive Fragger"
        elif clutch_rate > 40:
            return "🧠 Clutch Player"
        elif headshot_pct > 30:
            return "🔫 Aim Master"
        else:
            return "🎮 Balanced Player"
    
    async def close(self):
        """Закрыть все клиенты"""
        await self.client.aclose()

# Тестирование с CloudScraper
async def test_cloudscraper():
    """Тест CloudScraper интеграции"""
    api = TrackerGGAPI()
    
    try:
        print("🧪 Тестирование TrackerGG с CloudScraper...")
        profile = await api.get_player_profile("porsche enjoyer", "ild")
        
        if profile:
            print("✅ Профиль получен успешно!")
            summary = api.get_player_summary(profile)
            print(f"📊 Игрок: {summary.get('riot_id', 'Unknown')}")
            print(f"🎮 Уровень: {summary.get('account_level', 0)}")
            print(f"🏆 Стиль: {summary.get('play_style', 'Unknown')}")
            
            # Показать детальную статистику
            current_season = summary.get('current_season', {})
            if current_season:
                print(f"\n📈 Статистика сезона:")
                print(f"   🎯 Матчей: {current_season.get('matches_played', 0)}")
                print(f"   🏆 Винрейт: {current_season.get('win_rate', 0):.1f}%")
                print(f"   ⚔️ K/D: {current_season.get('kd_ratio', 0):.2f}")
                print(f"   🎯 HS%: {current_season.get('headshot_percentage', 0):.1f}%")
                
            top_agents = summary.get('top_agents', [])
            if top_agents:
                print(f"\n👥 Топ агенты:")
                for i, agent in enumerate(top_agents, 1):
                    print(f"   {i}. {agent.get('name', 'Unknown')} ({agent.get('role', 'Unknown')})")
                    print(f"      🎮 Игр: {agent.get('matches_played', 0)} | 🏆 WR: {agent.get('win_rate', 0):.1f}% | ⚔️ K/D: {agent.get('kd_ratio', 0):.2f}")
        else:
            print("❌ Не удалось получить профиль")
            
    finally:
        await api.close()

if __name__ == "__main__":
    asyncio.run(test_cloudscraper())