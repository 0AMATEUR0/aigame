from game import Item
import copy


class Inventory:
    def __init__(self, capacity: int = 20, max_weight: float = 100.0):
        """
        :param capacity: 最大格子数
        :param max_weight: 最大承重
        """
        self.capacity = capacity
        self.max_weight = max_weight
        self.items = []  # [{"item": Item(...), "quantity": 5}]

    # ----------------- 基本属性 -----------------
    def current_weight(self) -> float:
        """计算当前总重量"""
        return sum(slot["item"].weight * slot["quantity"] for slot in self.items)

    def is_full(self) -> bool:
        """判断是否格子用完（不考虑堆叠是否还能继续放）"""
        return len(self.items) >= self.capacity

    # ----------------- 添加物品 -----------------
    def add(self, item: Item, quantity: int = 1):
        """往背包添加物品，原子操作（要么全成功，要么不加）"""
        if not item.stackable and quantity > 1:
            return False, f"{item.name} 不可堆叠"

        # 保存原始数量用于返回信息
        add_total = quantity

        # 超重检查
        if self.current_weight() + item.weight * quantity > self.max_weight:
            return False, "超出背包最大承重"

        # 模拟操作（避免加一半失败）
        remain = quantity
        temp_slots = copy.deepcopy(self.items)

        if item.stackable:
            # 优先填充已有堆
            for slot in temp_slots:
                if slot["item"].id == item.id:  # 用唯一ID判断更安全
                    can_add = min(remain, item.max_stack - slot["quantity"])
                    slot["quantity"] += can_add
                    remain -= can_add
                    if remain == 0:
                        break
            # 还剩下 → 新开堆
            while remain > 0 and len(temp_slots) < self.capacity:
                add_amount = min(remain, item.max_stack)
                temp_slots.append({"item": item, "quantity": add_amount})
                remain -= add_amount
        else:
            # 不可堆叠
            if len(temp_slots) >= self.capacity:
                return False, "背包格子不足"
            temp_slots.append({"item": item, "quantity": 1})
            remain -= 1

        if remain > 0:
            return False, "背包格子不足"

        # 模拟成功 → 真正写入
        self.items = temp_slots
        return True, f"已添加 {item.name} * {add_total}"

    # ----------------- 移除物品 -----------------
    def remove(self, item: Item, quantity: int = 1):
        """移除物品，原子操作"""
        total_have = sum(slot["quantity"] for slot in self.items if slot["item"].id == item.id)
        if total_have < quantity:
            return False, f"{item.name} 数量不足，未能移除 {quantity} 个"

        to_remove = quantity
        for slot in self.items[:]:  # 用切片复制避免遍历时修改
            if slot["item"].id == item.id:
                if slot["quantity"] > to_remove:
                    slot["quantity"] -= to_remove
                    return True, f"已移除 {item.name} * {quantity}"
                else:
                    to_remove -= slot["quantity"]
                    self.items.remove(slot)
                    if to_remove == 0:
                        return True, f"已移除 {item.name} * {quantity}"

    # ----------------- 查询 -----------------
    def list_items(self):
        """列出所有物品"""
        return [(slot["item"].name, slot["quantity"]) for slot in self.items]

    def find(self, item_name: str):
        """按名称查找物品（可能有多堆）"""
        return [slot for slot in self.items if slot["item"].name == item_name]
