import pygame
import asyncio
import platform
import random
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Advanced Memory Match Game")

# Colors
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
BLACK = (0, 0, 0)
BLUE = (50, 50, 200)

# Game states
MENU, PLAYING, GAME_OVER = 0, 1, 2
game_state = MENU

# Card settings
CARD_WIDTH, CARD_HEIGHT = 100, 100
CARD_MARGIN = 10
cards = []
card_images = []
card_back = None
flipped_cards = []
matched_pairs = []

# Game variables
difficulty = 4  # Default: 4x4 grid
theme = "Image"  # Default theme
moves = 0
start_time = 0
score = 0
high_scores = {4: float('inf'), 6: float('inf'), 8: float('inf')}
flip_timers = {}
particles = []
font = pygame.font.SysFont("Arial", 30)
small_font = pygame.font.SysFont("Arial", 24)

# Load assets
try:
    card_back = pygame.image.load("images/back.png")
    card_back = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))
except FileNotFoundError:
    print("Back image not found; using gray rectangle.")
    card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    card_back.fill(GRAY)

try:
    flip_sound = pygame.mixer.Sound("sounds/flip.mp3")
    match_sound = pygame.mixer.Sound("sounds/match.mp3")
    win_sound = pygame.mixer.Sound("sounds/victory.mp3")
except FileNotFoundError:
    print("Sound files not found; running without audio.")
    flip_sound = match_sound = win_sound = None

# Button class
class Button:
    def __init__(self, x, y, width, height, text, action):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action

# Card class
class Card:
    def __init__(self, x, y, image_index):
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.image_index = image_index
        self.flipped = False
        self.matched = False
        self.flip_progress = 0
        self.hover = False

# Particle class
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        self.lifetime = random.randint(30, 60)

