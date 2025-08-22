# main.py (pygame 入口)
import pygame
from game.Entity.character import Character
from game.Entity.monster import Monster
from game.Item.item import Weapon

pygame.init()

# 窗口
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("AI DnD Game")

# 创建角色与怪物
player = Character(occupation="Soldier", deputy_occupation="Fighter")
monster = Monster(exp_reward=50, item_reward=["Gold Coin"])

# 示例装备
sword = Weapon("Sword", damage_dice="1d8", attack_bonus=2)
player.add_item(sword)
player.equip(sword)

# 游戏主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((30, 30, 30))
    # TODO: 绘制角色、怪物、UI
    pygame.display.flip()

pygame.quit()
