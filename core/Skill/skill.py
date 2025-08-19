class Skill:
    def __init__(self, name, damage_func=None, mp_cost=0, target_type="single",
                 description="", uses_per_battle=None):
        """
        name: 技能名
        damage_func: 函数，接受使用者和目标，返回伤害数值
        mp_cost: 消耗的魔法值
        target_type: "single" 或 "aoe"
        description: 技能描述
        uses_per_battle: 每场战斗可使用次数（None 表示无限）
        """
        self.name = name
        self.damage_func = damage_func
        self.mp_cost = mp_cost
        self.target_type = target_type
        self.description = description
        self.uses_per_battle = uses_per_battle
        self.remaining_uses = uses_per_battle  # 初始化时等于最大值

    def reset_uses(self):
        """在新战斗开始时重置次数"""
        self.remaining_uses = self.uses_per_battle

    def use(self, user, targets):
        # 🔹 检查环数
        if self.uses_per_battle is not None:
            if self.remaining_uses <= 0:
                print(f"{user.name} 尝试使用 {self.name}，但是已经没有使用次数了！")
                return False

        # 🔹 检查 MP
        if user.mp < self.mp_cost:
            print(f"{user.name} 尝试使用 {self.name}，但魔力不足！（需要 {self.mp_cost} MP，当前 {user.mp} MP）")
            return False

        # 🔹 扣除 MP & 环数
        user.mp -= self.mp_cost
        if self.uses_per_battle is not None:
            self.remaining_uses -= 1

        print(f"{user.name} 使用 {self.name}！（消耗 {self.mp_cost} MP，剩余 {user.mp}/{user.max_mp} MP；剩余次数 {self.remaining_uses if self.uses_per_battle is not None else '∞'}）")

        # 🔹 处理目标
        if self.target_type == "single":
            targets = [targets] if not isinstance(targets, list) else targets

        for target in targets:
            damage = self.damage_func(user, target) if self.damage_func else 0
            target.take_damage(damage, source=user)
            print(f"{target.name} 受到了 {damage} 点伤害！（{target.hp}/{target.max_hp} HP）")

        return True
