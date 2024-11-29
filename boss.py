import pygame
from enemy import Enemy

class Boss(Enemy):
    def __init__(self, x, y, speed, sprite_sheet_path, tile_width, tile_height, facing_right):
        super().__init__(x, y, speed, sprite_sheet_path, tile_width, tile_height, facing_right)
        self.bullets = []  # Список снарядов босса
        self.shoot_timer = 0  # Таймер для стрельбы
        self.shoot_cooldown = 2000  # Время между выстрелами в миллисекундах (2 секунды)
        self.health = 10  # Здоровье босса
        self.rect = pygame.Rect(x, y, tile_width * 2, tile_height * 2)  # Босс крупнее обычного врага

        # Масштабируем спрайты босса
        self.animations = self.scale_animations(self.animations, 2)

    def scale_animations(self, animations, scale_factor):
        """Масштабирует все кадры анимации босса."""
        scaled_animations = []
        for animation in animations:
            scaled_frames = []
            for frame in animation:
                width = int(frame.get_width() * scale_factor)
                height = int(frame.get_height() * scale_factor)
                scaled_frame = pygame.transform.scale(frame, (width, height))
                scaled_frames.append(scaled_frame)
            scaled_animations.append(scaled_frames)
        return scaled_animations

    def update(self, player, walls, delta_time):
        super().update(player, walls, delta_time)
        self.shoot_timer += delta_time
        if self.shoot_timer >= self.shoot_cooldown:
            self.shoot_timer = 0
            self.shoot(player)

        self.update_bullets(delta_time, walls)

    def shoot(self, player):
        """Босс стреляет в направлении игрока."""
        direction = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
        if direction.length() != 0:
            direction = direction.normalize()
        bullet = {
            'rect': pygame.Rect(self.rect.centerx, self.rect.centery, 10, 10),
            'direction': direction
        }
        self.bullets.append(bullet)

    def update_bullets(self, delta_time, walls):
        """Обновляет позиции снарядов босса."""
        bullets_to_remove = []
        for bullet in self.bullets:
            bullet['rect'].x += bullet['direction'].x * 5  # Скорость снаряда босса
            bullet['rect'].y += bullet['direction'].y * 5

            # Проверяем столкновение с стенами
            for wall in walls:
                if bullet['rect'].colliderect(wall):
                    bullets_to_remove.append(bullet)
                    break

            # Удаляем снаряды, вышедшие за пределы экрана
            if (bullet['rect'].x < 0 or bullet['rect'].x > self.rect.width * 20 or
                    bullet['rect'].y < 0 or bullet['rect'].y > self.rect.height * 20):
                bullets_to_remove.append(bullet)

        for bullet in bullets_to_remove:
            if bullet in self.bullets:
                self.bullets.remove(bullet)

    def draw_bullets(self, screen):
        """Рисует снаряды босса."""
        for bullet in self.bullets:
            pygame.draw.rect(screen, (255, 0, 0), bullet['rect'])  # Красные снаряды

    def draw(self, screen):
        pygame.draw.rect(screen, (128, 0, 128), self.rect)
        self.draw_bullets(screen)

    def load_sprite_sheet(self, filepath, tile_width, tile_height):
        """Заглушка для метода загрузки спрайтов."""
        return []