
import pygame
import math
from collections import deque
from settings import WIDTH, HEIGHT, TILE_SIZE  # Предположим, у вас есть TILE_SIZE = 50

class Enemy:
    def __init__(self, x, y, speed, sprite_sheet_path, tile_width, tile_height, facing_right, patrol_points=None):
        # Уменьшенный прямоугольник (30x30 вместо 40x40) + смещение, чтобы центр врага оставался примерно там же
        self.rect = pygame.Rect(x + 5, y + 5, 30, 30)
        self.speed = speed
        self.patrol_points = patrol_points or []
        self.current_point = 0
        self.direction = pygame.Vector2(0, 0)
        self.detect_radius = 250  # Радиус обнаружения игрока
        self.chasing = False
        self.last_known_position = None  # Последняя известная позиция игрока

        # Путь (список координат в пикселях), по которым двигается враг
        self.path = []
        self.path_index = 0

        # Анимации
        self.animations = self.load_sprite_sheet(sprite_sheet_path, tile_width, tile_height)
        self.current_animation = 0  # 0: idle, 1: walk, 2: run, и т.д.
        self.current_frame = 0
        self.frame_timer = 0
        self.animation_speed = 150  # мс на кадр
        self.facing_right = facing_right  # Направление (True = вправо)

    # -------------------------------
    #   Загрузка и анимации
    # -------------------------------
    def load_sprite_sheet(self, filepath, tile_width, tile_height):
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
        for x in range(frame.get_width()):
            for y in range(frame.get_height()):
                if frame.get_at((x, y))[3] > 0:  # Альфа-канал > 0
                    return False
        return True

    def set_animation(self, animation_index):
        if self.current_animation != animation_index:
            self.current_animation = animation_index
            self.current_frame = 0  # Сброс на первый кадр

    def update_animation(self, delta_time):
        self.frame_timer += delta_time
        if self.frame_timer >= self.animation_speed:
            self.frame_timer = 0
            self.current_frame += 1
            # Зацикливаем
            if self.current_frame >= len(self.animations[self.current_animation]):
                self.current_frame = 0

    # -------------------------------
    #   Логика врага
    # -------------------------------
    def update(self, player, walls, delta_time, current_time=None):
        # 1. Анимация
        self.update_animation(delta_time)

        # 2. Определяем, видим ли игрока
        if self.can_see_player(player, walls):
            self.chasing = True
            self.last_known_position = player.rect.center
            self.set_animation(2)  # Пусть будет "2" для преследования
            self.go_to_position(self.last_known_position, walls)
        elif self.chasing and self.last_known_position:
            # Если преследуем, но игрока не видно: идём к последней известной позиции
            self.set_animation(2)
            # Если уже достигли, сбрасываем
            dist = pygame.Vector2(self.rect.center).distance_to(self.last_known_position)
            if dist < 5:
                self.last_known_position = None
                self.chasing = False
            else:
                self.go_to_position(self.last_known_position, walls)
        else:
            # Патрулирование
            if self.patrol_points:
                self.set_animation(1)  # 1: walk (или 0: idle)
                self.patrol(walls)
            else:
                # Если нет patrol_points, враг просто стоит idle
                self.set_animation(0)


    def go_to_position(self, target_pos, walls):
        """
        Двигаемся к позиции target_pos.
        Используем path (если пустой или устарел — перестраиваем).
        """
        # Проверяем, есть ли путь и не достигли ли конца
        if not self.path or self.path_index >= len(self.path):
            # Строим новый путь BFS
            self.path = self.build_path(self.rect.center, target_pos, walls)
            self.path_index = 0

        if self.path:
            # Двигаемся к текущей точке из path
            current_target = self.path[self.path_index]
            direction = pygame.Vector2(current_target) - pygame.Vector2(self.rect.center)
            if direction.length_squared() > 0:
                direction = direction.normalize()
            self.facing_right = (direction.x > 0)

            # Перемещаемся
            movement = direction * self.speed
            old_rect = self.rect.copy()
            self.rect.x += movement.x
            self.collide(walls, 'x', old_rect)
            self.rect.y += movement.y
            self.collide(walls, 'y', old_rect)

            # Проверяем, достигли ли мы "узла"
            if pygame.Vector2(self.rect.center).distance_to(current_target) < 5:
                self.path_index += 1



    def can_see_player(self, player, walls):
        """
        Проверяет, видит ли враг игрока (без учёта сложного pathfinding).
        Просто луч и радиус видимости.
        """
        distance = pygame.Vector2(self.rect.center).distance_to(player.rect.center)
        if distance > self.detect_radius:
            return False

        # Луч от врага до игрока
        ray = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        ray_length = ray.length()
        if ray_length == 0:
            return False

        ray_direction = ray.normalize()
        current_pos = pygame.Vector2(self.rect.center)
        steps = int(ray_length)  # По одному пикселю

        for _ in range(steps):
            current_pos += ray_direction
            # Если встречаем стену - не видим
            if any(wall.collidepoint(current_pos) for wall in walls):
                return False
        return True

    # -------------------------------
    #   BFS-поиск пути по сетке
    # -------------------------------
    def build_path(self, start_pos, end_pos, walls):
        """
        Простейший поиск пути (BFS) по сетке с размером тайла TILE_SIZE.
        Возвращает список координат (x, y) в пикселях от start_pos до end_pos.
        Если путь не найден — возвращаем пустой список.
        """

        # Конвертируем пиксельные координаты в координаты тайлов
        start_tile = (int(start_pos[0] // TILE_SIZE), int(start_pos[1] // TILE_SIZE))
        end_tile   = (int(end_pos[0]   // TILE_SIZE), int(end_pos[1]   // TILE_SIZE))

        if start_tile == end_tile:
            return []  # Уже там


# Собираем множество заблокированных тайлов на основе walls
        blocked_tiles = set()
        for wall in walls:
            # wall.x, wall.y, wall.width, wall.height
            # Перебираем тайлы, которые занимает стенка (примерно)
            x_start = wall.left // TILE_SIZE
            x_end   = (wall.right  - 1) // TILE_SIZE
            y_start = wall.top  // TILE_SIZE
            y_end   = (wall.bottom - 1) // TILE_SIZE
            for tx in range(x_start, x_end + 1):
                for ty in range(y_start, y_end + 1):
                    blocked_tiles.add((tx, ty))

        # BFS
        queue = deque([start_tile])
        came_from = {start_tile: None}
        found_path = False

        while queue:
            current = queue.popleft()
            if current == end_tile:
                found_path = True
                break

            for nx, ny in self.get_neighbors(current):
                if (nx, ny) not in came_from and (nx, ny) not in blocked_tiles:
                    came_from[(nx, ny)] = current
                    queue.append((nx, ny))

        if not found_path:
            return []

        # Восстанавливаем путь по словарю came_from
        path_tiles = []
        cur = end_tile
        while cur is not None:
            path_tiles.append(cur)
            cur = came_from[cur]
        path_tiles.reverse()

        # Преобразуем список тайлов в пиксельные координаты (центр тайла)
        result_path = []
        for (tx, ty) in path_tiles:
            cx = tx * TILE_SIZE + TILE_SIZE // 2
            cy = ty * TILE_SIZE + TILE_SIZE // 2
            result_path.append((cx, cy))

        return result_path

    def get_neighbors(self, tile_xy):
        """Соседние тайлы (4 направления, без диагоналей)."""
        (x, y) = tile_xy
        return [
            (x+1, y),
            (x-1, y),
            (x, y+1),
            (x, y-1),
        ]

    # -------------------------------
    #   Коллизии
    # -------------------------------
    def collide(self, walls, axis, old_rect):
        """
        Если при перемещении по оси X или Y столкнулись со стеной,
        откатываем позицию. Учитывая, что self.rect меньше, чем тайл.
        """
        for wall in walls:
            if self.rect.colliderect(wall):
                if axis == 'x':
                    self.rect.x = old_rect.x
                elif axis == 'y':
                    self.rect.y = old_rect.y

    # -------------------------------
    #   Рисование
    # -------------------------------
    def draw(self, screen):
        frame = self.animations[self.current_animation][self.current_frame]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        screen.blit(frame, self.rect.topleft)

        #Для отладки можно нарисовать путь
        for i in range(len(self.path) - 1):
            pygame.draw.line(screen, (255, 0, 0), self.path[i], self.path[i+1], 2)

        #pygame.draw.circle(screen, (255, 0, 0), self.rect.center, 3)
        #pygame.draw.circle(screen, (0, 255, 0), (int(self.last_known_position[0]),
        #                                          int(self.last_known_position[1])), 5)