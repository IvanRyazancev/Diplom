import pygame
import sys
from settings import FPS, WHITE, BLUE, GREEN
from player import Player
from level import Level

# pygame.mixer.pre_init(44100, -16, 2, 256)
pygame.init()
pygame.mixer.init()

sound_shoot = pygame.mixer.Sound("src/sounds/shoot.mp3")
sound_shoot.set_volume(0.5)

sound_hit = pygame.mixer.Sound("src/sounds/hit.wav")
sound_hit.set_volume(0.7)

sound_click = pygame.mixer.Sound("src/sounds/shoot_2.mp3")
sound_click.set_volume(0.3)

# --------------------------------------------
#  Глобальные переменные (пример)
# --------------------------------------------
WIDTH, HEIGHT = 950, 500
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


# --------------------------------------------
#  Вспомогательные функции
# --------------------------------------------

def draw_gradient_background(surf, top_color, bottom_color):
    """
    Рисует простой вертикальный градиент от top_color к bottom_color.
    """
    rect = surf.get_rect()
    # Высота экрана
    height = rect.height

    for y in range(height):
        # Вычисляем пропорцию между top_color и bottom_color
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        pygame.draw.line(surf, (r, g, b), (0, y), (rect.width, y))


def draw_button(surf, rect, text, font, mouse_pos):
    """
    Рисует кнопку (прямоугольник + текст).
    Подсвечивает кнопку, если курсор мыши внутри rect.
    """
    (mx, my) = mouse_pos
    color_normal = (70, 70, 70)
    color_hovered = (120, 120, 120)
    text_color = (255, 255, 255)

    # Если курсор в пределах кнопки — подсветить
    if rect.collidepoint(mx, my):
        pygame.draw.rect(surf, color_hovered, rect, border_radius=8)
    else:
        pygame.draw.rect(surf, color_normal, rect, border_radius=8)

    # Рисуем текст по центру кнопки
    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)
    surf.blit(text_surf, text_rect)


