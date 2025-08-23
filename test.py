from game.Map.map import Map, Tile
from game.Skill.skill import Skill
from game.Event.battle import BattleEvent
from game.Entity.entityfactory import EntityFactory
from game.Item.item import Weapon, HPPotion
from game.Team.team import Team
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
        # TODO:优劣势检定
        dmg_res = roll_detail("2d6")
        damage = dmg_res.total + (user.INT - 10)//2
        target = target[0] if isinstance(target, list) else target
        target.take_damage(damage)
        return damage

    fireball = Skill(
        "火球术",
        effect_func=fireball_damage,
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
            # TODO:优劣势检定
            dmg_res = roll_detail("1d6")  # 示例伤害
            damage = dmg_res.total + (user.STR - 10)//2
            t.take_damage(damage)
            results.append((t, damage))
        return results

    whirlwind = Skill(
        "旋风斩",
        effect_func=whirlwind_damage,
        mp_cost=3,
        target_type="aoe",
        description="对所有敌人造成旋风伤害",
        uses_per_battle=2
    )

    # --------------------------
    # 创建玩家
    # --------------------------
    player1 = EntityFactory.create_character("战士")
    player2 = EntityFactory.create_character("法师")

    # 给玩家装备武器
    sword = Weapon("铁剑", attack_bonus=2, damage_dice="1d6")
    staff = Weapon("法杖", attack_bonus=1, damage_dice="1d4")
    player1.equip(sword)
    player2.equip(staff)

    # 背包加入药水
    player1.add_item(hp_potion_small)
    player1.add_item(hp_potion_large)
    player2.add_item(hp_potion_small)

    # 技能加入玩家
    player1.learn_skill(whirlwind)
    player2.learn_skill(fireball)

    p1info = player1.info()
    p2info = player2.info()

    print(f"玩家1信息: {p1info}")
    print(f"玩家2信息: {p2info}")

    # --------------------------
    # 创建敌人
    # --------------------------
    monster1 = EntityFactory.create_monster("哥布林")
    monster2 = EntityFactory.create_monster("兽人")

    # --------------------------
    # 开始探索
    # --------------------------
    team = Team([player1, player2])
    battle_event = BattleEvent([monster1, monster2])
    game_map = Map(5, 5, team)


    game_map.grid[0][1] = Tile(event = battle_event, tile_type = "M")

    game_map.show()

    # 玩家移动
    while True:
        cmd = input("输入方向 (w/a/s/d, q退出): ")
        if cmd == "q":
            break
        moves = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}
        if cmd in moves:
            dx, dy = moves[cmd]
            team.move(dx, dy, game_map)
            game_map.show()



    # battle = BattleManager(
    #     players=[player1, player2],
    #     enemies=[monster1, monster2],
    #     mode="manual"  # 手动回合，可选择攻击/道具/技能/逃跑
    # )
    # battle.start_battle()