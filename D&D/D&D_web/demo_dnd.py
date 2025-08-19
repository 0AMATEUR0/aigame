# -*- coding: utf-8 -*-
"""
AI驱动 D&D 叙事引擎（中国古代架空）Web版
- 支持 AI 或本地场景
- 每回合生成场景(JSON) -> 玩家选择 -> 检定 -> 叙事结算(JSON)
- 无数值战斗，仅叙事后果（状态/线索/物品/关系）
"""

import os, json, time, random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from flask import Flask, render_template, jsonify, request

# ---------------- 配置 ----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"
TIMEOUT = 60
RETRIES = 2
USE_AI = True if OPENAI_API_KEY else False
SAVE_FILE = "dnd_ai_save.json"

# ---------------- 工具 ----------------
def extract_json(text: str) -> str:
    if not text: raise ValueError("empty ai response")
    l, r = text.find("{"), text.rfind("}")
    if l == -1 or r == -1 or r <= l: raise ValueError("no json object")
    return text[l:r+1]

def jloads(text: str) -> dict:
    return json.loads(extract_json(text))

def backoff(i:int): time.sleep(min(2**i, 6))

# ---------------- 领域模型 ----------------
@dataclass
class Player:
    name: str = "无名侠客"
    identity: str = "行脚人"
    traits: List[str] = field(default_factory=lambda: ["谨慎","果断"])
    conditions: List[str] = field(default_factory=list)
    inventory: List[Dict[str,Any]] = field(default_factory=list)

@dataclass
class World:
    era: str = "幻朝"
    region: str = "关外群山"
    factions: List[str] = field(default_factory=lambda: ["雾隐山堂","墨家遗脉","流沙客"])
    tone: str = "写意武侠 + 玄奇志怪"

@dataclass
class GameState:
    background: str = "中国古代架空世界"
    turn: int = 1
    player: Player = field(default_factory=Player)
    world: World = field(default_factory=World)
    story_log: List[str] = field(default_factory=list)
    context: Dict[str,Any] = field(default_factory=dict)
    recent_checks: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "background": self.background,
            "turn": self.turn,
            "player": asdict(self.player),
            "world": asdict(self.world),
            "story_log": self.story_log[-200:],
            "context": self.context,
            "recent_checks": self.recent_checks[-3:],
        }

    @staticmethod
    def from_dict(d:dict):
        gs = GameState()
        gs.background = d.get("background", gs.background)
        gs.turn = d.get("turn", gs.turn)
        p = d.get("player", {}); w = d.get("world", {})
        gs.player = Player(**p) if p else Player()
        gs.world  = World(**w) if w else World()
        gs.story_log = d.get("story_log", [])
        gs.context = d.get("context", {})
        gs.recent_checks = d.get("recent_checks", [])
        return gs

# ---------------- 存档 ----------------
def save_game(s:GameState):
    with open(SAVE_FILE,"w",encoding="utf-8") as f:
        json.dump(s.to_dict(), f, ensure_ascii=False, indent=2)
    print("💾 已存档")

def load_game()->Optional[GameState]:
    try:
        with open(SAVE_FILE,"r",encoding="utf-8") as f:
            return GameState.from_dict(json.load(f))
    except FileNotFoundError:
        return None
    except Exception as e:
        print("⚠️ 读档失败：", e)
        return None

# ---------------- OpenAI ----------------
def ai_chat(messages: List[Dict[str,str]])->str:
    if not USE_AI: raise RuntimeError("AI disabled")
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    err = None
    for i in range(RETRIES+1):
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, temperature=0.9, timeout=TIMEOUT
            )
            return resp.choices[0].message.content
        except Exception as e:
            err = e; print(f"⚠️ AI失败({i+1})：{e}"); backoff(i)
    raise err

# ---------------- 装备与检定 ----------------
def gather_effect_tags(p:Player)->List[str]:
    tags = []
    for it in p.inventory:
        tags += it.get("effect_tags",[])
    return list(dict.fromkeys(tags))

def choice_advantage(choice_tags:List[str], effect_tags:List[str], conditions:List[str])->str:
    if any(t in effect_tags for t in choice_tags):
        if "疲惫" not in conditions and "受惊" not in conditions:
            return "advantage"
    if ("疲惫" in conditions and ("athletics" in choice_tags or "stealth" in choice_tags)) \
       or ("受惊" in conditions and ("social" in choice_tags or "insight" in choice_tags)):
        return "disadvantage"
    return "normal"

def roll_d20(mode:str)->int:
    a = random.randint(1,20); b = random.randint(1,20)
    if mode=="advantage": return max(a,b)
    if mode=="disadvantage": return min(a,b)
    return a

def outcome_from_roll(r:int)->str:
    if r>=15: return "成功"
    if r>=8:  return "部分成功"
    return "失败"

