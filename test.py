from core.Skill.skill import Skill
from core.battle import BattleManager
from core.character import Character, Monster
from core.Item.item import Weapon, Armor, HPPotion
from utils.dice import roll_detail

if __name__ == "__main__":
    # --------------------------
    # 创建道具
    # --------------------------
    hp_potion_small = HPPotion("小生命药水", heal_amount=10)
    hp_potion_large = HPPotion("大生命药水", heal_amount=25)

    # --------------------------
    # 创建技能
    # --------------------------
    # 单体技能
    def fireball_damage(user, target):
        dmg_res = roll_detail("2d6")
        damage = dmg_res["total"] + user.intelligence
        return damage

    fireball = Skill(
        "火球术",
        damage_func=fireball_damage,
        mp_cost=5,
        target_type="single",
        description="对单体敌人造成火焰伤害",
        uses_per_battle=3
    )

    # 群体技能
    def whirlwind_damage(user, targets):
        # targets 必须是列表
        if not isinstance(targets, list):
            targets = [targets]
        results = []
        for t in targets:
            dmg_res = roll_detail("1d6")  # 示例伤害
            damage = dmg_res["total"] + user.strength
            results.append((t, damage))
        return results

    whirlwind = Skill(
        "旋风斩",
        damage_func=whirlwind_damage,
        mp_cost=3,
        target_type="aoe",
        description="对所有敌人造成旋风伤害",
        uses_per_battle=2
    )

    # --------------------------
    # 创建玩家
    # --------------------------
    player1 = Character("战士A", gender="男", max_hp=30, strength=5, agility=3, intelligence=1)
    player2 = Character("法师B", gender="女", max_hp=30, strength=2, agility=3, intelligence=5)

    # 给玩家装备武器
    sword = Weapon("铁剑", attack_bonus=2, damage_dice="1d6")
    staff = Weapon("法杖", attack_bonus=1, damage_dice="1d4")
    player1.add_item(sword)
    player2.add_item(staff)
    player1.equip(sword)
    player2.equip(staff)

    # 背包加入药水
    player1.add_item(hp_potion_small)
    player1.add_item(hp_potion_large)
    player2.add_item(hp_potion_small)

    # 技能加入玩家
    player1.add_skill(whirlwind)
    player2.add_skill(fireball)

    p1info = player1.get_info()
    p2info = player2.get_info()

    print(f"玩家1信息: {p1info}")
    print(f"玩家2信息: {p2info}")

    # --------------------------
    # 创建敌人
    # --------------------------
    monster1 = Monster("哥布林A", level=1, max_hp=20, strength=3, agility=10, intelligence=1, exp_reward=50)
    monster2 = Monster("哥布林B", level=1, max_hp=15, strength=2, agility=10, intelligence=1, exp_reward=50)

    # 敌人掉落
    monster1.loot_table = [(hp_potion_small, 1.0)]
    monster2.loot_table = [(hp_potion_large, 1.0)]

    # --------------------------
    # 开始战斗
    # --------------------------
    battle = BattleManager(
        players=[player1, player2],
        enemies=[monster1, monster2],
        mode="manual"  # 手动回合，可选择攻击/道具/技能/逃跑
    )
    battle.start_battle()