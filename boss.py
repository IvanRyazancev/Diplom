
import pygame
import math
import random

class Boss:
    STATE_NORMAL = 0
    STATE_FINAL_BARRAGE = 1
    STATE_FINAL_CHAOS = 2

    def __init__(self, x, y, tile_size, arena_width=950, arena_height=500):
        width = tile_size * 2
        height = tile_size * 2
        self.rect = pygame.Rect(x, y, width, height)

        self.arena_width = arena_width
        self.arena_height = arena_height

        # Здоровье и «обычные» параметры
        self.max_health = 14
        self.health = self.max_health
        self.is_dead = False

        self.bullets = []
        self.shoot_cooldown = 1000
        self.last_shot_time = 0
        self.detect_radius = 300
        self.shots_left = 20  # Кол-во выстрелов в NORMAL

        # Параметры движения
        self.speed = 2.0
        angle = random.random() * 2 * math.pi
        self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.speed

        self.change_dir_cooldown = 3000
        self.last_change_dir_time = 0

        # Уклонение
        self.dodge_radius = 100
        self.dodge_strength = 1.0

        # Три стадии
        self.state = self.STATE_NORMAL

        # ------- FINAL_BARRAGE -------
        self.barrage_shoot_interval = 50  # мс между пулями в финальной/хаотичной стадии
        self.last_barrage_shot_time = 0
        self.center_target = (arena_width // 2, arena_height // 2)

        # Сколько длится стадия FINAL_BARRAGE (10 секунд)
        self.final_barrage_duration = 5000  # мс
        self.final_barrage_start_time = 0    # когда мы перешли в финальную стадию

        # ------- FINAL_CHAOS -------
        # Тут босс игнорирует стены и двигается хаотично, продолжая стрелять
        # Можно завести флаги/таймеры, но пока оставим бесконечно.

    def update(self, player, walls, delta_time, current_time):
        """Главная логика босса, вызывается каждый кадр."""
        if self.is_dead:

            return

        # Если здоровье < 50% или патроны кончились -> FINAL_BARRAGE (если ещё не началось)
        if (self.shots_left <= 0 or self.health <= self.max_health // 2) and self.state == self.STATE_NORMAL:
            self.state = self.STATE_FINAL_BARRAGE
            self.final_barrage_start_time = current_time  # Зафиксировали время начала

        # Если мы уже в FINAL_BARRAGE более 10 секунд -> переходим в FINAL_CHAOS
        if self.state == self.STATE_FINAL_BARRAGE:
            if (current_time - self.final_barrage_start_time) > self.final_barrage_duration:
                self.state = self.STATE_FINAL_CHAOS

        # Вызываем соответствующий метод обновления
        if self.state == self.STATE_NORMAL:
            self.update_normal(player, walls, delta_time, current_time)
        elif self.state == self.STATE_FINAL_BARRAGE:
            self.update_final_barrage(player, delta_time, current_time)
        elif self.state == self.STATE_FINAL_CHAOS:
            self.update_final_chaos(player, delta_time, current_time)

        # Обновляем пули
        self.update_bullets(walls, player)

    # -----------------------------
    # 1) NORMAL
    # -----------------------------
    def update_normal(self, player, walls, delta_time, current_time):
        # Двигаемся и уклоняемся
        self.move_around(walls, delta_time, current_time, player)
        # Стреляем в игрока, если видим
        distance = pygame.Vector2(self.rect.center).distance_to(player.rect.center)
        if distance < self.detect_radius and self.shots_left > 0:
            if current_time - self.last_shot_time >= self.shoot_cooldown:
                self.shoot_toward_player(player.rect.center)
                self.last_shot_time = current_time
                self.shots_left -= 1


# -----------------------------
    # 2) FINAL_BARRAGE (10 секунд)
    # -----------------------------
    def update_final_barrage(self, player, delta_time, current_time):
        """
        Босс идёт в центр, стоит на месте и спамит пули в случайных направлениях.
        Игнорируем уклонение, не трогаем стены.
        """
        center_pos = pygame.Vector2(self.center_target)
        to_center = center_pos - pygame.Vector2(self.rect.center)
        dist = to_center.length()

        # Идём в центр, если ещё не там
        if dist > 5:
            move_speed = 4.5
            direction = to_center.normalize()
            movement = direction * move_speed * (delta_time / 16.67)
            self.rect.x += movement.x
            self.rect.y += movement.y
        else:
            # На центре. Спамим пули
            if current_time - self.last_barrage_shot_time >= self.barrage_shoot_interval:
                self.shoot_random_bullet()
                self.last_barrage_shot_time = current_time

    # -----------------------------
    # 3) FINAL_CHAOS (хаотичное движение, игнор стен)
    # -----------------------------
    def update_final_chaos(self, player, delta_time, current_time):
        """
        Босс двигается хаотично, НЕ уклоняется, игнорирует стены
        (можно просто не вызывать check_collision_x / check_collision_y),
        продолжает выпускать случайные пули (поток).
        """
        # 1) Хаотично меняем направление время от времени
        if current_time - self.last_change_dir_time > self.change_dir_cooldown:
            self.change_direction()
            self.last_change_dir_time = current_time

        # 2) Двигаем rect (никаких коллизий со стенами)
        movement = self.velocity * (delta_time / 16.67)
        self.rect.x += movement.x
        self.rect.y += movement.y

        # Если вышли за арену — либо телепортируемся, либо отражаем
        # или просто оставим, пусть улетает, на ваш выбор.
        # Допустим, чтобы не вылетел далеко, сделаем «отражение» по краям экрана:
        if self.rect.left < 0 or self.rect.right > self.arena_width:
            self.velocity.x *= -1
        if self.rect.top < 0 or self.rect.bottom > self.arena_height:
            self.velocity.y *= -1

        # 3) Спам пуль
        if current_time - self.last_barrage_shot_time >= self.barrage_shoot_interval:
            self.shoot_random_bullet()
            self.last_barrage_shot_time = current_time

    # -----------------------------
    #   Общие методы стрельбы
    # -----------------------------
    def shoot_toward_player(self, target_pos):
        direction = pygame.Vector2(target_pos) - pygame.Vector2(self.rect.center)
        if direction.length_squared() > 0:
            direction = direction.normalize()
        bullet_speed = 7

        bullet_rect = pygame.Rect(self.rect.centerx, self.rect.centery, 10, 10)
        bullet = {
            'rect': bullet_rect,
            'direction': direction,
            'speed': bullet_speed
        }
        self.bullets.append(bullet)

    def shoot_random_bullet(self):
        """Стреляет пулей в случайную сторону из центра босса."""
        angle = random.uniform(0, 2 * math.pi)
        direction = pygame.Vector2(math.cos(angle), math.sin(angle))
        bullet_speed = 6

        bullet_rect = pygame.Rect(self.rect.centerx, self.rect.centery, 10, 10)
        bullet = {
            'rect': bullet_rect,
            'direction': direction,
            'speed': bullet_speed
        }
        self.bullets.append(bullet)

    # -----------------------------
    #   Обновление пуль
    # -----------------------------
    def update_bullets(self, walls, player):
        bullets_to_remove = []
        for bullet in self.bullets:
            # Движение пули
            bullet['rect'].x += bullet['direction'].x * bullet['speed']
            bullet['rect'].y += bullet['direction'].y * bullet['speed']


# Столкновение со стенами (кроме финального хаоса —
            # но тут пули всё равно можно уничтожать о стены)
            for wall in walls:
                if bullet['rect'].colliderect(wall):
                    bullets_to_remove.append(bullet)
                    break

            # Попадание в игрока
            if bullet['rect'].colliderect(player.rect):
                if not player.invincible:
                    player.lives -= 1
                    player.invincible = True
                    player.invincible_timer = player.invincible_time
                    if player.lives <= 0:
                        player.die()
                bullets_to_remove.append(bullet)
                continue

            # Если вышли за границы
            if (bullet['rect'].x < -50 or bullet['rect'].x > 2000 or
                bullet['rect'].y < -50 or bullet['rect'].y > 2000):
                bullets_to_remove.append(bullet)

        for b in bullets_to_remove:
            if b in self.bullets:
                self.bullets.remove(b)

    # -----------------------------
    #   ДВИЖЕНИЕ + УВОРОТ (NORMAL)
    # -----------------------------
    def move_around(self, walls, delta_time, current_time, player):
        # Меняем направление раз в 3 секунды
        if current_time - self.last_change_dir_time > self.change_dir_cooldown:
            self.change_direction()
            self.last_change_dir_time = current_time

        # Уклоняемся от пуль
        self.dodge_bullets(player)

        # Перемещение с учётом коллизии
        movement = self.velocity * (delta_time / 16.67)
        old_rect = self.rect.copy()

        self.rect.x += movement.x
        self.check_collision_x(walls, old_rect)
        self.rect.y += movement.y
        self.check_collision_y(walls, old_rect)

    def change_direction(self):
        angle = random.random() * 2 * math.pi
        self.velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * self.speed

    def dodge_bullets(self, player):
        if not hasattr(player, 'bullets'):
            return
        for b in player.bullets:
            dist = pygame.Vector2(self.rect.center).distance_to(b['rect'].center)
            if dist < self.dodge_radius:
                away = pygame.Vector2(self.rect.center) - pygame.Vector2(b['rect'].center)
                if away.length_squared() > 0:
                    away = away.normalize() * self.dodge_strength
                    self.velocity += away * 1.5
                if self.velocity.length() > self.speed * 2.5:
                    self.velocity = self.velocity.normalize() * (self.speed * 2.5)

    def check_collision_x(self, walls, old_rect):
        for wall in walls:
            if self.rect.colliderect(wall):
                self.rect.x = old_rect.x
                self.velocity.x *= -1
                break

    def check_collision_y(self, walls, old_rect):
        for wall in walls:
            if self.rect.colliderect(wall):
                self.rect.y = old_rect.y
                self.velocity.y *= -1
                break

    # -----------------------------
    #   ЗДОРОВЬЕ
    # -----------------------------
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:

            self.is_dead = True

    # -----------------------------
    #   РИСОВАНИЕ
    # -----------------------------
    def draw(self, screen):
        if not self.is_dead:
            pygame.draw.rect(screen, (200, 0, 0), self.rect)
            self.draw_health_bar(screen)
        for bullet in self.bullets:
            pygame.draw.rect(screen, (0, 0, 0), bullet['rect'])

    def draw_health_bar(self, screen):
        bar_width = self.rect.width
        bar_height = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - bar_height - 5
        pygame.draw.rect(screen, (0, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        health_ratio = self.health / self.max_health
        current_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, current_width, bar_height))