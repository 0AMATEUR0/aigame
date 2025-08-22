# -*- coding: utf-8 -*-
"""
AI驱动 D&D 叙事引擎（中国古代架空）
- 每回合：AI生成场景(JSON) -> 玩家选择 -> 引擎掷d20(可优势/劣势) -> AI按结果叙事(JSON) -> 应用状态 -> 推进到下一场景
- 无数值战斗，仅叙事后果（状态/线索/物品/关系）
- 检定类型避免重复；装备以“效果标签”影响检定
"""

import os, json, time, random
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

# ---------------- 配置 ----------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o-mini"
TIMEOUT = 60
RETRIES = 2
USE_AI = True            # 无网可切 False 走本地模板
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
    name: str = "浪人"
    identity: str = "侠客"
    traits: List[str] = field(default_factory=lambda: ["谨慎","果断"])
    conditions: List[str] = field(default_factory=list)        # 叙事状态：疲惫/受惊/风尘等
    inventory: List[Dict[str,Any]] = field(default_factory=list) # 装备：{name,desc,effect_tags,usage_notes}

@dataclass
class World:
    era: str = "明朝"
    region: str = "边疆"
    factions: List[str] = field(default_factory=lambda: ["大漠盗贼","可汗精兵","流沙客"])
    tone: str = "写意武侠 + 玄奇志怪"

@dataclass
class GameState:
    background: str = "中国古代架空世界"
    turn: int = 1
    player: Player = field(default_factory=Player)
    world: World = field(default_factory=World)
    story_log: List[str] = field(default_factory=list)
    context: Dict[str,Any] = field(default_factory=dict)   # {seed, env_tags, last_check_tag, ...}
    recent_checks: List[str] = field(default_factory=list) # 近3次检定类型去重

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

# ---------------- 装备与检定：标签体系 ----------------
# 检定标签全集示例：perception/stealth/social/athletics/mystic/survival/insight
# 装备 effect_tags 例如：["stealth","night","mystic"]
def gather_effect_tags(p:Player)->List[str]:
    tags = []
    for it in p.inventory:
        tags += it.get("effect_tags",[])
    return list(dict.fromkeys(tags))  # 去重保序

def choice_advantage(choice_tags:List[str], effect_tags:List[str], conditions:List[str])->str:
    """返回 'advantage' | 'disadvantage' | 'normal'"""
    # 简单规则：有≥1交集且无负面状态 -> 优势
    if any(t in effect_tags for t in choice_tags):
        if "疲惫" not in conditions and "受惊" not in conditions:
            return "advantage"
    # 某些状态对特定检定吃亏
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

# ---------------- Prompt：场景生成 ----------------
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

仅输出严格JSON，字段如下（全部必填）：
{{
  "scene_id": "string, 本场景短ID（拼音/英文/短汉字均可）",
  "scene": "string, 环境描写<=120字",
  "env_tags": ["string"],            # 如 forest/night/ruins/market/temple/mountain/rain/river
  "npcs": ["string"],
  "threats": ["string"],
  "clues": ["string"],
  "loot": [                          # 可获得的装备（叙事效果，不要数值）
    {{"name":"string","description":"string",
      "effect_tags":["string"],"usage_notes":"string"}}
  ],
  "choices": [                       # 2~4项
    {{
      "action":"string",
      "hint":"string",
      "check_tag":"perception|stealth|social|athletics|mystic|survival|insight",
      "choice_tags":["string"],      # 用于与装备 effect_tags 计算优势/劣势
      "leads":"string"               # 下一场景走向种子（短语/地点/目标）
    }}
  ]
}}
注意：避免使用最近检定类型；中文输出；不要加入任何解释或额外文本。
""".strip()

# ---------------- Prompt：结算叙事 ----------------
def prompt_resolve(state:GameState, choice:dict, roll:int, outcome:str)->str:
    return f"""
你是DM。下面进行一次叙事结算：引擎已掷出d20并判定结果，你根据结果给出叙事后果。
不要数值战斗或伤害，只给状态/线索/关系/物品的变化与描写。

【玩家】
{json.dumps(asdict(state.player),ensure_ascii=False)}
【选择的行动】
{json.dumps(choice,ensure_ascii=False)}
【掷点与结果】
{{"d20": {roll}, "outcome": "{outcome}"}}
【上下文】
{json.dumps(state.context,ensure_ascii=False)}

