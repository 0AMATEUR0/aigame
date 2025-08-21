import json
import os
import random
from openai import OpenAI
from dotenv import load_dotenv

# ---------------- DnD 模块导入 ----------------
from core.character import Character
from core.battle import start_battle    # 确保 core/battle.py 文件存在
from core.item import create_preset_item   # 装备模块
# from core.dice import roll_check      # 检定模块，可选

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- 本地兜底 ----------------
DEFAULT_TERRAINS = ["平原", "森林", "山地", "湖泊", "废墟", "洞穴", "外星飞船残骸"]
DEFAULT_EVENTS = [
    "你发现了一些奇怪的脚印。",
    "这里静悄悄的，似乎有什么在观察你。",
    "地面上有一些闪烁的物品。",
    "你听到远处传来低沉的声响。",
    "你找到一个古老的遗迹入口。"
]

# ---------------- 地图生成 ----------------
def ai_generate_map(prompt, width=5, height=5):
    try:
        ai_prompt = f"""
用户提示词：{prompt}
生成 {width}x{height} 地图，返回严格JSON：
{{"map_name":"...", "width":..., "height":..., "tiles":[[{{"terrain":"...", "event":"..."}}]]}}
不要输出说明文字，只返回JSON。
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content": ai_prompt}],
            temperature=0.8
        )
        content = response.choices[0].message.content
        raw = content.strip() if content else "{}"
        map_data = json.loads(raw)
        for y in range(map_data["height"]):
            for x in range(map_data["width"]):
                tile = map_data["tiles"][y][x]
                if "event" not in tile:
                    tile["event"] = random.choice(DEFAULT_EVENTS)
                tile["events"] = [{"description": tile["event"], "type":"普通","extra":{}}]
        return map_data
    except Exception as e:
        print(f"[AI地图生成失败，启用本地兜底] 错误: {e}")
        tiles = []
        for y in range(height):
            row = []
            for x in range(width):
                terrain = random.choice(DEFAULT_TERRAINS)
                event = random.choice(DEFAULT_EVENTS)
                row.append({"terrain": terrain, "event": event, "events":[{"description": event,"type":"普通","extra":{}}]})
            tiles.append(row)
        return {"map_name": prompt, "width": width, "height": height, "tiles": tiles}

def save_map_json(map_data, filename="map.json"):
    with open(filename,"w",encoding="utf-8") as f:
        json.dump(map_data,f,ensure_ascii=False,indent=2)

def load_map(filename="map.json"):
    if not os.path.exists(filename):
        print(f"[警告] {filename} 不存在，请先生成地图。")
        return None
    with open(filename,"r",encoding="utf-8") as f:
        return json.load(f)

# ---------------- AI事件生成 ----------------
def ai_generate_event(tile_info):
    try:
        prompt = f"""
你是《无疆传说》的地图探索事件生成器。
玩家当前格子信息：{tile_info}
生成事件，JSON格式：{{"type":"战斗/掉落/线索/其他","description":"事件描述","extra":{{可选附加信息}}}}
不要输出其他文字
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            temperature=0.8
        )
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[AI事件生成失败，启用本地事件] 错误: {e}")
        return {"type":"普通","description": tile_info.get("event","你什么也没有发现。"), "extra":{}}

# ---------------- 事件触发 ----------------
def handle_event(event_info, player):
    event_type = event_info.get("type","普通")
    desc = event_info.get("description","无描述事件")
    extra = event_info.get("extra",{})

    print(f"\n事件类型：{event_type}")
    print(f"事件描述：{desc}")

    if event_type == "战斗":
        monster_type = extra.get("monster_type","普通野兽")
        print(f"[触发战斗模块] 怪物类型：{monster_type}")
        start_battle(player, monster_type)
    elif event_type == "掉落":
        item_type = extra.get("item_type", random.choice(["药水","武器","护甲"]))
        rarity = extra.get("rarity", random.choice(["普通","稀有","史诗"]))
        item = create_preset_item(item_type)
        item.rarity = rarity
        print(f"[掉落事件] 你获得 {rarity} 道具：{item.name}")
        player.inventory.add(item)
    elif event_type == "线索":
        clue_detail = extra.get("clue_detail", desc)
        print(f"[线索事件] 你获得线索：{clue_detail}")
        player.add_clue(clue_detail)
    else:
        print("[普通事件] 无额外操作")

# ---------------- 地图可视化 ----------------
def print_map(map_data, player_pos):
    print("\n地图状态:")
    for y, row in enumerate(map_data["tiles"]):
        line = ""
        for x, tile in enumerate(row):
            if (x,y) == player_pos:
                line += "[P]"  # 玩家位置
            else:
                remaining = len(tile.get("events",[]))
                line += f"[{remaining}]"
        print(line)
    print("")

# ---------------- 探索逻辑 ----------------
def explore_map(map_data, player):
    width, height = map_data.get("width",5), map_data.get("height",5)
    x, y = 0, 0
    print(f"你现在在地图起点 (0,0)，地图名：《{map_data.get('map_name','未知地图')}》")

    while True:
        print_map(map_data, (x,y))
        cmd = input("移动方向 (w:上 s:下 a:左 d:右, q:退出): ")

        if cmd=="q":
            print("探索结束。")
            break
        elif cmd=="w" and y>0: y-=1
        elif cmd=="s" and y<height-1: y+=1
        elif cmd=="a" and x>0: x-=1
        elif cmd=="d" and x<width-1: x+=1
        else:
            print("无法移动，请重新输入。")
            continue

        tile = map_data["tiles"][y][x]
        print(f"\n你来到了 ({x},{y}) - {tile['terrain']}")

        events_list = tile.get("events", [{"description": tile.get("event","这里什么也没有。"),"type":"普通","extra":{}}])
        trigger_count = min(len(events_list), random.randint(1,2))
        triggered_events = random.sample(events_list, trigger_count)

        for ev in triggered_events:
            tile_info_for_ai = {"terrain": tile["terrain"], "event": ev.get("description","无事件")}
            event_info = ai_generate_event(tile_info_for_ai)
            handle_event(event_info, player)
            tile["events"].remove(ev)

        save_map_json(map_data)

# ---------------- 主程序 ----------------
if __name__=="__main__":
    prompt = input("请输入地图生成提示词: ").strip() or "无疆传说地图"
    width = int(input("请输入地图宽度: ") or 5)
    height = int(input("请输入地图高度: ") or 5)

    map_data = ai_generate_map(prompt, width, height)
    save_map_json(map_data)

    player = Character(name="玩家1")
    explore_map(map_data, player)