# --------------------------------------------
#  Меню настроек (регулировка громкости)
# --------------------------------------------
def settings_menu():
    font = pygame.font.SysFont(None, 50)

    # Берём текущую громкость (0.0 - 1.0)
    current_volume = pygame.mixer.music.get_volume()

    # Параметры ползунка
    slider_width = 300
    slider_height = 30
    slider_x = (WIDTH - slider_width) // 2
    slider_y = 220

    # Для отслеживания, «таскает» ли пользователь ползунок
    dragging = False

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False  # Возвращаемся в главное меню

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    # Проверяем, кликнул ли пользователь по ползунку
                    # Считаем, что ползунком считается прямоугольник [slider_x..slider_x+slider_width]
                    # и по высоте [slider_y..slider_y+slider_height].
                    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
                    if slider_rect.collidepoint(mouse_pos):
                        dragging = True
                        # Обновляем громкость сразу
                        current_volume = (mouse_pos[0] - slider_x) / slider_width
                        current_volume = max(0.0, min(1.0, current_volume))
                        pygame.mixer.music.set_volume(current_volume)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False

            elif event.type == pygame.MOUSEMOTION:
                # Если пользователь «тащит» ползунок
                if dragging:
                    current_volume = (mouse_pos[0] - slider_x) / slider_width
                    current_volume = max(0.0, min(1.0, current_volume))
                    pygame.mixer.music.set_volume(current_volume)

        # Рисуем фон (градиент для красоты)
        draw_gradient_background(screen, (30, 10, 70), (5, 5, 30))

        # Заголовок
        title = font.render("Настройки", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title, title_rect)

        # Текст громкости
        volume_text = font.render(f"Громкость: {int(current_volume * 100)}%", True, (220, 220, 220))
        volume_rect = volume_text.get_rect(center=(WIDTH // 2, 150))
        screen.blit(volume_text, volume_rect)

        # Отрисовка "полоски" (background) для громкости
        pygame.draw.rect(screen, (100, 100, 100), (slider_x, slider_y, slider_width, slider_height), border_radius=8)

        # Отрисовка "залитой части" (синий цвет, например)
        fill_width = int(current_volume * slider_width)
        pygame.draw.rect(screen, (0, 120, 200), (slider_x, slider_y, fill_width, slider_height), border_radius=8)

        # Подпись о возврате
        tip = font.render("ESC - вернуться в меню", True, (180, 180, 180))
        tip_rect = tip.get_rect(center=(WIDTH // 2, 350))
        screen.blit(tip, tip_rect)

        pygame.display.flip()
        clock.tick(FPS)


# --------------------------------------------
#  Главное меню
# --------------------------------------------
def main_menu():
    pygame.mixer.music.stop()
    pygame.mixer.music.load("src/music/back_music.mp3")
    pygame.mixer.music.set_volume(0.1)  # Стартовая громкость
    pygame.mixer.music.play(-1)  # -1 => играть в цикле

    font_big = pygame.font.SysFont(None, 72)
    font_small = pygame.font.SysFont(None, 50)

    # Координаты и размеры "кнопок"
    start_button_rect = pygame.Rect(350, 180, 250, 60)
    settings_button_rect = pygame.Rect(350, 260, 250, 60)
    quit_button_rect = pygame.Rect(350, 340, 250, 60)

    in_menu = True
    while in_menu:
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                channel = pygame.mixer.find_channel(True)  # Найти свободный канал (или создать)
                channel.play(sound_click)

                if event.button == 1:  # Левая кнопка мыши
                    if start_button_rect.collidepoint(event.pos):
                        # Начать игру
                        in_menu = False
                    elif settings_button_rect.collidepoint(event.pos):
                        # Переход в меню настроек
                        settings_menu()
                    elif quit_button_rect.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

        # Рисуем фон (градиент)
        draw_gradient_background(screen, (50, 50, 150), (20, 20, 60))

        # Заголовок
        title_surface = font_big.render("Wizardo", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(WIDTH // 2, 80))
        screen.blit(title_surface, title_rect)

        # Кнопки
        draw_button(screen, start_button_rect, "Начать игру", font_small, mouse_pos)
        draw_button(screen, settings_button_rect, "Настройки", font_small, mouse_pos)
        draw_button(screen, quit_button_rect, "Выход", font_small, mouse_pos)

        pygame.display.flip()
        clock.tick(FPS)


# Определение уровней

def victory_screen(screen):
    """Отображает экран победы в том же окне, пока пользователь не выйдет."""
    font = pygame.font.SysFont(None, 60)
    victory_loop = True
    while victory_loop:
        # 1) События
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Например, возвращаем в главное меню
                    main_menu()
                    return
                elif event.key == pygame.K_r:
                    # Если хотите перезапустить уровень
                    victory_loop = False  # Прервём этот цикл => вернёмся в main_game

        # 2) Рисуем фон, текст
        screen.fill((30, 30, 30))
        # Надпись "ПОБЕДА!"
        victory_text = font.render("ПОБЕДА!", True, (255, 215, 0))
        victory_rect = victory_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        screen.blit(victory_text, victory_rect)

        # Пример счёта (заглушка). Может быть, count_killed_enemies, etc.
        score_text = font.render("Очки: 999", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10))
        screen.blit(score_text, score_rect)

        tip_text = font.render("ESC - меню, R - перезапуск", True, (200, 200, 200))
        tip_rect = tip_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 80))
        screen.blit(tip_text, tip_rect)

        # 3) Обновляем экран
        pygame.display.flip()
        clock.tick(FPS)


def main_game():
    pygame.mixer.music.stop()
    pygame.mixer.music.load("src/music/for_battle.mp3")
    pygame.mixer.music.set_volume(0.1)  # Стартовая громкость
    pygame.mixer.music.play(-1)  # -1 => играть в цикле

    levels = [
        [
            "11111111111111F1111111",
            "1      1 P  1        1",
            "1      1    1111111 T1",
            "1  E   1    1        1",
            "1           1        1",
            "1      1    1E       1",
            "111 111111111        1",
            "1           1   E    1",
            "1  E   1    S        1",
            "1111111111111111111111"
        ],
        [
            "1111111111111111111",
            "1         P       1",
            "1                 1",
            "1   1         1   1",
            "1                 1",
            "1                 1",
            "1   1         1   1",
            "1       B         1",
            "1                 1",
            "1111111111111111111"
        ],
    ]

    current_level = 0

    screen = pygame.display.set_mode((950, 500))
    level = Level(levels[current_level])

    screen = pygame.display.set_mode((level.width, level.height))
    # Загружаем изображение сердечка
    heart_image = pygame.image.load("src/sprites/sheart.png").convert_alpha()
    heart_image = pygame.transform.scale(heart_image, (32, 32))  # Масштабируем сердечко

    def draw_lives(screen, lives):
        """Рисует сердечки в правом верхнем углу."""
        for i in range(lives):
            screen.blit(heart_image, (850 - i * 40, 10))  # Отступ между сердечками

    pygame.display.set_caption(f"Моя Игра - Уровень {current_level + 1}")

    # Создаем игрока
    player = Player(level.start_pos[0], level.start_pos[1], "src/sprites/wizard_tiles.png", 32,
                    32, sound_shoot)
    enemies = level.enemies

    # Шрифт для «Game Over»
    font_game_over = pygame.font.SysFont(None, 60)

    running = True
    while running:
        delta_time = clock.tick(FPS)

        # 1) Считываем события
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.shoot()

        # 2) Обновляем логику, если игрок ещё не умер (либо анимация смерти уже идёт, но не завершилась)
        #    Важно продолжать вызывать update, чтобы кадры смерти переключались!

        current_time = pygame.time.get_ticks()

        player.update(delta_time, level.walls)

        for trap in level.traps:
            if (player.rect.colliderect(trap)):
                player.rect.x, player.rect.y = level.start_pos
        for bonus in level.bonuses:
            if (player.rect.colliderect(bonus)):
                player.lives += 1
                level.bonuses.remove(bonus)

        for enemy in enemies:
            enemy.update(player, level.walls, delta_time, current_time)

        for enemy in enemies:
            if hasattr(enemy, 'is_dead'):
                if (enemy.is_dead):
                    victory_screen(screen)
        # 3) Проверяем столкновения с врагами (уменьшаем жизни и вызываем die(), если <= 0)

        for enemy in enemies:

            if player.rect.colliderect(enemy.rect):
                if not player.invincible:  # Если неуязвимость не активна
                    player.lives -= 1
                    sound_hit.play()

                    # Включаем i-frames
                    player.invincible = True
                    player.invincible_timer = player.invincible_time

                    if player.lives <= 0:
                        player.die()
                # Противника не удаляем!
                break

        # 4) Проверяем финиш
        if level.finish_rect and player.rect.colliderect(level.finish_rect):
            current_level += 1
            if current_level >= len(levels):
                print("Игра пройдена!")
                pygame.quit()
                sys.exit()
            else:
                level = Level(levels[current_level])
                screen = pygame.display.set_mode((level.width, level.height))
                pygame.display.set_caption(f"Моя Игра - Уровень {current_level + 1}")
                player = Player(level.start_pos[0], level.start_pos[1], "src/sprites/wizard_tiles.png",
                                32, 32, sound_shoot)
                enemies = level.enemies

        # 5) Обновляем снаряды
        player.update_bullets(level.walls, enemies)

        # 6) Отрисовка текущего кадра
        screen.fill(GREEN)
        level.draw(screen)

        # Отрисовываем игрока и врагов
        player.draw(screen)
        player.draw_bullets(screen)
        draw_lives(screen, player.lives)
        for enemy in enemies:
            enemy.draw(screen)

        pygame.display.flip()

        # 7) Теперь проверяем: если жизнь <= 0 и анимация смерти уже достигла последнего кадра — показываем «Game Over»

        if player.lives <= 0 and player.is_dead:
            # Проверим, достиг ли игрок конца анимации смерти:
            current_anim = player.animations[player.current_animation]
            # Если мы на последнем кадре (или превысили его)
            if player.current_frame >= len(current_anim) - 1:
                # Запускаем под-цикл «Game Over»
                game_over_loop = True
                while game_over_loop:
                    # Рисуем тот же кадр (окружение, фон) — чтобы всё оставалось на экране
                    screen.fill(GREEN)
                    level.draw(screen)

                    for e in enemies:
                        e.draw(screen)

                    # Рисуем игрока на последнем кадре смерти
                    player.draw(screen)

                    # Выводим текст
                    go_text = font_game_over.render("GAME OVER", True, (255, 0, 0))
                    go_rect = go_text.get_rect(center=(screen.get_width() // 2, 100))
                    screen.blit(go_text, go_rect)

                    info_text = font_game_over.render("ESC - меню, R - перезапуск", True, (255, 255, 255))
                    info_rect = info_text.get_rect(center=(screen.get_width() // 2, 200))
                    screen.blit(info_text, info_rect)

                    pygame.display.flip()
                    clock.tick(FPS)

                    # События внутри экрана «Game Over»
                    for ev in pygame.event.get():
                        if ev.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        elif ev.type == pygame.KEYDOWN:
                            if ev.key == pygame.K_ESCAPE:
                                # Выходим в главное меню
                                main_menu()
                                main_game()
                                return  # Полностью выходим из main_game, т.к. меню перезапустит/закроет игру

                            elif ev.key == pygame.K_r:
                                # Перезапуск текущего уровня
                                level = Level(levels[current_level])
                                player = Player(level.start_pos[0], level.start_pos[1],
                                                "src/sprites/wizard_tiles.png", 32, 32, sound_shoot)
                                enemies = level.enemies
                                player.lives = 3  # Восстанавливаем жизни

                                game_over_loop = False  # выходим из «Game Over»
                # Когда вышли из под-цикла (нажали R) — игрок/уровень пересозданы, игра продолжается


if __name__ == '__main__':
    main_menu()
    main_game()
