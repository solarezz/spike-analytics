import aiohttp
import asyncio
from typing import Optional, Dict, Any
from bot.utils.validation import APIError
from api.models.player import Player, RankInfo


class HenrikAPIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.henrikdev.xyz/valorant/"):
        self.base_url = base_url
        self.api_key = api_key
        
    async def _make_requests(self, endpoint: str, params: Optional[Dict] = None) -> tuple[Optional[Dict[str, Any]], Optional[APIError]]:
        url = f"{self.base_url}{endpoint}"
        headers = {"Authorization": self.api_key,"Accept":"*/*"}
        
        try: 
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 404:
                        return None, APIError.PLAYER_NOT_FOUND
                    elif response.status == 429:
                        return None, APIError.RATE_LIMITED
                    elif response.status >= 500:
                        return None, APIError.API_UNAVAILABLE
                    
                    response.raise_for_status()
                    data = await response.json()
                    return data, None
        except asyncio.TimeoutError:
            return None, APIError.TIMEOUT
        except aiohttp.ClientError as e:
            print(f"Error making request: {e}")
            return None, APIError.API_UNAVAILABLE
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None, APIError.API_UNAVAILABLE
        
    async def get_player_stats(self, name: str, tag: str) -> Optional[Player]:
        endpoint = f"v1/account/{name}/{tag}"
        response = await self._make_requests(endpoint)
        if response and response.get('status') == 200:
            return Player(**response['data'])
        return None
    
    async def get_matchlist(self, name: str, tag: str, region: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v3/matches/{region}/{name}/{tag}"
        return await self._make_requests(endpoint)
    
    async def get_match(self, matchid: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v2/match/{matchid}"
        return await self._make_requests(endpoint)
    
    async def get_mmr_history(self, region: str, name: str, tag: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v1/mmr-history/{region}/{name}/{tag}"
        return await self._make_requests(endpoint)
    
    async def get_mmr(self, region: str, puuid: str) -> Optional[Dict[str, Any]]:
        endpoint = f"v2/by-puuid/mmr/{region}/{puuid}"
        return await self._make_requests(endpoint)
    
    async def get_full_player_info(self, name: str, tag: str) -> tuple[Optional[Player], Optional[APIError]]:
        player_data, error = await self._make_requests(f"v1/account/{name}/{tag}")
        if error:
            return None, error
        
        if not player_data or player_data.get('status') != 200:
            return None, APIError.PLAYER_NOT_FOUND
        
        try:
            player = Player(**player_data['data'])
        except Exception as e:
            print(f"Error creationg Player: {e}")
            return None, APIError.API_UNAVAILABLE
        
        mmr_data, mmr_error = await self._make_requests(f"v2/by-puuid/mmr/{player.region}/{player.puuid}")
        
        if mmr_error:
            return player, None
        
        if mmr_data or mmr_data.get('status') == 200 and "error" not in mmr_data.get('data', {}):
            try:
                rank_info = RankInfo(**mmr_data['data'])
                player_data = player.model_dump()
                player_data['rank_info'] = rank_info
                return Player(**player_data), None
            except Exception as e:
                print(f"Error creating RankInfo: {e}")
                return player, None
            
        return player, None