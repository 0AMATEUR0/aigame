# === 事件系统 ===
from game.Map.map import Tile
from game.Team.team import Team


class Event:
    def __init__(self, description: str = "", repeatable=False):
        self.description = description
        self.repeatable = repeatable
        self.triggered = False

    def trigger(self, team: Team, tile: Tile):
        print(f"事件触发: {self.description}")
