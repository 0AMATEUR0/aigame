from utils.dice import roll_detail
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json


class ItemRarity(Enum):
    """物品稀有度"""
    COMMON = "普通"
    UNCOMMON = "优秀"
    RARE = "稀有"
    EPIC = "史诗"
    LEGENDARY = "传说"


class ItemType(Enum):
    """物品类型"""
    WEAPON = "武器"
    ARMOR = "护甲"
    CONSUMABLE = "消耗品"
    MATERIAL = "材料"
    QUEST = "任务物品"
    TREASURE = "宝藏"


class EquipmentSlot(Enum):
    """装备槽位"""
    WEAPON = "weapon"
    ARMOR = "armor"
    SHIELD = "shield"
    HELMET = "helmet"
    GLOVES = "gloves"
    BOOTS = "boots"
    RING = "ring"
    AMULET = "amulet"


class BaseItem:
    """物品基类"""

    def __init__(self,
                 name: str,
                 description: str = "",
                 value: int = 0,
                 rarity: ItemRarity = ItemRarity.COMMON,
                 item_type: ItemType = ItemType.MATERIAL,
                 weight: float = 0.0,
                 stackable: bool = False,
                 max_stack: int = 1,
                 tags: List[str] = None):
        self.name = name
        self.description = description
        self.value = value
        self.rarity = rarity
        self.item_type = item_type
        self.weight = weight
        self.stackable = stackable
        self.max_stack = max_stack
        self.tags = tags or []
        self.id = f"{name}_{rarity.value}_{item_type.value}"

    def __repr__(self):
        return f"<{self.rarity.value}{self.item_type.value}: {self.name}>"

    def get_display_name(self) -> str:
        """获取显示名称（包含稀有度颜色）"""
        rarity_colors = {
            ItemRarity.COMMON: "",
            ItemRarity.UNCOMMON: "🟢",
            ItemRarity.RARE: "🔵",
            ItemRarity.EPIC: "🟣",
            ItemRarity.LEGENDARY: "🟡"
        }
        return f"{rarity_colors.get(self.rarity, '')}{self.name}"

    def get_full_description(self) -> str:
        """获取完整描述"""
        desc = f"{self.get_display_name()}\n"
        desc += f"类型: {self.item_type.value}\n"
        desc += f"稀有度: {self.rarity.value}\n"
        desc += f"价值: {self.value} 金币\n"
        if self.weight > 0:
            desc += f"重量: {self.weight} 磅\n"
        if self.description:
            desc += f"描述: {self.description}\n"
        if self.tags:
            desc += f"标签: {', '.join(self.tags)}\n"
        return desc.strip()

    def can_use(self, character) -> bool:
        """检查角色是否可以使用此物品"""
        return True

    def use(self, character) -> bool:
        """使用物品（基类默认实现）"""
        return False

    def to_dict(self) -> Dict:
        """转换为字典（用于保存）"""
        return {
            "name": self.name,
            "description": self.description,
            "value": self.value,
            "rarity": self.rarity.value,
            "item_type": self.item_type.value,
            "weight": self.weight,
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BaseItem':
        """从字典创建物品"""
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            value=data.get("value", 0),
            rarity=ItemRarity(data.get("rarity", "普通")),
            item_type=ItemType(data.get("item_type", "材料")),
            weight=data.get("weight", 0.0),
            stackable=data.get("stackable", False),
            max_stack=data.get("max_stack", 1),
            tags=data.get("tags", [])
        )


