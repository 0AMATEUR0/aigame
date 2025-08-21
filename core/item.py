class Item:
    def __init__(self, name, item_type="其他", rarity="普通"):
        self.name = name
        self.type = item_type
        self.rarity = rarity

def create_preset_item(item_type):
    # 创建预设物品
    if item_type == "药水":
        return Item("生命药水", "药水")
    elif item_type == "武器":
        return Item("铁剑", "武器")
    elif item_type == "护甲":
        return Item("皮甲", "护甲")
    else:
        return Item("未知物品")
