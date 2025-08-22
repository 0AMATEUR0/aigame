class BattleManager:
    def start_battle(self, monster, player):
        print(f"Encountered {monster['name']}! HP: {monster['hp']}")
        monster_hp = monster["hp"]
        while monster_hp > 0 and player.hp > 0:
            # 玩家攻击
            damage = player.get_attack_power()
            monster_hp -= damage
            print(f"You attack {monster['name']} for {damage} damage. Monster HP: {max(monster_hp,0)}")
            if monster_hp <= 0:
                break
            # 怪物攻击
            player.hp -= monster["attack"]
            print(f"{monster['name']} attacks you for {monster['attack']} damage. Your HP: {max(player.hp,0)}")
        if player.hp <= 0:
            return "You died! Game Over."
        else:
            return f"{monster['name']} defeated!"
