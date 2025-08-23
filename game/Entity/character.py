from game.Item.item import EquipmentSlot, Equipment
from game.Inventory.inventory import Inventory
from game.Entity.entity import Entity

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
    def __init__(self, background="", occupation="", deputy_occupation="", **kwargs):
        super().__init__(**kwargs)

        # 角色特有
        self.background = background
        self.occupation = occupation
        self.deputy_occupation = deputy_occupation

        # 成长系统
        self.experience = 0
        self.attribute_points = 0

        # TODO: 技能、背包
        self.skills = []  # [Skill]
        self.inventory = Inventory()

        print(f"角色已创建：{self.info()}")

    def info(self):
        info = super().info()
        info.update({
            "background": self.background,
            "occupation": self.occupation,
            "deputy_occupation": self.deputy_occupation,
            "experience": self.experience,
            "attribute_points": self.attribute_points,
            "skills": [skill.name for skill in self.skills],
            "inventory": self.inventory.list_items(),
            "equipment": {slot.name: (item.name if item else None) for slot, item in self.equipment.items()}
        })
        return info

    def learn_skill(self, skill):
        print(f"✅ {skill.name} 习得了技能 {skill.name}")
        self.skills.append(skill)

    def use_skill(self, skill, targets):
        if skill in self.skills:
            return skill.use(self, targets)
        else:
            print(f"{self.name} 没有学会技能 {skill.name}！")
            return False

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
    def add_item(self, item, quantity: int = 1):
        success, msg = self.inventory.add(item, quantity)
        if not success:
            return False, msg
        else:
            return True, msg

    def use_item(self, item):
        found = self.inventory.find(item.name)
        if not found:
            return False, f"{self.name} 背包中没有 {item.name}"

        success, msg = self.inventory.remove(item, 1)

        if not success:
            return False, msg

        if hasattr(item, "use") and callable(item.use):
            item.use(self)
            return True, f"{self.name} 使用了 {item.name}"
        else:
            return False, f"{item.name} 不能使用"

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


