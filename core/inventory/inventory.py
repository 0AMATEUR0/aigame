class Inventory:
    def __init__(self, capacity=None):
        self.items = {}  # {item_name: [item1, item2, ...]}
        self.capacity = capacity  # 可选：格子/重量上限

    def add(self, item):
        if item.name not in self.items:
            self.items[item.name] = []
        self.items[item.name].append(item)
        print(f"获得物品：{item.name}")

    def remove(self, item_name, count=1):
        if item_name in self.items and len(self.items[item_name]) >= count:
            removed = [self.items[item_name].pop(0) for _ in range(count)]
            if not self.items[item_name]:
                del self.items[item_name]
            return removed
        else:
            print(f"物品不足：{item_name}")
            return []

    def use(self, item_name, user):
        if item_name in self.items and self.items[item_name]:
            item = self.items[item_name][0]
            if hasattr(item, "use"):
                item.use(user)
                self.remove(item_name, 1)
                print(f"{user.name} 使用了 {item_name}")
            else:
                print(f"{item_name} 不能直接使用！")
        else:
            print(f"没有找到物品：{item_name}")

    def list_items(self):
        if not self.items:
            print("背包是空的。")
            return
        print("背包：")
        for name, stack in self.items.items():
            print(f"- {name} x{len(stack)}")
