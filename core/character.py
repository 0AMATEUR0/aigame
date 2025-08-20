import random
from core.equipment.Item import Consumable
from utils.dice import roll_detail, roll

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
    def __init__(self, name, level=1, max_hp=10, hp=None, max_mp=10, mp=None, strength=0, agility=0, intelligence=0, equipment=None):
        self.name = name
        self.level = level
        self.max_hp = max_hp
        self.hp = hp or max_hp
        self.max_mp = max_mp
        self.mp = mp if mp is not None else max_mp
        self.strength = strength
        self.agility = agility
        self.intelligence = intelligence
        self.equipment = equipment or {"weapon": None, "armor": None}

    def get_info(self):
        return {
            "name": self.name,
            "level": self.level,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "strength": self.strength,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "equipment": {slot: item.name if item else None for slot, item in self.equipment.items()}
        }

    # 战斗方法
    def attack(self, target):
        """普通攻击，掷 d20 决定命中，伤害用骰子 + 力量"""
        roll_res = roll_detail("1d20")
        natural_roll = roll_res["rolls"][0]
        attack_roll = roll_res["total"] + self.agility  # total = d20点数
        crit = (natural_roll == 20)  # 暴击判定

        target_ac = 10 + (target.agility - 10) // 2  # 基础AC
        if target.equipment["armor"]:  # 如果目标有护甲
            target_ac += target.equipment["armor"].defense_bonus

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

    def take_damage(self, amount, source=None):
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.on_death(source)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def is_alive(self):
        return self.hp > 0

    def on_death(self, killer=None):
        """可以被子类重写"""
        print(f"{self.name} 已经死亡！")

# ======================
# 玩家类
# ======================
class Character(Entity):
    def __init__(self, name= "", gender = "?", career="footman", background="", level=1,
                 experience=0, attribute_points=0,
                 max_hp=10, hp=10, max_mp=10, mp=10, strength=0, agility=0, intelligence=0,
                 inventory=None, skills=None):
        super().__init__(name, level, max_hp, hp, max_mp, mp, strength, agility, intelligence)
        self.gender = gender
        self.career = career
        self.background = background
        self.experience = experience
        self.attribute_points = attribute_points
        self.inventory = inventory or {}
        self.skills = skills or []

    def get_info(self):
        return {
            "name": self.name,
            "gender": self.gender,
            "career": self.career,
            "background": self.background,
            "experience": self.experience,
            "level": self.level,
            "attribute_points": self.attribute_points,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "strength": self.strength,
            "agility": self.agility,
            "intelligence": self.intelligence,
            "equipment": {slot: item.name if item else None for slot, item in self.equipment.items()},
            "inventory": {name: len(items) for name, items in self.inventory.items()},
            "skills": [skill.name for skill in self.skills],
        }

    def add_skill(self, skill):
        self.skills.append(skill)
        print(f"{self.name} 学会了技能：{skill.name}")

    # 升级逻辑
    def exp_to_next_level(self):
        return EXP_TABLE.get(self.level, 0)

    def gain_experience(self, exp):
        self.experience += exp
        print(f"{self.name} 获得 {exp} 经验！（当前 {self.experience} EXP）")
        while self.level < 12 and self.experience >= self.exp_to_next_level():
            self.experience -= self.exp_to_next_level()
            self.level_up()

    def level_up(self):
        self.level += 1
        self.attribute_points += 2
        print(f"{self.name} 升到了 {self.level} 级！获得 2 点属性点。")

    def allocate_points(self, attr, amount):
        if amount > self.attribute_points:
            print(f"点数不足！当前可用点数：{self.attribute_points}")
            return
        if attr == "strength":
            self.strength += amount
        elif attr == "agility":
            self.agility += amount
        elif attr == "intelligence":
            self.intelligence += amount
        else:
            print("无效属性！只能是 strength / agility / intelligence")
            return
        self.attribute_points -= amount
        print(f"{self.name} 分配了 {amount} 点到 {attr}，当前属性: 力量{self.strength}, 敏捷{self.agility}, 智力{self.intelligence}，剩余属性点 {self.attribute_points}。")

    # 背包与物品
    def add_item(self, item):
        if item.name not in self.inventory:
            self.inventory[item.name] = []
        self.inventory[item.name].append(item)
        print(f"{self.name} 获得了物品：{item.name}")

    def use_item(self, item_name):
        if item_name in self.inventory and self.inventory[item_name]:
            item = self.inventory[item_name][0]
            if isinstance(item, Consumable):
                item.use(self)
                self.inventory[item_name].pop(0)
                if not self.inventory[item_name]:  # 如果该物品用完，删除 key
                    del self.inventory[item_name]
                print(f"{self.name} 使用了 {item_name}")
            else:
                print(f"{item_name} 不能直接使用！")
                return
        print(f"没有找到可用物品：{item_name}")

    def list_inventory(self):
        if not self.inventory:
            print(f"{self.name} 的背包是空的。")
            return
        print(f"{self.name} 的背包：")
        for name, items in self.inventory.items():
            print(f"- {name} x{len(items)}")

    # 装备
    def equip(self, item):
        if not hasattr(item, "slot"):
            print(f"{item.name} 不是可装备物品！")
            return
        slot = item.slot
        if slot not in self.equipment:
            print(f"无效装备槽位：{slot}")
            return

        # 先从背包移除
        if item.name in self.inventory and item in self.inventory[item.name]:
            self.inventory[item.name].remove(item)
            if not self.inventory[item.name]:
                del self.inventory[item.name]

        # 卸下旧装备
        if self.equipment[slot]:
            old_item = self.equipment[slot]
            self.add_item(old_item)
            print(f"{self.name} 卸下了 {old_item.name}。")

        # 装备新物品
        self.equipment[slot] = item
        print(f"{self.name} 装备了 {item.name} 到 {slot}。")

    def unequip(self, slot):
        """卸下装备，回到背包"""
        if slot in self.equipment and self.equipment[slot]:
            item = self.equipment[slot]
            self.equipment[slot] = None
            self.add_item(item)
            print(f"{self.name} 卸下了 {item.name}。")
        else:
            print(f"{self.name} 没有装备在 {slot} 上。")

# ======================
# 怪物类
# ======================
class Monster(Entity):
    def __init__(self, name, level=1, max_hp=10, hp=None,
                 strength=0, agility=0, intelligence=0,
                 exp_reward=50, loot_table=None):
        super().__init__(name, level, max_hp, hp, max_mp=0, mp=0,
                         strength=strength, agility=agility, intelligence=intelligence)
        self.exp_reward = exp_reward
        self.loot_table = loot_table or []

    def on_death(self, killer=None):
        super().on_death(killer)
        if killer and isinstance(killer, Character) and self.exp_reward > 0:
            print(f"{killer.name} 击杀了 {self.name}，获得 {self.exp_reward} 经验！")
            killer.gain_experience(self.exp_reward)

        # 掉落物品
        if self.loot_table and killer:
            dropped_items = []
            for item, chance in self.loot_table:
                chance = max(0.0, min(chance, 1.0))  # 限制在 0~1
                roll_val = roll_detail("1d100")["total"]
                if chance >= 1.0 or roll_val <= chance * 100:
                    dropped_items.append(item)

            for it in dropped_items:
                killer.add_item(it)
                print(f"{self.name} 掉落了 {it.name}！")
