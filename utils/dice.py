import random
import re
from dataclasses import dataclass
from typing import List, Callable

# -----------------------------
# 骰子表达式的解析规则
# -----------------------------
# 语法支持：
#   - "1d6"    -> 掷 1 个六面骰
#   - "d20"    -> 省略数量，等价于 "1d20"
#   - "2d6+3"  -> 掷 2 个六面骰后，加 3
#   - "4d8- 2" -> 掷 4 个八面骰后，减 2（允许空格）
#   - "d%"     -> 百分骰，等价于 "d100"
#
# 正则分组说明：
#   group(1) = 骰子数量 (可选，默认为 1)
#   group(2) = 骰子面数 (支持整数或 %)
#   group(3) = 加值/减值 (可选，可能含空格)
#
_DICE_RE = re.compile(r'^\s*(\d*)d(\d+|%)\s*([+-]\s*\d+)?\s*$', re.IGNORECASE)


# -----------------------------
# 数据结构：骰子表达式
# -----------------------------
@dataclass
class DiceNotation:
    """
    保存解析后的骰子表达式信息
    """
    num: int          # 掷骰数量，例如 2d6 中的 2
    sides: int        # 骰子面数，例如 2d6 中的 6；d% 记为 100
    modifier: int     # 修正值，例如 +3 或 -2
    normalized: str   # 标准化表示，例如 "2d6+3"


def _parse_notation(dice: str) -> DiceNotation:
    """
    解析骰子表达式字符串，返回 DiceNotation 对象。

    参数:
        dice (str): 骰子表达式字符串，例如 "2d6+1"、"d20"

    返回:
        DiceNotation: 结构化的骰子信息
    """
    # 用正则匹配骰子表达式
    m = _DICE_RE.fullmatch(dice.strip())
    if not m:
        raise ValueError(f"Invalid dice notation: {dice!r}")

    # 解析骰子数量，默认值为 1
    num = int(m.group(1) or '1')

    # 解析骰子面数，支持 "%" 作为 100
    sides = 100 if m.group(2) == "%" else int(m.group(2))

    # 解析加减修正值，例如 "+3" 或 "-2"
    modifier = int((m.group(3) or '0').replace(' ', ''))

    # 基本合法性检查
    if num <= 0 or sides <= 0:
        raise ValueError("Number of dice and sides must be >= 1")

    # 构造标准化表示（例如 "2d6+3"）
    sign = f"{'+' if modifier > 0 else ''}{modifier}" if modifier else ""
    normalized = f"{num}d{sides}{sign}"

    return DiceNotation(num, sides, modifier, normalized)


# -----------------------------
# 数据结构：骰子结果
# -----------------------------
@dataclass
class DiceResult:
    """
    保存一次掷骰的完整结果
    """
    notation: str      # 标准化的骰子表达式，例如 "2d6+1"
    num: int           # 掷骰数量（未考虑暴击加倍）
    sides: int         # 骰子面数
    modifier: int      # 加值/减值
    crit: bool         # 是否触发暴击
    dice_rolled: int   # 实际掷骰次数（考虑暴击模式后的次数）
    rolls: List[int]   # 每次掷骰的具体结果
    sum: int           # 骰子结果之和（不含修正值）
    total: int         # 最终结果（含修正值和暴击修正）
    breakdown: str     # 人类可读的运算过程，例如 "(4 + 5) + 2 = 11"


# -----------------------------
# 掷骰函数
# -----------------------------
def roll_detail(
    dice: str,
    crit: bool = False,
    crit_mode: str = "double_dice",
    rng: Callable[[int, int], int] = random.randint
) -> DiceResult:
    """
    掷骰函数，支持不同的暴击规则。

    参数:
        dice (str):
            骰子表达式，例如 "1d20+5"
        crit (bool):
            是否暴击，默认 False
        crit_mode (str):
            暴击模式，支持：
              - "double_dice": 掷骰次数加倍
                    例如 "1d8" -> 实际掷 "2d8"
              - "double_result": 骰子点数和加倍
                    例如 "1d8=5" -> 结果变成 10
        rng (callable):
            随机数生成函数，默认 random.randint
            可以替换为可控 RNG 以便测试

    返回:
        DiceResult: 掷骰结果的详细信息
    """
    # 解析骰子表达式
    notation = _parse_notation(dice)

    # 根据暴击模式决定实际掷骰次数
    if crit and crit_mode == "double_dice":
        dice_rolled = notation.num * 2
    else:
        dice_rolled = notation.num

    # 实际掷骰，调用 rng(1, sides) 生成结果
    rolls = [rng(1, notation.sides) for _ in range(dice_rolled)]

    # 骰子点数和（不含修正）
    dice_sum = sum(rolls)

    # 最终结果计算
    if crit and crit_mode == "double_result":
        # double_result 模式：骰子和加倍后再加修正
        total = dice_sum * 2 + notation.modifier
    else:
        # 普通模式：骰子和 + 修正
        total = dice_sum + notation.modifier

    # 构造人类可读的 breakdown 字符串
    rolls_part = " + ".join(map(str, rolls)) or "0"
    if notation.modifier != 0:
        breakdown = f"({rolls_part}) {'+' if notation.modifier > 0 else '-'} {abs(notation.modifier)} = {total}"
    else:
        breakdown = f"({rolls_part}) = {total}"

    # 返回结果对象
    return DiceResult(
        notation=notation.normalized,
        num=notation.num,
        sides=notation.sides,
        modifier=notation.modifier,
        crit=crit,
        dice_rolled=dice_rolled,
        rolls=rolls,
        sum=dice_sum,
        total=total,
        breakdown=breakdown,
    )

if __name__ == "__main__":
    # 1. 普通掷骰：2d6+3
    result1 = roll_detail("2d6+3")
    print("🎲 普通掷骰")
    print("表达式:", result1.notation)
    print("掷骰次数:", result1.dice_rolled)
    print("每次结果:", result1.rolls)
    print("点数和:", result1.sum)
    print("最终结果:", result1.total)
    print("过程说明:", result1.breakdown)
    print()

    # 2. 暴击模式：double_dice（骰子数量加倍）
    result2 = roll_detail("1d20", crit=True, crit_mode="double_dice")
    print("💥 暴击掷骰 (double_dice)")
    print("表达式:", result2.notation)
    print("掷骰次数:", result2.dice_rolled)
    print("每次结果:", result2.rolls)
    print("点数和:", result2.sum)
    print("最终结果:", result2.total)
    print("过程说明:", result2.breakdown)
    print()

    # 3. 暴击模式：double_result（骰子点数加倍）
    result3 = roll_detail("1d8", crit=True, crit_mode="double_result")
    print("💥 暴击掷骰 (double_result)")
    print("表达式:", result3.notation)
    print("掷骰次数:", result3.dice_rolled)
    print("每次结果:", result3.rolls)
    print("点数和:", result3.sum)
    print("最终结果:", result3.total)
    print("过程说明:", result3.breakdown)
    print()

    # 4. 百分骰（d% 等价于 d100）
    result4 = roll_detail("d%")
    print("🎯 百分骰 (d%)")
    print("表达式:", result4.notation)
    print("掷骰次数:", result4.dice_rolled)
    print("每次结果:", result4.rolls)
    print("点数和:", result4.sum)
    print("最终结果:", result4.total)
    print("过程说明:", result4.breakdown)
