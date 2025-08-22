import json
from typing import Dict, Any
from game.Entity.character import Character
from game.Entity.monster import Monster

class EntityFactory:
    """
    Entity 工厂类
    -----------------
    负责创建 Character / Monster 对象，
    以及 JSON 的保存和加载
    """

    # 角色模板
    CHARACTER_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "战士": {"name": "战士", "STR": 16, "DEX": 12, "CON": 14, "INT": 8, "WIS": 10, "CHA": 10,
                "HP": 30, "MP": 10, "occupation": "战士"},
        "法师": {"name": "法师", "STR": 8, "DEX": 12, "CON": 10, "INT": 16, "WIS": 14, "CHA": 10,
                "HP": 20, "MP": 30, "occupation": "法师"},
    }

    # 怪物模板
    MONSTER_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "哥布林": {"name": "哥布林", "STR": 8, "DEX": 14, "CON": 10, "INT": 6, "WIS": 8, "CHA": 6,
                  "HP": 30, "MP": 0, "AC": 12, "Speed": 30, "exp_reward": 50, "item_reward": []},
        "兽人": {"name": "兽人", "STR": 16, "DEX": 10, "CON": 14, "INT": 8, "WIS": 10, "CHA": 8,
                 "HP": 35, "MP": 0, "AC": 13, "Speed": 30, "exp_reward": 120, "item_reward": []},
    }

    @classmethod
    def create_character(cls, template_name: str) -> Character:
        """根据模板生成 Character"""
        template = cls.CHARACTER_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"未知角色模板: {template_name}")
        return Character(**template)

    @classmethod
    def create_monster(cls, template_name: str) -> Monster:
        """根据模板生成 Monster"""
        template = cls.MONSTER_TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"未知怪物模板: {template_name}")
        return Monster(**template)

    @staticmethod
    def save_entity_to_json(entity, filepath: str):
        """保存 Character 或 Monster 到 JSON 文件"""
        data = entity.get_info()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"{entity.name} 已保存到 {filepath}")

    @staticmethod
    def load_entity_from_json(filepath: str):
        """从 JSON 文件加载实体，自动判断是 Character 还是 Monster"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 判断是角色还是怪物
        if "occupation" in data:  # Character 特有字段
            entity = Character(**data)
        elif "exp_reward" in data:  # Monster 特有字段
            entity = Monster(**data)
        else:
            entity = Character(**data)  # 默认当 Character
        print(f"{entity.name} 已从 {filepath} 加载")
        return entity
