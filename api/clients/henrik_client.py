import requests
from typing import Optional, Dict, Any
from api.models.player import Player, RankInfo


class HenrikAPIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.henrikdev.xyz/valorant/"):
        self.base_url = base_url
        self.api_key = api_key
        
    def _make_requests(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": self.api_key,"Accept":"*/*"}
        
        try: 
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request: {e}")
            return None
        
    def get_player_stats(self, name: str, tag: str) -> Optional[Player]:
        endpoint = f"v1/account/{name}/{tag}"
        response = self._make_requests(endpoint)
        if response and response.get('status') == 200:
            return Player(**response['data'])
        return None
    
    def get_matchlist(self, name: str, tag: str, region: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v3/matches/{region}/{name}/{tag}"
        return self._make_requests(endpoint)
    
    def get_match(self, matchid: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v2/match/{matchid}"
        return self._make_requests(endpoint)
    
    def get_mmr_history(self, region: str, name: str, tag: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v1/mmr-history/{region}/{name}/{tag}"
        return self._make_requests(endpoint)
    
    def get_mmr(self, region: str, puuid: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v2/by-puuid/mmr/{region}/{puuid}"
        return self._make_requests(endpoint)
    
    def get_full_player_info(self, name: str, tag: str) -> Optional[Player]:
        player = self.get_player_stats(name, tag)
        if not player:
            return None
        
        mmr_response = self._make_requests(f"v2/by-puuid/mmr/{player.region}/{player.puuid}")
        
        if mmr_response and mmr_response.get("status") == 200:
            if "error" not in mmr_response.get('data', {}):
                try:        
                    rank_info = RankInfo(**mmr_response['data'])
                    player_data = player.model_dump()
                    player_data['rank_info'] = rank_info
                    return Player(**player_data)
                except Exception as e:
                    print(f"Ошибка создания RankInfo: {e}")
                    return player
        return player