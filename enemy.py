import pygame
import math
from settings import WIDTH, HEIGHT


class Enemy:
    def __init__(self, x, y, speed, sprite_sheet_path, tile_width, tile_height, facing_right, patrol_points=None):
        self.rect = pygame.Rect(x, y, 40, 40)  # Размер врага
        self.speed = speed  # Скорость врага
        self.patrol_points = patrol_points  # Точки патрулирования
        self.current_point = 0
        self.direction = pygame.Vector2(0, 0)
        self.detect_radius = 200  # Радиус обнаружения игрока
        self.chasing = False
        self.last_known_position = None  # Последняя известная позиция игрока

        # Анимации
        self.animations = self.load_sprite_sheet(sprite_sheet_path, tile_width, tile_height)
        self.current_animation = 0  # 0: idle, 1: walk, 2: run, и т.д.
        self.current_frame = 0
        self.frame_timer = 0
        self.animation_speed = 100  # Скорость анимации (мс на кадр)
        self.facing_right = facing_right  # Направление врага (True = вправо)

    def load_sprite_sheet(self, filepath, tile_width, tile_height):
        """Загружает и разбивает спрайтовый лист на кадры."""
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
                if frame.get_at((x, y))[3] > 0:  # Если альфа-канал > 0, кадр не пустой
                    return False
        return True

    def set_animation(self, animation_index):
        """Меняет текущую анимацию."""
        if self.current_animation != animation_index:
            self.current_animation = animation_index
            self.current_frame = 0  # Сброс на первый кадр

    def update_animation(self, delta_time):
        """Обновляет текущий кадр анимации."""
        self.frame_timer += delta_time
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            self.current_frame += 1

            if self.current_frame >= len(self.animations[self.current_animation]):
                self.current_frame = 0  # Зацикливаем анимацию

    def update(self, player, walls, delta_time):
        """Обновляет логику врага."""
        self.update_animation(delta_time)  # Обновление анимации

        if self.can_see_player(player, walls):
            self.chasing = True
            self.last_known_position = player.rect.center  # Обновляем последнюю известную позицию
            self.set_animation(2)  # 2: walk анимация
            self.move_towards_player(player.rect, walls)
        elif self.chasing and self.last_known_position:
            # Если враг преследует, но игрок вне видимости
            self.set_animation(2)  # 2: walk анимация
            self.move_towards_position(self.last_known_position, walls)
            if pygame.Vector2(self.rect.center).distance_to(self.last_known_position) < 5:
                # Достигли последней известной позиции
                self.last_known_position = None
                self.chasing = False
        else:
            # Если нет последней известной позиции, патрулируем
            if self.patrol_points:
                self.set_animation(0)  # 0: idle анимация
                self.patrol(walls)

    def move_towards_player(self, player_rect, walls):
        self.move_towards_position(player_rect.center, walls)

    def move_towards_position(self, position, walls):
        direction = pygame.Vector2(position) - pygame.Vector2(self.rect.center)
        if direction.length_squared() != 0:
            direction = direction.normalize()
            self.facing_right = direction.x > 0  # Определяем направление движения
            movement = direction * self.speed
            old_rect = self.rect.copy()
            self.rect.x += movement.x
            self.collide(walls, 'x', old_rect)
            self.rect.y += movement.y
            self.collide(walls, 'y', old_rect)


    def patrol(self, walls):
        target = self.patrol_points[self.current_point]
        direction = pygame.Vector2(target) - pygame.Vector2(self.rect.center)
        if direction.length_squared() != 0:
            direction = direction.normalize()
            self.facing_right = direction.x > 0  # Определяем направление движения
            movement = direction * self.speed
            old_rect = self.rect.copy()
            self.rect.x += movement.x
            self.collide(walls, 'x', old_rect)
            self.rect.y += movement.y
            self.collide(walls, 'y', old_rect)

            if pygame.Vector2(self.rect.center).distance_to(target) < 5:
                self.current_point = (self.current_point + 1) % len(self.patrol_points)

    def can_see_player(self, player, walls):
        """Проверяет, видит ли враг игрока."""
        distance = pygame.Vector2(self.rect.center).distance_to(player.rect.center)
        if distance > self.detect_radius:
            return False

        # Проверяем наличие прямой видимости (Ray Casting)
        ray = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        ray_length = ray.length()
        if ray_length == 0:
            return False

        ray_direction = ray.normalize()
        current_pos = pygame.Vector2(self.rect.center)
        for _ in range(int(ray_length)):
            current_pos += ray_direction
            if any(wall.collidepoint(current_pos) for wall in walls):
                return False
        return True

    def collide(self, walls, dir, old_rect):
        for wall in walls:  
            if self.rect.colliderect(wall):
                if dir == 'x':
                    self.rect.x = old_rect.x
                elif dir == 'y':
                    self.rect.y = old_rect.y

    def draw(self, screen):
        """Рисует врага с текущей анимацией."""
        frame = self.animations[self.current_animation][self.current_frame]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)  # Переворот по горизонтали
        screen.blit(frame, self.rect.topleft)
        
        pygame.draw.circle(screen, (255, 0, 0), self.rect.center, self.detect_radius, 1) # для отладки