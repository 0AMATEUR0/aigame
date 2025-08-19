# app.py
# -*- coding: utf-8 -*-
"""
Flask Web版：AI 驱动 D&D 叙事引擎（事件切换修复）
- 要求 OpenAI API（可用 .env 或 /api/set_key 临时注入）
- 前端通过 /api/scene 获取当前场景，通过 /api/choose 提交选项
"""
import os, json, time, random, pathlib
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from flask import Flask, jsonify, request, render_template
from dotenv import load_dotenv

load_dotenv()  # 从 .env 加载 OPENAI_API_KEY（可选）

# ---------- CONFIG ----------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
TIMEOUT = 60
RETRIES = 2
SAVE_FILE = "dnd_ai_state.json"
USE_AI = bool(OPENAI_API_KEY)

# ---------- HELPERS ----------
def extract_json(text: str) -> str:
    if not text:
        raise ValueError("empty ai response")
    l = text.find("{"); r = text.rfind("}")
    if l == -1 or r == -1 or r <= l:
        raise ValueError("no json object")
    return text[l:r+1]

def jloads(text: str) -> dict:
    return json.loads(extract_json(text))

def backoff(i:int): time.sleep(min(2**i, 6))

# ---------- DOMAIN ----------
@dataclass
class Player:
    name: str = "浪人"
    identity: str = "侠客"
    traits: List[str] = field(default_factory=lambda: ["谨慎","果断"])
    conditions: List[str] = field(default_factory=list)
    inventory: List[Dict[str,Any]] = field(default_factory=list)

@dataclass
class World:
    era: str = "明朝"
    region: str = "边疆"
    tone: str = "写意武侠 + 玄奇志怪"

@dataclass
class GameState:
    turn: int = 1
    player: Player = field(default_factory=Player)
    world: World = field(default_factory=World)
    current_scene: Dict[str,Any] = field(default_factory=dict)
    story_log: List[str] = field(default_factory=list)
    context: Dict[str,Any] = field(default_factory=dict)
    recent_checks: List[str] = field(default_factory=list)

    def to_dict(self):
        return {
            "turn": self.turn,
            "player": asdict(self.player),
            "world": asdict(self.world),
            "current_scene": self.current_scene,
            "story_log": self.story_log[-200:],
            "context": self.context,
            "recent_checks": self.recent_checks[-3:]
        }

    @staticmethod
    def from_dict(d:dict):
        gs = GameState()
        gs.turn = d.get("turn", gs.turn)
        p = d.get("player", {}); gs.player = Player(**p) if p else Player()
        w = d.get("world", {}); gs.world = World(**w) if w else World()
        gs.current_scene = d.get("current_scene", {}) or {}
        gs.story_log = d.get("story_log", [])
        gs.context = d.get("context", {})
        gs.recent_checks = d.get("recent_checks", [])
        return gs

# ---------- SAVE / LOAD ----------
def save_state(s:GameState):
    with open(SAVE_FILE,"w",encoding="utf-8") as f:
        json.dump(s.to_dict(), f, ensure_ascii=False, indent=2)

def load_state()->Optional[GameState]:
    try:
        with open(SAVE_FILE,"r",encoding="utf-8") as f:
            return GameState.from_dict(json.load(f))
    except FileNotFoundError:
        return None
    except Exception as e:
        print("⚠️ 读档失败：", e)
        return None

# ---------- OPENAI WRAPPER ----------
def ai_chat(messages: List[Dict[str,str]])->str:
    if not USE_AI:
        raise RuntimeError("OpenAI API key 未配置（OPENAI_API_KEY 为空），AI 模式不可用。")
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("openai 包不可用，请 pip install openai") from e
    client = OpenAI(api_key=OPENAI_KEY())
    err = None
    for i in range(RETRIES+1):
        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL, messages=messages, temperature=0.9, timeout=TIMEOUT
            )
            return resp.choices[0].message.content
        except Exception as e:
            err = e
            print(f"⚠️ AI 请求失败({i+1})：{e}")
            backoff(i)
    raise err

