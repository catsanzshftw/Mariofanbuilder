import pygame
import json
import sys
import os
import random
import math
from collections import deque

pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 700
HUD_HEIGHT = 100
GRID_SIZE = 50
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
DARK_GRAY = (50, 50, 50)

# Define Mario Fan Builder-inspired Themes
themes = {
    'Mario Fan Builder Default': {
        'ground': (120, 80, 30),        # Brown
        'brick': (200, 120, 50),        # Light Brown
        'question': (255, 223, 0),      # Yellow
        'coin': (255, 215, 0),          # Gold
        'enemy': (220, 20, 60),         # Crimson
        'water': (64, 164, 223),        # Blue
        'background': (107, 136, 255),  # Sky Blue (Mario Fan Builder style)
        'pipe': (0, 168, 0),            # Green
        'powerup': (255, 0, 0),         # Red
    },
    'Mario Fan Builder Cave': {
        'ground': (80, 50, 20),         # Dark Brown
        'brick': (120, 80, 40),         # Medium Brown
        'question': (200, 180, 0),      # Dark Yellow
        'coin': (255, 215, 0),          # Gold
        'enemy': (180, 20, 40),         # Dark Red
        'water': (40, 100, 180),        # Dark Blue
        'background': (30, 30, 40),     # Dark Cave
        'pipe': (0, 128, 0),            # Dark Green
        'powerup': (200, 0, 0),         # Dark Red
    },
    'Mario Fan Builder Snow': {
        'ground': (210, 230, 255),      # White-Blue
        'brick': (180, 200, 230),       # Light Blue-Gray
        'question': (255, 223, 0),      # Yellow
        'coin': (255, 215, 0),          # Gold
        'enemy': (220, 20, 60),         # Crimson
        'water': (100, 200, 255),       # Light Blue
        'background': (200, 230, 255),  # Pale Blue
        'pipe': (180, 255, 180),        # Light Green
        'powerup': (255, 0, 0),         # Red
    }
}

current_theme = 'Mario Fan Builder Default'  # Default theme

# Initialize the window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT + HUD_HEIGHT))
pygame.display.set_caption("Mario Fan Builder vx.0 [C] @Team Flames 20XX [C] Nintendo")
game_clock = pygame.time.Clock()

# Font
FONT = pygame.font.Font(None, 24)

# Mario Fan Builder Physics Constants
GRAVITY = 0.4
TERMINAL_VELOCITY = 12
JUMP_STRENGTH = -11
RUN_ACCEL = 0.6
RUN_SPEED_MAX = 7
WALK_SPEED_MAX = 4
SKID_DECEL = 0.8
AIR_CONTROL = 0.4
GROUND_FRICTION = 0.15

