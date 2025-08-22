import os, json, random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_ai_map(prompt: str, width: int = 5, height: int = 5) -> dict:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "你是《无疆传说》的世界地图生成器。"},
                {"role": "user", "content": f"根据提示生成一张 {width}x{height} 的DND地图，内容包括地形、特殊区域、每个格子的事件。提示：{prompt}"}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
        if content is None:
            print("[AI返回内容为空，启用本地兜底]")
            return generate_fallback_map(width, height)
        map_data = json.loads(content)
        return map_data
    except Exception as e:
        print(f"[AI地图生成失败，启用本地兜底] 错误：{e}")
        return generate_fallback_map(width, height)

def generate_fallback_map(width: int, height: int) -> dict:
    terrains = ["平原", "森林", "山脉", "河流", "遗迹", "村庄"]
    events = [
        "你遇到了一群旅行商人。",
        "一只野兽从灌木丛中跳出！",
        "你发现了一处遗迹，似乎藏着秘密。",
        "前方的道路被倒下的树木挡住。",
        "一个神秘的流浪者正在等你。"
    ]
    map_data = {"width": width, "height": height, "tiles": []}
    for y in range(height):
        row = []
        for x in range(width):
            row.append({
                "x": x,
                "y": y,
                "terrain": random.choice(terrains),
                "event": random.choice(events)
            })
        map_data["tiles"].append(row)
    return map_data

def save_map_to_json(map_data: dict, filename: str = "map.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(map_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    prompt = input("请输入地图生成提示词: ")
    map_data = generate_ai_map(prompt)
    save_map_to_json(map_data)
    print("地图已保存到 map.json ✅")