class Equipment(BaseItem):
    """装备基类"""

    def __init__(self,
                 name: str,
                 slot: EquipmentSlot,
                 level_requirement: int = 1,
                 effects: Dict[str, Any] = None,
                 **kwargs):
        super().__init__(name, item_type=ItemType.WEAPON if slot == EquipmentSlot.WEAPON else ItemType.ARMOR, **kwargs)
        self.slot = slot
        self.level_requirement = level_requirement
        self.effects = effects or {}
        self.durability = 100
        self.max_durability = 100

    def can_equip(self, character) -> tuple[bool, str]:
        """检查角色是否可以装备"""
        if character.level < self.level_requirement:
            return False, f"需要等级 {self.level_requirement}"
        return True, "可以装备"

    def equip_to(self, character) -> bool:
        """装备到角色"""
        can_equip, msg = self.can_equip(character)
        if not can_equip:
            print(f"❌ {character.name} 无法装备 {self.name}：{msg}")
            return False

        current_eq = character.equipment.get(self.slot)
        if current_eq:
            print(f"⚠️ {character.name} 已经装备了 {current_eq.name} 在 {self.slot.value} 槽，先卸下它。")
            current_eq.unequip_from(character)

        character.equipment[self.slot] = self
        self.apply_effects(character)
        print(f"✅ {character.name} 装备了 {self.name} 到 {self.slot.value} 槽")
        return True

    def unequip_from(self, character) -> bool:
        """从角色卸下装备"""
        for slot, eq in character.equipment.items():
            if eq == self:
                self.remove_effects(character)
                character.equipment[slot] = None
                print(f"✅ {character.name} 卸下了 {self.name} 从 {slot.value} 槽")
                return True
        print(f"❌ {self.name} 未装备在 {character.name} 上")
        return False

    def apply_effects(self, character):
        """应用装备效果到角色"""
        for effect_name, effect_value in self.effects.items():
            if hasattr(character, effect_name):
                current_value = getattr(character, effect_name)
                setattr(character, effect_name, current_value + effect_value)

    def remove_effects(self, character):
        """移除装备效果"""
        for effect_name, effect_value in self.effects.items():
            if hasattr(character, effect_name):
                current_value = getattr(character, effect_name)
                setattr(character, effect_name, current_value - effect_value)

    def take_damage(self, amount: int):
        """装备受到伤害（降低耐久度）"""
        self.durability = max(0, self.durability - amount)
        if self.durability <= 0:
            print(f"⚠️ {self.name} 已经损坏！")

    def repair(self, amount: int = 100):
        """修复装备"""
        self.durability = min(self.max_durability, self.durability + amount)
        print(f"🔧 {self.name} 被修复了 {amount} 点耐久度")

    def info(self) -> str:
        desc = super().get_full_description()
        desc += f"\n装备槽: {self.slot.value}"
        desc += f"\n等级要求: {self.level_requirement}"
        desc += f"\n耐久度: {self.durability}/{self.max_durability}"
        if self.effects:
            desc += f"\n效果: {', '.join([f'{k}+{v}' for k, v in self.effects.items()])}"
        return desc


class Weapon(Equipment):
    """武器类"""

    def __init__(self,
                 name: str,
                 damage_dice: str,
                 damage_type: str = "物理",
                 weapon_type: str = "近战",
                 attack_bonus: int = 0,
                 critical_range: int = 20,
                 critical_multiplier: int = 2,
                 **kwargs):
        super().__init__(name, slot=EquipmentSlot.WEAPON, **kwargs)
        self.damage_dice = damage_dice
        self.damage_type = damage_type
        self.weapon_type = weapon_type
        self.attack_bonus = attack_bonus
        self.critical_range = critical_range
        self.critical_multiplier = critical_multiplier

    def get_damage(self, strength: int, crit: bool = False) -> int:
        """计算伤害"""
        dmg_res = roll_detail(self.damage_dice, crit=crit)
        damage = dmg_res.total + (strength - 10)//2
        print(f"{self.name} 伤害: {dmg_res.rolls} + 力量({(strength - 10)//2}) → {damage}")
        return damage

    def get_full_description(self) -> str:
        desc = super().get_full_description()
        desc += f"\n伤害: {self.damage_dice} + 力量"
        desc += f"\n伤害类型: {self.damage_type}"
        desc += f"\n武器类型: {self.weapon_type}"
        desc += f"\n攻击加值: {self.attack_bonus:+d}"
        desc += f"\n暴击范围: {self.critical_range}"
        desc += f"\n暴击倍数: x{self.critical_multiplier}"
        return desc


class Armor(Equipment):
    """护甲类"""

    def __init__(self,
                 name: str,
                 armor_class: int,
                 armor_type: str = "轻甲",
                 max_dex_bonus: Optional[int] = None,
                 **kwargs):
        super().__init__(name, slot=EquipmentSlot.ARMOR, **kwargs)
        self.armor_class = armor_class
        self.armor_type = armor_type
        self.max_dex_bonus = max_dex_bonus

    def get_full_description(self) -> str:
        desc = super().get_full_description()
        desc += f"\n护甲等级: {self.armor_class}"
        desc += f"\n护甲类型: {self.armor_type}"
        if self.max_dex_bonus is not None:
            desc += f"\n最大敏捷加值: {self.max_dex_bonus}"
        return desc


class Consumable(BaseItem):
    """消耗品类"""

    def __init__(self,
                 name: str,
                 use_effect: Callable = None,
                 charges: int = 1,
                 **kwargs):
        super().__init__(name, item_type=ItemType.CONSUMABLE, stackable=True, **kwargs)
        self.use_effect = use_effect
        self.charges = charges

    def use(self, character) -> bool:
        """使用消耗品"""
        if self.use_effect:
            return self.use_effect(character, self)
        return False

    def get_full_description(self) -> str:
        desc = super().get_full_description()
        desc += f"\n使用次数: {self.charges}"
        return desc


