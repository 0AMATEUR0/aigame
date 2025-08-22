import math

class Skill:
    """
    技能类 Skill
    ---------------------
    泛用技能框架，可用于 RPG / DnD 风格游戏。
    支持：
        - 单体 / 群体技能
        - 消耗魔力 (MP)
        - 每战次数限制
        - 外部定义的效果函数 effect_func
        - 技能类型标记 (伤害/治疗/增益/减益)
    """

    def __init__(self, name, effect_func=None, mp_cost=0, target_type="single",
                 description="", uses_per_battle=None, effect_type="damage"):
        """
        初始化技能

        参数：
        - name: 技能名称
        - effect_func: 技能效果函数，函数签名 effect_func(user, targets)
        - mp_cost: 消耗魔力值
        - target_type: 技能目标类型 "single" 或 "all"
        - description: 技能描述，用于 UI / 日志
        - uses_per_battle: 每战可用次数，如果 None 表示无限次
        - effect_type: 技能类型标签，用于 UI / AI 判断，"damage"/"heal"/"buff"/"debuff"
        """
        self.name = name
        self.effect_func = effect_func
        self.mp_cost = mp_cost
        self.target_type = target_type
        self.description = description
        self.uses_per_battle = uses_per_battle
        self.remaining_uses = None  # 战斗中剩余使用次数
        self.effect_type = effect_type
        self.reset_uses()  # 初始化剩余次数

    def reset_uses(self):
        """
        重置技能使用次数
        - 在每场战斗开始时调用
        - 无限次数技能会设为 float("inf")
        """
        self.remaining_uses = self.uses_per_battle if self.uses_per_battle is not None else float("inf")

    def use(self, user, targets):
        """
        使用技能

        参数：
        - user: 施法者对象
        - targets: 技能目标，可以是单个对象或列表

        返回：
        - dict，包含技能使用结果和信息
        """
        # ---------------- 使用次数 / MP 检查 ----------------
        if self.remaining_uses <= 0:
            return {"success": False, "msg": f"{user.name} 尝试使用 {self.name}，但是已经没有使用次数了！"}
        if getattr(user, "MP", getattr(user, "mp", 0)) < self.mp_cost:
            return {"success": False, "msg": f"{user.name} 魔力不足！（需要 {self.mp_cost} MP）"}

        # 扣除 MP
        user.MP -= self.mp_cost if hasattr(user, "MP") else self.mp_cost
        if not math.isinf(self.remaining_uses):
            self.remaining_uses -= 1  # 扣除技能使用次数

        # ---------------- 目标处理 ----------------
        if not isinstance(targets, list):
            targets = [targets]  # 确保 targets 为列表
        if self.target_type == "single" and len(targets) > 1:
            return {"success": False, "msg": f"{self.name} 只能对单一目标使用！"}

        # ---------------- 执行技能效果 ----------------
        result = None
        if self.effect_func:
            result = self.effect_func(user, targets)  # 调用外部定义的技能效果函数

        # 如果没有 effect_func，默认返回成功消息
        return result or {"success": True, "msg": f"{user.name} 使用了 {self.name}"}

    def get_info(self):
        """
        获取技能信息
        返回字典，便于 UI / 调试使用
        """
        return {
            "name": self.name,
            "description": self.description,
            "mp_cost": self.mp_cost,
            "target_type": self.target_type,
            "uses_per_battle": self.uses_per_battle,
            "remaining_uses": self.remaining_uses if not math.isinf(self.remaining_uses) else "∞",
            "effect_type": self.effect_type
        }
