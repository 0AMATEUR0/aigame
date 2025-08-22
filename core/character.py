from core.Item.item import EquipmentSlot, Equipment
from core.Inventory.inventory import Inventory
from core.entity import Entity
from utils.dice import roll_detail
from typing import Optional, List, Dict

# ----------------------
# 固定经验需求表
# ----------------------
EXP_TABLE = {
    1: 100, 2: 200, 3: 400, 4: 800, 5: 1200, 6: 1800,
    7: 2500, 8: 3500, 9: 5000, 10: 6500, 11: 8000, 12: None
}



# ======================
# 玩家类
# ======================
class Character(Entity):
    def __init__(self,
                 name: str = "",
                 gender: str = "",
                 race: str = "",
                 background: str = "",
                 occupation: str = "",
                 deputy_occupation: Optional[str] = None):
        # 初始属性可以自定义，示例给定默认值
        super().__init__(name, gender, race, level=1,
                         STR=10, DEX=10, CON=10,
                         INT=10, WIS=10, CHA=10,
                         HP=20, MP=10, AC=10, Speed=30)

        # 角色特有属性
        self.background = background
        self.occupation = occupation
        self.deputy_occupation = deputy_occupation

        # 进阶系统
        self.experience = 0
        self.currency = 0
        self.attribute_points = 0

        # TODO:装备、技能、背包占位
        self.skills = []        # [Skill]
        self.inventory = Inventory()

    def get_info(self):
        return {
            "name": self.name,
            "gender": self.gender,
            "race": self.race,
            "background": self.background,
            "occupation": self.occupation,
            "deputy_occupation": self.deputy_occupation,
            "level": self.level,
            "experience": self.experience,
            "hp": self.HP,
            "max_hp": self.MAX_HP,
            "mp": self.MP,
            "max_mp": self.MAX_MP,
            "Strength": self.STR,
            "Dexterity": self.DEX,
            "Constitution": self.CON,
            "Intelligence": self.INT,
            "Wisdom": self.WIS,
            "Charisma": self.CHA,
            "AC": self.AC,
            "Speed": self.Speed,
            "Condition": self.Condition if self.Condition else ["正常"],
            "attribute_points": self.attribute_points,
            # TODO: 装备、技能、背包信息
            "Item": {slot: item.name if item else None for slot, item in self.equipment.items()},
            "skills": [skill.get_info() for skill in self.skills],
            "Inventory": self.inventory.get_info(),
        }

    def learn_skill(self, skill):
        self.skills.append(skill)

    # 升级逻辑
    def gain_experience(self, amount: int):
        self.experience += amount
        while EXP_TABLE.get(self.level) and self.experience >= EXP_TABLE[self.level]:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.attribute_points += 2  # 示例：每级送 2 点属性
        self.MAX_HP += 5
        self.HP = self.MAX_HP
        # TODO: 职业特性提升
        print(f"{self.name} 升级到 {self.level} 级！")

    def allocate_points(self, attr: str, points: int):
        ATTR_MAP = {
            "Strength": "STR",
            "Dexterity": "DEX",
            "Constitution": "CON",
            "Intelligence": "INT",
            "Wisdom": "WIS",
            "Charisma": "CHA",
        }
        if self.attribute_points >= points:
            real_attr = ATTR_MAP.get(attr, attr)
            setattr(self, real_attr, getattr(self, real_attr) + points)
            self.attribute_points -= points
        else:
            print("点数不足！")
    # 背包与物品
    def add_item(self, item):
        self.inventory.add(item)

    def use_item(self, item):
        if item in self.inventory:
            # TODO:这里调用 item.use(self) 之类的方法
            item.use(self)
            print(f"{self.name} 使用了 {item}")
            self.inventory.remove(item)

    # TODO:装备/卸下
    def equip(self, equipment:Equipment):
        equipment.equip_to(self)

    def unequip(self, slot: EquipmentSlot):
        if slot in self.equipment and self.equipment.get(slot):
            item = self.equipment.get(slot)
            item.unequip_from(self)
            print(f"{self.name} 卸下了 {item.name}")
        else:
            print(f"{self.name} 没有装备在 {slot} 槽位的物品")


