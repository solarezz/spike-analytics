from typing import Optional, Tuple
from enum import Enum

class APIError:
    PLAYER_NOT_FOUND = "player_not_found"
    API_UNAVAILABLE = "api_unavailable"
    RATE_LIMITED = "rate_limited"
    IVALID_REGION = "invalid_region"
    TIMEOUT = "timeout"
    
def validate_riot_id(riot_id: str) -> Optional[Tuple[str, str]]:
    if not riot_id or '#' not in riot_id:
        return None
    
    parts = riot_id.split("#")
    if len(parts) != 2:
        return None
    
    name, tag = parts[0].strip(), parts[1].strip()
    
    if not name or len(name) < 3 or len(name) > 16:
        return None
    if not tag or len(tag) < 3 or len(tag) > 5:
        return None
    
    if any(char in name for char in ['<', '>', '"', '|', '\\', '/', ':']):
        return None
    
    return name, tag

def get_error_message(error_type: APIError) -> str:
    messages = {
        APIError.PLAYER_NOT_FOUND: "❌ Игрок не найден. Проверьте правильность имени и тега.",
        APIError.API_UNAVAILABLE: "⚠️ API Valorant временно недоступен. Попробуйте позже.",
        APIError.RATE_LIMITED: "⏳ Слишком много запросов. Попробуйте через минуту.",
        APIError.IVALID_REGION: "🌍 Неподдерживаемый регион игрока.",
        APIError.TIMEOUT: "⏱️ Запрос занял слишком много времени. Попробуйте еще раз."
    }
    return messages.get(error_type, "❌ Произошла неизвестная ошибка.")