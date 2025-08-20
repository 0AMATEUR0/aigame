"""
物品系统模块 - 基于JSON配置的物品系统
"""

from utils.dice import roll_detail
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import json
import copy
import os

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

class Item:
    """统一的物品类，根据type实现不同功能"""
    def __init__(self, data: Dict):
        # 基础属性
        self.name = data["name"]
        self.type = data.get("type", "material")
        self.description = data.get("description", "")
        self.value = data.get("value", 0)
        self.rarity = ItemRarity(data.get("rarity", "普通"))
        self.weight = data.get("weight", 0.0)
        self.tags = data.get("tags", [])
        
        # 装备属性
        if self.type in ["weapon", "armor"]:
            self.level_requirement = data.get("level_requirement", 1)
            self.effects = data.get("effects", {})
            self.durability = data.get("durability", 100)
            self.max_durability = data.get("max_durability", 100)
        
        # 武器特有属性
        if self.type == "weapon":
            self.damage_dice = data.get("damage_dice", "1d4")
            self.damage_type = data.get("damage_type", "物理")
            self.weapon_type = data.get("weapon_type", "近战")
            self.attack_bonus = data.get("attack_bonus", 0)
            self.critical_range = data.get("critical_range", 20)
            self.critical_multiplier = data.get("critical_multiplier", 2)
        
        # 护甲特有属性
        elif self.type == "armor":
            self.armor_class = data.get("armor_class", 0)
            self.armor_type = data.get("armor_type", "轻甲")
            self.max_dex_bonus = data.get("max_dex_bonus")
        
        # 消耗品特有属性
        elif self.type in ["hppotion", "mppotion", "consumable"]:
            self.charges = data.get("charges", 1)
            self.heal_amount = data.get("heal_amount", 0)
            self.mana_amount = data.get("mana_amount", 0)

    def get_display_name(self) -> str:
        """获取带有稀有度标记的显示名称"""
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
        desc = [
            self.get_display_name(),
            f"类型: {self.type}",
            f"稀有度: {self.rarity.value}",
            f"价值: {self.value} 金币"
        ]
        
        if self.weight > 0:
            desc.append(f"重量: {self.weight} 磅")
        if self.description:
            desc.append(f"描述: {self.description}")
        if self.tags:
            desc.append(f"标签: {', '.join(self.tags)}")
            
        # 装备属性
        if self.type in ["weapon", "armor"]:
            desc.extend([
                f"等级要求: {self.level_requirement}",
                f"耐久度: {self.durability}/{self.max_durability}"
            ])
            if self.effects:
                desc.append(f"效果: {', '.join([f'{k}+{v}' for k, v in self.effects.items()])}")
        
        # 武器属性
        if self.type == "weapon":
            desc.extend([
                f"伤害: {self.damage_dice} + 力量",
                f"伤害类型: {self.damage_type}",
                f"武器类型: {self.weapon_type}",
                f"攻击加值: {self.attack_bonus:+d}",
                f"暴击范围: {self.critical_range}",
                f"暴击倍数: x{self.critical_multiplier}"
            ])
        
        # 护甲属性
        elif self.type == "armor":
            desc.extend([
                f"护甲等级: {self.armor_class}",
                f"护甲类型: {self.armor_type}"
            ])
            if self.max_dex_bonus is not None:
                desc.append(f"最大敏捷加值: {self.max_dex_bonus}")
        
        # 消耗品属性
        elif self.type in ["hppotion", "mppotion", "consumable"]:
            desc.append(f"使用次数: {self.charges}")
            if self.heal_amount:
                desc.append(f"治疗效果: 恢复 {self.heal_amount} 点生命值")
            if self.mana_amount:
                desc.append(f"魔法效果: 恢复 {self.mana_amount} 点魔法值")
        
        return "\n".join(desc)

    def use(self, character) -> bool:
        """使用物品"""
        if self.type == "hppotion" and self.charges > 0:
            if character.hp >= character.max_hp:
                print(f"❌ {character.name} 生命值已满")
                return False
            character.heal(self.heal_amount)
            print(f"💚 {character.name} 使用了 {self.name}，恢复了 {self.heal_amount} 点生命！（{character.hp}/{character.max_hp} HP）")
            self.charges -= 1
            return True
            
        elif self.type == "mppotion" and self.charges > 0:
            if character.mp >= character.max_mp:
                print(f"❌ {character.name} 魔法值已满")
                return False
            character.mp = min(character.max_mp, character.mp + self.mana_amount)
            print(f"🔮 {character.name} 使用了 {self.name}，恢复了 {self.mana_amount} 点魔法！（{character.mp}/{character.max_mp} MP）")
            self.charges -= 1
            return True
            
        return False

    def can_equip(self, character) -> tuple[bool, str]:
        """检查是否可以装备"""
        if self.type not in ["weapon", "armor"]:
            return False, "此物品不可装备"
        if character.level < self.level_requirement:
            return False, f"需要等级 {self.level_requirement}"
        return True, "可以装备"

    def apply_effects(self, character):
        """应用装备效果"""
        if self.type in ["weapon", "armor"]:
            for effect_name, effect_value in self.effects.items():
                if hasattr(character, effect_name):
                    current_value = getattr(character, effect_name)
                    setattr(character, effect_name, current_value + effect_value)

    def remove_effects(self, character):
        """移除装备效果"""
        if self.type in ["weapon", "armor"]:
            for effect_name, effect_value in self.effects.items():
                if hasattr(character, effect_name):
                    current_value = getattr(character, effect_name)
                    setattr(character, effect_name, current_value - effect_value)

    def get_damage(self, strength: int, crit: bool = False) -> int:
        """计算武器伤害"""
        if self.type != "weapon":
            return 0
        dmg_res = roll_detail(self.damage_dice, crit=crit)
        damage = dmg_res["total"] + strength
        print(f"{self.name} 伤害: {dmg_res['rolls']} + 力量({strength}) → {damage}")
        return damage

# 全局物品注册表
class ItemRegistry:
    """物品注册表类"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._items = {}
            cls._instance._loaded = False
        return cls._instance

    def load_from_json(self, json_path: str) -> None:
        """从JSON文件加载物品模板"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._items = {name: Item(item_data) for name, item_data in data.items()}
            self._loaded = True
            print(f"✅ 已从 {json_path} 加载 {len(self._items)} 个物品模板")
        except Exception as e:
            print(f"❌ 加载物品时出错: {e}")

    def get_item(self, item_name: str) -> Item:
        """获取物品实例"""
        if not self._loaded:
            self.load_from_json("data/items.json")
        if item_name not in self._items:
            raise KeyError(f"未找到物品: {item_name}")
        return copy.deepcopy(self._items[item_name])

    def list_items(self) -> List[str]:
        """列出所有可用物品"""
        if not self._loaded:
            self.load_from_json("data/items.json")
        return list(self._items.keys())

# 创建全局注册表实例
registry = ItemRegistry()

def get_item(item_name: str) -> Item:
    """获取物品实例的快捷方法"""
    return registry.get_item(item_name)

def list_items() -> List[str]:
    """列出所有可用物品的快捷方法"""
    return registry.list_items()
