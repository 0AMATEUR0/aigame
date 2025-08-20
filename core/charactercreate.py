# -*- coding: utf-8 -*-
import json, re
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")

def detect_lang(s: str) -> str:
    if re.search(r"[\u3040-\u30ff]", s):
        return "ja"
    if re.search(r"[\u4e00-\u9fff]", s):
        return "zh"
    return "en"

def force_json(text: str):
    """确保提取 JSON"""
    text = text.strip()
    try:
        return json.loads(text)
    except:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            return json.loads(m.group(0))
    return None

def generate_character(prompt: str, level: int = 3, pretty: bool = True):
    lang = detect_lang(prompt)

    sys_prompt = (
        "You are a Dungeons & Dragons 5e character generator. "
        "Return ONLY a JSON object with these keys: "
        "race, subrace, class, subclass, alignment, background, "
        "stats(with STR,DEX,CON,INT,WIS,CHA), stat_mods, "
        "hit_points, speed, weapon_proficiencies, tool_proficiencies, "
        "saving_throws, skills, resistances, vulnerabilities, traits, equipment, "
        "appearance(with age,height,weight,eyes,skin,hair)."
    )

    if lang == "zh":
        sys_prompt += " 字段名必须是英文，但字段值必须用中文。"
    elif lang == "ja":
        sys_prompt += " フィールド名は英語、値は日本語で書いてください。"
    else:
        sys_prompt += " All values in English."

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type":"json_object"},
        temperature=0.7,
        messages=[
            {"role":"system","content":sys_prompt},
            {"role":"user","content":f"Prompt: {prompt}, Level: {level}"}
        ]
    )

    data = force_json(resp.choices[0].message.content)
    if not data:
        raise ValueError("❌ AI did not return valid JSON")

    if pretty:
        # 格式化输出接近你示例
        lines = [
            f"Race: {data.get('race')}",
            f"Class: {data.get('class')}",
            f"Sub-Class: {data.get('subclass')}",
            f"Level: {level}",
            f"Alignment: {data.get('alignment')}",
            f"Background: {data.get('background')}",
        ]
        stats = data.get("stats", {})
        mods = data.get("stat_mods", {})
        for k in ["STR","DEX","CON","INT","WIS","CHA"]:
            lines.append(f"{k} {stats.get(k)}  MOD: {mods.get(k)}")
        lines += [
            f"Hit Points: {data.get('hit_points')}",
            f"Speed: {data.get('speed')}",
            f"Weapon Proficiencies: {', '.join(data.get('weapon_proficiencies', []))}",
            f"Tool Proficiencies: {', '.join(data.get('tool_proficiencies', []))}",
            f"Saving Throw Proficiencies: {', '.join(data.get('saving_throws', []))}",
            f"Skill Proficiencies: {', '.join(data.get('skills', []))}",
            f"Resistances: {', '.join(data.get('resistances', []))}",
            f"Vulnerabilities: {', '.join(data.get('vulnerabilities', []))}",
            f"Traits: {', '.join(data.get('traits', []))}",
            f"Equipment: {', '.join(data.get('equipment', []))}",
        ]
        app = data.get("appearance", {})
        lines.append(f"Age: {app.get('age')} | Height: {app.get('height')} | Weight: {app.get('weight')}")
        lines.append(f"Eyes: {app.get('eyes')} | Skin: {app.get('skin')} | Hair: {app.get('hair')}")
        return "\n".join(lines)

    return data

if __name__ == "__main__":
    prompt = input("请输入角色提示词: ")
    out = generate_character(prompt, level=3, pretty=True)
    print(out)
