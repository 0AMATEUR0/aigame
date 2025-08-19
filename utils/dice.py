import random
import re

def roll(dice: str) -> int:
    """
    简单骰子解析：如 "1d8" 或 "2d6"
    """
    match = re.match(r"(\d+)d(\d+)", dice.lower())
    if not match:
        raise ValueError(f"Invalid dice format: {dice}")
    num, sides = map(int, match.groups())
    return sum(random.randint(1, sides) for _ in range(num))