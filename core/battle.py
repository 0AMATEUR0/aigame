import math
import random
from core.equipment.Item import Consumable

class BattleManager:
    def __init__(self, players, enemies, mode="auto", log_callback=None):
        self.players = players
        self.enemies = enemies
        self.round_num = 1
        self.mode = mode  # auto / manual
        self.log_callback = log_callback  # 用于前端或界面接收日志
        self.log = []  # 保存战斗日志

    # 日志输出
    def log_msg(self, msg):
        self.log.append(msg)
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(msg)

    # 存活单位
    def all_alive(self, units):
        return [u for u in units if u.is_alive()]

    # 战斗开始
    def start_battle(self):
        self.log_msg(f"\n战斗开始！玩家 {', '.join(p.name for p in self.players)} VS 敌人 {', '.join(e.name for e in self.enemies)}")

        while self.all_alive(self.players) and self.all_alive(self.enemies):
            self.log_msg(f"\n--- 回合 {self.round_num} ---")
            self.player_turn()
            self.enemy_turn()
            self.print_status()
            self.round_num += 1

        if self.all_alive(self.players):
            self.log_msg("\n玩家胜利！")
        else:
            self.log_msg("\n敌人胜利！")

    # ------------------
    # 玩家回合
    # ------------------
    # ------------------ 玩家回合 ------------------
    def player_turn(self):
        escaped_players = []
        for player in self.all_alive(self.players):
            alive_enemies = self.all_alive(self.enemies)
            if not alive_enemies:
                break

            if self.mode == "auto":
                target = random.choice(alive_enemies)
                player.attack(target)
                continue

            # 手动回合
            while True:
                self.log_msg(f"\n{player.name} 的回合！")

                # 显示敌人
                self.log_msg("敌人列表：")
                for i, e in enumerate(alive_enemies):
                    self.log_msg(f"{i + 1}. {e.name} (HP {e.hp}/{e.max_hp})")

                # 显示背包道具
                self.log_msg("\n背包道具：")
                items_list = player.inventory.list_items()
                if items_list:
                    for j, item in enumerate(items_list):
                        self.log_msg(f"{j + 1}. {item.name}")
                else:
                    self.log_msg("无可用道具")

                # 动作选择
                self.log_msg("\n动作选择：1. 攻击  2. 使用道具  3. 使用技能  4. 逃跑")
                choice = input("请选择动作编号: ")

                # ----------------------- 攻击 -----------------------
                if choice == "1":
                    while True:
                        target_choice = input("选择攻击目标编号: ")
                        try:
                            idx = int(target_choice) - 1
                            if 0 <= idx < len(alive_enemies):
                                target = alive_enemies[idx]
                                player.attack(target)
                                break
                            else:
                                self.log_msg("无效编号，请重新输入。")
                        except:
                            self.log_msg("输入错误，请输入数字编号。")
                    break

                # ----------------------- 道具 -----------------------
                elif choice == "2":
                    if not items_list:
                        self.log_msg("背包为空，没有可用道具！")
                        continue
                    while True:
                        item_choice = input("选择道具编号使用: ")
                        try:
                            idx = int(item_choice) - 1
                            if 0 <= idx < len(items_list):
                                item = items_list[idx]
                                if isinstance(item, Consumable):
                                    item.use(player)
                                    player.inventory.remove(item.name, 1)
                                    self.log_msg(f"{player.name} 使用了 {item.name}")
                                    break
                                else:
                                    self.log_msg("该物品不可使用，请重新选择。")
                            else:
                                self.log_msg("无效编号，请重新输入。")
                        except:
                            self.log_msg("输入错误，请输入数字编号")
                    break

                # ----------------------- 技能 -----------------------
                elif choice == "3":
                    if not player.skills:
                        self.log_msg("没有可用技能！")
                        continue
                    while True:
                        self.log_msg("技能列表：")
                        for i, sk in enumerate(player.skills):
                            uses_left = sk.remaining_uses if not math.isinf(sk.remaining_uses) else "∞"
                            self.log_msg(f"{i + 1}. {sk.name} - {sk.description} (剩余次数 {uses_left})")
                        try:
                            idx = int(input("选择技能编号: ")) - 1
                            if 0 <= idx < len(player.skills):
                                skill = player.skills[idx]

                                # 单体技能
                                if skill.target_type == "single":
                                    while True:
                                        for j, e in enumerate(alive_enemies):
                                            self.log_msg(f"{j + 1}. {e.name} (HP {e.hp}/{e.max_hp})")
                                        try:
                                            target_idx = int(input("选择技能目标编号: ")) - 1
                                            if 0 <= target_idx < len(alive_enemies):
                                                target = alive_enemies[target_idx]
                                                skill.use(player, target)
                                                break
                                            else:
                                                self.log_msg("无效目标编号")
                                        except:
                                            self.log_msg("输入错误，请输入数字编号")
                                    break

                                # 群体技能
                                else:
                                    skill.use(player, alive_enemies)
                                    break
                            else:
                                self.log_msg("无效技能编号")
                        except:
                            self.log_msg("输入错误，请输入数字编号")
                    break

                # ----------------------- 逃跑 -----------------------
                elif choice == "4":
                    alive_enemies = self.all_alive(self.enemies)
                    if not alive_enemies:
                        self.log_msg("没有敌人可以逃跑！")
                        continue
                    enemy_agility_avg = sum(e.agility for e in alive_enemies) // len(alive_enemies)
                    escape_roll = random.randint(1, 20) + player.agility
                    self.log_msg(
                        f"{player.name} 尝试逃跑：d20 + 敏捷({player.agility}) = {escape_roll} vs 敌方敏捷平均 {enemy_agility_avg}")
                    if escape_roll >= enemy_agility_avg:
                        self.log_msg(f"🏃 {player.name} 成功逃脱战斗！")
                        escaped_players.append(player)
                    else:
                        self.log_msg(f"❌ {player.name} 逃跑失败！")
                    break

                else:
                    self.log_msg("无效选择，请重新输入。")

        # 回合结束后移除逃跑玩家
        for player in escaped_players:
            if player in self.players:
                self.players.remove(player)

    # ------------------
    # 敌人回合
    # ------------------
    def enemy_turn(self):
        for enemy in self.all_alive(self.enemies):
            alive_players = self.all_alive(self.players)
            if not alive_players:
                break
            target = random.choice(alive_players)
            enemy.attack(target)

    # ------------------
    # 当前状态
    # ------------------
    def print_status(self):
        self.log_msg("\n当前状态：")
        for p in self.players:
            self.log_msg(f"玩家 {p.name}: {p.hp}/{p.max_hp} HP, {p.mp}/{p.max_mp} MP")
        for e in self.enemies:
            self.log_msg(f"敌人 {e.name}: {e.hp}/{e.max_hp} HP")
