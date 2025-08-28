import pygame
import random
import sys
import os

# --------------------------
# Init
# --------------------------
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1000, 700
FPS = 60
CARD_SIZE = (100, 140)
GRID_COLS = 8
GRID_ROWS = 8
MARGIN = 10

# Colors
BG_COLOR = (12, 14, 22)
WHITE = (255, 255, 255)
ACCENT = (0, 200, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match Game")

clock = pygame.time.Clock()

# --------------------------
# Load Assets
# --------------------------
def load_image(path, size=None):
    img = pygame.image.load(path).convert_alpha()
    if size:
        img = pygame.transform.smoothscale(img, size)
    return img

def load_sound(path):
    return pygame.mixer.Sound(path)

# Folders
IMG_FOLDER = "images"
SND_FOLDER = "sounds"
AST_FOLDER = "assets"

# Images
back_img = load_image(os.path.join(IMG_FOLDER, "back.png"), CARD_SIZE)
card_faces = [load_image(os.path.join(IMG_FOLDER, f"{i}.png"), CARD_SIZE) for i in range(1, 33)]

# Sounds
snd_flip = load_sound(os.path.join(SND_FOLDER, "flip.wav"))
snd_match = load_sound(os.path.join(SND_FOLDER, "match.wav"))
snd_mismatch = load_sound(os.path.join(SND_FOLDER, "mismatch.wav"))
snd_win = load_sound(os.path.join(SND_FOLDER, "win.wav"))
snd_button = load_sound(os.path.join(SND_FOLDER, "button.wav"))

# Font
font = pygame.font.Font(os.path.join(AST_FOLDER, "font.ttf"), 40)

# Music
try:
    pygame.mixer.music.load(os.path.join(AST_FOLDER, "bg_music.mp3"))
    pygame.mixer.music.play(-1)  # loop forever
    pygame.mixer.music.set_volume(0.2)
except:
    print("Background music not found")

# --------------------------
# Game Objects
# --------------------------
class Card:
    def __init__(self, x, y, face):
        self.rect = pygame.Rect(x, y, CARD_SIZE[0], CARD_SIZE[1])
        self.face = face
        self.flipped = False
        self.matched = False

    def draw(self, surf):
        if self.matched or self.flipped:
            surf.blit(self.face, self.rect)
        else:
            surf.blit(back_img, self.rect)

# --------------------------
# Build Card Grid
# --------------------------
def create_cards():
    # Take 32 faces -> duplicate -> shuffle
    faces = card_faces * 2
    random.shuffle(faces)

    cards = []
    start_x = (WIDTH - (GRID_COLS * (CARD_SIZE[0] + MARGIN))) // 2
    start_y = (HEIGHT - (GRID_ROWS * (CARD_SIZE[1] + MARGIN))) // 2

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = start_x + col * (CARD_SIZE[0] + MARGIN)
            y = start_y + row * (CARD_SIZE[1] + MARGIN)
            face = faces.pop()
            cards.append(Card(x, y, face))
    return cards

# --------------------------
# Screens
# --------------------------
def draw_text(text, size, color, center):
    fnt = pygame.font.Font(os.path.join(AST_FOLDER, "font.ttf"), size)
    txt = fnt.render(text, True, color)
    rect = txt.get_rect(center=center)
    screen.blit(txt, rect)

def home_screen():
    running = True
    while running:
        screen.fill(BG_COLOR)
        draw_text("Memory Match Game", 64, ACCENT, (WIDTH // 2, HEIGHT // 3))
        draw_text("Press SPACE to Start", 40, WHITE, (WIDTH // 2, HEIGHT // 2))
        draw_text("Press ESC to Quit", 30, WHITE, (WIDTH // 2, HEIGHT // 2 + 60))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    snd_button.play()
                    running = False
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        pygame.display.flip()
        clock.tick(FPS)

def game_screen():
    cards = create_cards()
    flipped_cards = []
    matches_found = 0
    total_pairs = len(cards) // 2

    running = True
    while running:
        screen.fill(BG_COLOR)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for card in cards:
                    if card.rect.collidepoint(event.pos) and not card.flipped and not card.matched:
                        snd_flip.play()
                        card.flipped = True
                        flipped_cards.append(card)

        # Check matches
        if len(flipped_cards) == 2:
            pygame.time.delay(400)  # small pause
            if flipped_cards[0].face == flipped_cards[1].face:
                snd_match.play()
                flipped_cards[0].matched = True
                flipped_cards[1].matched = True
                matches_found += 1
            else:
                snd_mismatch.play()
                flipped_cards[0].flipped = False
                flipped_cards[1].flipped = False
            flipped_cards = []

        # Draw cards
        for card in cards:
            card.draw(screen)

        # Check win
        if matches_found == total_pairs:
            snd_win.play()
            draw_text("You Win!", 70, ACCENT, (WIDTH // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(3000)
            return  # back to home

        pygame.display.flip()
        clock.tick(FPS)

# --------------------------
# Main Loop
# --------------------------
while True:
    home_screen()
    game_screen()
