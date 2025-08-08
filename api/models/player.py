from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class CurrentRankData(BaseModel):
    currenttier: int
    currenttierpatched: str = Field(description="Current rank")
    ranking_in_tier: int = Field(description="Current mmr(0-100)")

class HighestRank(BaseModel):
    tier: int
    patched_tier: str = Field(..., description="Highest rank in episode")
    season: str = Field(description="Season highest rank")

class RankInfo(BaseModel):
    current_data: Optional[CurrentRankData] = None
    highest_rank: Optional[HighestRank] = None
    
    name: Optional[str] = None
    tag: Optional[str] = None
    error: Optional[str] = None

class PlayerCard(BaseModel):
    small: str
    large: str
    wide: str
    id: str

class Player(BaseModel):
    puuid: str
    region: str
    account_level: int = Field(..., description="Valorant account level")
    name: str = Field(..., description="Valorant account name")
    tag: str = Field(..., description="Valorant account tag")
    card: PlayerCard
    rank_info: Optional[RankInfo] = None
    
    def format_for_telegram(self) -> str:
        base_info = (
         f"👤 <b>{self.name}#{self.tag}</b>\n"
         f"🏆 Уровень: {self.account_level}\n"   
        )
        
        if self.rank_info:
            current_rank = self.rank_info.current_data.currenttierpatched
            rr = self.rank_info.current_data.ranking_in_tier
            peak_rank = self.rank_info.highest_rank.patched_tier
            rank_info = (
                f"\n🎯 Ранг: {current_rank}\n"
                f"⭐ RR {rr}\n"
                f"🏔️ Пиковый ранг: {peak_rank}"
            )
            base_info += rank_info
            
        return base_info