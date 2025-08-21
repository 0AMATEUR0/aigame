import json

class EventManager:
    def __init__(self, event_file, monster_file):
        with open(event_file, "r") as f:
            self.events = json.load(f)
        with open(monster_file, "r") as f:
            self.monsters = {m["name"]: m for m in json.load(f)}

    def check_event(self, tile):
        # 简化逻辑：tile 对应事件
        for event in self.events:
            if event["type"] in tile:
                return event
        return None

    def resolve_event(self, event):
        if event["type"] == "battle":
            monster = self.monsters[event["monster"]]
            return f"Battle with {monster['name']} starts! Reward: {event['reward']}"
        elif event["type"] == "treasure":
            return f"Found {event['item']}! Reward: {event['reward']}"