仅输出严格JSON（全部必填）：
{{
  "narration": "string, <=150字",
  "context_update": {{}},             # 如 {{ "seed":"潜入祠庙", "tracks":["黑狐踪影"] }}
  "player_update": {{
     "add_conditions": ["string"],
     "remove_conditions": ["string"],
     "add_inventory": [                # 从本场景loot或叙事派生
       {{"name":"string","description":"string","effect_tags":["string"],"usage_notes":"string"}}
     ],
     "remove_inventory": ["string"]
  }},
  "log_entry": "string"
}}
仅输出JSON，不要解释。
""".strip()

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
    return json.loads(json.dumps(random.choice(LOCAL_SCENES), ensure_ascii=False))

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

# ---------------- 主循环 ----------------
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
            # 去重：按名字
            if not any(x.get("name")==it["name"] for x in p.inventory):
                p.inventory.append(it)
    for name in remi:
        p.inventory = [x for x in p.inventory if x.get("name")!=name]

def play():
    state = load_game() or GameState()
    if state.player.name=="浪人":
        n = input("给角色起名（回车默认“无名侠客”）：").strip()
        if n: state.player.name=n

    # 初始种子
    if "seed" not in state.context:
        state.context["seed"] = "大漠边疆，荒凉驿站"
        state.story_log.append("荒凉落寞的大漠边疆，浪人孤身一人。")

    while True:
        print("\n"+"="*40)
        print(f"回合 {state.turn}｜地点：{state.world.region}｜状态：{','.join(state.player.conditions) or '良好'}")
        eff = gather_effect_tags(state.player)
        # 生成场景
        scene = ai_generate_scene(state)

        # 强制去重检定：若AI仍给了重复的check_tag，做一次本地替换
        valid_tags = ["perception","stealth","social","athletics","mystic","survival","insight"]
        recent = set(state.recent_checks[-3:])
        for ch in scene.get("choices",[]):
            tag = ch.get("check_tag","")
            if tag in recent:
                ch["check_tag"] = random.choice([t for t in valid_tags if t not in recent] or valid_tags)

        # 展示
        print(f"\n【场景】{scene.get('scene','')}")
        if scene.get("npcs"):    print("【人物】"+"、".join(scene["npcs"]))
        if scene.get("threats"): print("【潜在】"+"、".join(scene["threats"]))
        if scene.get("clues"):   print("【线索】"+"、".join(scene["clues"]))
        if scene.get("loot"):
            print("【可得物】"+ "；".join([f"{x['name']}（{','.join(x.get('effect_tags',[]))}）" for x in scene["loot"]]))

        choices = scene.get("choices",[])
        if len(choices)<2:
            print("⚠️ 选项不足，使用本地场景补齐")
            choices = local_scene()["choices"]
        for i,ch in enumerate(choices,1):
            print(f"  {i}. {ch.get('action','')} —— {ch.get('hint','')} 〔检定: {ch.get('check_tag','?')}〕")

        sel = input("选择编号（S存档 / Q退出）：").strip().lower()
        if sel=="q":
            save_game(state); print("👋 再会，侠客。"); break
        if sel=="s":
            save_game(state); continue
        try:
            idx = int(sel)-1
            assert 0<=idx<len(choices)
        except:
            print("❌ 输入无效"); continue

        chosen = choices[idx]
        ctag = chosen.get("check_tag","")
        state.recent_checks.append(ctag)

        # 依据装备标签计算优势/劣势，并由引擎掷骰（不让AI决定掷值，避免重复/矛盾）
        mode = choice_advantage(chosen.get("choice_tags",[]), eff, state.player.conditions)
        r = roll_d20(mode)
        oc = outcome_from_roll(r)

        # 交给AI做叙事结算
        res = ai_resolve(state, chosen, r, oc)
        print(f"\n【检定】d20={r}（{mode or 'normal'}）→ {oc}")
        print(f"【叙事】{res.get('narration','')}")
        state.story_log.append(res.get("log_entry",""))

        # 应用变化
        apply_player_updates(state.player, res.get("player_update") or {})
        # 更新上下文与下一场景种子
        ctxu = res.get("context_update") or {}
        state.context.update(ctxu)
        # 若无seed则从choice.leads补
        if "seed" not in state.context and chosen.get("leads"):
            state.context["seed"] = chosen["leads"]

        # 显示背包与装备效果
        if state.player.inventory:
            items = "；".join([f"{it['name']}（{','.join(it.get('effect_tags',[]))}）" for it in state.player.inventory])
            print("【背包】"+items)
        if state.player.conditions:
            print("【状态】"+ "、".join(state.player.conditions))

        # 推进回合并存档
        state.turn += 1
        save_game(state)

if __name__ == "__main__":
    try:
        play()
    except KeyboardInterrupt:
        print("\n👋 安全退出。")
