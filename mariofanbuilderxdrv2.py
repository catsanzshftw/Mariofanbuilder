import pygame
import json
import sys
from collections import deque

pygame.init()

# Constants
WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 700  # Increased window size for better HUD
HUD_HEIGHT = 100
GRID_SIZE = 50

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
DARK_GRAY = (50, 50, 50)

# Define Themes
themes = {
    'Retro': {
        'ground': (139, 69, 19),        # Brown
        'brick': (205, 133, 63),        # Light Brown
        'question': (255, 223, 0),      # Yellow
        'coin': (255, 215, 0),          # Gold
        'enemy': (178, 34, 34),         # Firebrick
        'water': (0, 191, 255),         # Deep Sky Blue
        'background': (34, 34, 34),     # Dark Gray
    },
    'SMB 8-bit': {
        'ground': (165, 42, 42),         # Brown
        'brick': (255, 165, 0),          # Orange
        'question': (255, 255, 0),       # Bright Yellow
        'coin': (255, 223, 0),           # Gold
        'enemy': (255, 0, 0),            # Red
        'water': (0, 0, 255),            # Blue
        'background': (135, 206, 235),   # Sky Blue
    },
    'NSMB': {
        'ground': (160, 82, 45),         # Sienna
        'brick': (222, 184, 135),        # Burlywood
        'question': (255, 255, 224),     # Light Yellow
        'coin': (255, 223, 0),           # Gold
        'enemy': (220, 20, 60),          # Crimson
        'water': (64, 164, 223),         # Blue
        'background': (70, 130, 180),    # Steel Blue
    }
}

current_theme = 'Retro'  # Default theme

# Initialize the window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT + HUD_HEIGHT))
pygame.display.set_caption("Mario Maker 3 PC/M1 Port")
game_clock = pygame.time.Clock()

# Font
FONT = pygame.font.Font(None, 24)

