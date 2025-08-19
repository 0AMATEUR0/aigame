from utils.dice import roll


class Item:
    def __init__(self, name, description="", value=0):
        self.name = name
        self.description = description
        self.value = value  # 金币价值

    def __repr__(self):
        return f"<Item: {self.name}>"

class Weapon(Item):
    def __init__(self, name, attack_bonus=0, damage_dice="1d6", description="", value=0):
        super().__init__(name, description, value)
        self.attack_bonus = attack_bonus
        self.damage_dice = damage_dice  # 伤害骰子

    def get_damage(self, strength):
        roll_damage = roll(self.damage_dice)
        print(f"{self.name} 造成了 {roll_damage}({self.damage_dice}) + {strength} + {self.attack_bonus} 点伤害！")
        return roll_damage + strength + self.attack_bonus


class Armor(Item):
    def __init__(self, name, defense_bonus=0, description="", value=0):
        super().__init__(name, description, value)
        self.defense_bonus = defense_bonus


class Consumable(Item):
    def __init__(self, name, description="", value=0):
        super().__init__(name, description, value)

    def use(self, target):
        """使用物品的效果"""
        raise NotImplementedError("子类必须实现 use() 方法")


class HPPotion(Consumable):
    def __init__(self, name, heal_amount, description="恢复生命的药水", value=0):
        super().__init__(name, description, value)
        self.heal_amount = heal_amount

    def use(self, target):
        target.heal(self.heal_amount)
        print(f"{target.name} 使用了 {self.name}，恢复了 {self.heal_amount} 点生命！（{target.hp}/{target.max_hp} HP）")