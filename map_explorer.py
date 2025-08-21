import json
import random
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_map(filename="map.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def ai_generate_event(tile_info: dict) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是《无疆传说》的地图探索事件生成器。"},
                {"role": "user", "content": f"玩家进入 {tile_info['terrain']}，请生成一个简短事件。"}
            ],
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI事件生成失败，启用本地兜底] 错误：{e}")
        return tile_info["event"]

def explore_map(map_data: dict):
    x, y = 0, 0
    width, height = map_data["width"], map_data["height"]

    print(f"你现在在地图的起点 ({x}, {y})")
    while True:
        command = input("移动方向 (w:上 s:下 a:左 d:右, q:退出): ").strip().lower()
        if command == "q":
            print("探索结束。")
            break
        elif command == "w" and y > 0: y -= 1
        elif command == "s" and y < height - 1: y += 1
        elif command == "a" and x > 0: x -= 1
        elif command == "d" and x < width - 1: x += 1
        else:
            print("无法移动。")
            continue

        tile = map_data["tiles"][y][x]
        print(f"你来到了 ({x}, {y}) - {tile['terrain']}")
        event = ai_generate_event(tile)
        print(f"事件：{event}")

if __name__ == "__main__":
    map_data = load_map()
    
    explore_map(map_data)
