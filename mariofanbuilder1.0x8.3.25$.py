import pygame
import json
import sys
import os
from collections import deque
from enum import Enum
import math

pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 800
HUD_HEIGHT = 120
GRID_SIZE = 50
FPS = 60

# Enhanced Color Palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
DARK_GRAY = (50, 50, 50)
PURPLE = (255, 0, 255)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Animation Constants
ANIMATION_SPEED = 0.1
COIN_ROTATION_SPEED = 5
QUESTION_BLOCK_PULSE = 0.05

# Enhanced Themes with gradient support
themes = {
    'Mario Forever Classic': {
        'ground': (165, 42, 42),
        'brick': (205, 133, 63),
        'question': (255, 223, 0),
        'coin': (255, 215, 0),
        'enemy': (178, 34, 34),
        'water': (0, 119, 190),
        'background': (92, 148, 252),
        'pipe': (0, 128, 0),
        'cloud': (255, 255, 255),
        'gradient_top': (135, 206, 235),
        'gradient_bottom': (25, 25, 112),
    },
    'Mario Forever World': {
        'ground': (139, 69, 19),
        'brick': (160, 82, 45),
        'question': (255, 255, 0),
        'coin': (255, 223, 0),
        'enemy': (220, 20, 60),
        'water': (64, 164, 223),
        'background': (70, 130, 180),
        'pipe': (34, 139, 34),
        'cloud': (245, 245, 245),
        'gradient_top': (255, 127, 80),
        'gradient_bottom': (255, 20, 147),
    },
    'Mario Forever Galaxy': {
        'ground': (75, 0, 130),
        'brick': (138, 43, 226),
        'question': (255, 255, 224),
        'coin': (255, 223, 0),
        'enemy': (255, 0, 255),
        'water': (0, 0, 139),
        'background': (0, 0, 0),
        'pipe': (192, 192, 192),
        'cloud': (255, 255, 255),
        'gradient_top': (25, 25, 112),
        'gradient_bottom': (0, 0, 0),
    },
    'SMB 8-bit': {
        'ground': (165, 42, 42),
        'brick': (255, 165, 0),
        'question': (255, 255, 0),
        'coin': (255, 223, 0),
        'enemy': (255, 0, 0),
        'water': (0, 0, 255),
        'background': (135, 206, 235),
        'pipe': (0, 255, 0),
        'cloud': (255, 255, 255),
        'gradient_top': (135, 206, 235),
        'gradient_bottom': (135, 206, 235),
    },
    'NSMB Modern': {
        'ground': (160, 82, 45),
        'brick': (222, 184, 135),
        'question': (255, 255, 224),
        'coin': (255, 223, 0),
        'enemy': (220, 20, 60),
        'water': (64, 164, 223),
        'background': (70, 130, 180),
        'pipe': (0, 100, 0),
        'cloud': (255, 255, 255),
        'gradient_top': (135, 206, 250),
        'gradient_bottom': (255, 255, 255),
    }
}

current_theme = 'Mario Forever Classic'

# Initialize window with double buffering for smooth 60 FPS
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT + HUD_HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption("Mario Maker 3 - Enhanced Edition")
game_clock = pygame.time.Clock()

# Fonts
FONT = pygame.font.Font(None, 24)
FONT_LARGE = pygame.font.Font(None, 36)
FONT_SMALL = pygame.font.Font(None, 18)

# Particle System for visual effects
class Particle:
    def __init__(self, pos, velocity, color, lifetime=30):
        self.pos = list(pos)
        self.velocity = velocity
        self.color = color
        self.lifetime = lifetime
        self.initial_lifetime = lifetime
        
    def update(self):
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        self.velocity[1] += 0.5  # Gravity
        self.lifetime -= 1
        
    def draw(self, surface):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.initial_lifetime))
            size = int(5 * (self.lifetime / self.initial_lifetime))
            pygame.draw.circle(surface, self.color, (int(self.pos[0]), int(self.pos[1])), size)

particles = []

