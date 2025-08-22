#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
event_test.py
交互式事件生成与发展测试
"""

import random
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# ========== 初始化 OpenAI ==========
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ========== 彩色终端输出工具 ==========
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

def log_event(msg, level="info"):
    now = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "info": f"{Colors.OKBLUE}[INFO]{Colors.ENDC}",
        "success": f"{Colors.OKGREEN}[SUCCESS]{Colors.ENDC}",
        "warn": f"{Colors.WARNING}[WARNING]{Colors.ENDC}",
        "error": f"{Colors.FAIL}[ERROR]{Colors.ENDC}",
        "header": f"{Colors.HEADER}[EVENT]{Colors.ENDC}",
    }.get(level, f"{Colors.OKCYAN}[LOG]{Colors.ENDC}")
    print(f"{Colors.BOLD}[{now}]{Colors.ENDC} {prefix} {msg}")

def log_separator():
    print(f"{Colors.BOLD}{'-'*60}{Colors.ENDC}")

# ========== 玩家 ==========
class DummyPlayer:
    def __init__(self, name):
        self.name = name
        self.inventory = []
        self.clues = []

    def add_item(self, item):
        self.inventory.append(item)
        log_event(f"🎒 背包新增: {item}", "success")

    def add_clue(self, clue):
        self.clues.append(clue)
        log_event(f"🧩 获得线索: {clue}", "success")

# ========== AI 事件生成 ==========
def ai_generate_event(prompt, prev_event=None):
    """
    根据提示词或上一个事件，生成新事件
    """
    try:
        if prev_event:
            context = f"上一个事件: {prev_event}"
        else:
            context = f"玩家输入提示词: {prompt}"

        system_prompt = f"""
你是《无疆传说》的事件发展生成器。
请基于玩家输入或上一个事件，生成一个新的事件。

输出严格为 JSON 格式：
{{
  "type": "战斗/掉落/线索/陷阱/谜题/普通",
  "description": "事件描述",
  "extra": {{ 可选附加信息 }},
  "next_possible": ["战斗","掉落","线索","陷阱","谜题","普通"]  # 事件可能的发展方向
}}
不要输出任何额外解释。
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            temperature=0.8
        )
        raw = response.choices[0].message.content.strip()
        log_event(f"AI返回: {raw}", "info")
        return json.loads(raw)

    except Exception as e:
        log_event(f"AI事件生成失败: {e}", "error")
        return {"type":"普通","description":"什么也没有发生","extra":{},"next_possible":["普通"]}

# ========== 事件触发 ==========
def trigger_event(event_info, player):
    event_type = event_info.get("type","普通")
    desc = event_info.get("description","无描述事件")
    extra = event_info.get("extra",{})

    log_separator()
    log_event(f"事件类型: {event_type} | 描述: {desc}", "header")

    if event_type == "战斗":
        monster = extra.get("monster_type","未知敌人")
        log_event(f"⚔️ 遭遇战斗: {monster}", "warn")
    elif event_type == "掉落":
        item = f"{extra.get('rarity','普通')} {extra.get('item_type','未知物品')}"
        player.add_item(item)
    elif event_type == "线索":
        clue = extra.get("clue_detail", desc)
        player.add_clue(clue)
    elif event_type == "陷阱":
        log_event("☠️ 触发陷阱! 玩家受伤", "error")
    elif event_type == "谜题":
        log_event("❓ 遇到谜题! 玩家需要解谜", "warn")
    else:
        log_event("🌿 普通事件，无特殊操作。", "info")

# ========== 主入口 ==========
if __name__ == "__main__":
    log_separator()
    log_event("🌌 《无疆传说》交互式事件测试开始", "header")

    player = DummyPlayer("陵兰")

    # 玩家输入提示词
    user_prompt = input("请输入场景提示词: ").strip()

    current_event = ai_generate_event(user_prompt)

    while True:
        trigger_event(current_event, player)

        # 是否继续发展？
        cont = input("\n是否发展下一个事件？(y/n): ").strip().lower()
        if cont != "y":
            break

        current_event = ai_generate_event(user_prompt, prev_event=current_event)

    log_separator()
    log_event("✨ 测试结束，结果如下:", "header")
    print("🎒 背包:", player.inventory)
    print("🧩 线索:", player.clues)
