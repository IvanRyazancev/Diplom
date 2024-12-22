import pygame

from boss import Boss
from settings import WIDTH, HEIGHT


class Player:
    def __init__(self, x, y, sprite_sheet_path, tile_width, tile_height, sound_shoot):
        self.invincible = False  # Флаг неуязвимости
        self.invincible_time = 2000  # (мс) сколько длится неуязвимость
        self.invincible_timer = 0  # Счётчик оставшейся неуязвимости
        self.rect = pygame.Rect(x, y, 25, 31)
        self.speed = 4
        self.sound_shoot = sound_shoot
        self.bullets = []
        self.direction = pygame.Vector2(0, -1)  # Начальное направление (вверх)
        self.facing_right = True  # Направление взгляда (True = вправо)
        self.is_shooting = False  # Флаг анимации стрельбы
        self.is_dead = False  # Флаг анимации смерти
        self.lives = 5

        # Индексы анимаций:
        # 0 - idle, 1 - walk, 6 - death, 7 - shoot (по вашему коду)
        self.animations = self.load_sprite_sheet(sprite_sheet_path, tile_width, tile_height)
        self.current_animation = 0
        self.current_frame = 0
        self.frame_timer = 0
        self.animation_speed = 150  # Мс на кадр

    def load_sprite_sheet(self, filepath, tile_width, tile_height):
        """Загружает и разбивает спрайтовый лист на кадры, пропуская пустые кадры."""
        sheet = pygame.image.load(filepath).convert_alpha()
        sheet_width, sheet_height = sheet.get_size()
        sprites = []

        for y in range(0, sheet_height, tile_height):
            row = []
            for x in range(0, sheet_width, tile_width):
                rect = pygame.Rect(x, y, tile_width, tile_height)
                frame = sheet.subsurface(rect)
                if not self.is_frame_empty(frame):
                    row.append(frame)
            sprites.append(row)
        return sprites

    def is_frame_empty(self, frame):
        """Проверяет, является ли кадр пустым (все пиксели прозрачные)."""
        for x in range(frame.get_width()):
            for y in range(frame.get_height()):
                # Альфа-канал > 0 означает, что пиксель не полностью прозрачный
                if frame.get_at((x, y))[3] > 0:
                    return False
        return True

    def move(self, walls):
        """Двигается, если жив. Стрельба (is_shooting) — не блокирует движение."""
        if self.is_dead:
            return  # Не двигаемся, если мертвы

        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(0, 0)

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            movement.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            movement.x -= 1
            self.facing_right = False
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            movement.x += 1
            self.facing_right = True

        # Если есть движение — переключаемся на walk, иначе idle
        if movement.length_squared() > 0:
            movement = movement.normalize() * self.speed
            self.direction = movement.normalize()
            # Если не мертвы и не стреляем, то ставим анимацию walk
            if not self.is_dead and not self.is_shooting:
                self.set_animation(1)  # 1: walk
        else:
            if not self.is_dead and not self.is_shooting:
                self.set_animation(0)  # 0: idle

        # Коллизии (x, y)
        old_rect = self.rect.inflate(-1, -1)
        self.rect.x += movement.x
        self.collide(walls, 'x', old_rect)
        self.rect.y += movement.y
        self.collide(walls, 'y', old_rect)

    def set_animation(self, animation_index):
        """Меняем анимацию. Сбрасываем кадр в 0, если это новая анимация."""
        # Если уже умерли и кадр дошёл до конца, не переключаемся
        if self.is_dead and self.current_animation == 6:
            # Анимация смерти (индекс 6) — не перезаписываем
            return

        if self.current_animation != animation_index:
            self.current_animation = animation_index
            self.current_frame = 0
            self.frame_timer = 0

    def update_animation(self, delta_time):
        """Обновляем текущий кадр анимации."""
        self.frame_timer += delta_time
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            self.current_frame += 1

            # Если дошли до конца текущей анимации
            if self.current_frame >= len(self.animations[self.current_animation]):
                # Если анимация смерти — останавливаемся на последнем кадре
                if self.is_dead and self.current_animation == 6:
                    self.current_frame = len(self.animations[6]) - 1
                # Если анимация стрельбы
                elif self.is_shooting and self.current_animation == 7:
                    # Закончили стрельбу, возвращаемся в idle
                    self.is_shooting = False
                    self.set_animation(0)  # idle
                else:
                    # Для walk / idle — зацикливаем
                    self.current_frame = 0

    def collide(self, walls, direction, old_rect):
        """Не даём игроку пройти сквозь стены."""
        for wall in walls:
            if self.rect.colliderect(wall):
                if direction == 'x':
                    self.rect.x = old_rect.x
                elif direction == 'y':
                    self.rect.y = old_rect.y

    def shoot(self):

        """Стреляем (если не мертвы и не в процессе стрельбы). Пуля создаётся сразу."""
        if self.is_dead:
            return
        self.sound_shoot.play()
        self.is_shooting = True
        # 1) Создаём пулю сразу же
        self.create_bullet()
        # 2) Ставим анимацию стрельбы
        self.set_animation(7)  # 7: shoot

    def die(self):
        """Запускаем анимацию смерти (индекс 6)."""
        if self.is_dead:
            return  # Уже мёртв
        self.is_dead = True
        self.set_animation(6)  # 6: death

    def create_bullet(self):
        """Создаёт снаряд (пуля) в направлении self.direction."""
        offset = self.direction * (self.rect.width // 2 + 5)
        bullet_pos = pygame.Vector2(self.rect.center) + offset

        bullet = {
            'bounced': False,
            'rect': pygame.Rect(bullet_pos.x - 5, bullet_pos.y - 5, 10, 10),
            'direction': self.direction.copy()
        }
        self.bullets.append(bullet)

    def update_bullets(self, walls, enemies):
        """Обновляем полёт пуль, проверяем столкновения со стенами/врагами/игроком."""
        if self.is_dead:
            return  # Если игрок мертв, не двигаем его пули

        bullets_to_remove = []
        for bullet in self.bullets:
            # Движение пули
            bullet['rect'].x += bullet['direction'].x * 10
            bullet['rect'].y += bullet['direction'].y * 10

            # Столкновение с врагами
            for enemy in enemies:
                if bullet['rect'].colliderect(enemy.rect):
                    bullets_to_remove.append(bullet)  # пуля исчезает

                    if isinstance(enemy, Boss):
                        # Если это босс, уменьшаем здоровье
                        enemy.take_damage(1)
                        # Если босс погиб после урона, только тогда удаляем

                    else:
                        # Обычный враг умирает мгновенно
                        if enemy in enemies:
                            enemies.remove(enemy)

                    # Выходим из цикла, т.к. пуля уже потрачена
                    break

            # Столкновение со стенами (отскок один раз)
            for wall in walls:
                if bullet['rect'].colliderect(wall):
                    if bullet['bounced']:
                        bullets_to_remove.append(bullet)
                    else:
                        dx = bullet['rect'].centerx - wall.centerx
                        dy = bullet['rect'].centery - wall.centery
                        if abs(dx) > abs(dy):  # Горизонтальное столкновение
                            bullet['direction'].x *= -1
                        else:  # Вертикальное столкновение
                            bullet['direction'].y *= -1
                        bullet['bounced'] = True
                    break

            # Попадание в самого себя
            # if bullet['rect'].colliderect(self.rect):
            # bullets_to_remove.append(bullet)
            # if not self.invincible:  # Если неуязвимость не активна
            # self.lives -= 1

            # Включаем i-frames
            # self.invincible = True
            # self.invincible_timer = self.invincible_time

            # if self.lives <= 0:
            #    self.die()

            # break

            # Проверяем выход за границы
            if (bullet['rect'].x < 0 or bullet['rect'].x > WIDTH or
                    bullet['rect'].y < 0 or bullet['rect'].y > HEIGHT):
                bullets_to_remove.append(bullet)

        # Удаляем нужные пули
        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)

    def draw_bullets(self, screen):
        """Рисуем все пули (простой прямоугольник)."""
        for bullet in self.bullets:
            pygame.draw.rect(screen, (0, 0, 255), bullet['rect'])

    def draw(self, screen):
        if self.invincible:
            # Мигаем с некоторой частотой
            # (Например, раз в 200 мс скрываем спрайт)
            t = pygame.time.get_ticks() // 200
            if t % 2 == 0:
                # Рисуем обычный спрайт
                frame = self.animations[self.current_animation][self.current_frame]
                screen.blit(frame, self.rect.topleft)
            else:
                # Пропускаем кадр, не рисуем (эффект мигания)
                pass
        else:
            # Обычная отрисовка
            frame = self.animations[self.current_animation][self.current_frame]
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, self.rect.topleft)
        """Рисуем нужный кадр анимации (учитывая направление)."""

    def update(self, delta_time, walls):
        """Главный метод, вызывается каждый кадр для обновления логики игрока."""
        # Снижаем таймер неуязвимости
        if self.invincible:
            self.invincible_timer -= delta_time
            if self.invincible_timer <= 0:
                self.invincible_timer = 0
                self.invincible = False

        self.move(walls)
        self.update_animation(delta_time)
