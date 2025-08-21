import json

class MapManager:
    def __init__(self, map_file):
        with open(map_file, "r") as f:
            self.map_data = json.load(f)
        self.player_pos = [0,0]

    def move_player(self, dx, dy):
        x, y = self.player_pos
        nx, ny = x+dx, y+dy
        if 0 <= nx < len(self.map_data["tiles"]) and 0 <= ny < len(self.map_data["tiles"][0]):
            self.player_pos = [nx, ny]
        return self.get_current_tile()

    def get_current_tile(self):
        x, y = self.player_pos
        return self.map_data["tiles"][x][y]