# Classes for various game elements
class Tile(pygame.sprite.Sprite):
    def __init__(self, pos, tile_type):
        super().__init__()
        self.tile_type = tile_type
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.rect = self.image.get_rect(topleft=pos)
        self.update_image()

    def update_image(self):
        theme_colors = themes[current_theme]
        self.image.fill(theme_colors.get(self.tile_type, WHITE))
        
        # Additional graphics for specific tiles
        if self.tile_type == 'question':
            pygame.draw.line(self.image, BLACK, (10, 10), (30, 10), 3)
            pygame.draw.line(self.image, BLACK, (10, 10), (10, 30), 3)
        elif self.tile_type == 'coin':
            pygame.draw.circle(self.image, WHITE, (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 2 - 5)
        elif self.tile_type == 'water':
            pygame.draw.rect(self.image, BLUE, (10, 10, 20, 20))  # Simple wave pattern

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(themes[current_theme]['enemy'])
        self.rect = self.image.get_rect(topleft=pos)
        self.velocity = pygame.Vector2(2, 0)  # Moves horizontally

    def update(self, solid_tiles):
        self.rect.x += self.velocity.x
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        if collisions:
            self.velocity.x *= -1
            self.rect.x += self.velocity.x  # Move back to prevent sticking

class Coin(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE), pygame.SRCALPHA)
        pygame.draw.circle(self.image, themes[current_theme]['coin'], (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 2 - 5)
        self.rect = self.image.get_rect(topleft=pos)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.Vector2(0, 0)
        self.on_ground = False
        self.coins_collected = 0

    def update(self, solid_tiles, enemies, coins):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0

        # Horizontal movement
        if keys[pygame.K_LEFT]:
            self.velocity.x = -5
        if keys[pygame.K_RIGHT]:
            self.velocity.x = 5

        # Apply gravity
        self.velocity.y += 0.5  # Gravity
        self.velocity.y = min(self.velocity.y, 10)  # Terminal velocity

        # Move horizontally and handle collisions
        self.rect.x += self.velocity.x
        self.handle_collisions(self.velocity.x, 0, solid_tiles)

        # Move vertically and handle collisions
        self.rect.y += self.velocity.y
        self.on_ground = False
        self.handle_collisions(0, self.velocity.y, solid_tiles)

        # Prevent player from falling below the screen
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT
            self.velocity.y = 0
            self.on_ground = True

        # Check collision with enemies
        if pygame.sprite.spritecollideany(self, enemies):
            print("Hit by enemy! Restarting playtest...")
            playtest_reset()

        # Check collision with coins
        collected = pygame.sprite.spritecollide(self, coins, True)
        self.coins_collected += len(collected)

    def handle_collisions(self, vel_x, vel_y, solid_tiles):
        collisions = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in collisions:
            if vel_x > 0:  # Moving right; Hit the left side of the tile
                self.rect.right = tile.rect.left
            elif vel_x < 0:  # Moving left; Hit the right side of the tile
                self.rect.left = tile.rect.right
            if vel_y > 0:  # Moving down; Hit the top side of the tile
                self.rect.bottom = tile.rect.top
                self.velocity.y = 0
                self.on_ground = True
            elif vel_y < 0:  # Moving up; Hit the bottom side of the tile
                self.rect.top = tile.rect.bottom
                self.velocity.y = 0

    def jump(self):
        if self.on_ground:
            self.velocity.y = -12
            self.on_ground = False

# Helper functions
def snap_to_grid(pos, size):
    return (pos[0] // size) * size, (pos[1] // size) * size

# Save and Load Functions
def save_level(filename="level.json"):
    level_data = {
        "tiles": [],
        "enemies": [],
        "coins": [],
        "theme": current_theme
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
            "y": enemy.rect.y
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
    print(f"Level saved to {filename}.")

def load_level(filename="level.json"):
    global current_theme
    try:
        with open(filename, "r") as file:
            level_data = json.load(file)
            theme = level_data.get("theme", "Retro")
            set_theme(theme)
            tiles_group.empty()
            enemies_group.empty()
            coins_group.empty()
            all_sprites.empty()
            all_sprites.add(player)

            # Load tiles
            for tile_data in level_data["tiles"]:
                tile = Tile((tile_data["x"], tile_data["y"]), tile_data["type"])
                tiles_group.add(tile)
                all_sprites.add(tile)

            # Load enemies
            for enemy_data in level_data["enemies"]:
                enemy = Enemy((enemy_data["x"], enemy_data["y"]))
                enemies_group.add(enemy)
                all_sprites.add(enemy)

            # Load coins
            for coin_data in level_data["coins"]:
                coin = Coin((coin_data["x"], coin_data["y"]))
                coins_group.add(coin)
                all_sprites.add(coin)
        print(f"Level loaded from {filename}.")
    except FileNotFoundError:
        print(f"File {filename} not found.")

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
                sprite.image.fill((0, 0, 0, 0))  # Clear the surface
                pygame.draw.circle(sprite.image, themes[current_theme]['coin'], (GRID_SIZE // 2, GRID_SIZE // 2), GRID_SIZE // 2 - 5)
        print(f"Theme set to '{theme_name}'.")
    else:
        print(f"Theme '{theme_name}' does not exist.")

def load_construct_level(level_data, theme_name='Retro'):
    set_theme(theme_name)
    tiles_group.empty()
    enemies_group.empty()
    coins_group.empty()
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
                tiles_group.add(tile)
                all_sprites.add(tile)
            elif char == 'C':  # Coin
                coin = Coin(pos)
                coins_group.add(coin)
                all_sprites.add(coin)
            elif char == 'E':  # Enemy
                enemy = Enemy(pos)
                enemies_group.add(enemy)
                all_sprites.add(enemy)
            elif char == 'W':  # Water
                tile = Tile(pos, 'water')
                tiles_group.add(tile)
                all_sprites.add(tile)
    print("Construct level loaded.")

def playtest_reset():
    global playtest_mode
    # Reset player position and coins
    player.rect.center = (400, WINDOW_HEIGHT - GRID_SIZE)
    player.velocity = pygame.Vector2(0, 0)
    player.coins_collected = 0
    playtest_mode = False
    print("Playtest mode ended. Back to editor.")

# Initialize sprite groups
tiles_group = pygame.sprite.Group()
enemies_group = pygame.sprite.Group()
coins_group = pygame.sprite.Group()
all_sprites = pygame.sprite.Group()

# Create the player
player = Player((400, WINDOW_HEIGHT - GRID_SIZE))
all_sprites.add(player)

# HUD Setup
HUD_RECT = pygame.Rect(0, WINDOW_HEIGHT, WINDOW_WIDTH, HUD_HEIGHT)

# Define tile types and their icons
tile_types = ['ground', 'brick', 'question', 'water', 'enemy', 'coin']
tile_icons = {}

# Initialize tile icons
for index, tile_type in enumerate(tile_types):
    icon = pygame.Surface((40, 40), pygame.SRCALPHA)
    theme_colors = themes[current_theme]
    if tile_type in theme_colors:
        icon.fill(theme_colors[tile_type])
    elif tile_type == 'coin':
        pygame.draw.circle(icon, themes[current_theme]['coin'], (20, 20), 15)
    elif tile_type == 'enemy':
        icon.fill(themes[current_theme]['enemy'])
    else:
        icon.fill(WHITE)
    tile_icons[tile_type] = icon

# HUD buttons positions
button_positions = {}
for i, tile_type in enumerate(tile_types):
    x = 10 + i * 60  # Adjusted spacing for better layout
    y = WINDOW_HEIGHT + 10
    button_positions[tile_type] = pygame.Rect(x, y, 40, 40)

# Theme selection buttons
theme_names = list(themes.keys())
theme_buttons = {}
for i, theme_name in enumerate(theme_names):
    x = 10 + i * 110
    y = WINDOW_HEIGHT + 60
    theme_buttons[theme_name] = pygame.Rect(x, y, 100, 30)

# Save, Load, Load Construct, and Playtest buttons
buttons = {
    "save": pygame.Rect(400, WINDOW_HEIGHT + 10, 80, 30),
    "load": pygame.Rect(490, WINDOW_HEIGHT + 10, 80, 30),
    "load_construct": pygame.Rect(580, WINDOW_HEIGHT + 10, 120, 30),
    "playtest": pygame.Rect(710, WINDOW_HEIGHT + 10, 120, 30),
    "settings": pygame.Rect(400, WINDOW_HEIGHT + 50, 150, 30),
    "quit": pygame.Rect(570, WINDOW_HEIGHT + 50, 150, 30),
}

selected_tile_type = 'ground'  # Default selected tile type
playtest_mode = False  # Flag to indicate playtest mode

# Undo/Redo stacks
undo_stack = deque(maxlen=20)
redo_stack = deque(maxlen=20)

# Example level data for Mario Construct/Flash-like levels
construct_level_data = [
    "GGGGGGGGGGGGGGGGGGGG",
    "                    ",
    "   GGGGGGGGGGGGGGG  ",
    "                    ",
    "      B    Q        ",
    "     WWWWWWWW       ",
    "    GGG    C    GGG ",
    "    W     W         ",
    "    WWWWWW          ",
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

        window.fill(GRAY)

        # Draw buttons
        pygame.draw.rect(window, BLACK, start_button)
        pygame.draw.rect(window, BLACK, load_button)
        pygame.draw.rect(window, BLACK, quit_button)

        # Draw button text
        start_text = FONT.render("Start Editor", True, WHITE)
        load_text = FONT.render("Load Level", True, WHITE)
        quit_text = FONT.render("Quit", True, WHITE)
        window.blit(start_text, (start_button.x + 20, start_button.y + 5))
        window.blit(load_text, (load_button.x + 20, load_button.y + 5))
        window.blit(quit_text, (quit_button.x + 40, quit_button.y + 5))

        pygame.display.update()
        game_clock.tick(60)

# Define main menu buttons
start_button = pygame.Rect(400, 200, 200, 50)
load_button = pygame.Rect(400, 300, 200, 50)
quit_button = pygame.Rect(400, 400, 200, 50)

# Call the main menu
main_menu()

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
        # Remove the tile or object at the position
        for sprite in all_sprites:
            if sprite.rect.topleft == self.pos and sprite != player:
                sprite.kill()

    def redo(self):
        # Re-add the tile or object
        if self.tile_type in ['ground', 'brick', 'question', 'water']:
            tile = Tile(self.pos, self.tile_type)
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

class RemoveAction(Action):
    def __init__(self, sprite):
        self.sprite = sprite
        self.pos = sprite.rect.topleft
        self.tile_type = sprite.tile_type if isinstance(sprite, Tile) else None

    def undo(self):
        # Re-add the sprite
        if isinstance(self.sprite, Tile):
            tile = Tile(self.pos, self.tile_type)
            tiles_group.add(tile)
            all_sprites.add(tile)
        elif isinstance(self.sprite, Enemy):
            enemy = Enemy(self.pos)
            enemies_group.add(enemy)
            all_sprites.add(enemy)
        elif isinstance(self.sprite, Coin):
            coin = Coin(self.pos)
            coins_group.add(coin)
            all_sprites.add(coin)

    def redo(self):
        # Remove the sprite
        self.sprite.kill()

# Settings Menu Function
def open_settings():
    settings_running = True
    selected_grid_size = GRID_SIZE
    selected_theme = current_theme

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
                # Close settings if clicking outside the settings panel
                if not settings_panel_rect.collidepoint(mouse_pos):
                    settings_running = False

        # Draw settings panel
        pygame.draw.rect(window, DARK_GRAY, settings_panel_rect)
        pygame.draw.rect(window, BLACK, settings_panel_rect, 2)

        # Settings Title
        settings_title = FONT.render("Settings", True, WHITE)
        window.blit(settings_title, (settings_panel_rect.x + 10, settings_panel_rect.y + 10))

        # Grid Size Option
        grid_size_text = FONT.render(f"Grid Size: {selected_grid_size}", True, WHITE)
        window.blit(grid_size_text, (settings_panel_rect.x + 10, settings_panel_rect.y + 50))
        # Grid Size Buttons
        small_grid_btn = pygame.Rect(settings_panel_rect.x + 150, settings_panel_rect.y + 40, 40, 30)
        medium_grid_btn = pygame.Rect(settings_panel_rect.x + 200, settings_panel_rect.y + 40, 40, 30)
        large_grid_btn = pygame.Rect(settings_panel_rect.x + 250, settings_panel_rect.y + 40, 40, 30)
        pygame.draw.rect(window, BLACK, small_grid_btn)
        pygame.draw.rect(window, BLACK, medium_grid_btn)
        pygame.draw.rect(window, BLACK, large_grid_btn)
        small_text = FONT.render("25", True, WHITE)
        medium_text = FONT.render("50", True, WHITE)
        large_text = FONT.render("100", True, WHITE)
        window.blit(small_text, small_grid_btn.center)
        window.blit(medium_text, medium_grid_btn.center)
        window.blit(large_text, large_grid_btn.center)

        # Theme Selection Option
        theme_text = FONT.render("Theme:", True, WHITE)
        window.blit(theme_text, (settings_panel_rect.x + 10, settings_panel_rect.y + 100))
        for i, theme_name in enumerate(theme_names):
            theme_btn = pygame.Rect(settings_panel_rect.x + 100 + i * 110, settings_panel_rect.y + 90, 100, 30)
            pygame.draw.rect(window, BLACK, theme_btn)
            theme_label = FONT.render(theme_name, True, WHITE)
            theme_label_rect = theme_label.get_rect(center=theme_btn.center)
            window.blit(theme_label, theme_label_rect)

        # Handle Grid Size Button Clicks
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:
            mouse_pos = pygame.mouse.get_pos()
            if small_grid_btn.collidepoint(mouse_pos):
                selected_grid_size = 25
            elif medium_grid_btn.collidepoint(mouse_pos):
                selected_grid_size = 50
            elif large_grid_btn.collidepoint(mouse_pos):
                selected_grid_size = 100

            # Handle Theme Button Clicks
            for i, theme_name in enumerate(theme_names):
                theme_btn = pygame.Rect(settings_panel_rect.x + 100 + i * 110, settings_panel_rect.y + 90, 100, 30)
                if theme_btn.collidepoint(mouse_pos):
                    set_theme(theme_name)

        # Update grid size if changed
        if selected_grid_size != GRID_SIZE:
            update_grid_size(selected_grid_size)

        pygame.display.update()
        game_clock.tick(60)

def update_grid_size(new_size):
    global GRID_SIZE
    GRID_SIZE = new_size
    # Update all tiles, enemies, and coins positions to snap to new grid
    for sprite in all_sprites:
        sprite.rect.topleft = snap_to_grid(sprite.rect.topleft, GRID_SIZE)

# Define settings panel rectangle
settings_panel_rect = pygame.Rect(WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 - 150, 400, 300)

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not playtest_mode:
                player.jump()
            elif event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                # Ctrl+Z for Undo
                if undo_stack:
                    action = undo_stack.pop()
                    redo_stack.append(action)
                    action.undo()
            elif event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                # Ctrl+Y for Redo
                if redo_stack:
                    action = redo_stack.pop()
                    undo_stack.append(action)
                    action.redo()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            if not playtest_mode:
                # Check if clicking on HUD tile icons
                for tile_type, rect in button_positions.items():
                    if rect.collidepoint(mouse_pos):
                        selected_tile_type = tile_type
                        break

                # Check if clicking on Theme buttons
                for theme_name, rect in theme_buttons.items():
                    if rect.collidepoint(mouse_pos):
                        set_theme(theme_name)
                        break

                # Check if clicking on Save/Load buttons
                if buttons["save"].collidepoint(mouse_pos):
                    save_level()
                elif buttons["load"].collidepoint(mouse_pos):
                    load_level()
                elif buttons["load_construct"].collidepoint(mouse_pos):
                    load_construct_level(construct_level_data, theme_name='Retro')
                elif buttons["playtest"].collidepoint(mouse_pos):
                    playtest_mode = True
                    player.rect.center = (400, WINDOW_HEIGHT - GRID_SIZE)
                    player.velocity = pygame.Vector2(0, 0)
                    player.coins_collected = 0
                    print("Playtest mode started.")
                elif buttons["settings"].collidepoint(mouse_pos):
                    # Open settings menu
                    open_settings()
                elif buttons["quit"].collidepoint(mouse_pos):
                    pygame.quit()
                    sys.exit()
                else:
                    # Placing or removing tiles/objects
                    if mouse_pos[1] < WINDOW_HEIGHT:  # Ensure we are not clicking on the HUD
                        grid_pos = snap_to_grid(mouse_pos, GRID_SIZE)
                        if event.button == 1:  # Left click to add a tile or object
                            # Record action for undo
                            action = AddAction(grid_pos, selected_tile_type)
                            undo_stack.append(action)
                            redo_stack.clear()

                            # Remove existing tile or object at grid position
                            for sprite in all_sprites:
                                if sprite.rect.topleft == grid_pos and sprite != player:
                                    remove_action = RemoveAction(sprite)
                                    undo_stack.append(remove_action)
                                    redo_stack.clear()
                                    sprite.kill()
                            # Add the selected tile or object
                            if selected_tile_type in ['ground', 'brick', 'question', 'water']:
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
                        elif event.button == 3:  # Right click to remove a tile or object
                            for sprite in all_sprites:
                                if sprite.rect.collidepoint(mouse_pos) and sprite != player:
                                    # Record action for undo
                                    action = RemoveAction(sprite)
                                    undo_stack.append(action)
                                    redo_stack.clear()
                                    sprite.kill()
                                    break

    if playtest_mode:
        # Update player and other sprites
        solid_tiles = pygame.sprite.Group([tile for tile in tiles_group if tile.tile_type in ['ground', 'brick', 'question', 'water']])
        player.update(solid_tiles, enemies_group, coins_group)
        enemies_group.update(solid_tiles)
    else:
        # Update static sprites (only enemies need to move if in edit mode)
        solid_tiles = pygame.sprite.Group([tile for tile in tiles_group if tile.tile_type in ['ground', 'brick', 'question', 'water']])
        enemies_group.update(solid_tiles)

    # Draw everything
    window.fill(themes[current_theme]['background'])

    # Draw grid
    for x in range(0, WINDOW_WIDTH, GRID_SIZE):
        pygame.draw.line(window, GRAY, (x, 0), (x, WINDOW_HEIGHT))
    for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
        pygame.draw.line(window, GRAY, (0, y), (WINDOW_WIDTH, y))

    # Draw all sprites
    all_sprites.draw(window)

    # Draw HUD background
    pygame.draw.rect(window, DARK_GRAY, HUD_RECT)

    # Draw tile selection icons
    for tile_type, rect in button_positions.items():
        window.blit(tile_icons[tile_type], rect.topleft)
        if tile_type == selected_tile_type:
            pygame.draw.rect(window, GREEN, rect, 3)
        else:
            pygame.draw.rect(window, BLACK, rect, 1)

    # Draw Theme selection buttons
    for theme_name, rect in theme_buttons.items():
        pygame.draw.rect(window, BLACK, rect, 2)
        theme_text = FONT.render(theme_name, True, BLACK)
        text_rect = theme_text.get_rect(center=rect.center)
        window.blit(theme_text, text_rect)

    # Draw Save, Load, Load Construct, Playtest, Settings, and Quit buttons
    for key, rect in buttons.items():
        pygame.draw.rect(window, BLACK, rect, 2)
        if key == "save":
            text = "Save"
        elif key == "load":
            text = "Load"
        elif key == "load_construct":
            text = "Load Construct"
        elif key == "playtest":
            text = "Playtest"
        elif key == "settings":
            text = "Settings"
        elif key == "quit":
            text = "Quit"
        button_text = FONT.render(text, True, BLACK)
        text_rect = button_text.get_rect(center=rect.center)
        window.blit(button_text, text_rect)

    # Draw FPS counter
    fps = int(game_clock.get_fps())
    fps_text = FONT.render(f"FPS: {fps}", True, YELLOW)
    window.blit(fps_text, (WINDOW_WIDTH - 100, 10))

    if playtest_mode:
        # Display playtest information
        info_text = FONT.render(f"Coins Collected: {player.coins_collected}", True, YELLOW)
        window.blit(info_text, (WINDOW_WIDTH - 200, WINDOW_HEIGHT + 10))
        if player.rect.bottom >= WINDOW_HEIGHT and player.velocity.y == 0:
            # Check if player reached the end (for simplicity, end is at right edge)
            if player.rect.right >= WINDOW_WIDTH - GRID_SIZE:
                success_text = FONT.render("Level Completed!", True, GREEN)
                window.blit(success_text, (WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT // 2))
                pygame.display.update()
                pygame.time.delay(2000)
                playtest_reset()
    else:
        # Display edit mode information
        edit_text = FONT.render("Edit Mode - Place Tiles: Left Click | Remove: Right Click", True, WHITE)
        window.blit(edit_text, (10, WINDOW_HEIGHT + 70))

    # Update display
    pygame.display.update()
    game_clock.tick(60)

pygame.quit()
