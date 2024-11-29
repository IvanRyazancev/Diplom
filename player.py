import pygame
from settings import WIDTH, HEIGHT


class Player:
    def __init__(self, x, y, sprite_sheet_path, tile_width, tile_height):
        self.rect = pygame.Rect(x, y, 40, 40)  # Уменьшенный размер для лучшего восприятия
        self.speed = 4  # Скорость движения
        self.bullets = []  # Список снарядов
        self.direction = pygame.Vector2(1, 0)  # Начальное направление (вверх)
        self.facing_right = True  # Направление взгляда (True = вправо)
        self.is_shooting = False  # Флаг для анимации стрельбы
        self.is_dead = False  # Флаг для анимации смерти
        self.lives = 3

        # Загрузка спрайтового листа и разделение на кадры
        self.animations = self.load_sprite_sheet(sprite_sheet_path, tile_width, tile_height)
        self.current_animation = 0  # 0: idle, 1: walk, 2: shoot, 3: death
        self.current_frame = 0
        self.frame_timer = 0
        self.animation_speed = 50  # Скорость анимации (мс на кадр)

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

                # Проверяем, является ли кадр "пустым"
                if not self.is_frame_empty(frame):
                    row.append(frame)

            sprites.append(row)

        return sprites

    def is_frame_empty(self, frame):
        """Проверяет, является ли кадр пустым (все пиксели прозрачные)."""
        for x in range(frame.get_width()):
            for y in range(frame.get_height()):
                if frame.get_at((x, y))[3] > 0:  # Если альфа-канал > 0, кадр не пустой
                    return False
        return True

    def move(self, walls):
        if self.is_shooting or self.is_dead:
            return  # Игрок не двигается, если стреляет или умирает

        keys = pygame.key.get_pressed()
        movement = pygame.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            movement.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            movement.x -= 1
            self.facing_right = False  # Смотрим влево
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            movement.x += 1
            self.facing_right = True  # Смотрим вправо

        if movement.length_squared() > 0:
            movement = movement.normalize() * self.speed
            self.direction = movement.normalize()  # Обновляем направление
            self.set_animation(1)  # 1: walk анимация
        else:
            self.set_animation(0)  # 0: idle анимация

        old_rect = self.rect.copy()
        self.rect.x += movement.x
        self.collide(walls, 'x', old_rect)
        # self.collide_water(waters, 'x', old_rect)
        self.rect.y += movement.y
        self.collide(walls, 'y', old_rect)
        # self.collide_water(waters, 'y', old_rect)

    def set_animation(self, animation_index):
        """Меняет текущую анимацию."""
        if self.is_dead and self.current_frame >= len(self.animations[self.current_animation]):  # Не меняем анимацию, если игрок мертв
            return
        if self.current_animation != animation_index:
            self.current_animation = animation_index
            self.current_frame = 0  # Сброс на первый кадр

    def update_animation(self, delta_time):
        """Обновляет текущий кадр анимации."""
        self.frame_timer += delta_time
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            self.current_frame += 1

            # Проверяем завершение анимации
            if self.current_frame >= len(self.animations[self.current_animation]):
                if self.is_shooting:
                    self.is_shooting = False  # Завершение анимации стрельбы
                    self.create_bullet()  # Создаем снаряд после завершения анимации
                    self.set_animation(0)  # Возвращаемся в idle
                elif self.is_dead:
                    # Фиксируем последний кадр анимации смерти
                    self.current_frame = len(self.animations[self.current_animation]) - 1
                else:
                    # Зацикливаем анимацию
                    self.current_frame = 0


    # Проверяем завершение анимации
            if self.current_frame >= len(self.animations[self.current_animation]):
                if self.is_shooting:
                    self.is_shooting = False  # Завершение анимации стрельбы
                    self.set_animation(0)  # Возвращаемся в idle
                elif self.is_dead:
                    self.current_frame = len(self.animations[self.current_animation]) - 1  # Остаемся на последнем кадре
                else:
                    self.current_frame = 0  # Зацикливаем анимацию

    def collide(self, walls, dir, old_rect): # функция столкновения со стенами
        for wall in walls:
            if self.rect.colliderect(wall):
                if dir == 'x':
                    self.rect.x = old_rect.x
                elif dir == 'y':
                    self.rect.y = old_rect.y

    def collide_water(self, waters, dir, old_rect): # функция столкновения с водой
        for water in waters:
            if self.rect.colliderect(water):
                if dir == 'x':
                    self.rect.x = old_rect.x
                elif dir == 'y':
                    self.rect.y = old_rect.y

    def shoot(self):
        if self.is_shooting or self.is_dead:
            return  # Не стреляем, если уже стреляем или мертвы

        self.is_shooting = True
        self.set_animation(7)  # 7: shoot анимация



    def die(self):
        """Управляет анимацией смерти."""
        if self.is_dead:
            return  # Уже мертв
        self.is_dead = True
        self.set_animation(6)  # 6: death анимация
        self.current_frame = 0  # Начинаем с первого кадра анимации смерти

    def create_bullet(self):
        """Создает снаряд после завершения анимации стрельбы."""
        # Вычисляем смещение для появления снаряда
        offset = self.direction * (self.rect.width // 2 + 5)  # Смещение за границу игрока
        bullet_pos = pygame.Vector2(self.rect.center) + offset

        # Создаем снаряд, движущийся в текущем направлении
        bullet = {
            'bounced': False,
            'rect': pygame.Rect(bullet_pos.x - 5, bullet_pos.y - 5, 10, 10),  # Снаряд немного смещен от игрока
            'direction': self.direction.copy()
        }
        self.bullets.append(bullet)

    def update_bullets(self, walls, enemies):
        if self.is_dead:
            return  # Не обновляем снаряды, если мертв

        bullets_to_remove = []
        for bullet in self.bullets:
            bullet['rect'].x += bullet['direction'].x * 10
            bullet['rect'].y += bullet['direction'].y * 10

            for enemy in enemies:
                if bullet['rect'].colliderect(enemy.rect):
                    if bullet in self.bullets:
                        bullets_to_remove.append(bullet)
                    if enemy in enemies:
                        enemies.remove(enemy)
                    break
            for wall in walls:
                if bullet['rect'].colliderect(wall):
                    if bullet in self.bullets:
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

            if bullet['rect'].colliderect(self.rect):
                self.die()  # Игрок умирает от своего снаряда
                bullets_to_remove.append(bullet)
                break

            if (bullet['rect'].x < 0 or bullet['rect'].x > WIDTH or
                    bullet['rect'].y < 0 or bullet['rect'].y > HEIGHT):
                if bullet in self.bullets:
                    bullets_to_remove.append(bullet)

            if (bullet['rect'].x < 0 or bullet['rect'].x > WIDTH or
                    bullet['rect'].y < 0 or bullet['rect'].y > HEIGHT):
                if bullet in self.bullets:
                    bullets_to_remove.append(bullet)

        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)

    def draw_bullets(self, screen):
        for bullet in self.bullets:
            pygame.draw.rect(screen, (0, 0, 255), bullet['rect'])

    def draw(self, screen):
        # Отрисовка текущего кадра анимации
        frame = self.animations[self.current_animation][self.current_frame]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)  # Переворачиваем по горизонтали
        screen.blit(frame, self.rect.topleft)

    def update(self, delta_time, walls):
        self.move(walls)
        self.update_animation(delta_time)