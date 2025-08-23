# === 地图系统 ===
from game.Inventory.inventory import Inventory


class Tile:
    def __init__(self, walkable=True, event=None, tile_type="."):
        self.walkable = walkable
        self.event = event
        self.tile_type = tile_type  # "." 空地, "M" 怪物, "S" 商店, "T" 宝物等
        self.explored = False       # 是否已探索过（Fog of War 用）
        self.inventory = Inventory(capacity=float("inf"), max_weight=float("inf"))


class Map:
    def __init__(self, width, height, team):
        self.width = width
        self.height = height
        self.grid = [[Tile() for _ in range(width)] for _ in range(height)]
        self.team = team

    def show(self):
        tx, ty = self.team.position
        for y in range(self.height):
            row = ""
            for x in range(self.width):
                tile = self.grid[y][x]
                # 计算与队伍的距离
                dist = abs(tx - x) + abs(ty - y)
                if dist <= self.team.vision:
                    tile.explored = True
                    if (x, y) == (tx, ty):
                        row += "P "  # 玩家位置
                    else:
                        row += tile.tile_type + " "
                else:
                    row += "? " if not tile.explored else ". "
            print(row)
