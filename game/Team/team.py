# === 队伍 ===
from typing import List

from game import Item
from game.Entity.character import Character
from game.Inventory.inventory import Inventory


class Team:
    def __init__(self, members: List[Character], start_pos=(0,0), vision: int = 3):
        self.members = members
        self.currency = 0
        self.inventory = Inventory()
        self.position = start_pos
        self.vision = vision # 视野广度

    def info(self):
        return {
            "members": [c.info() for c in self.members],
            "currency": self.currency,
            "x": self.x,
            "y": self.y,
            "vision": self.vision,
        }

    def is_alive(self) -> bool:
        """判断队伍是否还有存活成员"""
        return any(member.is_alive() for member in self.members)

    def gain_currency(self, currency: int):
        """取得货币"""
        self.currency += currency
        print(f"💰 队伍获得 {currency} 金币（总计 {self.currency}）")

    def gain_experience(self, experience: int):
        """取得经验"""
        for member in self.members:
            member.gain_experience(experience)
            print(f"{member.name} 获得了 {experience} 经验")

    def gain_item(self, item: Item):
        self.inventory.add(item)

    def move(self, dx, dy, game_map):
        x, y = self.position
        new_x, new_y = x + dx, y + dy
        if 0 <= new_x < game_map.width and 0 <= new_y < game_map.height:
            tile = game_map.grid[new_y][new_x]
            if tile.walkable:
                self.position = (new_x, new_y)
                print(f"移动到 {self.position}")
                if tile.event:
                    print("触发事件！")
                    tile.event.trigger(self)
            else:
                print("这里不能走。")
        else:
            print("超出地图边界。")