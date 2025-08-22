# ======================
# 怪物类
# ======================
from typing import Optional, List

from core.entity import Entity


class Monster(Entity):
    def __init__(self,
                 name: str = "",
                 gender:str = "",
                 race: str = "",
                 level: int = "",
                 exp_reward: int = 0,
                 item_reward: Optional[List[str]] = None):
        # 默认怪物属性比角色低一点
        super().__init__(name, gender=gender, race=race, level=level,
                         STR=8 + level, DEX=8 + level, CON=8 + level,
                         INT=5, WIS=5, CHA=5,
                         HP=15 + level * 5, MP=0,
                         AC=8 + level, Speed=20)
        self.exp_reward = exp_reward
        self.item_reward = item_reward or []

    # 怪物掉落
    def drop_loot(self):
        return {
            "exp": self.exp_reward,
            "items": self.item_reward
        }