# Draw menu
def draw_menu():
    screen.fill(BLACK)
    title = font.render("Memory Match Game", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    
    buttons = [
        Button(WIDTH // 2 - 100, 200, 200, 50, "Easy (4x4)", lambda: set_difficulty(4)),
        Button(WIDTH // 2 - 100, 270, 200, 50, "Medium (6x6)", lambda: set_difficulty(6)),
        Button(WIDTH // 2 - 100, 340, 200, 50, "Hard (8x8)", lambda: set_difficulty(8)),
        Button(WIDTH // 2 - 100, 410, 200, 50, f"Theme: {theme}", toggle_theme)
    ]
    
    for button in buttons:
        pygame.draw.rect(screen, BLUE, button.rect)
        text = small_font.render(button.text, True, WHITE)
        screen.blit(text, (button.rect.x + 50, button.rect.y + 15))
    
    return buttons

# Set difficulty
def set_difficulty(level):
    global difficulty
    difficulty = level
    setup()

# Toggle theme
def toggle_theme():
    global theme
    theme = "Color" if theme == "Image" else "Image"

# Initialize game state
def setup():
    global cards, flipped_cards, matched_pairs, game_state, moves, start_time, score, flip_timers, card_images, theme
    cards = []
    flipped_cards = []
    matched_pairs = []
    flip_timers = {}
    moves = 0
    score = 0
    start_time = pygame.time.get_ticks()
    game_state = PLAYING

    card_images.clear()
    if theme == "Image":
        try:
            for i in range(1, 33):
                img = pygame.image.load(f"images/image_{i}.png")
                img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
                card_images.append(img)
        except FileNotFoundError:
            print("Images not found; falling back to colors.")
            theme = "Color"
    if theme == "Color":
        for i in range(32):
            img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
            img.fill((random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)))
            card_images.append(img)

    num_pairs = (difficulty * difficulty) // 2
    selected_images = card_images[:num_pairs]
    selected_images.extend(selected_images)
    random.shuffle(selected_images)

    rows = cols = difficulty
    for row in range(rows):
        for col in range(cols):
            x = col * (CARD_WIDTH + CARD_MARGIN) + (WIDTH - cols * (CARD_WIDTH + CARD_MARGIN)) // 2
            y = row * (CARD_HEIGHT + CARD_MARGIN) + 100
            card = Card(x, y, row * cols + col)
            cards.append(card)

# Calculate score
def calculate_score():
    elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
    return max(10000 - elapsed_time * 10 - moves * 50, 0)

# Update game state
def update_loop():
    global flipped_cards, matched_pairs, game_state, moves, score, particles, difficulty
    
    if game_state == MENU:
        buttons = draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                for button in buttons:
                    if button.rect.collidepoint(pos):
                        button.action()
                        break
        pygame.display.flip()
        return True

    if game_state == PLAYING:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and len(flipped_cards) < 2:
                pos = event.pos
                for card in cards:
                    if card.rect.collidepoint(pos) and not card.flipped and not card.matched:
                        card.flipped = True
                        card.flip_progress = 0
                        flip_timers[id(card)] = pygame.time.get_ticks()
                        flipped_cards.append(card)
                        moves += 1
                        if flip_sound:
                            flip_sound.play()
                        break

        mouse_pos = pygame.mouse.get_pos()
        for card in cards:
            if card.rect.collidepoint(mouse_pos) and not card.flipped and not card.matched:
                card.hover = True
            else:
                card.hover = False

        current_time = pygame.time.get_ticks()
        for card in cards:
            if id(card) in flip_timers:
                progress = (current_time - flip_timers[id(card)]) / 500
                card.flip_progress = min(progress, 1)
                if card.flip_progress >= 1:
                    del flip_timers[id(card)]

        if len(flipped_cards) == 2 and all(card.flip_progress >= 1 for card in flipped_cards):
            if card_images[flipped_cards[0].image_index] == card_images[flipped_cards[1].image_index]:
                flipped_cards[0].matched = flipped_cards[1].matched = True
                matched_pairs.append(flipped_cards)
                if match_sound:
                    match_sound.play()
            else:
                pygame.time.wait(1000)
                for card in flipped_cards:
                    card.flipped = False
                    card.flip_progress = 0
                    flip_timers[id(card)] = pygame.time.get_ticks()
                if flip_sound:
                    flip_sound.play()
            flipped_cards = []

        if len(matched_pairs) == (difficulty * difficulty) // 2:
            score = calculate_score()
            high_scores[difficulty] = min(high_scores[difficulty], score)
            game_state = GAME_OVER
            if win_sound:
                win_sound.play()
            particles.clear()
            for _ in range(100):
                particles.append(Particle(WIDTH // 2, HEIGHT // 2))

    screen.fill(BLACK)
    for card in cards:
        if card.matched:
            screen.blit(card_images[card.image_index], (card.rect.x, card.rect.y))
        else:
            scale = abs(math.cos(card.flip_progress * math.pi))
            if card.flip_progress < 0.5:
                img = pygame.transform.scale(card_back, (int(CARD_WIDTH * scale), CARD_HEIGHT))
            else:
                img = pygame.transform.scale(card_images[card.image_index], (int(CARD_WIDTH * scale), CARD_HEIGHT))
            x_offset = (CARD_WIDTH - img.get_width()) // 2
            if card.hover and not card.flipped:
                pygame.draw.rect(screen, (255, 255, 0), card.rect, 2)
                img = pygame.transform.scale(img, (int(CARD_WIDTH * 1.05), int(CARD_HEIGHT * 1.05)))
                x_offset = (CARD_WIDTH - img.get_width()) // 2
            screen.blit(img, (card.rect.x + x_offset, card.rect.y))

    if game_state == PLAYING or game_state == GAME_OVER:
        time_text = font.render(f"Time: {(pygame.time.get_ticks() - start_time) // 1000}s", True, WHITE)
        moves_text = font.render(f"Moves: {moves}", True, WHITE)
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(time_text, (10, 10))
        screen.blit(moves_text, (10, 40))
        screen.blit(score_text, (10, 70))

    if game_state == GAME_OVER:
        new_particles = []
        for p in particles:
            p.x += p.vx
            p.y += p.vy
            p.lifetime -= 1
            if p.lifetime > 0:
                new_particles.append(p)
                pygame.draw.circle(screen, p.color, (int(p.x), int(p.y)), 3)
        particles = new_particles

        win_text = font.render("You Win! Press R to Restart", True, WHITE)
        high_score_text = font.render(f"High Score ({difficulty}x{difficulty}): {high_scores[difficulty]}", True, WHITE)
        screen.blit(win_text, (WIDTH // 2 - 150, HEIGHT // 2))
        screen.blit(high_score_text, (WIDTH // 2 - 150, HEIGHT // 2 + 30))
        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            if difficulty == 4:
                difficulty = 6
            elif difficulty == 6:
                difficulty = 8
            else:
                difficulty = 4
            setup()

    pygame.display.flip()
    return True

# Main game loop
async def main():
    setup()
    while True:
        if not update_loop():
            break
        await asyncio.sleep(1.0 / 60)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())