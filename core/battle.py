import math
import random
from core.equipment import Item
from .character import Character

class BattleManager:
    def __init__(self, players, enemies, mode="auto", log_callback=None):
        self.players = players
        self.enemies = enemies
        self.mode = mode  # auto / manual
        self.log_callback = log_callback
        self.log = []
        self.round_num = 1

    # ------------------
    # 日志方法
    # ------------------
    def log_msg(self, msg):
        self.log.append(msg)
        if self.log_callback:
            self.log_callback(msg)
        else:
            print(msg)

    # ------------------
    # 存活单位
    # ------------------
    def all_alive(self, units):
        return [u for u in units if u.is_alive()]

    # ------------------
    # 战斗开始
    # ------------------
    def start_battle(self):
        self.log_msg(f"\n战斗开始！玩家 {', '.join(p.name for p in self.players)} VS 敌人 {', '.join(e.name for e in self.enemies)}")

        while self.all_alive(self.players) and self.all_alive(self.enemies):
            self.log_msg(f"\n--- 回合 {self.round_num} ---")
            self.process_turn()
            self.print_status()
            self.round_num += 1

        if self.all_alive(self.players):
            self.log_msg("\n玩家胜利！")
        else:
            self.log_msg("\n敌人胜利！")

    # ------------------
    # 回合处理（敏捷先后）
    # ------------------
    def process_turn(self):
        units = self.all_alive(self.players + self.enemies)
        # 按敏捷排序
        units.sort(key=lambda u: getattr(u, "agility", 0), reverse=True)
        escaped_players = []

        for unit in units:
            if not unit.is_alive():
                continue
            if unit in self.players:
                escaped = self.player_turn(unit)
                if escaped:
                    escaped_players.append(unit)
            else:
                self.enemy_turn(unit)

        # 移除逃跑玩家
        for p in escaped_players:
            if p in self.players:
                self.players.remove(p)

    # ------------------
    # 玩家回合
    # ------------------
    def player_turn(self, player):
        alive_enemies = self.all_alive(self.enemies)
        if not alive_enemies:
            return False

        if self.mode == "auto":
            target = min(alive_enemies, key=lambda e: e.hp)  # 优先攻击血量最低敌人
            player.attack(target)
            return False

        # 手动回合
        while True:
            self.log_msg(f"\n{player.name} 的回合！")
            self.display_enemies()
            self.display_inventory(player)

            self.log_msg("\n动作选择：1. 攻击  2. 使用道具  3. 使用技能  4. 逃跑")
            choice = input("请选择动作编号: ")

            if choice == "1":
                self.choose_attack(player)
                break
            elif choice == "2":
                self.use_item(player)
                break
            elif choice == "3":
                self.use_skill(player)
                break
            elif choice == "4":
                return self.attempt_escape(player)
            else:
                self.log_msg("无效选择，请重新输入。")
        return False

    # ------------------
    # 敌人回合
    # ------------------
    def enemy_turn(self, enemy):
        alive_players = self.all_alive(self.players)
        if not alive_players:
            return
        target = random.choice(alive_players)
        enemy.attack(target)

    # ------------------
    # 显示敌人
    # ------------------
    def display_enemies(self):
        self.log_msg("敌人列表：")
        for i, e in enumerate(self.all_alive(self.enemies)):
            self.log_msg(f"{i + 1}. {e.name} (HP {e.hp}/{e.max_hp})")

    # ------------------
    # 显示背包
    # ------------------
    def display_inventory(self, player):
        self.log_msg("\n背包道具：")
        items_list = player.inventory.list_items()
        if items_list:
            for j, item in enumerate(items_list):
                self.log_msg(f"{j + 1}. {item.name}")
        else:
            self.log_msg("无可用道具")

    # ------------------
    # 攻击选择
    # ------------------
    def choose_attack(self, player):
        alive_enemies = self.all_alive(self.enemies)
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

    # ------------------
    # 使用道具
    # ------------------
    def use_item(self, player):
        items_list = player.inventory.list_items()
        if not items_list:
            self.log_msg("背包为空，没有可用道具！")
            return

        while True:
            item_choice = input("选择道具编号使用: ")
            try:
                idx = int(item_choice) - 1
                if 0 <= idx < len(items_list):
                    item = items_list[idx]
                    if isinstance(item, Item) and hasattr(item, 'use'):
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

    # ------------------
    # 使用技能
    # ------------------
    def use_skill(self, player):
        if not player.skills:
            self.log_msg("没有可用技能！")
            return

        while True:
            self.log_msg("技能列表：")
            for i, sk in enumerate(player.skills):
                uses_left = sk.remaining_uses if not math.isinf(sk.remaining_uses) else "∞"
                self.log_msg(f"{i + 1}. {sk.name} - {sk.description} (剩余次数 {uses_left})")
            try:
                idx = int(input("选择技能编号: ")) - 1
                if 0 <= idx < len(player.skills):
                    skill = player.skills[idx]
                    alive_enemies = self.all_alive(self.enemies)
                    if skill.target_type == "single":
                        self.choose_skill_target(player, skill, alive_enemies)
                    else:
                        skill.use(player, alive_enemies)
                    break
                else:
                    self.log_msg("无效技能编号")
            except:
                self.log_msg("输入错误，请输入数字编号")

    def choose_skill_target(self, player, skill, enemies):
        while True:
            for j, e in enumerate(enemies):
                self.log_msg(f"{j + 1}. {e.name} (HP {e.hp}/{e.max_hp})")
            try:
                target_idx = int(input("选择技能目标编号: ")) - 1
                if 0 <= target_idx < len(enemies):
                    skill.use(player, enemies[target_idx])
                    break
                else:
                    self.log_msg("无效目标编号")
            except:
                self.log_msg("输入错误，请输入数字编号")

    # ------------------
    # 逃跑尝试
    # ------------------
    def attempt_escape(self, player):
        alive_enemies = self.all_alive(self.enemies)
        if not alive_enemies:
            self.log_msg("没有敌人可以逃跑！")
            return False

        enemy_agility_avg = sum(e.agility for e in alive_enemies) // len(alive_enemies)
        escape_roll = random.randint(1, 20) + player.agility
        self.log_msg(f"{player.name} 尝试逃跑：d20 + 敏捷({player.agility}) = {escape_roll} vs 敌方敏捷平均 {enemy_agility_avg}")
        if escape_roll >= enemy_agility_avg:
            self.log_msg(f"🏃 {player.name} 成功逃脱战斗！")
            return True
        else:
            self.log_msg(f"❌ {player.name} 逃跑失败！")
            return False

    # ------------------
    # 打印状态
    # ------------------
    def print_status(self):
        self.log_msg("\n当前状态：")
        for p in self.players:
            self.log_msg(f"玩家 {p.name}: {p.hp}/{p.max_hp} HP, {p.mp}/{p.max_mp} MP")
        for e in self.enemies:
            self.log_msg(f"敌人 {e.name}: {e.hp}/{e.max_hp} HP")
