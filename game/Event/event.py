# === 事件系统 ===
from typing import List

from game.Entity.monster import Monster
from game.Event.battle import BattleManager
from game.Team.team import Team


class Event:
    def __init__(self, description: str = "", repeatable=False):
        self.description = description
        self.repeatable = repeatable
        self.triggered = False

    def trigger(self, team: Team):
        print(f"事件触发: {self.description}")


class BattleEvent(Event):
    def __init__(self, monsters: List[Monster], description: str = ""):
        super().__init__(description)
        self.monsters = monsters

    def trigger(self, team: Team):
        if self.triggered:
            print("⚠️ 战斗事件已解决，无法再次触发。")
            return

        battle = BattleManager(
            players=team.members,
            enemies=self.monsters,
            mode="manual"  # 手动回合，可选择攻击/道具/技能/逃跑
        )
        battle.start_battle()

        if not team.is_alive():
            print("💀 游戏结束")
        else:
            reward = battle.reward or {}
            print(f"🎉 战斗胜利！奖励: {reward}")

            # 取得经验
            exp = reward.get("exp", 0)
            if exp > 0:
                team.gain_experience(exp)

            # 取得货币
            money = reward.get("currency", 0)
            if money > 0:
                team.gain_currency(money)

            # 掉落物品
            items = reward.get("items", [])
            if not isinstance(items, list):
                items = []
            items = [i for i in items if i]  # ✅ 清理掉 [] 或 None

            for item in items:
                choice = input(f"是否拾取 {item.name}? (y/n): ")
                if choice.lower() == "y":
                    team.gain_item(item)

            # 进入分配逻辑
            to_distribute = team.inventory.items[:]  # 复制内部列表
            for item in to_distribute:
                allocated = False
                while not allocated:
                    print(f"\n准备分配：{item.name}")
                    for i, member in enumerate(team.members):
                        print(f"{i}. {member.name} (已有 {len(member.inventory)} 件物品)")
                    print("s. 跳过 / 保存到队伍公用背包")

                    target = input("请输入要分配的角色编号：")
                    if target.lower() == "s" or target.strip() == "":
                        print(f"物品 {item.name} 保存在队伍背包")
                        allocated = True
                        continue

                    if target.isdigit():
                        idx = int(target)
                        if 0 <= idx < len(team.members):
                            success, msg = team.members[idx].inventory.add(item)
                            if success:
                                print(f"角色 {team.members[idx].name} 获得物品 {item.name}")
                                team.inventory.remove(item)  # 从队伍背包中删除
                                allocated = True
                            else:
                                print(f"物品分配失败：{msg}，请重新选择。")
                        else:
                            print("无效编号，请重新输入。")
                    else:
                        print("输入无效，请输入数字或 s。")

        self.triggered = True


class StoryEvent(Event):
    def trigger(self, team: Team):
        print(f"📖 剧情事件: {self.description}")