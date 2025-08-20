from utils.dice import roll_detail


class Item:
    def __init__(self, name, description="", value=0):
        self.name = name
        self.description = description
        self.value = value  # 金币价值

    def __repr__(self):
        return f"<Item: {self.name}>"

class Weapon:
    def __init__(self, name: str, damage_dice: str, attack_bonus: int = 0):
        self.name = name
        self.damage_dice = damage_dice  # 例如 "1d8"
        self.attack_bonus = attack_bonus
        self.slot = "weapon"  # 武器装备槽

    def get_damage(self, strength: int, crit: bool = False) -> int:
        """计算伤害，暴击时骰子翻倍"""
        dmg_res = roll_detail(self.damage_dice, crit=crit)
        damage = dmg_res["total"] + strength
        print(f"{self.name} 伤害: {dmg_res['rolls']} + 力量({strength}) → {damage}")
        return damage



class Armor(Item):
    def __init__(self, name, defense_bonus=0, description="", value=0):
        super().__init__(name, description, value)
        self.defense_bonus = defense_bonus
        self.slot = "armor"


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