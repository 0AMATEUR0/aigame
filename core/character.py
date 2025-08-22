import random
from core.inventory.inventory import Inventory
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
# 公共实体类
# ======================
class Entity:
    def __init__(self, name: str, gender:str, race: str, level: int,
                 STR: int, DEX: int, CON: int,
                 INT: int, WIS: int, CHA: int,
                 HP: int, MP: int, AC: int, Speed: int):
        self.name = name
        self.gender = gender
        self.race = race
        self.level = level

        # 六维属性
        self.STR = STR
        self.DEX = DEX
        self.CON = CON
        self.INT = INT
        self.WIS = WIS
        self.CHA = CHA

        # 战斗属性
        self.MAX_HP = HP
        self.HP = HP
        self.MAX_MP = MP
        self.MP = MP
        self.AC = AC
        self.Speed = Speed
        self.Condition: List[str] = []  # 状态（中毒、眩晕等）

    def get_info(self):
        return {
            "name": self.name,
            "race": self.race,
            "level": self.level,
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
        }

    # TODO: 待修改
    def attack(self, target):
        """普通攻击，掷 d20 决定命中，伤害用骰子 + 力量"""
        roll_res = roll_detail("1d20")
        natural_roll = roll_res.rolls
        attack_roll = roll_res.total + self.agility  # total = d20点数
        crit = (natural_roll == 20)  # 暴击判定

        target_ac = 10 + (target.agility - 10) // 2  # 基础AC
        if target.equipment["armor"]:  # 如果目标有护甲
            target_ac += target.equipment["armor"].armor_class

        print(f"{self.name} 掷命中骰子: d20={natural_roll} + 敏捷修正({self.agility}) → {attack_roll} vs AC {target_ac}")

        if attack_roll >= target_ac or crit:
            # 伤害骰子
            if self.equipment["weapon"]:
                damage = self.equipment["weapon"].get_damage(self.strength, crit=crit)
            else:
                dmg_res = roll_detail("1d4", crit=crit)
                damage = dmg_res["total"] + self.strength
                print(f"{self.name} 徒手攻击伤害: {dmg_res['rolls']} + 力量({self.strength}) → {damage}")

            target.take_damage(damage, source=self)

            if crit:
                print(f"✨ 暴击！{self.name} 重创了 {target.name}！")
            print(f"💥 {self.name} 命中 {target.name}，造成 {damage} 点伤害！（{target.hp}/{target.max_hp} HP）")
        else:
            print(f"❌ {self.name} 攻击未命中 {target.name}！")

    # 承受伤害
    def take_damage(self, amount: int):
        self.HP = max(self.HP - amount, 0)

    # 治疗
    def heal(self, amount: int):
        self.HP = min(self.HP + amount, self.MAX_HP)

    # 治疗
    def is_alive(self) -> bool:
        return self.HP > 0

# ======================
# 玩家类
# ======================
class Character(Entity):
    def __init__(self, name: str , gender: str, race: str, background: str, occupation: str, deputy_occupation: Optional[str] = None):
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
        self.equipment = {}     # {slot: Item}
        self.skills = []        # [Skill]
        self.inventory = []     # [Item]

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
            "equipment": {slot: item.name if item else None for slot, item in self.equipment.items()},
            "skills": [skill.get_info() for skill in self.skills],
            "inventory": self.inventory.get_info(),
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
        print(f"{self.name} 升级到 {self.level} 级！")

    def allocate_points(self, attr: str, points: int):
        if self.attribute_points >= points:
            setattr(self, attr, getattr(self, attr) + points)
            self.attribute_points -= points
        else:
            print("点数不足！")
    # 背包与物品
    def add_item(self, item):
        self.inventory.append(item)

    def use_item(self, item):
        if item in self.inventory:
            # TODO:这里调用 item.use(self) 之类的方法
            print(f"{self.name} 使用了 {item}")
            self.inventory.remove(item)

    # TODO:装备/卸下
    def equip(self, slot: str, equipment):
        equipment.equip_to(self)

    def unequip(self, slot: str):
        if slot in self.equipment:
            self.equipment[slot].unequip_from(self)


# ======================
# 怪物类
# ======================
class Monster(Entity):
    def __init__(self, name: str, race: str, level: int, exp_reward: int, item_reward: Optional[List[str]] = None):
        # 默认怪物属性比角色低一点
        super().__init__(name, race, level,
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
