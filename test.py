from core.Skill.skill import Skill
from core.battle import BattleManager
from core.charactor import Charactor, Monster
from core.equipment.Item import Weapon, Armor, HPPotion
from utils.dice import roll

if __name__ == "__main__":
    hero = Charactor("勇者", gender="男", level=2, strength=5, agility=4, hp=20, max_hp=20)
    mage = Charactor("法师", gender="女", level=1, strength=2, agility=3, hp=12, max_hp=12, max_mp=20, mp=20)

    # 火球术 1d8 + INT
    fireball = Skill(
        name="火球术",
        damage_func=lambda user, target: roll("3d8") + user.intelligence,
        mp_cost=3,
        target_type="aoe",
        uses_per_battle = 3,
        description="对单个敌人造成智力加成伤害 (3d8 + INT)"
    )

    # 雷霆风暴 1d4 + INT 群体
    thunderstorm = Skill(
        name="雷霆风暴",
        damage_func=lambda user, target: roll("6d4") + user.intelligence,
        mp_cost=5,
        target_type="aoe",
        uses_per_battle=3,
        description="对所有敌人造成智力加成伤害 (6d4 + INT)"
    )

    mage.add_skill(fireball)
    mage.add_skill(thunderstorm)

    goblin1 = Monster("哥布林1", level=1, hp=50, max_hp=50, strength=2, agility=2, exp_reward=50)
    goblin2 = Monster("哥布林2", level=1, hp=30, max_hp=30, strength=2, agility=2, exp_reward=50)

    # # 自动战斗
    # battle = BattleManager(players=[hero, mage], enemies=[goblin1, goblin2], mode="auto")
    # battle.start_battle()

    # 手动战斗
    battle = BattleManager(players=[hero, mage], enemies=[goblin1, goblin2], mode="manual")
    battle.start_battle()