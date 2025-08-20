import math

class Skill:
    def __init__(self, name, damage_func=None, mp_cost=0, target_type="single",
                 description="", uses_per_battle=None):
        self.name = name
        self.damage_func = damage_func
        self.mp_cost = mp_cost
        self.target_type = target_type
        self.description = description
        self.uses_per_battle = uses_per_battle
        self.remaining_uses = None
        self.reset_uses()

    def reset_uses(self):
        self.remaining_uses = self.uses_per_battle if self.uses_per_battle is not None else float("inf")

    def use(self, user, targets):
        # 检查次数
        if self.remaining_uses <= 0:
            print(f"{user.name} 尝试使用 {self.name}，但是已经没有使用次数了！")
            return False
        # 检查 MP
        if user.mp < self.mp_cost:
            print(f"{user.name} 尝试使用 {self.name}，魔力不足！（需要 {self.mp_cost} MP，当前 {user.mp} MP）")
            return False

        user.mp -= self.mp_cost
        if not math.isinf(self.remaining_uses):
            self.remaining_uses -= 1
        uses_left = self.remaining_uses if not math.isinf(self.remaining_uses) else "∞"
        print(f"{user.name} 使用 {self.name}！（消耗 {self.mp_cost} MP，剩余 {user.mp}/{user.max_mp} MP；剩余次数 {uses_left}）")

        # 统一处理 targets 列表
        if not isinstance(targets, list):
            targets = [targets]

        if self.target_type == "single":
            # 单体技能，damage_func 返回整数
            target = targets[0]
            damage = self.damage_func(user, target) if self.damage_func else 0
            damage = max(0, damage or 0)
            target.take_damage(damage, source=user)
            print(f"{target.name} 受到了 {damage} 点伤害！（{target.hp}/{target.max_hp} HP）")
        else:
            # 群体技能，damage_func 返回列表 [(target, damage), ...]
            damage_results = self.damage_func(user, targets) if self.damage_func else []
            for t, dmg in damage_results:
                dmg = max(0, dmg or 0)
                t.take_damage(dmg, source=user)
                print(f"{t.name} 受到了 {dmg} 点伤害！（{t.hp}/{t.max_hp} HP）")

        return True