def OPENAI_KEY():
    # 动态读取环境变量（支持 /api/set_key 动态修改 .env）
    return os.getenv("OPENAI_API_KEY","")

# ---------- DICE & TAGS ----------
def gather_effect_tags(p:Player)->List[str]:
    tags=[] 
    for it in p.inventory: tags += it.get("effect_tags",[])
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
    a=random.randint(1,20); b=random.randint(1,20)
    if mode=="advantage": return max(a,b)
    if mode=="disadvantage": return min(a,b)
    return a

def outcome_from_roll(r:int)->str:
    if r>=15: return "成功"
    if r>=8: return "部分成功"
    return "失败"

# ---------- PROMPTS ----------
def prompt_scene(state:GameState)->str:
    blacklist = state.recent_checks[-3:]
    return f"""
你是即兴地城主持（DM），背景固定为中国古代架空（{state.world.era}·{state.world.region}，风格：{state.world.tone}）。
请基于玩家与上下文生成【新场景与可选行动】，避免最近检定类型重复：{blacklist}。

【玩家】
{json.dumps(asdict(state.player),ensure_ascii=False)}
【世界】
{json.dumps(asdict(state.world),ensure_ascii=False)}
【上下文】
{json.dumps(state.context,ensure_ascii=False)}
【最近日志(最多8条)】
{json.dumps(state.story_log[-8:],ensure_ascii=False)}

仅输出严格JSON（不要额外文本），格式如下（全部必填）：
{{
  "scene_id":"string",
  "scene":"string（中文，<=120字）",
  "env_tags":["string"],
  "npcs":["string"],
  "threats":["string"],
  "clues":["string"],
  "loot":[{{"name":"string","description":"string","effect_tags":["string"],"usage_notes":"string"}}],
  "choices":[{{"action":"string","hint":"string","check_tag":"perception|stealth|social|athletics|mystic|survival|insight","choice_tags":["string"],"leads":"string"}}]
}}
"""

def prompt_resolve(state:GameState, choice:dict, roll:int, outcome:str)->str:
    return f"""
你是DM。玩家选择：{choice.get('action')}
玩家当前信息：{json.dumps(asdict(state.player),ensure_ascii=False)}
上下文：{json.dumps(state.context,ensure_ascii=False)}
掷点：d20={roll}，结果：{outcome}

请返回严格 JSON（不要解释），字段（全部必填），并**可选**包含 "next_scene"（完整场景 JSON，若提供服务器将优先使用）：
{{
  "narration":"string（<=150字）",
  "context_update":{{}},
  "player_update":{{"add_conditions":["string"],"remove_conditions":["string"],"add_inventory":[{{"name":"string","description":"string","effect_tags":["string"],"usage_notes":"string"}}],"remove_inventory":["string"]}},
  "log_entry":"string",
  "next_scene":{{}}  # 可选
}}
"""

# ---------- LOCAL FALLBACK (小型) ----------
LOCAL_SCENES = [
    {
      "scene_id":"gu_yi",
      "scene":"薄雾笼旧驿，风铃自鸣，驿墙碑文残缺。",
      "env_tags":["fog","ruins","road"],
      "npcs":["挑担书生"],
      "threats":["黑衣人潜踪"],
      "clues":["碑文残句","石缝竹筒"],
      "loot":[{"name":"竹筒残简","description":"墨迹漫漶，疑似暗号。","effect_tags":["insight","night"],"usage_notes":"夜读更易辨识"}],
      "choices":[
        {"action":"与书生闲叙打探","hint":"或得旧闻","check_tag":"social","choice_tags":["social"],"leads":"书生指向荒祠"},
        {"action":"沿墙寻碑文","hint":"也许能续句","check_tag":"perception","choice_tags":["perception"],"leads":"碑文指向祠庙北径"},
        {"action":"埋伏观察","hint":"耐心考验","check_tag":"stealth","choice_tags":["stealth","night"],"leads":"黑影往北"}
      ]
    }
]
def local_scene()->dict: return random.choice(LOCAL_SCENES)
def local_resolution(choice, roll, outcome):
    base={
      "narration": f"你按计行事，气息如线；{outcome}。",
      "context_update":{"seed": choice.get("leads",""), "trail":"细碎足印"},
      "player_update":{"add_conditions":[],"remove_conditions":[],"add_inventory":[],"remove_inventory":[]},
      "log_entry": f"检定{choice.get('check_tag','?')}→{outcome}(d20={roll})"
    }
    if outcome=="失败": base["player_update"]["add_conditions"].append("疲惫")
    return base

