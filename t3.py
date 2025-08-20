import tkinter as tk
from tkinter import messagebox
import random
from core.Skill.skill import Skill
from core.character import Character, Monster
from core.equipment.Item import Weapon, HPPotion
from utils.dice import roll_detail

# --------------------------
# 创建示例道具和技能
# --------------------------
hp_small = HPPotion("小生命药水", heal_amount=10)
hp_large = HPPotion("大生命药水", heal_amount=25)

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
# 创建玩家和敌人
# --------------------------
player1 = Character("战士A", strength=5, agility=3, intelligence=1)
player2 = Character("法师B", strength=2, agility=3, intelligence=5)
player1.equip(Weapon("铁剑", attack_bonus=2, damage_dice="1d6"))
player2.equip(Weapon("法杖", attack_bonus=1, damage_dice="1d4"))
player1.add_skill(whirlwind)
player2.add_skill(fireball)
player1.add_item(hp_small)
player1.add_item(hp_large)
player2.add_item(hp_small)

monster1 = Monster("哥布林A", max_hp=20, strength=3, agility=2, intelligence=1)
monster2 = Monster("哥布林B", max_hp=15, strength=2, agility=3, intelligence=1)
enemies = [monster1, monster2]
players = [player1, player2]

# --------------------------
# Tkinter GUI
# --------------------------
class BattleGUI:
    def __init__(self, master):
        self.master = master
        master.title("战斗演示")
        self.log_text = tk.Text(master, height=15, width=60)
        self.log_text.pack()

        # 玩家状态
        self.player_frames = {}
        for p in players:
            frame = tk.Frame(master)
            frame.pack()
            label = tk.Label(frame, text=f"{p.name}: {p.hp}/{p.max_hp} HP, {p.mp}/{p.max_mp} MP")
            label.pack()
            self.player_frames[p] = label

        # 敌人状态
        self.enemy_frames = {}
        for e in enemies:
            frame = tk.Frame(master)
            frame.pack()
            label = tk.Label(frame, text=f"{e.name}: {e.hp}/{e.max_hp} HP")
            label.pack()
            self.enemy_frames[e] = label

        # 动作按钮
        self.action_frame = tk.Frame(master)
        self.action_frame.pack()
        self.attack_btn = tk.Button(self.action_frame, text="攻击", command=self.attack_action)
        self.attack_btn.grid(row=0, column=0)
        self.skill_btn = tk.Button(self.action_frame, text="技能", command=self.skill_action)
        self.skill_btn.grid(row=0, column=1)
        self.item_btn = tk.Button(self.action_frame, text="道具", command=self.item_action)
        self.item_btn.grid(row=0, column=2)
        self.escape_btn = tk.Button(self.action_frame, text="逃跑", command=self.escape_action)
        self.escape_btn.grid(row=0, column=3)

        self.current_player_idx = 0
        self.update_ui()

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def update_ui(self):
        for p in players:
            self.player_frames[p].config(text=f"{p.name}: {p.hp}/{p.max_hp} HP, {p.mp}/{p.max_mp} MP")
        for e in enemies:
            self.enemy_frames[e].config(text=f"{e.name}: {e.hp}/{e.max_hp} HP")

    def next_turn(self):
        self.update_ui()
        alive_players = [p for p in players if p.is_alive()]
        alive_enemies = [e for e in enemies if e.is_alive()]
        if not alive_players:
            self.log("敌人胜利！")
            self.disable_buttons()
            return
        if not alive_enemies:
            self.log("玩家胜利！")
            self.disable_buttons()
            return
        self.current_player_idx = (self.current_player_idx + 1) % len(alive_players)

    def attack_action(self):
        player = [p for p in players if p.is_alive()][self.current_player_idx]
        target = random.choice([e for e in enemies if e.is_alive()])
        player.attack(target)
        self.log(f"{player.name} 攻击 {target.name}！")
        self.next_turn()

    def skill_action(self):
        player = [p for p in players if p.is_alive()][self.current_player_idx]
        if not player.skills:
            messagebox.showinfo("提示", "没有技能可用")
            return
        skill = player.skills[0]
        alive_enemies = [e for e in enemies if e.is_alive()]
        if skill.target_type == "single":
            target = random.choice(alive_enemies)
            skill.use(player, target)
        else:
            skill.use(player, alive_enemies)
        self.log(f"{player.name} 使用 {skill.name}！")
        self.next_turn()

    def item_action(self):
        player = [p for p in players if p.is_alive()][self.current_player_idx]
        items = player.get_info().get("inventory", {})
        if not items:
            messagebox.showinfo("提示", "没有道具可用")
            return
        item = items[0]
        item.use(player)
        player.inventory[item.name].remove(item)
        self.log(f"{player.name} 使用 {item.name}！")
        self.next_turn()

    def escape_action(self):
        player = [p for p in players if p.is_alive()][self.current_player_idx]
        roll_res = roll_detail("1d20")
        escape_check = roll_res["total"] + player.agility
        if escape_check >= 15:
            self.log(f"{player.name} 成功逃跑！")
            players.remove(player)
        else:
            self.log(f"{player.name} 逃跑失败！")
        self.next_turn()

    def disable_buttons(self):
        self.attack_btn.config(state=tk.DISABLED)
        self.skill_btn.config(state=tk.DISABLED)
        self.item_btn.config(state=tk.DISABLED)
        self.escape_btn.config(state=tk.DISABLED)

# --------------------------
# 启动GUI
# --------------------------
root = tk.Tk()
app = BattleGUI(root)
root.mainloop()
