# ======================
# 怪物类
# ======================

from game.Entity.entity import Entity


class Monster(Entity):
    def __init__(self, exp_reward=0, currency_reward=0, item_reward=None, **kwargs):
        super().__init__(**kwargs)

        # 怪物特有
        self.exp_reward = exp_reward
        self.currency_reward = currency_reward
        self.item_reward = item_reward or []

    # 怪物掉落
    def drop_loot(self):
        return {
            "exp": self.exp_reward,
            "currency": self.currency_reward,
            "items": self.item_reward
        }

    def info(self):
        info = super().info()
        info.update({
            "exp_reward": self.exp_reward,
            "currency_reward": self.currency_reward,
            "item_reward": self.item_reward
        })
        return info