import random
from core.equipment.Item import Consumable
from utils.dice import roll

# ----------------------
# 固定经验需求表
# ----------------------
EXP_TABLE = {
    1: 100, 2: 200, 3: 400, 4: 800, 5: 1200, 6: 1800,
    7: 2500, 8: 3500, 9: 5000, 10: 6500, 11: 8000, 12: 0
}

# ======================
# 公共实体类
# ======================
class Entity:
    def __init__(self, name, level=1, max_hp=10, hp=None, strength=0, agility=0, intelligence=0):
        self.name = name
        self.level = level
        self.max_hp = max_hp
        self.hp = hp or max_hp
        self.strength = strength
        self.agility = agility
        self.intelligence = intelligence

    # 战斗方法
    def attack(self, target):
        attack_roll = random.randint(1, 20) + self.agility
        target_ac = 10 + (target.agility // 2)
        if hasattr(target, 'equipment') and target.equipment.get("armor"):
            target_ac += target.equipment["armor"].defense_bonus

        if attack_roll >= target_ac:
            if hasattr(self, 'equipment') and self.equipment.get("weapon"):
                damage = self.equipment["weapon"].get_damage(self.strength)
            else:
                damage = roll("1d4") + self.strength
            target.take_damage(damage, source=self)
            if target.is_alive():
                print(f"{self.name} 命中 {target.name}，造成 {damage} 点伤害！（{target.hp}/{target.max_hp} HP）")
        else:
            print(f"{self.name} 攻击未命中 {target.name}！")

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
class Charactor(Entity):
    def __init__(self, name, gender, career="footman", background="", level=1,
                 experience=0, attribute_points=0,
                 max_hp=10, hp=10, strength=0, agility=0, intelligence=0,
                 inventory=None, equipment=None):
        super().__init__(name, level, max_hp, hp, strength, agility, intelligence)
        self.gender = gender
        self.career = career
        self.background = background
        self.experience = experience
        self.attribute_points = attribute_points
        self.inventory = inventory or []
        self.equipment = equipment or {"weapon": None, "armor": None}

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
        self.inventory.append(item)
        print(f"{self.name} 获得了物品：{item.name}")

    def use_item(self, item_name):
        for item in self.inventory:
            if item.name == item_name and isinstance(item, Consumable):
                item.use(self)
                self.inventory.remove(item)
                return
        print(f"没有找到可用物品：{item_name}")

    # 装备
    def equip(self, slot, item):
        if slot in self.equipment:
            self.equipment[slot] = item
            print(f"{self.name} 装备了 {item.name} 在 {slot}。")

    def unequip(self, slot):
        if slot in self.equipment and self.equipment[slot]:
            item = self.equipment[slot]
            self.equipment[slot] = None
            print(f"{self.name} 卸下了 {item.name}。")

# ======================
# 怪物类
# ======================
class Monster(Entity):
    def __init__(self, name, level=1, max_hp=10, hp=None,
                 strength=0, agility=0, intelligence=0,
                 exp_reward=50, loot_table=None):
        super().__init__(name, level, max_hp, hp, strength, agility, intelligence)
        self.exp_reward = exp_reward
        self.loot_table = loot_table or []

    def on_death(self, killer=None):
        super().on_death(killer)
        if killer and isinstance(killer, Charactor) and self.exp_reward > 0:
            print(f"{killer.name} 击杀了 {self.name}，获得 {self.exp_reward} 经验！")
            killer.gain_experience(self.exp_reward)

        # 掉落物品
        if self.loot_table and killer:
            dropped_items = [item for item, chance in self.loot_table if random.random() <= chance]
            if dropped_items:
                print(f"{self.name} 掉落了物品：{[item.name for item in dropped_items]}")
                killer.inventory.extend(dropped_items)
