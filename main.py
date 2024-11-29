import pygame
import sys

from enemy import Enemy
from settings import FPS, WHITE, BLUE, GREEN
from player import Player
from level import Level

pygame.init()
clock = pygame.time.Clock()

icon = pygame.image.load('src/icon.png')  # загружаем иконку для всего проекта
pygame.display.set_icon(icon)

# Определение уровней
levels = [
    [
        "1111111111111111111",
        "1    E       E    1",
        "1WWWW 1111111 WWWW1",
        "1         1   1   1",
        "1P    T   1 W 1  F1",
        "1           W 1   1",
        "1111 11111111   111",
        "1   E            E1",
        "1111111111111111111"
    ],
    [
        "1111111111111111111",
        "1 E  P            1",
        "11111111111111111 1",
        "1                 1",
        "1 11111111111111111",
        "1                 1",
        "1   1    B E  1   1",
        "1                 1",
        "1  E              1",
        "111111111F111111111"
    ],
    [
        "1111111111111111111",
        "1         P       1",
        "1   111      111  1",
        "1         1       1",
        "1   E    1 1  E   1",
        "1         1       1",
        "1   1         1   1",
        "1                 1",
        "1   E    D    E   1",
        "111111111F111111111"
    ],

]

current_level = 0

screen = pygame.display.set_mode((1400, 500))
level = Level(levels[current_level])
screen = pygame.display.set_mode((level.width, level.height))
# Загружаем изображение сердечка
heart_image = pygame.image.load("src/sprites/sheart.png").convert_alpha()
heart_image = pygame.transform.scale(heart_image, (32, 32))  # Масштабируем сердечко

def draw_lives(screen, lives):
    """Рисует сердечки в правом верхнем углу."""
    for i in range(lives):
        screen.blit(heart_image, (level.width - i * 50 - 50, 10))  # Отступ между сердечками 40 пикселей


# Устанавливаем размер экрана на основе размеров уровня

pygame.display.set_caption(f"Обитель зла. Начало. - Уровень {current_level + 1}")
# player = Player(x, y, "src/sprites/wizard_tiles.png", 32, 32)
player = Player(level.start_pos[0], level.start_pos[1], "src/sprites/wizard_tiles.png",
                32, 32)

enemies = level.enemies
enemies_boss = level.enemies_boss

while True:
    delta_time = clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()

    # Логика игры
    player.move(level.walls)
    # player.move(level.waters)

    for enemy in enemies:
        if player.rect.colliderect(enemy.rect):  # Проверяем столкновение с врагом
            player.lives -= 1  # Уменьшаем количество жизней
            enemies.remove(enemy)  # Убираем врага
            if player.lives <= 0:
                player.die()  # Вызываем метод смерти игрока
            break

    # Проверка достижения финиша
    if level.finish_rect and player.rect.colliderect(level.finish_rect):
        current_level += 1
        if current_level >= len(levels):
            print("Игра пройдена!")
            pygame.quit()
            sys.exit()
        else:
            level = Level(levels[current_level])
            screen = pygame.display.set_mode((level.width, level.height))
            pygame.display.set_caption(f"Обитель зла. Начало - Уровень {current_level + 1}")
            player = Player(level.start_pos[0], level.start_pos[1],
                            "src/sprites/wizard_tiles.png", 32, 32)
            enemies = level.enemies
            enemies_boss = level.enemies_boss

    # Обновление врагов

    for enemy in enemies:
        enemy.update(player, level.walls, delta_time)
        enemy.draw(screen)

    # Обновление снарядов
    player.update(delta_time, level.walls)
    player.update_bullets(level.walls, enemies)

    # Рендеринг
    screen.fill((112, 98, 7))
    level.draw(screen)
    player.draw(screen)
    player.draw_bullets(screen)
    draw_lives(screen, player.lives)

    for enemy in enemies:
        enemy.draw(screen)

    for boss in enemies_boss:
        boss.update(screen)  # Обновляем босса

    pygame.display.flip()
    clock.tick(FPS)
