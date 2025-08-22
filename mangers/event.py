import random
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# ---------------- 初始化 ----------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------------- 本地兜底事件库 ----------------
LOCAL_EVENTS = {
    "战斗": [
        {"type":"战斗", "description":"遇到敌人攻击！", "extra":{"monster_type":"狼"}},
        {"type":"战斗", "description":"敌对NPC伏击你！", "extra":{"monster_type":"盗贼"}}
    ],
    
}

# ---------------- 事件生成 ----------------
def ai_generate_event(tile_info):
    """尝试使用AI生成事件，失败则使用本地兜底"""
    try:
        prompt = f"""
你是《无疆传说》的地图探索事件生成器。
玩家当前格子信息：{tile_info}
生成事件，JSON格式：{{"type":"战斗/掉落/线索/陷阱/谜题/普通","description":"事件描述","extra":{{可选附加信息}}}}
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
        # AI失败使用本地兜底
        print(f"[AI事件生成失败，启用本地事件] 错误: {e}")
        event_type = random.choice(list(LOCAL_EVENTS.keys()))
        return random.choice(LOCAL_EVENTS[event_type])

# ---------------- 事件触发 ----------------
def trigger_event(event_info, player, battle_func, item_func):
    """
    触发单个事件
    battle_func(player, monster_type)
    item_func(item_type) -> 返回item对象，可加入player.inventory
    """
    event_type = event_info.get("type","普通")
    desc = event_info.get("description","无描述事件")
    extra = event_info.get("extra",{})

    print(f"\n[事件] 类型: {event_type} | 描述: {desc}")

    if event_type == "战斗":
        monster_type = extra.get("monster_type", "普通野兽")
        battle_func(player, monster_type)
    elif event_type == "掉落":
        item_type = extra.get("item_type", random.choice(["药水","武器","护甲"]))
        rarity = extra.get("rarity", random.choice(["普通","稀有","史诗"]))
        item = item_func(item_type)
        item.rarity = rarity
        print(f"获得道具: {rarity} {item.name}")
        player.inventory.add(item)
    elif event_type == "线索":
        clue = extra.get("clue_detail", desc)
        if hasattr(player,"add_clue"):
            player.add_clue(clue)
        print(f"获得线索: {clue}")
    elif event_type == "陷阱":
        print("触发陷阱! 请谨慎行动。")
    elif event_type == "谜题":
        print("出现谜题! 需要玩家解答或触发检定。")
    else:
        print("普通事件，无特殊操作。")

# ---------------- 每格事件处理 ----------------
def handle_tile_events(tile, player, battle_func, item_func, max_trigger=2):
    """
    每格触发事件，优先AI事件，如无AI事件可从本地兜底
    battle_func / item_func 为具体的回调函数
    """
    events = tile.get("events", [])
    if not events:
        event_info = ai_generate_event(tile)
        trigger_event(event_info, player, battle_func, item_func)
        return

    trigger_count = min(len(events), max_trigger)
    triggered = random.sample(events, trigger_count)

    for ev in triggered:
        event_info = ai_generate_event(ev)
        trigger_event(event_info, player, battle_func, item_func)
        tile["events"].remove(ev)
