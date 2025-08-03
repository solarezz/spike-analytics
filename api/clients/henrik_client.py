import requests
from typing import Optional, Dict, Any


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
        
    def get_player_stats(self, name: str, tag: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v1/account/{name}/{tag}"
        return self._make_requests(endpoint)
    
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