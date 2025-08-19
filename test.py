from core.battle import battle
from core.charactor import Charactor, Monster
from core.equipment.Item import Weapon, Armor, Potion

if __name__ == "__main__":
    # 创建角色
    hero = Charactor("勇者", gender="男", strength=6, agility=4, max_hp=20, hp=10)
    goblin = Monster("哥布林", strength=4, agility=3, max_hp=12, hp=12, exp_reward=1000)

    # 创建武器、防具、药水
    sword = Weapon("长剑", attack_bonus=2, damage_dice="1d8")
    armor = Armor("皮甲", defense_bonus=2)
    potion = Potion("小型治疗药水", heal_amount=8)

    # 装备
    hero.equip("weapon", sword)
    hero.equip("armor", armor)

    # 背包
    hero.add_item(potion)

    # 战斗开始前喝药水
    hero.use_item("小型治疗药水")

    # 战斗
    battle(hero, goblin)

    hero.allocate_points('strength', 2)
    hero.allocate_points('agility', 2)
    hero.allocate_points('intelligence', 2)