# Enhanced Tile class with animations
class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, tile_type):
        super().__init__()
        self.tile_type = tile_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.animation_time = 0
        self.pulse = 0
        self.update_image()
        
    def update(self):
        self.animation_time += ANIMATION_SPEED
        if self.tile_type == 'question':
            self.pulse = abs(math.sin(self.animation_time)) * QUESTION_BLOCK_PULSE
            
    def update_image(self):
        theme_colors = themes[current_theme]
        base_color = theme_colors.get(self.tile_type, WHITE)
        self.image.fill(base_color)
        
        # Enhanced graphics for different tile types
        if self.tile_type == 'ground':
            # Add texture pattern
            for i in range(0, GRID_SIZE, 4):
                pygame.draw.line(self.image, 
                               (base_color[0] - 20, base_color[1] - 20, base_color[2] - 20),
                               (i, 0), (i, GRID_SIZE), 1)
                pygame.draw.line(self.image, 
                               (base_color[0] - 20, base_color[1] - 20, base_color[2] - 20),
                               (0, i), (GRID_SIZE, i), 1)
                               
        elif self.tile_type == 'brick':
            # Brick pattern
            brick_color = (base_color[0] - 30, base_color[1] - 30, base_color[2] - 30)
            for y in range(0, GRID_SIZE, 10):
                for x in range(0, GRID_SIZE, 20):
                    offset = 10 if (y // 10) % 2 else 0
                    pygame.draw.rect(self.image, brick_color,
                                   (x - offset, y, 18, 8), 1)
                                   
        elif self.tile_type == 'question':
            # Animated question mark
            size = int(GRID_SIZE * (0.8 + self.pulse))
            temp_surface = pygame.Surface((GRID_SIZE, GRID_SIZE))
            temp_surface.fill(base_color)
            pygame.draw.rect(temp_surface, 
                           (base_color[0] + 30, base_color[1] + 30, base_color[2]),
                           (5, 5, GRID_SIZE - 10, GRID_SIZE - 10), 2)
            # Draw question mark
            font = pygame.font.Font(None, 36)
            text = font.render("?", True, BLACK)
            text_rect = text.get_rect(center=(GRID_SIZE // 2, GRID_SIZE // 2))
            temp_surface.blit(text, text_rect)
            self.image = pygame.transform.scale(temp_surface, (size, size))
            self.rect = self.image.get_rect(center=self.rect.center)
            
        elif self.tile_type == 'water':
            # Animated water effect
            wave_offset = int(math.sin(self.animation_time * 2) * 3)
            pygame.draw.rect(self.image, base_color, (0, 0, GRID_SIZE, GRID_SIZE))
            lighter_blue = (base_color[0] + 30, base_color[1] + 30, min(255, base_color[2] + 30))
            for i in range(0, GRID_SIZE, 10):
                pygame.draw.line(self.image, lighter_blue,
                               (0, i + wave_offset), (GRID_SIZE, i + wave_offset), 2)
                               
        elif self.tile_type == 'pipe':
            # Pipe graphics
            pygame.draw.rect(self.image, base_color, (5, 0, GRID_SIZE - 10, GRID_SIZE))
            pygame.draw.rect(self.image, (base_color[0] + 20, base_color[1] + 20, base_color[2] + 20),
                           (0, 0, GRID_SIZE, 15))
            pygame.draw.rect(self.image, BLACK, (5, 0, GRID_SIZE - 10, GRID_SIZE), 2)
            pygame.draw.rect(self.image, BLACK, (0, 0, GRID_SIZE, 15), 2)

# Enhanced Enemy with animations
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, enemy_type='goomba'):
        super().__init__()
        self.enemy_type = enemy_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.velocity = pygame.Vector2(2, 0)
        self.animation_time = 0
        self.facing_right = True
        self.update_image()
        
    def update(self, solid_tiles):
        self.animation_time += ANIMATION_SPEED
        self.rect.x += self.velocity.x
        
        # Check collisions
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        if collisions:
            self.velocity.x *= -1
            self.facing_right = not self.facing_right
            self.rect.x += self.velocity.x
            
        # Apply gravity
        self.rect.y += 2
        floor_collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        if floor_collisions:
            self.rect.bottom = floor_collisions[0].rect.top
            
        self.update_image()
        
    def update_image(self):
        self.image.fill(themes[current_theme]['enemy'])
        
        # Draw enemy features
        if self.enemy_type == 'goomba':
            # Body
            pygame.draw.ellipse(self.image, themes[current_theme]['enemy'],
                              (5, 10, GRID_SIZE - 10, GRID_SIZE - 15))
            # Eyes
            eye_offset = int(math.sin(self.animation_time * 2) * 2)
            pygame.draw.circle(self.image, WHITE, (15, 20 + eye_offset), 5)
            pygame.draw.circle(self.image, WHITE, (35, 20 + eye_offset), 5)
            pygame.draw.circle(self.image, BLACK, (17 if self.facing_right else 13, 20 + eye_offset), 3)
            pygame.draw.circle(self.image, BLACK, (37 if self.facing_right else 33, 20 + eye_offset), 3)

# Enhanced Coin with rotation
class Coin(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.original_image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(topleft=pos)
        self.rotation = 0
        self.bob_offset = 0
        self.animation_time = 0
        self.update_image()
        
    def update(self):
        self.animation_time += ANIMATION_SPEED
        self.rotation += COIN_ROTATION_SPEED
        self.bob_offset = math.sin(self.animation_time * 2) * 5
        
        # Rotate coin
        self.image = pygame.transform.rotate(self.original_image, self.rotation)
        self.rect = self.image.get_rect(center=(self.rect.centerx, 
                                               self.rect.centery + self.bob_offset))
        
    def update_image(self):
        coin_color = themes[current_theme]['coin']
        # Draw coin with 3D effect
        pygame.draw.ellipse(self.original_image, coin_color,
                          (10, 10, GRID_SIZE - 20, GRID_SIZE - 20))
        pygame.draw.ellipse(self.original_image, 
                          (min(255, coin_color[0] + 50), 
                           min(255, coin_color[1] + 50), 
                           coin_color[2]),
                          (15, 15, GRID_SIZE - 30, GRID_SIZE - 30), 3)
        # Coin symbol
        font = pygame.font.Font(None, 24)
        text = font.render("$", True, BLACK)
        text_rect = text.get_rect(center=(GRID_SIZE // 2, GRID_SIZE // 2))
        self.original_image.blit(text, text_rect)

# Enhanced Player with smooth animations
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((GRID_SIZE - 10, GRID_SIZE - 5))
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.coins_collected = 0
        self.facing_right = True
        self.animation_time = 0
        self.jump_power = -15
        self.update_image()
        
    def update(self, solid_tiles, enemies, coins):
        self.animation_time += ANIMATION_SPEED
        keys = pygame.key.get_pressed()
        
        # Smooth horizontal movement
        if keys[pygame.K_LEFT]:
            self.velocity.x = max(self.velocity.x - 1, -7)
            self.facing_right = False
        elif keys[pygame.K_RIGHT]:
            self.velocity.x = min(self.velocity.x + 1, 7)
            self.facing_right = True
        else:
            # Friction
            self.velocity.x *= 0.9
            
        # Apply gravity with terminal velocity
        self.velocity.y += 0.6
        self.velocity.y = min(self.velocity.y, 15)
        
        # Move and handle collisions
        self.rect.x += self.velocity.x
        self.handle_collisions(self.velocity.x, 0, solid_tiles)
        
        self.rect.y += self.velocity.y
        self.on_ground = False
        self.handle_collisions(0, self.velocity.y, solid_tiles)
        
        # Screen boundaries
        self.rect.x = max(0, min(self.rect.x, WINDOW_WIDTH - self.rect.width))
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT
            self.velocity.y = 0
            self.on_ground = True
            
        # Enemy collision with particle effect
        enemy_hit = pygame.sprite.spritecollideany(self, enemies)
        if enemy_hit:
            # Create particles
            for _ in range(20):
                particles.append(Particle(
                    self.rect.center,
                    [pygame.time.get_ticks() % 10 - 5, pygame.time.get_ticks() % 10 - 10],
                    RED,
                    30
                ))
            playtest_reset()
            
        # Coin collection with particle effect
        collected = pygame.sprite.spritecollide(self, coins, True)
        for coin in collected:
            self.coins_collected += 1
            # Create sparkle particles
            for _ in range(10):
                particles.append(Particle(
                    coin.rect.center,
                    [pygame.time.get_ticks() % 6 - 3, pygame.time.get_ticks() % 6 - 6],
                    YELLOW,
                    20
                ))
                
        self.update_image()
        
    def handle_collisions(self, vel_x, vel_y, solid_tiles):
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in collisions:
            if vel_x > 0:
                self.rect.right = tile.rect.left
                self.velocity.x = 0
            elif vel_x < 0:
                self.rect.left = tile.rect.right
                self.velocity.x = 0
            if vel_y > 0:
                self.rect.bottom = tile.rect.top
                self.velocity.y = 0
                self.on_ground = True
            elif vel_y < 0:
                self.rect.top = tile.rect.bottom
                self.velocity.y = 0
                # Hit question block effect
                if hasattr(tile, 'tile_type') and tile.tile_type == 'question':
                    for _ in range(5):
                        particles.append(Particle(
                            tile.rect.center,
                            [pygame.time.get_ticks() % 4 - 2, -5],
                            YELLOW,
                            25
                        ))
                        
    def jump(self):
        if self.on_ground:
            self.velocity.y = self.jump_power
            self.on_ground = False
            # Jump particles
            for _ in range(5):
                particles.append(Particle(
                    (self.rect.centerx, self.rect.bottom),
                    [pygame.time.get_ticks() % 4 - 2, 2],
                    WHITE,
                    15
                ))
                
    def update_image(self):
        # Simple Mario-like character
        self.image.fill(BLUE)
        # Head
        pygame.draw.rect(self.image, (255, 220, 177), 
                        (10, 5, self.rect.width - 20, 15))
        # Eyes
        eye_x = 25 if self.facing_right else 15
        pygame.draw.circle(self.image, BLACK, (eye_x, 12), 2)
        # Body
        pygame.draw.rect(self.image, RED, 
                        (5, 20, self.rect.width - 10, 15))
        # Legs animation
        leg_offset = int(math.sin(self.animation_time * 10) * 3) if abs(self.velocity.x) > 1 else 0
        pygame.draw.rect(self.image, BLUE, 
                        (10 + leg_offset, 35, 10, 10))
        pygame.draw.rect(self.image, BLUE, 
                        (20 - leg_offset, 35, 10, 10))

# Background renderer with gradient
def draw_background(surface):
    theme_colors = themes[current_theme]
    top_color = theme_colors['gradient_top']
    bottom_color = theme_colors['gradient_bottom']
    
    # Draw gradient
    for y in range(WINDOW_HEIGHT):
        ratio = y / WINDOW_HEIGHT
        color = (
            int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio),
            int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio),
            int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        )
        pygame.draw.line(surface, color, (0, y), (WINDOW_WIDTH, y))
        
    # Draw clouds if not galaxy theme
    if 'Galaxy' not in current_theme:
        cloud_color = theme_colors['cloud']
        for i in range(3):
            x = 100 + i * 300 + int(math.sin(pygame.time.get_ticks() * 0.0001 + i) * 50)
            y = 50 + i * 40
            # Simple cloud shape
            pygame.draw.ellipse(surface, cloud_color, (x, y, 80, 40))
            pygame.draw.ellipse(surface, cloud_color, (x + 20, y - 10, 60, 50))
            pygame.draw.ellipse(surface, cloud_color, (x + 50, y, 70, 40))

# Helper functions remain the same
def snap_to_grid(pos, size):
    return (pos[0] // size) * size, (pos[1] // size) * size

# Save and Load functions (enhanced with theme data)
def save_level(filename="level.json"):
    level_data = {
        "tiles": [],
        "enemies": [],
        "coins": [],
        "theme": current_theme,
        "version": "2.0"
    }
    for tile in tiles_group:
        tile_data = {
            "x": tile.rect.x,
            "y": tile.rect.y,
            "type": tile.tile_type
        }
        level_data["tiles"].append(tile_data)
    for enemy in enemies_group:
        enemy_data = {
            "x": enemy.rect.x,
            "y": enemy.rect.y,
            "type": enemy.enemy_type
        }
        level_data["enemies"].append(enemy_data)
    for coin in coins_group:
        coin_data = {
            "x": coin.rect.x,
            "y": coin.rect.y
        }
        level_data["coins"].append(coin_data)
    with open(filename, "w") as file:
        json.dump(level_data, file, indent=4)
    print(f"Level saved to {filename}")

def load_level(filename="level.json"):
    global current_theme
    try:
        with open(filename, "r") as file:
            level_data = json.load(file)
            theme = level_data.get("theme", "Mario Forever Classic")
            set_theme(theme)
            tiles_group.empty()
            enemies_group.empty()
            coins_group.empty()
            all_sprites.empty()
            all_sprites.add(player)
            
            for tile_data in level_data["tiles"]:
                tile = Tile((tile_data["x"], tile_data["y"]), tile_data["type"])
                tiles_group.add(tile)
                all_sprites.add(tile)
                
            for enemy_data in level_data["enemies"]:
                enemy_type = enemy_data.get("type", "goomba")
                enemy = Enemy((enemy_data["x"], enemy_data["y"]), enemy_type)
                enemies_group.add(enemy)
                all_sprites.add(enemy)
                
            for coin_data in level_data["coins"]:
                coin = Coin((coin_data["x"], coin_data["y"]))
                coins_group.add(coin)
                all_sprites.add(coin)
        print(f"Level loaded from {filename}")
    except FileNotFoundError:
        print(f"File {filename} not found")

def set_theme(theme_name):
    global current_theme
    if theme_name in themes:
        current_theme = theme_name
        # Update all sprites with new theme
        for sprite in all_sprites:
            if hasattr(sprite, 'update_image'):
                sprite.update_image()
        print(f"Theme set to '{theme_name}'")

def playtest_reset():
    global playtest_mode
    player.rect.center = (100, WINDOW_HEIGHT - GRID_SIZE * 2)
    player.velocity = pygame.Vector2(0, 0)
    player.coins_collected = 0
    playtest_mode = False
    # Reload coins
    coins_to_reload = []
    for coin_data in last_saved_coins:
        coin = Coin((coin_data[0], coin_data[1]))
        coins_to_reload.append(coin)
    for coin in coins_to_reload:
        coins_group.add(coin)
        all_sprites.add(coin)

# Initialize sprite groups
tiles_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
coins_group = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()

# Create player
player = Player((100, WINDOW_HEIGHT - GRID_SIZE * 2))
all_sprites.add(player)

# Enhanced tile types
tile_types = ['ground', 'brick', 'question', 'water', 'pipe', 'enemy', 'coin']

# Create tile icons with enhanced graphics
tile_icons = {}
for tile_type in tile_types:
    icon = pygame.Surface((40, 40), pygame.SRCALPHA)
    if tile_type in ['enemy', 'coin']:
        if tile_type == 'enemy':
            icon.fill(themes[current_theme]['enemy'])
            pygame.draw.circle(icon, WHITE, (15, 15), 5)
            pygame.draw.circle(icon, WHITE, (25, 15), 5)
            pygame.draw.circle(icon, BLACK, (15, 15), 3)
            pygame.draw.circle(icon, BLACK, (25, 15), 3)
        else:
            pygame.draw.circle(icon, themes[current_theme]['coin'], (20, 20), 15)
            font = pygame.font.Font(None, 20)
            text = font.render("$", True, BLACK)
            text_rect = text.get_rect(center=(20, 20))
            icon.blit(text, text_rect)
    else:
        icon.fill(themes[current_theme].get(tile_type, WHITE))
    tile_icons[tile_type] = icon

# HUD setup
HUD_RECT = pygame.Rect(0, WINDOW_HEIGHT, WINDOW_WIDTH, HUD_HEIGHT)

# Button positions
button_positions = {}
for i, tile_type in enumerate(tile_types):
    x = 10 + i * 60
    y = WINDOW_HEIGHT + 10
    button_positions[tile_type] = pygame.Rect(x, y, 40, 40)

# Theme buttons
theme_names = list(themes.keys())
theme_buttons = {}
for i, theme_name in enumerate(theme_names):
    x = 10 + i * 130
    y = WINDOW_HEIGHT + 60
    theme_buttons[theme_name] = pygame.Rect(x, y, 120, 30)

# Control buttons
buttons = {
    "save": pygame.Rect(450, WINDOW_HEIGHT + 10, 80, 30),
    "load": pygame.Rect(540, WINDOW_HEIGHT + 10, 80, 30),
    "playtest": pygame.Rect(630, WINDOW_HEIGHT + 10, 100, 30),
    "clear": pygame.Rect(740, WINDOW_HEIGHT + 10, 80, 30),
    "quit": pygame.Rect(830, WINDOW_HEIGHT + 10, 80, 30),
}

selected_tile_type = 'ground'
playtest_mode = False
last_saved_coins = []

# Main menu
def main_menu():
    menu_running = True
    logo_bounce = 0
    
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
                    
        # Animated background
        draw_background(window)
        
        # Animated logo
        logo_bounce = math.sin(pygame.time.get_ticks() * 0.002) * 10
        title_text = FONT_LARGE.render("Mario Maker 3 - Enhanced Edition", True, WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 100 + logo_bounce))
        window.blit(title_text, title_rect)
        
        # Subtitle
        subtitle_text = FONT.render("60 FPS • Multiple Themes • Enhanced Graphics", True, YELLOW)
        subtitle_rect = subtitle_text.get_rect(center=(WINDOW_WIDTH // 2, 150))
        window.blit(subtitle_text, subtitle_rect)
        
        # Draw menu buttons with hover effect
        mouse_pos = pygame.mouse.get_pos()
        
        for button, text in [(start_button, "Start Editor"), 
                           (load_button, "Load Level"), 
                           (quit_button, "Quit")]:
            color = GREEN if button.collidepoint(mouse_pos) else BLACK
            pygame.draw.rect(window, color, button, border_radius=10)
            pygame.draw.rect(window, WHITE, button, 3, border_radius=10)
            button_text = FONT.render(text, True, WHITE)
            text_rect = button_text.get_rect(center=button.center)
            window.blit(button_text, text_rect)
            
        pygame.display.flip()
        game_clock.tick(FPS)

# Menu buttons
start_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 300, 200, 50)
load_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 370, 200, 50)
quit_button = pygame.Rect(WINDOW_WIDTH // 2 - 100, 440, 200, 50)

# Run main menu
main_menu()

# Main game loop
running = True
mouse_held = False
erase_mode = False

while running:
    dt = game_clock.tick(FPS) / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.jump()
            elif event.key == pygame.K_ESCAPE and playtest_mode:
                playtest_reset()
            elif event.key == pygame.K_e:
                erase_mode = not erase_mode
                
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            mouse_held = True
            
            if not playtest_mode:
                # Check HUD interactions
                for tile_type, rect in button_positions.items():
                    if rect.collidepoint(mouse_pos):
                        selected_tile_type = tile_type
                        erase_mode = False
                        
                for theme_name, rect in theme_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        set_theme(theme_name)
                        
                if buttons["save"].collidepoint(mouse_pos):
                    last_saved_coins = [(coin.rect.x, coin.rect.y) for coin in coins_group]
                    save_level()
                elif buttons["load"].collidepoint(mouse_pos):
                    load_level()
                elif buttons["playtest"].collidepoint(mouse_pos):
                    playtest_mode = True
                    last_saved_coins = [(coin.rect.x, coin.rect.y) for coin in coins_group]
                    player.rect.center = (100, WINDOW_HEIGHT - GRID_SIZE * 2)
                    player.velocity = pygame.Vector2(0, 0)
                    player.coins_collected = 0
                elif buttons["clear"].collidepoint(mouse_pos):
                    tiles_group.empty()
                    enemies_group.empty()
                    coins_group.empty()
                    all_sprites.empty()
                    all_sprites.add(player)
                elif buttons["quit"].collidepoint(mouse_pos):
                    running = False
                    
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_held = False
            
        elif event.type == pygame.MOUSEMOTION and mouse_held and not playtest_mode:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[1] < WINDOW_HEIGHT:
                grid_pos = snap_to_grid(mouse_pos, GRID_SIZE)
                
                if erase_mode:
                    # Erase mode
                    for sprite in all_sprites:
                        if sprite.rect.collidepoint(mouse_pos) and sprite != player:
                            sprite.kill()
                else:
                    # Place mode
                    # Check if position is empty
                    occupied = False
                    for sprite in all_sprites:
                        if sprite.rect.topleft == grid_pos and sprite != player:
                            occupied = True
                            break
                            
                    if not occupied:
                        if selected_tile_type in ['ground', 'brick', 'question', 'water', 'pipe']:
                            tile = Tile(grid_pos, selected_tile_type)
                            tiles_group.add(tile)
                            all_sprites.add(tile)
                        elif selected_tile_type == 'enemy':
                            enemy = Enemy(grid_pos)
                            enemies_group.add(enemy)
                            all_sprites.add(enemy)
                        elif selected_tile_type == 'coin':
                            coin = Coin(grid_pos)
                            coins_group.add(coin)
                            all_sprites.add(coin)
    
    # Update
    if playtest_mode:
        solid_tiles = pygame.sprite.Group([tile for tile in tiles_group 
                                         if tile.tile_type in ['ground', 'brick', 'question', 'water', 'pipe']])
        player.update(solid_tiles, enemies_group, coins_group)
        enemies_group.update(solid_tiles)
        coins_group.update()
        tiles_group.update()
    else:
        # Update animations even in edit mode
        coins_group.update()
        tiles_group.update()
        
    # Update particles
    for particle in particles[:]:
        particle.update()
        if particle.lifetime <= 0:
            particles.remove(particle)
    
    # Draw everything
    draw_background(window)
    
    # Draw grid in edit mode
    if not playtest_mode:
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(window, (GRAY[0], GRAY[1], GRAY[2], 50), (x, 0), (x, WINDOW_HEIGHT), 1)
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(window, (GRAY[0], GRAY[1], GRAY[2], 50), (0, y), (WINDOW_WIDTH, y), 1)
    
    # Draw sprites
    all_sprites.draw(window)
    
    # Draw particles
    for particle in particles:
        particle.draw(window)
    
    # Draw HUD
    pygame.draw.rect(window, DARK_GRAY, HUD_RECT)
    pygame.draw.line(window, WHITE, (0, WINDOW_HEIGHT), (WINDOW_WIDTH, WINDOW_HEIGHT), 2)
    
    # Draw tile selection
    for tile_type, rect in button_positions.items():
        pygame.draw.rect(window, WHITE, rect, 2)
        window.blit(tile_icons[tile_type], rect.topleft)
        if tile_type == selected_tile_type and not erase_mode:
            pygame.draw.rect(window, GREEN, rect, 3)
    
    # Draw theme buttons
    for theme_name, rect in theme_buttons.items():
        color = GREEN if theme_name == current_theme else BLACK
        pygame.draw.rect(window, color, rect)
        pygame.draw.rect(window, WHITE, rect, 2)
        text = FONT_SMALL.render(theme_name[:12], True, WHITE)
        text_rect = text.get_rect(center=rect.center)
        window.blit(text, text_rect)
    
    # Draw control buttons
    for button_name, rect in buttons.items():
        pygame.draw.rect(window, BLACK, rect)
        pygame.draw.rect(window, WHITE, rect, 2)
        text = FONT.render(button_name.capitalize(), True, WHITE)
        text_rect = text.get_rect(center=rect.center)
        window.blit(text, text_rect)
    
    # Draw mode indicator
    mode_text = "PLAYTEST MODE" if playtest_mode else ("ERASE MODE" if erase_mode else "EDIT MODE")
    mode_color = RED if playtest_mode else (ORANGE if erase_mode else GREEN)
    mode_surface = FONT_LARGE.render(mode_text, True, mode_color)
    window.blit(mode_surface, (WINDOW_WIDTH - 200, 10))
    
    # Draw FPS counter
    fps = int(game_clock.get_fps())
    fps_color = GREEN if fps >= 55 else (YELLOW if fps >= 30 else RED)
    fps_text = FONT.render(f"FPS: {fps}", True, fps_color)
    window.blit(fps_text, (10, 10))
    
    # Draw coin counter in playtest mode
    if playtest_mode:
        coin_text = FONT_LARGE.render(f"Coins: {player.coins_collected}", True, YELLOW)
        window.blit(coin_text, (WINDOW_WIDTH // 2 - 50, 10))
        
        # Instructions
        inst_text = FONT.render("Arrow Keys: Move | Space: Jump | ESC: Exit Playtest", True, WHITE)
        window.blit(inst_text, (10, WINDOW_HEIGHT + 95))
    else:
        # Edit mode instructions
        inst_text = FONT.render("Click/Drag: Place | E: Toggle Erase Mode | Select tiles below", True, WHITE)
        window.blit(inst_text, (10, WINDOW_HEIGHT + 95))
    
    pygame.display.flip()

pygame.quit()
