import random

from core.equipment.Item import Consumable


class BattleManager:
    def __init__(self, players, enemies, mode="auto"):
        self.players = players
        self.enemies = enemies
        self.round_num = 1
        self.mode = mode  # auto / manual

    def all_alive(self, units):
        return [u for u in units if u.is_alive()]

    def start_battle(self):
        print(f"\n战斗开始！玩家 {', '.join(p.name for p in self.players)} VS 敌人 {', '.join(e.name for e in self.enemies)}")

        while self.all_alive(self.players) and self.all_alive(self.enemies):
            print(f"\n--- 回合 {self.round_num} ---")
            self.player_turn()
            self.enemy_turn()
            self.print_status()
            self.round_num += 1

        if self.all_alive(self.players):
            print("\n玩家胜利！")
        else:
            print("\n敌人胜利！")

    def player_turn(self):
        for player in self.all_alive(self.players):
            alive_enemies = self.all_alive(self.enemies)
            if not alive_enemies:
                break

            if self.mode == "auto":
                # 自动选择攻击目标
                target = random.choice(alive_enemies)
                player.attack(target)
            else:
                # 手动回合
                while True:
                    print(f"\n{player.name} 的回合！")
                    print("敌人列表：")
                    for i, e in enumerate(alive_enemies):
                        print(f"{i + 1}. {e.name} (HP {e.hp}/{e.max_hp})")

                    print("\n背包道具：")
                    for j, item in enumerate(player.inventory):
                        print(f"{j + 1}. {item.name}")

                    print("\n动作选择：")
                    print("1. 攻击")
                    print("2. 使用道具")
                    print("3. 使用技能")  # 可以扩展技能列表

                    choice = input("请选择动作编号: ")

                    if choice == "1":
                        # 攻击
                        while True:
                            target_choice = input("选择攻击目标编号: ")
                            try:
                                idx = int(target_choice) - 1
                                if 0 <= idx < len(alive_enemies):
                                    target = alive_enemies[idx]
                                    player.attack(target)
                                    break
                                else:
                                    print("无效编号，请重新输入。")
                            except:
                                print("输入错误，请输入数字编号。")
                        break  # 完成攻击，结束回合

                    elif choice == "2":
                        # 使用道具
                        if not player.inventory:
                            print("背包为空，没有可用道具！")
                            continue
                        while True:
                            item_choice = input("选择道具编号使用: ")
                            try:
                                idx = int(item_choice) - 1
                                if 0 <= idx < len(player.inventory):
                                    item = player.inventory[idx]
                                    if isinstance(item, Consumable):
                                        item.use(player)
                                        player.inventory.pop(idx)
                                        break
                                    else:
                                        print("该物品不可使用，请重新选择。")
                                else:
                                    print("无效编号，请重新输入。")
                            except:
                                print("输入错误，请输入数字编号。")
                        break  # 完成道具使用，结束回合


                    elif choice == "3":
                        # 使用技能
                        if not player.skills:
                            print("没有可用技能！")
                            continue
                        while True:
                            print("技能列表：")
                            for i, sk in enumerate(player.skills):
                                print(f"{i + 1}. {sk.name} - {sk.description}")
                            skill_choice = input("选择技能编号: ")
                            try:
                                idx = int(skill_choice) - 1
                                if 0 <= idx < len(player.skills):
                                    skill = player.skills[idx]
                                    # 选择目标
                                    if skill.target_type == "single":
                                        for j, e in enumerate(alive_enemies):
                                            print(f"{j + 1}. {e.name} (HP {e.hp}/{e.max_hp})")
                                        target_idx = int(input("选择技能目标编号: ")) - 1
                                        if 0 <= target_idx < len(alive_enemies):
                                            skill.use(player, alive_enemies[target_idx])
                                            break
                                        else:
                                            print("无效目标编号")
                                    else:
                                        # 群体技能
                                        skill.use(player, alive_enemies)
                                        break
                                else:
                                    print("无效技能编号")
                            except:
                                print("输入错误，请输入数字编号")
                    else:
                        print("无效选择，请重新输入。")

    def enemy_turn(self):
        for enemy in self.all_alive(self.enemies):
            alive_players = self.all_alive(self.players)
            if not alive_players:
                break
            target = random.choice(alive_players)
            enemy.attack(target)

    def print_status(self):
        print("\n当前状态：")
        for p in self.players:
            print(f"玩家 {p.name}: {p.hp}/{p.max_hp} HP")
        for e in self.enemies:
            print(f"敌人 {e.name}: {e.hp}/{e.max_hp} HP")