# Classes for various game elements
class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, tile_type):
        super().__init__()
        self.tile_type = tile_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.update_image()
        
        # Additional properties for Mario Fan Builder features
        self.is_solid = tile_type in ['ground', 'brick', 'question', 'pipe']
        self.is_platform = tile_type == 'platform'
        self.is_breakable = tile_type == 'brick'
        self.contains_item = None
        
        if tile_type == 'question':
            self.contains_item = 'coin'  # Default, can be changed

    def update_image(self):
        theme_colors = themes[current_theme]
        self.image.fill(theme_colors.get(self.tile_type, WHITE))
        
        # Additional graphics for specific tiles
        if self.tile_type == 'question':
            pygame.draw.line(self.image, BLACK, (10, 10), (30, 10), 3)
            pygame.draw.line(self.image, BLACK, (10, 10), (10, 30), 3)
            pygame.draw.line(self.image, BLACK, (30, 10), (30, 30), 3)
        elif self.tile_type == 'coin':
            pygame.draw.circle(self.image, WHITE, (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 2 - 5)
        elif self.tile_type == 'pipe':
            pygame.draw.rect(self.image, BLACK, (2, 2, GRID_SIZE - 4, GRID_SIZE - 4), 2)
        elif self.tile_type == 'platform':
            self.image.fill((0, 0, 0, 0))  # Transparent
            pygame.draw.rect(self.image, theme_colors.get('ground'), (0, 0, GRID_SIZE, GRID_SIZE // 4))
        elif self.tile_type == 'powerup':
            pygame.draw.rect(self.image, theme_colors.get('powerup'), (5, 5, GRID_SIZE - 10, GRID_SIZE - 10))
            pygame.draw.rect(self.image, WHITE, (10, 10, GRID_SIZE - 20, GRID_SIZE - 20))

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, enemy_type='goomba'):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(themes[current_theme]['enemy'])
        self.rect = self.image.get_rect(topleft=pos)
        self.velocity = pygame.Vector2(2, 0)  # Initial movement
        
        # Mario Fan Builder-style enemy properties
        self.movement_pattern = 'walk'  # 'walk', 'jump', 'fly', etc.
        self.can_be_stomped = True
        self.health = 1
        self.is_facing_right = False
        self.animation_frame = 0
        self.animation_speed = 0.1
        self.animation_timer = 0
        
        # Draw enemy details based on type
        if enemy_type == 'goomba':
            pygame.draw.ellipse(self.image, BLACK, (5, 25, 40, 20))
            pygame.draw.circle(self.image, WHITE, (15, 15), 5)
            pygame.draw.circle(self.image, WHITE, (35, 15), 5)
        elif enemy_type == 'koopa':
            pygame.draw.rect(self.image, (0, 200, 0), (5, 5, 40, 40))
            pygame.draw.ellipse(self.image, WHITE, (10, 10, 30, 20))
        elif enemy_type == 'piranha':
            pygame.draw.polygon(self.image, (0, 200, 0), [(10, 10), (40, 10), (40, 40), (10, 40)])
            pygame.draw.circle(self.image, WHITE, (25, 25), 5)

    def update(self, solid_tiles, platforms=None):
        # Apply gravity if not on ground
        self.velocity.y += GRAVITY
        self.velocity.y = min(self.velocity.y, TERMINAL_VELOCITY)
        
        # Move horizontally
        self.rect.x += self.velocity.x
        
        # Check horizontal collisions
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in collisions:
            if self.velocity.x > 0:  # Moving right
                self.rect.right = tile.rect.left
                self.velocity.x *= -1
                self.is_facing_right = False
            elif self.velocity.x < 0:  # Moving left
                self.rect.left = tile.rect.right
                self.velocity.x *= -1
                self.is_facing_right = True
        
        # Move vertically
        self.rect.y += self.velocity.y
        
        # Check vertical collisions
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in collisions:
            if self.velocity.y > 0:  # Falling
                self.rect.bottom = tile.rect.top
                self.velocity.y = 0
            elif self.velocity.y < 0:  # Jumping
                self.rect.top = tile.rect.bottom
                self.velocity.y = 0
                
        # Special enemy behaviors
        if self.enemy_type == 'koopa' and self.movement_pattern == 'jump':
            # Periodically jump
            if self.velocity.y == 0 and random.random() < 0.01:
                self.velocity.y = -8
                
        # Update animation
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2
            
        # Flip direction if at edge of screen
        if self.rect.left <= 0:
            self.velocity.x = abs(self.velocity.x)
            self.is_facing_right = True
        elif self.rect.right >= WINDOW_WIDTH:
            self.velocity.x = -abs(self.velocity.x)
            self.is_facing_right = False

class Coin(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        self.draw_coin()
        self.rect = self.image.get_rect(topleft=pos)
        self.animation_frame = 0
        self.animation_speed = 0.1
        self.animation_timer = 0
        self.value = 1  # Mario Fan Builder has different coin values
        
    def draw_coin(self):
        self.image.fill((0, 0, 0, 0))  # Clear with transparency
        pygame.draw.circle(self.image, themes[current_theme]['coin'], 
                          (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 2 - 5)
        pygame.draw.circle(self.image, (255, 255, 200), 
                          (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 2 - 10)
        
    def update(self):
        # Animate the coin (spinning effect)
        self.animation_timer += self.animation_speed
        if self.animation_timer >= 1:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4
            
            # Update appearance based on frame
            self.draw_coin()
            if self.animation_frame in [1, 3]:
                # Make the coin appear thinner when spinning
                self.image.fill((0, 0, 0, 0))
                pygame.draw.ellipse(self.image, themes[current_theme]['coin'], 
                                   (GRID_SIZE // 2 - 3, 10, 6, GRID_SIZE - 20))

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, pos, powerup_type='mushroom'):
        super().__init__()
        self.powerup_type = powerup_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=pos)
        self.velocity = pygame.Vector2(2, 0)
        
        # Draw the power-up
        if powerup_type == 'mushroom':
            pygame.draw.rect(self.image, RED, (5, 20, GRID_SIZE - 10, GRID_SIZE - 25))
            pygame.draw.circle(self.image, RED, (GRID_SIZE // 2, 20), GRID_SIZE // 2 - 5)
            pygame.draw.circle(self.image, WHITE, (GRID_SIZE // 3, 15), 5)
            pygame.draw.circle(self.image, WHITE, (2 * GRID_SIZE // 3, 15), 5)
        elif powerup_type == 'fire_flower':
            pygame.draw.circle(self.image, RED, (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 2 - 5)
            pygame.draw.circle(self.image, YELLOW, (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 3)
        elif powerup_type == 'star':
            points = []
            for i in range(5):
                angle = i * 2 * 3.14159 / 5 - 3.14159 / 2
                outer_x = GRID_SIZE // 2 + int((GRID_SIZE // 2 - 5) * math.cos(angle))
                outer_y = GRID_SIZE // 2 + int((GRID_SIZE // 2 - 5) * math.sin(angle))
                points.append((outer_x, outer_y))
                
                inner_angle = angle + 3.14159 / 5
                inner_x = GRID_SIZE // 2 + int((GRID_SIZE // 4) * math.cos(inner_angle))
                inner_y = GRID_SIZE // 2 + int((GRID_SIZE // 4) * math.sin(inner_angle))
                points.append((inner_x, inner_y))
            pygame.draw.polygon(self.image, YELLOW, points)
    
    def update(self, solid_tiles):
        # Apply gravity
        self.velocity.y += GRAVITY
        self.velocity.y = min(self.velocity.y, TERMINAL_VELOCITY)
        
        # Move horizontally
        self.rect.x += self.velocity.x
        
        # Check horizontal collisions
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in collisions:
            if self.velocity.x > 0:  # Moving right
                self.rect.right = tile.rect.left
                self.velocity.x *= -1
            elif self.velocity.x < 0:  # Moving left
                self.rect.left = tile.rect.right
                self.velocity.x *= -1
        
        # Move vertically
        self.rect.y += self.velocity.y
        
        # Check vertical collisions
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in collisions:
            if self.velocity.y > 0:  # Falling
                self.rect.bottom = tile.rect.top
                self.velocity.y = 0
            elif self.velocity.y < 0:  # Rising
                self.rect.top = tile.rect.bottom
                self.velocity.y = 0

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.coins_collected = 0
        self.score = 0
        self.lives = 3
        
        # Mario Fan Builder-style player states
        self.state = 'small'  # 'small', 'big', 'fire', 'raccoon', etc.
        self.is_running = False
        self.direction = 'right'
        self.invincible = False
        self.invincible_timer = 0
        self.can_jump = True
        self.jump_held = False
        self.jump_timer = 0
        self.max_jump_hold = 15  # Frames to hold jump for maximum height
        self.run_timer = 0       # For P-meter
        self.p_meter = 0         # 0-6, at 6 allows flight/special abilities
        self.character = 'mario' # 'mario', 'luigi', 'peach', 'toad', etc.

    def update(self, solid_tiles, enemies, coins, powerups=None, platforms=None):
        keys = pygame.key.get_pressed()
        
        # Reset horizontal acceleration
        self.accel_x = 0
        
        # Running/Walking (Mario Fan Builder-style physics)
        if keys[pygame.K_LEFT]:
            self.direction = 'left'
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                self.is_running = True
                if self.on_ground:
                    self.accel_x = -RUN_ACCEL
                else:
                    self.accel_x = -AIR_CONTROL
            else:
                self.is_running = False
                if self.on_ground:
                    self.accel_x = -RUN_ACCEL * 0.6
                else:
                    self.accel_x = -AIR_CONTROL * 0.6
        
        elif keys[pygame.K_RIGHT]:
            self.direction = 'right'
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                self.is_running = True
                if self.on_ground:
                    self.accel_x = RUN_ACCEL
                else:
                    self.accel_x = AIR_CONTROL
            else:
                self.is_running = False
                if self.on_ground:
                    self.accel_x = RUN_ACCEL * 0.6
                else:
                    self.accel_x = AIR_CONTROL * 0.6
        
        # Apply acceleration
        self.velocity.x += self.accel_x
        
        # Apply ground friction
        if self.on_ground and self.accel_x == 0:
            if abs(self.velocity.x) < GROUND_FRICTION:
                self.velocity.x = 0
            elif self.velocity.x > 0:
                self.velocity.x -= GROUND_FRICTION
            else:
                self.velocity.x += GROUND_FRICTION
        
        # Apply speed limit based on run state
        if self.is_running:
            self.velocity.x = max(-RUN_SPEED_MAX, min(RUN_SPEED_MAX, self.velocity.x))
            if abs(self.velocity.x) > WALK_SPEED_MAX and self.on_ground:
                self.run_timer += 1
                if self.run_timer >= 30 and self.p_meter < 6:
                    self.run_timer = 0
                    self.p_meter += 1
            else:
                if self.run_timer > 0:
                    self.run_timer -= 1
                else:
                    if self.p_meter > 0:
                        self.p_meter -= 1
        else:
            self.velocity.x = max(-WALK_SPEED_MAX, min(WALK_SPEED_MAX, self.velocity.x))
            if self.run_timer > 0:
                self.run_timer -= 1
            else:
                if self.p_meter > 0:
                    self.p_meter -= 1
                    
        # Mario Fan Builder-style jumping mechanics
        if keys[pygame.K_SPACE] or keys[pygame.K_UP]:
            if self.on_ground and self.can_jump:
                self.velocity.y = JUMP_STRENGTH 
                self.on_ground = False
                self.can_jump = False
                self.jump_held = True
                self.jump_timer = 0
            elif self.jump_held and not self.on_ground:
                self.jump_timer += 1
                if self.jump_timer < self.max_jump_hold:
                    self.velocity.y = min(self.velocity.y, JUMP_STRENGTH * 0.5)
        else:
            self.jump_held = False
            if not self.on_ground and self.velocity.y < 0:
                self.velocity.y *= 0.5
        
        if self.on_ground:
            self.can_jump = True
            
        # Apply gravity (varies by character in Mario Fan Builder)
        gravity_factor = 1.0
        if self.character == 'luigi':
            gravity_factor = 0.9  # Luigi jumps higher
        elif self.character == 'peach':
            gravity_factor = 0.7  # Peach floats
            if not self.on_ground and keys[pygame.K_SPACE]:
                gravity_factor = 0.3  # Even more float when holding jump
                
        self.velocity.y += GRAVITY * gravity_factor
        self.velocity.y = min(self.velocity.y, TERMINAL_VELOCITY)

        # Move horizontally and handle collisions
        self.rect.x += self.velocity.x
        self.handle_collisions(self.velocity.x, 0, solid_tiles)

        # Move vertically and handle collisions
        self.rect.y += self.velocity.y
        self.on_ground = False
        self.handle_collisions(0, self.velocity.y, solid_tiles)

        # Check platform collisions (for one-way platforms)
        if platforms:
            self.handle_platform_collisions(platforms)

        # Prevent player from falling below the screen
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT
            self.velocity.y = 0
            self.on_ground = True

        # Check collision with enemies
        enemy_collisions = pygame.sprite.spritecollide(self, enemies, False)
        for enemy in enemy_collisions:
            if self.velocity.y > 0 and self.rect.bottom < enemy.rect.centery:
                if enemy.can_be_stomped:
                    self.velocity.y = -6  # Bounce up
                    self.score += 100
                    enemy.kill()
            else:
                if not self.invincible:
                    if self.state != 'small':
                        self.state = 'small'
                        self.invincible = True
                        self.invincible_timer = 60  # Invincibility frames
                    else:
                        self.lives -= 1
                        if self.lives <= 0:
                            print("Game Over!")
                        else:
                            print(f"Lives left: {self.lives}")
                        playtest_reset()

        # Check collision with coins
        collected = pygame.sprite.spritecollide(self, coins, True)
        for coin in collected:
            self.coins_collected += coin.value
            self.score += 200

        # Check collision with powerups
        if powerups:
            pu_collected = pygame.sprite.spritecollide(self, powerups, True)
            for powerup in pu_collected:
                if powerup.powerup_type == 'mushroom' and self.state == 'small':
                    self.state = 'big'
                    self.score += 1000
                elif powerup.powerup_type == 'fire_flower' and self.state in ['small', 'big']:
                    self.state = 'fire'
                    self.score += 1000
                elif powerup.powerup_type == 'star':
                    self.invincible = True
                    self.invincible_timer = 600  # 10 seconds
                    self.score += 1000

        # Update invincibility timer
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

    def handle_collisions(self, vel_x, vel_y, solid_tiles):
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in collisions:
            if vel_x > 0:  # Moving right
                self.rect.right = tile.rect.left
                self.velocity.x = 0
            elif vel_x < 0:  # Moving left
                self.rect.left = tile.rect.right
                self.velocity.x = 0
            
            if vel_y > 0:  # Moving down
                self.rect.bottom = tile.rect.top
                self.velocity.y = 0
                self.on_ground = True
            elif vel_y < 0:  # Moving up
                self.rect.top = tile.rect.bottom
                self.velocity.y = 0
                if hasattr(tile, 'tile_type'):
                    if tile.tile_type == 'question' and tile.contains_item:
                        spawn_item(tile.rect.topleft, tile.contains_item)
                        tile.contains_item = None
                    elif tile.tile_type == 'brick' and self.state != 'small':
                        tile.kill()
                        self.score += 50

    def handle_platform_collisions(self, platforms):
        platform_collisions = pygame.sprite.spritecollide(self, platforms, False)
        for platform in platform_collisions:
            if self.velocity.y > 0 and self.rect.bottom < platform.rect.top + 10:
                self.rect.bottom = platform.rect.top
                self.velocity.y = 0
                self.on_ground = True

    def jump(self):
        if self.on_ground and self.can_jump:
            jump_power = JUMP_STRENGTH
            if self.character == 'luigi':
                jump_power *= 1.1  # Luigi jumps higher
            elif self.character == 'toad':
                jump_power *= 0.9  # Toad jumps lower but runs faster
                
            self.velocity.y = jump_power
            self.on_ground = False
            self.can_jump = False
            self.jump_held = True
            self.jump_timer = 0

# Helper functions
def snap_to_grid(pos, size):
    return (pos[0] // size) * size, (pos[1] // size) * size

def spawn_item(pos, item_type):
    if item_type == 'coin':
        coin = Coin(pos)
        coins_group.add(coin)
        all_sprites.add(coin)
    elif item_type == 'mushroom':
        powerup = PowerUp(pos, 'mushroom')
        powerups_group.add(powerup)
        all_sprites.add(powerup)

def save_level(filename="level.json"):
    level_data = {
        "tiles": [],
        "enemies": [],
        "coins": [],
        "powerups": [],
        "theme": current_theme
    }
    for tile in tiles_group:
        tile_data = {
            "x": tile.rect.x,
            "y": tile.rect.y,
            "type": tile.tile_type,
            "contains_item": tile.contains_item if hasattr(tile, 'contains_item') else None
        }
        level_data["tiles"].append(tile_data)
    for enemy in enemies_group:
        enemy_data = {
            "x": enemy.rect.x,
            "y": enemy.rect.y,
            "enemy_type": enemy.enemy_type if hasattr(enemy, 'enemy_type') else 'goomba'
        }
        level_data["enemies"].append(enemy_data)
    for coin in coins_group:
        coin_data = {
            "x": coin.rect.x,
            "y": coin.rect.y,
            "value": coin.value if hasattr(coin, 'value') else 1
        }
        level_data["coins"].append(coin_data)
    for powerup in powerups_group:
        powerup_data = {
            "x": powerup.rect.x,
            "y": powerup.rect.y,
            "powerup_type": powerup.powerup_type
        }
        level_data["powerups"].append(powerup_data)
    try:
        with open(filename, "w") as file:
            json.dump(level_data, file, indent=4)
        print(f"Level saved to {filename}.")
    except Exception as e:
        print(f"Error saving level: {e}")

def load_level(filename="level.json"):
    global current_theme
    try:
        with open(filename, "r") as file:
            level_data = json.load(file)
            theme = level_data.get("theme", "Mario Fan Builder Default")
            set_theme(theme)
            tiles_group.empty()
            enemies_group.empty()
            coins_group.empty()
            powerups_group.empty()
            all_sprites.empty()
            all_sprites.add(player)

            for tile_data in level_data["tiles"]:
                tile = Tile((tile_data["x"], tile_data["y"]), tile_data["type"])
                if "contains_item" in tile_data and tile_data["contains_item"]:
                    tile.contains_item = tile_data["contains_item"]
                tiles_group.add(tile)
                all_sprites.add(tile)

            for enemy_data in level_data["enemies"]:
                enemy_type = enemy_data.get("enemy_type", "goomba")
                enemy = Enemy((enemy_data["x"], enemy_data["y"]), enemy_type)
                enemies_group.add(enemy)
                all_sprites.add(enemy)

            for coin_data in level_data["coins"]:
                coin = Coin((coin_data["x"], coin_data["y"]))
                if "value" in coin_data:
                    coin.value = coin_data["value"]
                coins_group.add(coin)
                all_sprites.add(coin)
                
            if "powerups" in level_data:
                for powerup_data in level_data["powerups"]:
                    powerup_type = powerup_data.get("powerup_type", "mushroom")
                    powerup = PowerUp((powerup_data["x"], powerup_data["y"]), powerup_type)
                    powerups_group.add(powerup)
                    all_sprites.add(powerup)
        print(f"Level loaded from {filename}.")
    except FileNotFoundError:
        print(f"File {filename} not found.")
    except Exception as e:
        print(f"Error loading level: {e}")

def set_theme(theme_name):
    global current_theme
    if theme_name in themes:
        current_theme = theme_name
        for sprite in all_sprites:
            if isinstance(sprite, Tile):
                sprite.update_image()
            elif isinstance(sprite, Enemy):
                sprite.image.fill(themes[current_theme]['enemy'])
            elif isinstance(sprite, Coin):
                sprite.draw_coin()
        print(f"Theme set to '{theme_name}'.")
    else:
        print(f"Theme '{theme_name}' does not exist.")

def load_construct_level(level_data, theme_name='Mario Fan Builder Default'):
    set_theme(theme_name)
    tiles_group.empty()
    enemies_group.empty()
    coins_group.empty()
    powerups_group.empty()
    all_sprites.empty()
    all_sprites.add(player)

    for y, row in enumerate(level_data):
        for x, char in enumerate(row):
            pos = (x * GRID_SIZE, y * GRID_SIZE)
            if char == 'G':  # Ground
                tile = Tile(pos, 'ground')
                tiles_group.add(tile)
                all_sprites.add(tile)
            elif char == 'B':  # Brick
                tile = Tile(pos, 'brick')
                tiles_group.add(tile)
                all_sprites.add(tile)
            elif char == 'Q':  # Question block
                tile = Tile(pos, 'question')
                tile.contains_item = 'coin'  # Default item
                tiles_group.add(tile)
                all_sprites.add(tile)
            elif char == 'C':  # Coin
                coin = Coin(pos)
                coins_group.add(coin)
                all_sprites.add(coin)
            elif char == 'E':  # Enemy (Goomba by default)
                enemy = Enemy(pos, 'goomba')
                enemies_group.add(enemy)
                all_sprites.add(enemy)
            elif char == 'K':  # Koopa
                enemy = Enemy(pos, 'koopa')
                enemies_group.add(enemy)
                all_sprites.add(enemy)
            elif char == 'W':  # Water
                tile = Tile(pos, 'water')
                tiles_group.add(tile)
                all_sprites.add(tile)
            elif char == 'P':  # Pipe
                tile = Tile(pos, 'pipe')
                tiles_group.add(tile)
                all_sprites.add(tile)
            elif char == 'M':  # Mushroom
                powerup = PowerUp(pos, 'mushroom')
                powerups_group.add(powerup)
                all_sprites.add(powerup)
            elif char == 'F':  # Fire Flower
                powerup = PowerUp(pos, 'fire_flower')
                powerups_group.add(powerup)
                all_sprites.add(powerup)
            elif char == 'S':  # Star
                powerup = PowerUp(pos, 'star')
                powerups_group.add(powerup)
                all_sprites.add(powerup)
            elif char == '-':  # Platform
                tile = Tile(pos, 'platform')
                platforms_group.add(tile)
                all_sprites.add(tile)
    print("Mario Fan Builder level loaded.")

def playtest_reset():
    global playtest_mode
    player.rect.center = (400, WINDOW_HEIGHT - GRID_SIZE)
    player.velocity = pygame.Vector2(0, 0)
    player.state = 'small'
    player.coins_collected = 0
    player.score = 0
    player.invincible = False
    player.p_meter = 0
    playtest_mode = False
    print("Playtest mode ended. Back to editor.")

# Initialize sprite groups
tiles_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
coins_group = pygame.sprite.Group()
powerups_group = pygame.sprite.Group()
platforms_group = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()

# Create the player
player = Player((400, WINDOW_HEIGHT - GRID_SIZE))
all_sprites.add(player)

# HUD Setup
HUD_RECT = pygame.Rect(0, WINDOW_HEIGHT, WINDOW_WIDTH, HUD_HEIGHT)

# Define tile types and their icons
tile_types = ['ground', 'brick', 'question', 'pipe', 'platform', 'water', 'enemy', 'coin', 'powerup']
tile_icons = {}

for index, tile_type in enumerate(tile_types):
    icon = pygame.Surface((40, 40), pygame.SRCALPHA)
    theme_colors = themes[current_theme]
    if tile_type in theme_colors:
        icon.fill(theme_colors[tile_type])
    elif tile_type == 'coin':
        pygame.draw.circle(icon, themes[current_theme]['coin'], (20, 20), 15)
    elif tile_type == 'enemy':
        icon.fill(themes[current_theme]['enemy'])
    elif tile_type == 'platform':
        icon.fill((100, 100, 100, 150))
        pygame.draw.rect(icon, theme_colors.get('ground'), (0, 0, 40, 10))
    else:
        icon.fill(WHITE)
    tile_icons[tile_type] = icon

# HUD buttons positions
button_positions = {}
for i, tile_type in enumerate(tile_types):
    x = 10 + i * 60
    y = WINDOW_HEIGHT + 10
    button_positions[tile_type] = pygame.Rect(x, y, 40, 40)

# Theme selection buttons
theme_names = list(themes.keys())
theme_buttons = {}
for i, theme_name in enumerate(theme_names):
    x = 10 + i * 150
    y = WINDOW_HEIGHT + 60
    theme_buttons[theme_name] = pygame.Rect(x, y, 140, 30)

# Character selection buttons
characters = ['mario', 'luigi', 'peach', 'toad']
character_buttons = {}
for i, character in enumerate(characters):
    x = 550 + i * 100
    y = WINDOW_HEIGHT + 60
    character_buttons[character] = pygame.Rect(x, y, 90, 30)

# Save, Load, Load Construct, and Playtest buttons
buttons = {
    "save": pygame.Rect(400, WINDOW_HEIGHT + 10, 80, 30),
    "load": pygame.Rect(490, WINDOW_HEIGHT + 10, 80, 30),
    "load_construct": pygame.Rect(580, WINDOW_HEIGHT + 10, 120, 30),
    "playtest": pygame.Rect(710, WINDOW_HEIGHT + 10, 120, 30),
    "settings": pygame.Rect(840, WINDOW_HEIGHT + 10, 150, 30),
    "quit": pygame.Rect(840, WINDOW_HEIGHT + 50, 150, 30),
}

selected_tile_type = 'ground'  # Default selected tile type
playtest_mode = False  # Flag to indicate playtest mode

# Undo/Redo stacks
undo_stack = deque(maxlen=20)
redo_stack = deque(maxlen=20)

# Example level data for Mario Fan Builder-style levels
mario_fan_builder_level_data = [
    "GGGGGGGGGGGGGGGGGGGG",
    "                    ",
    "   GGGGGGGGGGGGGGG  ",
    "                    ",
    "      B    Q        ",
    "     WWWWWWWW       ",
    " P  GGG    C    GGG ",
    " P   M    W         ",
    " PWWWWWWW           ",
    "GGGGGGGGGGGGGGGGGGGG"
]

# Main menu function
def main_menu():
    menu_running = True
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if start_button.collidepoint(mouse_pos):
                    menu_running = False
                elif load_button.collidepoint(mouse_pos):
                    load_level()
                    menu_running = False
                elif quit_button.collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()

        window.fill(themes[current_theme]['background'])

        # Draw title
        title_text = pygame.font.Font(None, 48).render("Mario Fan Builder Level Editor", True, WHITE)
        window.blit(title_text, (WINDOW_WIDTH // 2 - title_text.get_width() // 2, 100))

        # Draw buttons
        pygame.draw.rect(window, BLACK, start_button)
        pygame.draw.rect(window, BLACK, load_button)
        pygame.draw.rect(window, BLACK, quit_button)

        # Draw button text
        start_text = FONT.render("Start Editor", True, WHITE)
        load_text = FONT.render("Load Level", True, WHITE)
        quit_text = FONT.render("Quit", True, WHITE)
        window.blit(start_text, (start_button.x + 20, start_button.y + 15))
        window.blit(load_text, (load_button.x + 20, load_button.y + 15))
        window.blit(quit_text, (quit_button.x + 40, quit_button.y + 15))

        pygame.display.update()
        game_clock.tick(60)

# Define main menu buttons
start_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 200, 200, 50)
load_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 300, 200, 50)
quit_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 400, 200, 50)

# Action Classes for Undo/Redo
class Action:
    def undo(self):
        pass

    def redo(self):
        pass

class AddAction(Action):
    def __init__(self, pos, tile_type):
        self.pos = pos
        self.tile_type = tile_type

    def undo(self):
        for sprite in all_sprites:
            if sprite.rect.topleft == self.pos and sprite != player:
                sprite.kill()
                if isinstance(sprite, Tile):
                    tiles_group.remove(sprite)
                    platforms_group.remove(sprite)
                elif isinstance(sprite, Enemy):
                    enemies_group.remove(sprite)
                elif isinstance(sprite, Coin):
                    coins_group.remove(sprite)
                elif isinstance(sprite, PowerUp):
                    powerups_group.remove(sprite)

    def redo(self):
        if self.tile_type in ['ground', 'brick', 'question', 'pipe', 'water', 'platform']:
            tile = Tile(self.pos, self.tile_type)
            if self.tile_type == 'platform':
                platforms_group.add(tile)
            else:
                tiles_group.add(tile)
            all_sprites.add(tile)
        elif self.tile_type == 'enemy':
            enemy = Enemy(self.pos)
            enemies_group.add(enemy)
            all_sprites.add(enemy)
        elif self.tile_type == 'coin':
            coin = Coin(self.pos)
            coins_group.add(coin)
            all_sprites.add(coin)
        elif self.tile_type == 'powerup':
            powerup = PowerUp(self.pos)
            powerups_group.add(powerup)
            all_sprites.add(powerup)

class RemoveAction(Action):
    def __init__(self, sprite):
        self.sprite = sprite
        self.pos = sprite.rect.topleft
        
        if hasattr(sprite, 'tile_type'):
            self.tile_type = sprite.tile_type 
        elif isinstance(sprite, Enemy):
            self.tile_type = 'enemy'
            if hasattr(sprite, 'enemy_type'):
                self.enemy_type = sprite.enemy_type
        elif isinstance(sprite, Coin):
            self.tile_type = 'coin'
        elif isinstance(sprite, PowerUp):
            self.tile_type = 'powerup'
            if hasattr(sprite, 'powerup_type'):
                self.powerup_type = sprite.powerup_type

    def undo(self):
        if hasattr(self, 'tile_type'):
            if self.tile_type in ['ground', 'brick', 'question', 'pipe', 'water', 'platform']:
                tile = Tile(self.pos, self.tile_type)
                if self.tile_type == 'platform':
                    platforms_group.add(tile)
                else:
                    tiles_group.add(tile)
                all_sprites.add(tile)
            elif self.tile_type == 'enemy':
                enemy_type = getattr(self, 'enemy_type', 'goomba')
                enemy = Enemy(self.pos, enemy_type)
                enemies_group.add(enemy)
                all_sprites.add(enemy)
            elif self.tile_type == 'coin':
                coin = Coin(self.pos)
                coins_group.add(coin)
                all_sprites.add(coin)
            elif self.tile_type == 'powerup':
                powerup_type = getattr(self, 'powerup_type', 'mushroom')
                powerup = PowerUp(self.pos, powerup_type)
                powerups_group.add(powerup)
                all_sprites.add(powerup)

    def redo(self):
        for sprite in all_sprites:
            if sprite.rect.topleft == self.pos and sprite != player:
                sprite.kill()
                if isinstance(sprite, Tile):
                    tiles_group.remove(sprite)
                    platforms_group.remove(sprite)
                elif isinstance(sprite, Enemy):
                    enemies_group.remove(sprite)
                elif isinstance(sprite, Coin):
                    coins_group.remove(sprite)
                elif isinstance(sprite, PowerUp):
                    powerups_group.remove(sprite)
                break

# Settings Menu Function
def open_settings():
    global GRID_SIZE, JUMP_STRENGTH, RUN_SPEED_MAX
    settings_running = True
    selected_grid_size = GRID_SIZE

    while settings_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    settings_running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if not settings_panel_rect.collidepoint(mouse_pos):
                    settings_running = False

        pygame.draw.rect(window, DARK_GRAY, settings_panel_rect)
        pygame.draw.rect(window, BLACK, settings_panel_rect, 2)

        settings_title = FONT.render("Mario Fan Builder Settings", True, WHITE)
        window.blit(settings_title, (settings_panel_rect.x + 10, settings_panel_rect.y + 10))

        grid_size_text = FONT.render(f"Grid Size: {selected_grid_size}", True, WHITE)
        window.blit(grid_size_text, (settings_panel_rect.x + 10, settings_panel_rect.y + 50))
        small_grid_btn = pygame.Rect(settings_panel_rect.x + 150, settings_panel_rect.y + 50, 40, 30)
        medium_grid_btn = pygame.Rect(settings_panel_rect.x + 200, settings_panel_rect.y + 50, 40, 30)
        large_grid_btn = pygame.Rect(settings_panel_rect.x + 250, settings_panel_rect.y + 50, 40, 30)
        pygame.draw.rect(window, BLACK, small_grid_btn)
        pygame.draw.rect(window, BLACK, medium_grid_btn)
        pygame.draw.rect(window, BLACK, large_grid_btn)
        small_text = FONT.render("25", True, WHITE)
        medium_text = FONT.render("50", True, WHITE)
        large_text = FONT.render("100", True, WHITE)
        window.blit(small_text, (small_grid_btn.x + 10, small_grid_btn.y + 5))
        window.blit(medium_text, (medium_grid_btn.x + 10, medium_grid_btn.y + 5))
        window.blit(large_text, (large_grid_btn.x + 10, large_grid_btn.y + 5))

        character_text = FONT.render("Character:", True, WHITE)
        window.blit(character_text, (settings_panel_rect.x + 10, settings_panel_rect.y + 100))
        for i, character_name in enumerate(characters):
            char_btn = pygame.Rect(settings_panel_rect.x + 100 + i * 70, settings_panel_rect.y + 100, 60, 30)
            pygame.draw.rect(window, BLACK, char_btn)
            char_label = FONT.render(character_name, True, WHITE)
            window.blit(char_label, (char_btn.x + 5, char_btn.y + 5))
            if player.character == character_name:
                pygame.draw.rect(window, GREEN, char_btn, 2)

        physics_text = FONT.render("Physics:", True, WHITE)
        window.blit(physics_text, (settings_panel_rect.x + 10, settings_panel_rect.y + 150))
        
        jump_text = FONT.render(f"Jump Strength: {abs(JUMP_STRENGTH)}", True, WHITE)
        window.blit(jump_text, (settings_panel_rect.x + 20, settings_panel_rect.y + 180))
        jump_slider = pygame.Rect(settings_panel_rect.x + 200, settings_panel_rect.y + 180, 150, 20)
        pygame.draw.rect(window, BLACK, jump_slider)
        
        run_text = FONT.render(f"Run Speed: {RUN_SPEED_MAX}", True, WHITE)
        window.blit(run_text, (settings_panel_rect.x + 20, settings_panel_rect.y + 210))
        run_slider = pygame.Rect(settings_panel_rect.x + 200, settings_panel_rect.y + 210, 150, 20)
        pygame.draw.rect(window, BLACK, run_slider)

        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            mouse_pos = pygame.mouse.get_pos()
            if small_grid_btn.collidepoint(mouse_pos):
                selected_grid_size = 25
            elif medium_grid_btn.collidepoint(mouse_pos):
                selected_grid_size = 50
            elif large_grid_btn.collidepoint(mouse_pos):
                selected_grid_size = 100

            for i, character_name in enumerate(characters):
                char_btn = pygame.Rect(settings_panel_rect.x + 100 + i * 70, settings_panel_rect.y + 100, 60, 30)
                if char_btn.collidepoint(mouse_pos):
                    player.character = character_name

            if jump_slider.collidepoint(mouse_pos):
                rel_x = mouse_pos[0] - jump_slider.x
                JUMP_STRENGTH = - (8 + int((rel_x / jump_slider.width) * 8))
                
            if run_slider.collidepoint(mouse_pos):
                rel_x = mouse_pos[0] - run_slider.x
                RUN_SPEED_MAX = 3 + int((rel_x / run_slider.width) * 7)

        if selected_grid_size != GRID_SIZE:
            update_grid_size(selected_grid_size)

        jump_pos = int(((abs(JUMP_STRENGTH) - 8) / 8) * jump_slider.width)
        pygame.draw.rect(window, GREEN, (jump_slider.x + jump_pos - 5, jump_slider.y, 10, 20))
        
        run_pos = int(((RUN_SPEED_MAX - 3) / 7) * run_slider.width)
        pygame.draw.rect(window, GREEN, (run_slider.x + run_pos - 5, run_slider.y, 10, 20))

        pygame.display.update()
        game_clock.tick(60)

def update_grid_size(new_size):
    global GRID_SIZE
    GRID_SIZE = new_size
    for sprite in all_sprites:
        if sprite != player:
            sprite.rect.topleft = snap_to_grid(sprite.rect.topleft, GRID_SIZE)

# Define settings panel rectangle
settings_panel_rect = pygame.Rect(WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 - 150, 400, 300)

# Call the main menu first
main_menu()

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and playtest_mode:
                player.jump()
            elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                if undo_stack:
                    action = undo_stack.pop()
                    redo_stack.append(action)
                    action.undo()
            elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                if redo_stack:
                    action = redo_stack.pop()
                    undo_stack.append(action)
                    action.redo()
            elif event.key == pygame.K_ESCAPE and playtest_mode:
                playtest_reset()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if not playtest_mode:
                for tile_type, rect in button_positions.items():
                    if rect.collidepoint(mouse_pos):
                        selected_tile_type = tile_type
                        break

                for theme_name, rect in theme_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        set_theme(theme_name)
                        break
                        
                for character_name, rect in character_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        player.character = character_name
                        break

                if buttons["save"].collidepoint(mouse_pos):
                    save_level()
                elif buttons["load"].collidepoint(mouse_pos):
                    load_level()
                elif buttons["load_construct"].collidepoint(mouse_pos):
                    load_construct_level(mario_fan_builder_level_data, theme_name='Mario Fan Builder Default')
                elif buttons["playtest"].collidepoint(mouse_pos):
                    playtest_mode = True
                    player.rect.center = (400, WINDOW_HEIGHT - GRID_SIZE)
                    player.velocity = pygame.Vector2(0, 0)
                    player.coins_collected = 0
                    player.score = 0
                    print("Playtest mode started. Use arrow keys to move, Space to jump, Shift to run.")
                elif buttons["settings"].collidepoint(mouse_pos):
                    open_settings()
                elif buttons["quit"].collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
                else:
                    if mouse_pos[1] < WINDOW_HEIGHT:
                        grid_pos = snap_to_grid(mouse_pos, GRID_SIZE)
                        if event.button == 1:  # Left click to add
                            action = AddAction(grid_pos, selected_tile_type)
                            undo_stack.append(action)
                            redo_stack.clear()

                            for sprite in all_sprites:
                                if sprite.rect.topleft == grid_pos and sprite != player:
                                    remove_action = RemoveAction(sprite)
                                    undo_stack.append(remove_action)
                                    sprite.kill()
                                    
                            if selected_tile_type in ['ground', 'brick', 'question', 'pipe', 'water']:
                                tile = Tile(grid_pos, selected_tile_type)
                                tiles_group.add(tile)
                                all_sprites.add(tile)
                            elif selected_tile_type == 'platform':
                                platform = Tile(grid_pos, 'platform')
                                platforms_group.add(platform)
                                all_sprites.add(platform)
                            elif selected_tile_type == 'enemy':
                                enemy = Enemy(grid_pos, 'goomba')
                                enemies_group.add(enemy)
                                all_sprites.add(enemy)
                            elif selected_tile_type == 'coin':
                                coin = Coin(grid_pos)
                                coins_group.add(coin)
                                all_sprites.add(coin)
                            elif selected_tile_type == 'powerup':
                                powerup = PowerUp(grid_pos, 'mushroom')
                                powerups_group.add(powerup)
                                all_sprites.add(powerup)
                        elif event.button == 3:  # Right click to remove
                            for sprite in all_sprites:
                                if sprite.rect.collidepoint(mouse_pos) and sprite != player:
                                    action = RemoveAction(sprite)
                                    undo_stack.append(action)
                                    redo_stack.clear()
                                    sprite.kill()
                                    break

    if playtest_mode:
        solid_tiles = pygame.sprite.Group([tile for tile in tiles_group if getattr(tile, 'is_solid', False)])
        player.update(solid_tiles, enemies_group, coins_group, powerups_group, platforms_group)
        enemies_group.update(solid_tiles)
        coins_group.update()
        powerups_group.update(solid_tiles)
    else:
        solid_tiles = pygame.sprite.Group([tile for tile in tiles_group if getattr(tile, 'is_solid', False)])
        enemies_group.update(solid_tiles)
        coins_group.update()

    window.fill(themes[current_theme]['background'])

    for x in range(0, WINDOW_WIDTH, GRID_SIZE):
        pygame.draw.line(window, GRAY, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
        pygame.draw.line(window, GRAY, (0, y), (WINDOW_WIDTH, y))

    all_sprites.draw(window)

    pygame.draw.rect(window, DARK_GRAY, HUD_RECT)

    for tile_type, rect in button_positions.items():
        window.blit(tile_icons[tile_type], rect.topleft)
        if tile_type == selected_tile_type:
            pygame.draw.rect(window, GREEN, rect, 3)
        else:
            pygame.draw.rect(window, BLACK, rect, 1)

    for theme_name, rect in theme_buttons.items():
        pygame.draw.rect(window, BLACK, rect, 2)
        theme_text = FONT.render(theme_name, True, BLACK)
        text_rect = theme_text.get_rect(center=rect.center)
        window.blit(theme_text, text_rect)
        if theme_name == current_theme:
            pygame.draw.rect(window, GREEN, rect, 2)
            
    for character_name, rect in character_buttons.items():
        pygame.draw.rect(window, BLACK, rect, 2)
        char_text = FONT.render(character_name, True, BLACK)
        text_rect = char_text.get_rect(center=rect.center)
        window.blit(char_text, text_rect)
        if character_name == player.character:
            pygame.draw.rect(window, GREEN, rect, 2)

    for key, rect in buttons.items():
        pygame.draw.rect(window, BLACK, rect, 2)
        if key == "save":
            text = "Save"
        elif key == "load":
            text = "Load"
        elif key == "load_construct":
            text = "Load Template"
        elif key == "playtest":
            text = "Playtest"
        elif key == "settings":
            text = "Settings"
        elif key == "quit":
            text = "Quit"
        button_text = FONT.render(text, True, BLACK)
        text_rect = button_text.get_rect(center=rect.center)
        window.blit(button_text, text_rect)

    fps = int(game_clock.get_fps())
    fps_text = FONT.render(f"FPS: {fps}", True, YELLOW)
    window.blit(fps_text, (WINDOW_WIDTH - 100, 10))

    if playtest_mode:
        player_state = player.state.capitalize()
        status_text = FONT.render(
            f"Character: {player.character.capitalize()} | State: {player_state} | Lives: {player.lives}",
            True, YELLOW
        )
        window.blit(status_text, (10, 10))
        
        score_text = FONT.render(f"Score: {player.score} | Coins: {player.coins_collected}", True, YELLOW)
        window.blit(score_text, (WINDOW_WIDTH - 300, WINDOW_HEIGHT + 10))
        
        p_meter_bg = pygame.Rect(10, WINDOW_HEIGHT + 40, 150, 20)
        pygame.draw.rect(window, BLACK, p_meter_bg)
        if player.p_meter > 0:
            p_meter_fill = pygame.Rect(10, WINDOW_HEIGHT + 40, player.p_meter * 25, 20)
            pygame.draw.rect(window, RED if player.p_meter >= 6 else YELLOW, p_meter_fill)
        p_meter_text = FONT.render("P-Meter", True, WHITE)
        window.blit(p_meter_text, (p_meter_bg.centerx - p_meter_text.get_width() // 2, p_meter_bg.y))
        
        controls_text = FONT.render(
            "Controls: Arrows to move, Space/Up to jump, Shift to run, ESC to exit",
            True, WHITE
        )
        window.blit(controls_text, (WINDOW_WIDTH // 2 - controls_text.get_width() // 2, WINDOW_HEIGHT + 70))
        
        if player.rect.right >= WINDOW_WIDTH - GRID_SIZE:
            success_text = pygame.font.Font(None, 36).render("Level Completed!", True, GREEN)
            window.blit(success_text, (WINDOW_WIDTH // 2 - success_text.get_width() // 2, WINDOW_HEIGHT // 2))
            pygame.display.update()
            pygame.time.delay(2000)
            playtest_reset()
    else:
        edit_text = FONT.render(
            "Edit Mode - Place: Left Click | Remove: Right Click | Undo: Ctrl+Z | Redo: Ctrl+Y", 
            True, WHITE
        )
        window.blit(edit_text, (WINDOW_WIDTH // 2 - edit_text.get_width() // 2, WINDOW_HEIGHT + 70))

    pygame.display.update()
    game_clock.tick(FPS)

pygame.quit()
sys.exit()