# ---------- AI WRAPPERS (使用 OpenAI 或 本地兜底) ----------
def ai_generate_scene(state:GameState)->dict:
    if USE_AI:
        raw = ai_chat([{"role":"user","content":prompt_scene(state)}])
        try:
            return jloads(raw)
        except Exception as e:
            print("⚠️ 解析 AI 场景 JSON 失败：", e)
            print("raw:", raw[:1000])
    return local_scene()

def ai_resolve(state:GameState, choice:dict, roll:int, outcome:str)->dict:
    if USE_AI:
        raw = ai_chat([{"role":"user","content":prompt_resolve(state, choice, roll, outcome)}])
        try:
            return jloads(raw)
        except Exception as e:
            print("⚠️ 解析 AI 结算 JSON 失败：", e)
            print("raw:", raw[:1000])
    return local_resolution(choice, roll, outcome)

# ---------- STATE HELPERS ----------
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
        if it and it.get("name") and not any(x.get("name")==it["name"] for x in p.inventory):
            p.inventory.append(it)
    for name in remi:
        p.inventory = [x for x in p.inventory if x.get("name")!=name]

def ensure_current_scene(state:GameState):
    if not state.current_scene:
        state.current_scene = ai_generate_scene(state) if USE_AI else local_scene()
        if not state.current_scene or not isinstance(state.current_scene, dict) or "scene" not in state.current_scene:
            state.current_scene = local_scene()
        save_state_local(state)

def generate_next_scene_from_resolution(state:GameState, chosen:dict, resolution:dict)->dict:
    # 1. resolution.next_scene 优先（完整 JSON）
    ns = resolution.get("next_scene")
    if isinstance(ns, dict) and ns.get("scene"):
        return ns
    # 2. 更新 context 并若 seed 存在则尝试生成
    ctxu = resolution.get("context_update") or {}
    if ctxu:
        state.context.update(ctxu)
        if state.context.get("seed"):
            try:
                nxt = ai_generate_scene(state) if USE_AI else local_scene()
                if nxt and isinstance(nxt, dict) and nxt.get("scene"): return nxt
            except Exception as e:
                print("⚠️ context.seed 生成失败：", e)
    # 3. choice.leads
    leads = chosen.get("leads") or ""
    if leads:
        state.context["seed"] = leads
        try:
            nxt = ai_generate_scene(state) if USE_AI else local_scene()
            if nxt and isinstance(nxt, dict) and nxt.get("scene"): return nxt
        except Exception as e:
            print("⚠️ leads 生成失败：", e)
    # 4. 兜底：强制再生成一次并尝试避免重复
    try:
        nxt = ai_generate_scene(state) if USE_AI else local_scene()
        if nxt and isinstance(nxt, dict) and nxt.get("scene") and state.current_scene.get("scene_id") == nxt.get("scene_id"):
            # 试着改变 seed 小诱导
            state.context["seed"] = (state.context.get("seed","") or "") + "；随后：" + (chosen.get("action","")[:20])
            nxt2 = ai_generate_scene(state) if USE_AI else local_scene()
            if nxt2 and nxt2.get("scene_id") != nxt.get("scene_id"): return nxt2
        return nxt
    except Exception as e:
        print("⚠️ 最终兜底失败：", e)
        return local_scene()

# ---------- PERSIST HELP FOR LOCAL save_state compatibility ----------
def save_state_local(state:GameState):
    try:
        save_state(state)
    except Exception:
        # fallback to older save function (compat)
        with open(SAVE_FILE,"w",encoding="utf-8") as f:
            json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

def save_state(state:GameState):
    with open(SAVE_FILE,"w",encoding="utf-8") as f:
        json.dump(state.to_dict(), f, ensure_ascii=False, indent=2)

