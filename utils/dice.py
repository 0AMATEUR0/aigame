import random
import re
from typing import Dict, List, Tuple

_DICE_RE = re.compile(r'^\s*(\d*)d(\d+)\s*([+-]\s*\d+)?\s*$', re.IGNORECASE)

def _parse_notation(dice: str) -> Tuple[int, int, int, str]:
    """
    解析骰子表达式，返回 (num, sides, modifier, normalized)
    支持: "1d8", "d20", "2d6+3", "4d8- 2"（含空格也行）
    """
    m = _DICE_RE.fullmatch(dice)
    if not m:
        raise ValueError(f"Invalid dice notation: {dice!r}")
    num = int((m.group(1) or '1'))
    sides = int(m.group(2))
    mod_str = (m.group(3) or '').replace(' ', '')
    modifier = int(mod_str) if mod_str else 0

    if num <= 0:
        raise ValueError("Number of dice must be >= 1")
    if sides <= 0:
        raise ValueError("Number of sides must be >= 1")

    normalized = f"{num}d{sides}{'+' if modifier >= 0 and modifier != 0 else ''}{modifier if modifier != 0 else ''}"
    return num, sides, modifier, normalized

def roll_detail(dice: str, crit: bool = False, rng=random.randint) -> Dict:
    """
    返回详细结果的掷骰：
    - crit=True 时，按 D&D 风格：**只翻倍骰子数量**（修正不翻倍）
    - 返回字段：
        notation: 规范化表达式（如 "2d6+3"）
        num: 原始骰子数量
        sides: 面数
        modifier: 修正
        crit: 是否暴击
        dice_rolled: 实际掷了几颗（暴击时翻倍）
        rolls: 每颗骰子的点数列表
        sum: 骰子总和（不含修正）
        total: 最终总和（含修正）
        breakdown: 便于日志打印的字符串
    """
    num, sides, modifier, normalized = _parse_notation(dice.lower())

    dice_rolled = num * (2 if crit else 1)
    rolls: List[int] = [rng(1, sides) for _ in range(dice_rolled)]
    dice_sum = sum(rolls)
    total = dice_sum + modifier

    # 生成日志
    rolls_part = " + ".join(str(r) for r in rolls) if rolls else "0"
    if modifier != 0:
        breakdown = f"({rolls_part}) {'+' if modifier > 0 else '-'} {abs(modifier)} = {total}"
    else:
        breakdown = f"({rolls_part}) = {total}"

    return {
        "notation": normalized,
        "num": num,
        "sides": sides,
        "modifier": modifier,
        "crit": crit,
        "dice_rolled": dice_rolled,
        "rolls": rolls,
        "sum": dice_sum,
        "total": total,
        "breakdown": breakdown,
    }

def roll(dice: str, crit: bool = False, rng=random.randint) -> int:
    """
    兼容旧接口：仅返回总点数。
    """
    return roll_detail(dice, crit=crit, rng=rng)["total"]


if __name__ == "__main__":
    res = roll_detail("2d6+3", crit=True)
    print(res)