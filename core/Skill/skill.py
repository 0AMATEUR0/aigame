import math

class Skill:
    def __init__(self, name, effect_func=None, mp_cost=0, target_type="single",
                 description="", uses_per_battle=None, effect_type="damage"):
        self.name = name
        self.effect_func = effect_func  # ✅ 泛用效果函数
        self.mp_cost = mp_cost
        self.target_type = target_type  # "single" / "all"
        self.description = description
        self.uses_per_battle = uses_per_battle
        self.remaining_uses = None
        self.effect_type = effect_type  # "damage" / "heal" / "buff" / "debuff"
        self.reset_uses()

    def reset_uses(self):
        self.remaining_uses = self.uses_per_battle if self.uses_per_battle is not None else float("inf")

    def use(self, user, targets):
        # ---------------- 检查次数 / MP ----------------
        if self.remaining_uses <= 0:
            print(f"{user.name} 尝试使用 {self.name}，但是已经没有使用次数了！")
            return False
        if user.mp < self.mp_cost:
            print(f"{user.name} 尝试使用 {self.name}，魔力不足！（需要 {self.mp_cost} MP，当前 {user.mp} MP）")
            return False

        user.mp -= self.mp_cost
        if not math.isinf(self.remaining_uses):
            self.remaining_uses -= 1
        uses_left = self.remaining_uses if not math.isinf(self.remaining_uses) else "∞"
        print(f"{user.name} 使用 {self.name}！（消耗 {self.mp_cost} MP，剩余 {user.mp}/{user.max_mp} MP；剩余次数 {uses_left}）")

        # ---------------- 效果处理 ----------------
        if not isinstance(targets, list):
            targets = [targets]

        # 交给外部定义的 effect_func
        if self.effect_func:
            self.effect_func(user, targets)

        return True

    def get_info(self):
        return {
            "name": self.name,
            "description": self.description,
            "mp_cost": self.mp_cost,
            "target_type": self.target_type,
            "uses_per_battle": self.uses_per_battle,
            "remaining_uses": self.remaining_uses if not math.isinf(self.remaining_uses) else "∞",
            "effect_type": self.effect_type
        }
