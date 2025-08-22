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

    def get_info(self):
        """
        返回物品栏信息（用于菜单或界面显示）
        格式：[ {name, count, type, extra_info}, ... ]
        """
        info_list = []
        for name, items in self.items.items():
            if not items:
                continue
            item_type = type(items[0]).__name__  # 类名，例如 Weapon, Armor, Consumable
            count = len(items)

            # 根据物品类型附加说明
            extra_info = ""
            sample = items[0]
            if hasattr(sample, "slot"):  # 装备
                if hasattr(sample, "attack_bonus"):
                    extra_info = f"攻击+{sample.attack_bonus}"
                elif hasattr(sample, "defense_bonus"):
                    extra_info = f"防御+{sample.defense_bonus}"
            elif item_type == "Consumable":
                extra_info = getattr(sample, "effect_desc", "可使用")

            info_list.append({
                "name": name,
                "count": count,
                "type": item_type,
                "extra_info": extra_info
            })

        return info_list