class HPPotion(Consumable):
    """生命药水"""

    def __init__(self,
                 name: str = "生命药水",
                 heal_amount: int = 10,
                 **kwargs):
        def heal_effect(character, item):
            character.heal(heal_amount)
            print(
                f"💚 {character.name} 使用了 {item.name}，恢复了 {heal_amount} 点生命！（{character.HP}/{character.MAX_HP} HP）")
            return True

        super().__init__(name, use_effect=heal_effect, **kwargs)
        self.heal_amount = heal_amount

    def get_full_description(self) -> str:
        desc = super().get_full_description()
        desc += f"\n治疗效果: 恢复 {self.heal_amount} 点生命值"
        return desc


class MPPotion(Consumable):
    """魔法药水"""

    def __init__(self,
                 name: str = "魔法药水",
                 mana_amount: int = 10,
                 **kwargs):
        def mana_effect(character, item):
            character.mp = min(character.MAX_MP, character.MP + mana_amount)
            print(
                f"🔮 {character.name} 使用了 {item.name}，恢复了 {mana_amount} 点魔法！（{character.MP}/{character.MAX_MP} MP）")
            return True

        super().__init__(name, use_effect=mana_effect, **kwargs)
        self.mana_amount = mana_amount

    def get_full_description(self) -> str:
        desc = super().get_full_description()
        desc += f"\n治疗效果: 恢复 {self.mana_amount} 点魔法值"
        return desc


class ItemFactory:
    """物品工厂类"""

    @staticmethod
    def create_weapon(name: str, damage_dice: str, **kwargs) -> Weapon:
        """创建武器"""
        return Weapon(name, damage_dice, **kwargs)

    @staticmethod
    def create_armor(name: str, armor_class: int, **kwargs) -> Armor:
        """创建护甲"""
        return Armor(name, armor_class, **kwargs)

    @staticmethod
    def create_hp_potion(name: str = "生命药水", heal_amount: int = 10, **kwargs) -> HPPotion:
        """创建生命药水"""
        return HPPotion(name, heal_amount, **kwargs)

    @staticmethod
    def create_mp_potion(name: str = "魔法药水", mana_amount: int = 10, **kwargs) -> MPPotion:
        """创建魔法药水"""
        return MPPotion(name, mana_amount, **kwargs)

    @staticmethod
    def create_from_template(template: Dict) -> BaseItem:
        """从模板创建物品，自动将字符串字段转换为枚举类型"""
        # 处理稀有度和类型
        t = template.copy()
        # 处理 rarity
        if "rarity" in t and not isinstance(t["rarity"], ItemRarity):
            try:
                t["rarity"] = ItemRarity(t["rarity"])
            except Exception:
                t["rarity"] = ItemRarity.COMMON
        # 处理 type/item_type
        item_type_str = t.get("type") or t.get("item_type")
        if item_type_str and not isinstance(item_type_str, ItemType):
            try:
                t["item_type"] = ItemType(item_type_str)
            except Exception:
                t["item_type"] = ItemType.MATERIAL
        # 处理装备槽
        if "slot" in t and isinstance(t["slot"], str):
            try:
                t["slot"] = EquipmentSlot(t["slot"])
            except Exception:
                pass

        # 类型分支优先用 type 字段（字符串）
        type_str = t.get("type")
        if type_str == "weapon":
            return Weapon(
                name=t["name"],
                damage_dice=t["damage_dice"],
                damage_type=t.get("damage_type", "物理"),
                weapon_type=t.get("weapon_type", "近战"),
                attack_bonus=t.get("attack_bonus", 0),
                **{k: v for k, v in t.items() if
                   k not in ["type", "item_type", "name", "damage_dice", "damage_type", "weapon_type", "attack_bonus"]}
            )
        elif type_str == "armor":
            return Armor(
                name=t["name"],
                armor_class=t["armor_class"],
                armor_type=t.get("armor_type", "轻甲"),
                **{k: v for k, v in t.items() if k not in ["type", "item_type", "name", "armor_class", "armor_type"]}
            )
        elif type_str == "hp_potion":
            return HPPotion(
                name=t["name"],
                heal_amount=t.get("heal_amount", 10),
                **{k: v for k, v in t.items() if k not in ["type", "item_type", "name", "heal_amount"]}
            )
        elif type_str == "mp_potion":
            return MPPotion(
                name=t["name"],
                mana_amount=t.get("mana_amount", 10),
                **{k: v for k, v in t.items() if k not in ["type", "item_type", "name", "mana_amount"]}
            )
        # 其它类型
        t.pop("type", None)
        return BaseItem(**t)


