# Item系统使用指南

## 概述

新的Item系统为您的D&D游戏提供了更加完善和灵活的物品管理功能。系统支持多种物品类型、稀有度、装备效果、耐久度等特性。

## 主要特性

### 1. 物品类型系统
- **武器 (Weapon)**: 用于攻击的装备
- **护甲 (Armor)**: 提供防护的装备
- **消耗品 (Consumable)**: 可使用的物品，如药水
- **材料 (Material)**: 用于制作或交易的物品
- **任务物品 (Quest)**: 与任务相关的特殊物品
- **宝藏 (Treasure)**: 珍贵的收藏品

### 2. 稀有度系统
- **普通 (Common)**: 基础物品
- **优秀 (Uncommon)**: 较好的物品
- **稀有 (Rare)**: 珍贵的物品
- **史诗 (Epic)**: 非常珍贵的物品
- **传说 (Legendary)**: 最珍贵的物品

### 3. 装备槽位
- **武器 (weapon)**: 主手武器
- **护甲 (armor)**: 身体护甲
- **盾牌 (shield)**: 副手盾牌
- **头盔 (helmet)**: 头部装备
- **手套 (gloves)**: 手部装备
- **靴子 (boots)**: 脚部装备
- **戒指 (ring)**: 戒指装备
- **项链 (amulet)**: 颈部装备

## 使用方法

### 创建物品

#### 使用预设物品

```python
from game.Item.item import create_preset_item

# 创建预设物品
iron_sword = create_preset_item("铁剑")
leather_armor = create_preset_item("皮甲")
hp_potion = create_preset_item("小生命药水")
```

#### 使用工厂创建物品

```python
from game.Item.item import ItemFactory, ItemRarity

# 创建自定义武器
custom_sword = ItemFactory.create_weapon(
    name="自定义长剑",
    damage_dice="2d6",
    damage_type="物理",
    weapon_type="近战",
    attack_bonus=3,
    value=100,
    rarity=ItemRarity.RARE,
    effects={"strength": 3, "agility": 1}
)

# 创建自定义护甲
custom_armor = ItemFactory.create_armor(
    name="自定义护甲",
    armor_class=8,
    armor_type="重甲",
    value=80,
    rarity=ItemRarity.UNCOMMON,
    effects={"strength": 2}
)

# 创建自定义药水
custom_potion = ItemFactory.create_hp_potion(
    name="超级生命药水",
    heal_amount=50,
    value=25,
    rarity=ItemRarity.RARE
)
```

#### 从JSON文件加载物品

```python
from game.Item.item import load_items_from_json

# 从JSON文件加载物品
items = load_items_from_json("data/items.json")
iron_sword = items["铁剑"]
```

### 角色装备管理

#### 装备物品

```python
from game.Entity.character import Character

player = Character(name="冒险者", level=5)

# 添加物品到背包
player.add_item(iron_sword)

# 装备物品
player.equip(iron_sword)

# 检查装备要求
can_equip, message = iron_sword.can_equip(player)
if can_equip:
    player.equip(iron_sword)
else:
    print(f"无法装备: {message}")
```

#### 卸下装备
```python
# 卸下装备
player.unequip("weapon")
```

#### 获取装备加成
```python
# 获取所有装备提供的属性加成
bonuses = player.get_equipment_bonuses()
print(f"装备加成: {bonuses}")

# 获取包含装备加成的总属性
total_stats = player.get_total_stats()
print(f"总属性: {total_stats}")
```

### 使用消耗品
```python
# 添加药水到背包
player.add_item(hp_potion)

# 使用药水
player.use_item("小生命药水")
```

### 装备耐久度
```python
# 装备受到伤害
iron_sword.take_damage(20)
print(f"耐久度: {iron_sword.durability}/{iron_sword.max_durability}")

# 修复装备
iron_sword.repair(30)
```

## 物品属性

### 基础属性
- **name**: 物品名称
- **description**: 物品描述
- **value**: 金币价值
- **rarity**: 稀有度
- **item_type**: 物品类型
- **weight**: 重量
- **stackable**: 是否可堆叠
- **max_stack**: 最大堆叠数量
- **tags**: 标签列表

### 武器属性
- **damage_dice**: 伤害骰子（如"1d8"）
- **damage_type**: 伤害类型（物理、魔法、火焰等）
- **weapon_type**: 武器类型（近战、远程）
- **attack_bonus**: 攻击加值
- **critical_range**: 暴击范围
- **critical_multiplier**: 暴击倍数

### 护甲属性
- **armor_class**: 护甲等级
- **armor_type**: 护甲类型（轻甲、中甲、重甲）
- **max_dex_bonus**: 最大敏捷加值

### 装备属性
- **slot**: 装备槽位
- **level_requirement**: 等级要求
- **effects**: 装备效果（属性加成）
- **durability**: 当前耐久度
- **max_durability**: 最大耐久度

## 预设物品

系统内置了多种预设物品：

### 武器
- 铁剑 (1d8物理伤害)
- 精钢剑 (1d10物理伤害)
- 魔法法杖 (1d6魔法伤害)
- 火焰剑 (1d8火焰伤害)

### 护甲
- 皮甲 (AC+2，轻甲)
- 锁子甲 (AC+4，中甲)
- 铁甲 (AC+6，重甲)
- 魔法护甲 (AC+5，轻甲，魔法防护)

### 药水
- 小生命药水 (恢复10HP)
- 生命药水 (恢复25HP)
- 大生命药水 (恢复50HP)
- 小魔法药水 (恢复10MP)
- 魔法药水 (恢复25MP)
- 大魔法药水 (恢复50MP)

### 材料
- 铁矿石
- 金矿石
- 魔法水晶
- 龙鳞

## 扩展功能

### 添加新的物品类型
```python
class CustomItem(BaseItem):
    def __init__(self, name, custom_property, **kwargs):
        super().__init__(name, **kwargs)
        self.custom_property = custom_property
    
    def use(self, character):
        # 自定义使用逻辑
        return True
```

### 添加新的装备效果
```python
# 在装备的effects中添加自定义效果
custom_weapon = ItemFactory.create_weapon(
    name="自定义武器",
    damage_dice="1d8",
    effects={
        "strength": 2,
        "custom_effect": 5  # 自定义效果
    }
)
```

## 注意事项

1. **装备要求**: 确保角色等级满足装备要求
2. **耐久度**: 装备会随着使用降低耐久度，需要定期修复
3. **属性加成**: 装备提供的属性加成会自动应用到角色身上
4. **物品堆叠**: 可堆叠物品会自动合并，节省背包空间
5. **稀有度显示**: 不同稀有度的物品会显示不同的颜色标识

## 测试

运行测试文件来验证系统功能：
```bash
python test_item_system.py
```

这将测试所有主要功能，包括物品创建、装备管理、消耗品使用等。