# ---------------- 本地兜底 ----------------
LOCAL_SCENES = [
    {
      "scene_id":"gu_yi",
      "scene":"薄雾笼旧驿，风铃自鸣，驿墙碑文残缺。",
      "env_tags":["fog","ruins","road"],
      "npcs":["挑担书生"],
      "threats":["黑衣人潜踪"],
      "clues":["碑文残句","石缝竹筒"],
      "loot":[{"name":"竹筒残简","description":"墨迹漫漶，疑似暗号。",
               "effect_tags":["insight","night"],"usage_notes":"夜读更易辨识"}],
      "choices":
      [
        {"action":"与书生闲叙打探","hint":"或得旧闻","check_tag":"social",
         "choice_tags":["social"],"leads":"书生指向荒祠"},
        {"action":"沿墙寻碑文","hint":"也许能续句","check_tag":"perception",
         "choice_tags":["perception"],"leads":"碑文指向祠庙北径"},
        {"action":"埋伏观察","hint":"耐心考验","check_tag":"stealth",
         "choice_tags":["stealth","night"],"leads":"黑影往北"}
      ]
    }
]

def local_scene()->dict:
    return random.choice(LOCAL_SCENES)

def local_resolution(choice:dict, roll:int, outcome:str)->dict:
    base = {
      "narration": f"你按计行事，气息如线；{outcome}。",
      "context_update": {"seed": choice.get("leads",""), "trail":"细碎足印"},
      "player_update": {"add_conditions":[],"remove_conditions":[],
                        "add_inventory":[],"remove_inventory":[]},
      "log_entry": f"检定{choice['check_tag']}→{outcome}(d20={roll})"
    }
    if outcome=="失败":
        base["player_update"]["add_conditions"].append("疲惫")
    return base

# ---------------- AI包装 ----------------
def ai_generate_scene(state:GameState)->dict:
    if USE_AI:
        try:
            raw = ai_chat([{"role":"user","content":prompt_scene(state)}])
            return jloads(raw)
        except Exception as e:
            print("⚠️ 场景改用本地：", e)
    return local_scene()

def ai_resolve(state:GameState, choice:dict, roll:int, outcome:str)->dict:
    if USE_AI:
        try:
            raw = ai_chat([{"role":"user","content":prompt_resolve(state, choice, roll, outcome)}])
            return jloads(raw)
        except Exception as e:
            print("⚠️ 结算改用本地：", e)
    return local_resolution(choice, roll, outcome)

# ---------------- Prompt ----------------
def prompt_scene(state:GameState)->str:
    blacklist = state.recent_checks[-3:]
    return f"""你是DM，中国古代架空世界...
【玩家】{json.dumps(asdict(state.player),ensure_ascii=False)}
【世界】{json.dumps(asdict(state.world),ensure_ascii=False)}
【上下文】{json.dumps(state.context,ensure_ascii=False)}
仅输出严格JSON，不要解释。"""

def prompt_resolve(state:GameState, choice:dict, roll:int, outcome:str)->str:
    return f"""你是DM，进行一次叙事结算...
【玩家】{json.dumps(asdict(state.player),ensure_ascii=False)}
【选择的行动】{json.dumps(choice,ensure_ascii=False)}
【掷点与结果】{{"d20": {roll}, "outcome": "{outcome}"}}
【上下文】{json.dumps(state.context,ensure_ascii=False)}
仅输出严格JSON，不要解释。"""

# ---------------- 主循环 / Web ----------------
def apply_player_updates(p:Player, upd:dict):
    addc = upd.get("add_conditions",[]) or []
    remc = upd.get("remove_conditions",[]) or []
    addi = upd.get("add_inventory",[]) or []
    remi = upd.get("remove_inventory",[]) or []

    for c in addc:
        if c and c not in p.conditions: p.conditions.append(c)
    for c in remc:
        if c in p.conditions: p.conditions.remove(c)
    for it in addi:
        if it and it.get("name"):
            if not any(x.get("name")==it["name"] for x in p.inventory):
                p.inventory.append(it)
    for name in remi:
        p.inventory = [x for x in p.inventory if x.get("name")!=name]

# ---------------- Flask ----------------
app = Flask(__name__)
state = load_game() or GameState()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/scene")
def get_scene():
    global state
    eff = gather_effect_tags(state.player)
    scene = ai_generate_scene(state)
    return jsonify(scene)

@app.route("/resolve", methods=["POST"])
def resolve():
    global state
    data = request.json
    choice = data.get("choice", {})
    mode = choice_advantage(choice.get("choice_tags",[]), gather_effect_tags(state.player), state.player.conditions)
    roll = roll_d20(mode)
    outcome = outcome_from_roll(roll)
    res = ai_resolve(state, choice, roll, outcome)
    apply_player_updates(state.player, res.get("player_update") or {})
    state.context.update(res.get("context_update") or {})
    state.recent_checks.append(choice.get("check_tag",""))
    save_game(state)
    return jsonify({"roll": roll, "mode": mode, "outcome": outcome, "result": res})

@app.route("/reset", methods=["POST"])
def reset_game():
    global state
    state = GameState()
    save_game(state)
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
