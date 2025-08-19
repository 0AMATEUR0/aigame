
def battle(player, enemy):
    print(f"\n战斗开始！{player.name} VS {enemy.name}")
    round_num = 1
    while player.is_alive() and enemy.is_alive():
        print(f"\n--- 回合 {round_num} ---")
        player.attack(enemy)
        if not enemy.is_alive():
            print(f"{enemy.name} 倒下了！{player.name} 获胜！")
            break
        enemy.attack(player)
        if not player.is_alive():
            print(f"{player.name} 倒下了！{enemy.name} 获胜！")
            break
        round_num += 1