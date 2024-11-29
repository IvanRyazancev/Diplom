import pygame, random
from settings import TILE_SIZE
from enemy import Enemy

class Level:
    def __init__(self, level_data):
        self.walls = []
        self.waters = []
        self.enemies = []
        self.enemies_boss = []
        self.water = []  # Добавляем тайлы воды
        self.traps = []  # Добавляем тайлы ловушек
        self.bonuses = []  # Добавляем тайлы бонусов
        self.start_pos = (0, 0)
        self.finish_rect = None
        self.width = 0
        self.height = 0
        self.parse_level(level_data)
    def random_bool(self):
        return random.choice([True, False])
    def parse_level(self, level_data):
        max_width = 0
        for y, row in enumerate(level_data):
            max_width = max(max_width, len(row))
            for x, tile in enumerate(row):
                position = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if tile == '1':
                    self.walls.append(position)
                elif tile == 'E':
                    enemy = Enemy(position.x, position.y, speed=5, sprite_sheet_path="src/sprites/enemy.png",
                                  tile_width=32, tile_height=32, facing_right = self.random_bool)
                    self.enemies.append(enemy)
                elif tile == 'D':
                    enemy_boss = Enemy(position.x, position.y, speed=4, sprite_sheet_path="src/sprites/boss.png",
                                       tile_width=32, tile_height=32, facing_right=self.random_bool)
                    self.enemies_boss.append(enemy_boss)
                elif tile == 'P':
                    self.start_pos = (position.x, position.y)
                elif tile == 'F':
                    self.finish_rect = position
                elif tile == 'W':  # Вода
                    self.waters.append(position)
                elif tile == 'T':  # Ловушка
                    self.traps.append(position)
                elif tile == 'B':  # Бонус
                    self.bonuses.append(position)

        self.width = max_width * TILE_SIZE
        self.height = len(level_data) * TILE_SIZE

    def draw(self, screen):
        # Рисуем стены
        for wall in self.walls:
            pygame.draw.rect(screen, (0, 0, 0), wall)
        # Рисуем воду
        for water in self.waters:
            pygame.draw.rect(screen, (0, 0, 255), water)
        # Рисуем ловушки
        for trap in self.traps:
            pygame.draw.rect(screen, (255, 0, 0), trap)
        # Рисуем бонусы
        for bonus in self.bonuses:
            pygame.draw.rect(screen, (0, 255, 0), bonus)
        # Рисуем финиш
        if self.finish_rect:
            pygame.draw.rect(screen, (255, 215, 0), self.finish_rect)