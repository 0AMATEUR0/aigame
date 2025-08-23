# ======================
# 公共实体类
# ======================
from typing import List

from game.Item.item import EquipmentSlot
from utils.dice import roll_detail


class Entity:
    def __init__(self,
                 name: str = "",
                 gender:str = "",
                 race: str = "",
                 level: int = 1,
                 STR: int = 10,
                 DEX: int = 10,
                 CON: int = 10,
                 INT: int = 10,
                 WIS: int = 10,
                 CHA: int = 10,
                 HP: int = 10,
                 MP: int = 10,
                 AC: int = 10,
                 Speed: int = 10):
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

        # TODO:装备槽位
        self.equipment = {slot: None for slot in EquipmentSlot}     # {slot: Item}

    def info(self):
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
        natural_roll = roll_res.rolls[0]
        attack_roll = roll_res.total + self.DEX  # total = d20点数
        crit = (natural_roll == 20)  # 暴击判定

        target_ac = 10 + (target.DEX - 10) // 2  # 基础AC
        if target.equipment[EquipmentSlot.ARMOR]:  # 如果目标有护甲
            target_ac += target.equipment[EquipmentSlot.ARMOR].armor_class

        print(f"{self.name} 掷命中骰子: d20={natural_roll} + 敏捷修正({self.DEX}) → {attack_roll} vs AC {target_ac}")

        if attack_roll >= target_ac or crit:
            # 伤害骰子
            if self.equipment.get(EquipmentSlot.WEAPON):
                damage = self.equipment.get(EquipmentSlot.WEAPON).get_damage(self.STR, crit=crit)

            else:
                dmg_res = roll_detail("1d4", crit=crit)
                damage = dmg_res.total + (self.STR - 10)//2
                print(f"{self.name} 徒手攻击伤害: {dmg_res.rolls} + 力量({(self.STR - 10)//2}) → {damage}")

            target.take_damage(damage)

            if crit:
                print(f"✨ 暴击！{self.name} 重创了 {target.name}！")
            print(f"💥 {self.name} 命中 {target.name}，造成 {damage} 点伤害！（{target.HP}/{target.MAX_HP} HP）")
        else:
            print(f"❌ {self.name} 攻击未命中 {target.name}！")

    # 承受伤害
    def take_damage(self, amount: int):
        self.HP = max(self.HP - amount, 0)

    # 治疗
    def heal(self, amount: int):
        self.HP = min(self.HP + amount, self.MAX_HP)

    # 是否存活
    def is_alive(self) -> bool:
        return self.HP > 0

    def get_AC(self):
        ac = 10 + (self.DEX - 10) // 2
        if self.equipment.get(EquipmentSlot.ARMOR):
            ac += self.equipment[EquipmentSlot.ARMOR].armor_class
        if self.equipment.get(EquipmentSlot.SHIELD):
            ac += self.equipment[EquipmentSlot.SHIELD].armor_class
        return ac

    def add_condition(self, condition: str):
        if condition not in self.Condition:
            self.Condition.append(condition)

    def remove_condition(self, condition: str):
        if condition in self.Condition:
            self.Condition.remove(condition)