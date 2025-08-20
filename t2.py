from core.Skill.skill import Skill
from core.battle import BattleManager
from core.character import Character, Monster
from core.equipment.Item import Weapon, HPPotion
from utils.dice import roll_detail
import random

# --------------------------
# 道具
# --------------------------
hp_small = HPPotion("小生命药水", heal_amount=10)
hp_large = HPPotion("大生命药水", heal_amount=25)

# --------------------------
# 技能
# --------------------------
def fireball_damage(user, target):
    dmg_res = roll_detail("2d6")
    return dmg_res["total"] + user.intelligence

fireball = Skill("火球术", damage_func=fireball_damage, mp_cost=5, target_type="single",
                 description="对单体敌人造成火焰伤害", uses_per_battle=3)

def whirlwind_damage(user, targets):
    if not isinstance(targets, list):
        targets = [targets]
    results = []
    for t in targets:
        dmg_res = roll_detail("1d6")
        damage = dmg_res["total"] + user.strength
        results.append((t, damage))
    return results

whirlwind = Skill("旋风斩", damage_func=whirlwind_damage, mp_cost=3, target_type="aoe",
                  description="对所有敌人造成旋风伤害", uses_per_battle=2)

# --------------------------
# 玩家
# --------------------------
player1 = Character("战士A", strength=5, agility=3, intelligence=1)
player2 = Character("法师B", strength=2, agility=3, intelligence=5)

# 装备武器
player1.equip(Weapon("铁剑", attack_bonus=2, damage_dice="1d6"))
player2.equip(Weapon("法杖", attack_bonus=1, damage_dice="1d4"))

# 背包道具
player1.add_item(hp_small)
player1.add_item(hp_large)
player2.add_item(hp_small)

# 技能加入玩家
player1.add_skill(whirlwind)
player2.add_skill(fireball)

# --------------------------
# 敌人
# --------------------------
monster1 = Monster("哥布林A", max_hp=20, strength=3, agility=2, intelligence=1)
monster2 = Monster("哥布林B", max_hp=15, strength=2, agility=3, intelligence=1)

# --------------------------
# 创建战斗管理器 (自动演示)
# --------------------------
battle = BattleManager(players=[player1, player2], enemies=[monster1, monster2], mode="auto")

# --------------------------
# 自动演示逻辑
# --------------------------
def auto_demo_turn(battle_mgr):
    """每回合自动演示攻击、技能、道具和逃跑"""
    for player in battle_mgr.all_alive(battle_mgr.players):
        alive_enemies = battle_mgr.all_alive(battle_mgr.enemies)
        if not alive_enemies:
            continue

        # 1. 玩家1用群体技能 (旋风斩)
        if player == player1 and whirlwind.remaining_uses > 0 and player.mp >= whirlwind.mp_cost:
            whirlwind.use(player, alive_enemies)
        # 2. 玩家2用单体技能 (火球术)
        elif player == player2 and fireball.remaining_uses > 0 and player.mp >= fireball.mp_cost:
            fireball.use(player, alive_enemies[0])
        # 3. 玩家1用道具
        elif player == player1 and hp_large in player.get_all_items():
            hp_large.use(player)
            player.inventory[hp_large.name].remove(hp_large)
        # 4. 玩家2尝试逃跑 (演示逃跑逻辑)
        else:
            print(f"{player.name} 尝试逃跑！")
            roll_res = roll_detail("1d20")
            escape_check = roll_res["total"] + player.agility
            if escape_check >= 15:  # 设定成功逃脱阈值
                print(f"{player.name} 成功逃脱战斗！")
                battle_mgr.players.remove(player)
            else:
                print(f"{player.name} 逃跑失败！")

# 替换BattleManager.player_turn方法为自动演示
battle.player_turn = lambda: auto_demo_turn(battle)

# --------------------------
# 开始战斗
# --------------------------
battle.start_battle()
