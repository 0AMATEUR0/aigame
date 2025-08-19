import random
import re

def roll(dice: str, crit=False) -> int:
    """
    掷骰子函数，支持暴击加成
    dice: 如 "1d8" 或 "2d6"
    crit: 是否暴击，暴击时翻倍
    """
    match = re.match(r"(\d+)d(\d+)", dice.lower())
    if not match:
        raise ValueError(f"Invalid dice format: {dice}")
    num, sides = map(int, match.groups())
    total = sum(random.randint(1, sides) for _ in range(num))
    if crit:
        total *= 2
    return total