# ---------- FLASK APP ----------
app = Flask(__name__, static_folder="static", template_folder="templates")
state = load_state() or GameState()

# initialize seed/story/current scene
if "seed" not in state.context:
    state.context["seed"] = "雾锁山道上的旧驿"
    state.story_log.append("启程于雾锁山道，旧驿风铃自鸣。")
ensure_current_scene(state)
save_state(state)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/scene", methods=["GET"])
def api_scene():
    return jsonify({
        "scene": state.current_scene,
        "player": asdict(state.player),
        "turn": state.turn,
        "history": state.story_log[-50:],
        "context": state.context
    })

@app.route("/api/set_name", methods=["POST"])
def api_set_name():
    data = request.json or {}
    state.player.name = data.get("name", state.player.name) or state.player.name
    save_state(state)
    return jsonify({"ok": True, "player": asdict(state.player)})

@app.route("/api/choose", methods=["POST"])
def api_choose():
    global USE_AI
    data = request.json or {}
    try:
        idx = int(data.get("choice_idx",0))
    except:
        return jsonify({"error":"choice_idx 必须是整数"}), 400
    scene = state.current_scene or local_scene()
    choices = scene.get("choices",[])
    if idx<0 or idx>=len(choices):
        return jsonify({"error":"无效选项"}), 400
    chosen = choices[idx]
    # recent checks
    ctag = chosen.get("check_tag","")
    state.recent_checks.append(ctag)
    # calc advantage
    eff = gather_effect_tags(state.player)
    mode = choice_advantage(chosen.get("choice_tags",[]), eff, state.player.conditions)
    roll = roll_d20(mode)
    outcome = outcome_from_roll(roll)
    # resolution via AI or local
    try:
        resolution = ai_resolve(state, chosen, roll, outcome)
    except Exception as e:
        resolution = local_resolution(chosen, roll, outcome)
        print("⚠️ ai_resolve 失败，使用本地结算：", e)
    # apply updates
    apply_player_updates(state.player, resolution.get("player_update") or {})
    ctxu = resolution.get("context_update") or {}
    if ctxu: state.context.update(ctxu)
    # append log
    state.story_log.append(resolution.get("log_entry",""))
    state.turn += 1
    # determine next scene
    next_scene = generate_next_scene_from_resolution(state, chosen, resolution)
    if not next_scene or not isinstance(next_scene, dict) or not next_scene.get("scene"):
        next_scene = local_scene()
    state.current_scene = next_scene
    save_state(state)
    return jsonify({
        "roll": roll, "mode": mode, "outcome": outcome,
        "resolution": resolution,
        "next_scene": next_scene,
        "player": asdict(state.player),
        "turn": state.turn,
        "history": state.story_log[-50:]
    })

# optional helper to set API key via POST (local testing convenience)
@app.route("/api/set_key", methods=["POST"])
def api_set_key():
    data = request.json or {}
    key = data.get("key","").strip()
    if not key:
        return jsonify({"error":"key 为空"}), 400
    # write to .env for persistence (dev-only!)
    p = pathlib.Path(".env")
    try:
        lines = []
        if p.exists():
            lines = p.read_text(encoding="utf-8").splitlines()
            lines = [l for l in lines if not l.startswith("OPENAI_API_KEY=")]
        lines.append(f"OPENAI_API_KEY={key}")
        p.write_text("\n".join(lines), encoding="utf-8")
        os.environ["OPENAI_API_KEY"] = key
        global USE_AI
        USE_AI = True
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/reset", methods=["POST"])
def api_reset():
    global state
    state = GameState()
    state.context["seed"] = "雾锁山道上的旧驿"
    state.story_log.append("启程于雾锁山道，旧驿风铃自鸣。")
    # try generate initial scene
    try:
        state.current_scene = ai_generate_scene(state) if USE_AI else local_scene()
    except Exception as e:
        print("⚠️ reset 生成场景失败：", e)
        state.current_scene = local_scene()
    save_state(state)
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("USE_AI =", USE_AI)
    app.run(host="0.0.0.0", port=8000, debug=True)
