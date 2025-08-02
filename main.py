import pygame
import asyncio
import platform
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match Game")

# Colors
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)

# Card settings
CARD_WIDTH, CARD_HEIGHT = 100, 100
CARD_ROWS, CARD_COLS = 4, 4
CARD_MARGIN = 10
cards = []
card_images = []
card_back = None
flipped_cards = []
matched_pairs = []
game_over = False

# Timer and font
start_time = 0
font = pygame.font.SysFont("Arial", 30)

# Load assets
try:
    card_back = pygame.image.load("images/card_back.png")
    card_back = pygame.transform.scale(card_back, (CARD_WIDTH, CARD_HEIGHT))
    for i in range(1, 9):  # 8 unique pairs for 16 cards
        img = pygame.image.load(f"images/card_{i}.png")
        img = pygame.transform.scale(img, (CARD_WIDTH, CARD_HEIGHT))
        card_images.extend([img, img])  # Add each image twice for pairs
except FileNotFoundError:
    print("Image files not found; using colored rectangles.")
    card_back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    card_back.fill(GRAY)
    for i in range(8):
        img = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
        img.fill((random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)))
        card_images.extend([img, img])

# Load sound effects
try:
    flip_sound = pygame.mixer.Sound("sounds/flip.wav")
    match_sound = pygame.mixer.Sound("sounds/match.wav")
    win_sound = pygame.mixer.Sound("sounds/win.wav")
except FileNotFoundError:
    print("Sound files not found; running without audio.")
    flip_sound = match_sound = win_sound = None

# Card class
class Card:
    def __init__(self, x, y, image_index):
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.image_index = image_index
        self.flipped = False
        self.matched = False

# Initialize game state
def setup():
    global cards, flipped_cards, matched_pairs, game_over, start_time
    cards = []
    flipped_cards = []
    matched_pairs = []
    game_over = False
    start_time = pygame.time.get_ticks()

    # Shuffle card images
    random.shuffle(card_images)

    # Create card grid
    for row in range(CARD_ROWS):
        for col in range(CARD_COLS):
            x = col * (CARD_WIDTH + CARD_MARGIN) + (WIDTH - CARD_COLS * (CARD_WIDTH + CARD_MARGIN)) // 2
            y = row * (CARD_HEIGHT + CARD_MARGIN) + 50
            card = Card(x, y, row * CARD_COLS + col)
            cards.append(card)

# Update game state
def update_loop():
    global flipped_cards, matched_pairs, game_over

    if game_over:
        return True

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and len(flipped_cards) < 2 and not game_over:
            pos = event.pos
            for card in cards:
                if card.rect.collidepoint(pos) and not card.flipped and not card.matched:
                    card.flipped = True
                    flipped_cards.append(card)
                    if flip_sound:
                        flip_sound.play()
                    break

    # Check for matches
    if len(flipped_cards) == 2:
        if card_images[flipped_cards[0].image_index] == card_images[flipped_cards[1].image_index]:
            flipped_cards[0].matched = flipped_cards[1].matched = True
            matched_pairs.append(flipped_cards)
            if match_sound:
                match_sound.play()
        else:
            pygame.time.wait(1000)  # Show cards briefly before flipping back
            flipped_cards[0].flipped = flipped_cards[1].flipped = False
        flipped_cards = []

    # Check for game over
    if len(matched_pairs) == len(card_images) // 2:
        game_over = True
        if win_sound:
            win_sound.play()

    # Draw everything
    screen.fill((0, 0, 0))  # Clear screen
    for card in cards:
        if card.matched or card.flipped:
            screen.blit(card_images[card.image_index], (card.rect.x, card.rect.y))
        else:
            screen.blit(card_back, (card.rect.x, card.rect.y))
    time_text = font.render(f"Time: {(pygame.time.get_ticks() - start_time) // 1000}s", True, WHITE)
    screen.blit(time_text, (10, 10))
    if game_over:
        win_text = font.render("You Win! Press R to Restart", True, WHITE)
        screen.blit(win_text, (WIDTH // 2 - 150, HEIGHT // 2))
    pygame.display.flip()

    # Handle restart
    keys = pygame.key.get_pressed()
    if keys[pygame.K_r] and game_over:
        setup()

    return True

# Main game loop for Pyodide compatibility
async def main():
    setup()  # Initialize game state
    while True:
        if not update_loop():
            break
        await asyncio.sleep(1.0 / 60)  # 60 FPS

# Run the game
if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())