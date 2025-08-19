import random, json
from dataclasses import asdict
from demo_dnd import GameState, ai_generate_scene, ai_resolve, roll_d20, outcome_from_roll, gather_effect_tags, choice_advantage, apply_player_updates, save_game, load_game

class GameEngine:
    def __init__(self):
        self.state = load_game() or GameState()
        if "seed" not in self.state.context:
            self.state.context["seed"] = "雾锁山道上的旧驿"
            self.state.story_log.append("启程于雾锁山道，旧驿风铃自鸣。")
        self.state.recent_checks = self.state.recent_checks[-3:]

    def set_player_name(self, name:str):
        if name: self.state.player.name = name
        save_game(self.state)

    def get_scene(self):
        eff = gather_effect_tags(self.state.player)
        scene = ai_generate_scene(self.state)
        valid_tags = ["perception","stealth","social","athletics","mystic","survival","insight"]
        recent = set(self.state.recent_checks[-3:])
        for ch in scene.get("choices",[]):
            tag = ch.get("check_tag","")
            if tag in recent:
                ch["check_tag"] = random.choice([t for t in valid_tags if t not in recent] or valid_tags)
        return scene

    def resolve_choice(self, choice_idx:int):
        scene = self.get_scene()
        choices = scene.get("choices",[])
        if not (0 <= choice_idx < len(choices)):
            return {"error":"invalid choice"}
        chosen = choices[choice_idx]
        ctag = chosen.get("check_tag","")
        self.state.recent_checks.append(ctag)

        eff = gather_effect_tags(self.state.player)
        mode = choice_advantage(chosen.get("choice_tags",[]), eff, self.state.player.conditions)
        r = roll_d20(mode)
        oc = outcome_from_roll(r)

        res = ai_resolve(self.state, chosen, r, oc)
        apply_player_updates(self.state.player, res.get("player_update") or {})
        ctxu = res.get("context_update") or {}
        self.state.context.update(ctxu)
        if "seed" not in self.state.context and chosen.get("leads"):
            self.state.context["seed"] = chosen["leads"]

        self.state.story_log.append(res.get("log_entry",""))
        self.state.turn += 1
        save_game(self.state)

        return {
            "scene": scene,
            "choice": chosen,
            "d20": r,
            "mode": mode,
            "outcome": oc,
            "resolution": res,
            "player": asdict(self.state.player)
        }