# 预设物品模板
PRESET_ITEMS = {
    # 武器
    "铁剑": {
        "type": "weapon",
        "name": "铁剑",
        "description": "一把普通的铁制长剑",
        "damage_dice": "1d8",
        "damage_type": "物理",
        "weapon_type": "近战",
        "attack_bonus": 0,
        "value": 15,
        "rarity": "普通",
        "level_requirement": 1,
        "effects": {"STR": 1}
    },

    "魔法法杖": {
        "type": "weapon",
        "name": "魔法法杖",
        "description": "镶嵌着魔法水晶的法杖",
        "damage_dice": "1d6",
        "damage_type": "魔法",
        "weapon_type": "远程",
        "attack_bonus": 2,
        "value": 50,
        "rarity": "优秀",
        "level_requirement": 3,
        "effects": {"INT": 2}
    },

    # 护甲
    "皮甲": {
        "type": "armor",
        "name": "皮甲",
        "description": "用皮革制成的轻便护甲",
        "armor_class": 2,
        "armor_type": "轻甲",
        "value": 10,
        "rarity": "普通",
        "level_requirement": 1,
        "effects": {"DEX": 1}
    },

    "铁甲": {
        "type": "armor",
        "name": "铁甲",
        "description": "厚重的铁制护甲",
        "armor_class": 5,
        "armor_type": "重甲",
        "max_dex_bonus": 2,
        "value": 30,
        "rarity": "普通",
        "level_requirement": 2,
        "effects": {"STR": 1}
    },

    # 药水
    "小生命药水": {
        "type": "hp_potion",
        "name": "小生命药水",
        "description": "恢复少量生命值的红色药水",
        "heal_amount": 10,
        "value": 5,
        "rarity": "普通"
    },

    "大生命药水": {
        "type": "hp_potion",
        "name": "大生命药水",
        "description": "恢复大量生命值的红色药水",
        "heal_amount": 25,
        "value": 15,
        "rarity": "优秀"
    },

    "小魔法药水": {
        "type": "mp_potion",
        "name": "小魔法药水",
        "description": "恢复少量魔法值的蓝色药水",
        "mana_amount": 10,
        "value": 8,
        "rarity": "普通"
    }
}


def create_preset_item(item_name: str) -> BaseItem:
    """创建预设物品"""
    if item_name in PRESET_ITEMS:
        return ItemFactory.create_from_template(PRESET_ITEMS[item_name])
    else:
        raise ValueError(f"未知的预设物品: {item_name}")


def load_items_from_json(file_path: str) -> Dict[str, BaseItem]:
    """从JSON文件加载物品"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        items = {}
        for item_name, template in data.items():
            items[item_name] = ItemFactory.create_from_template(template)

        return items
    except FileNotFoundError:
        print(f"物品文件未找到: {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"物品文件格式错误: {e}")
        return {}


def save_items_to_json(items: Dict[str, BaseItem], file_path: str):
    """保存物品到JSON文件"""
    data = {}
    for item_name, item in items.items():
        data[item_name] = item.to_dict()

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    from game.Entity.entityfactory import EntityFactory

    hero = EntityFactory.create_character("战士")
    print(hero.info())

    # 1. 创建预设物品
    sword = create_preset_item("铁剑")
    armor = create_preset_item("皮甲")
    hp_potion = create_preset_item("小生命药水")
    mp_potion = create_preset_item("小魔法药水")

    # 2. 查看物品描述
    print("\n📦 物品信息:")
    print(sword.get_full_description())
    print(armor.get_full_description())
    print(hp_potion.get_full_description())
    print(mp_potion.get_full_description())

    # 3. 使用药水
    print("\n💊 使用药水:")
    success, msg = hero.add_item(hp_potion)
    print(success, msg)
    success, msg = hero.add_item(mp_potion)
    print(success, msg)
    success, msg = hero.use_item(hp_potion)
    print(success, msg)
    success, msg = hero.use_item(mp_potion)
    print(success, msg)
    print(hero.info())

    # 4. 装备武器和护甲
    print("\n🗡️ 装备武器和护甲:")
    hero.equip(sword)
    hero.equip(armor)
    print(hero.info())

    # 5. 卸下装备
    print("\n🛡️ 卸下武器:")
    hero.unequip(sword.slot)
    hero.unequip(armor.slot)
    print(hero.info())
