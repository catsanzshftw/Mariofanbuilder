import pygame

class Block(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((50, 50))  # Size of the block
        self.image.fill((255, 0, 0))  # Color of the block
        self.rect = self.image.get_rect(topleft=pos)

    def update(self, *args, **kwargs):
        # Block update logic (if any) goes here
        pass

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect(center=(400, 300))
        self.velocity = pygame.Vector2(0, 0)
        self.acceleration = pygame.Vector2(0, 0)

    def update(self):
        self.velocity += self.acceleration
        self.rect.move_ip(self.velocity)
        if self.rect.left < 0 or self.rect.right > 800:
            self.velocity.x = -self.velocity.x

    def jump(self):
        if self.rect.bottom >= 600:
            self.velocity.y = -15

    def apply_gravity(self):
        if self.rect.bottom < 600:
            self.velocity.y += 1
        else:
            self.velocity.y = 0
            self.rect.bottom = 600

def snap_to_grid(pos, size):
    return (pos[0] // size) * size, (pos[1] // size) * size

pygame.init()
window = pygame.display.set_mode((800, 600))
game_clock = pygame.time.Clock()

player = Player()
blocks_group = pygame.sprite.Group()
running = True
block_size = 50  # Size of the grid

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.jump()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            grid_pos = snap_to_grid(pygame.mouse.get_pos(), block_size)
            if event.button == 1:  # Left click to add a block
                if not any(block.rect.topleft == grid_pos for block in blocks_group):
                    block = Block(grid_pos)
                    blocks_group.add(block)
            elif event.button == 3:  # Right click to remove a block
                for block in blocks_group:
                    if block.rect.collidepoint(pygame.mouse.get_pos()):
                        block.kill()
                        break

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player.acceleration.x = -0.5
    elif keys[pygame.K_RIGHT]:
        player.acceleration.x = 0.5
    else:
        player.acceleration.x = 0

    player.apply_gravity()
    player.update()
    blocks_group.update()

    window.fill((255, 255, 255))
    blocks_group.draw(window)
    window.blit(player.image, player.rect)
    pygame.display.update()
    game_clock.tick(60)

pygame.quit()
