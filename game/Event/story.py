from game.Event.event import Event
from game.Map.map import Tile
from game.Team.team import Team


class StoryEvent(Event):
    def trigger(self, team: Team, tile: Tile):
        print(f"📖 剧情事件: {self.description}")