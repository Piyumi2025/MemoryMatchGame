import pygame
import random
import sys
import os
import json
import time
from math import ceil, sqrt

# -----------------------------
# Basic setup & constants
# -----------------------------
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 1100, 800
FPS = 60

BG_COLOR = (12, 14, 22)
PANEL_COLOR = (22, 26, 36)
WHITE = (240, 244, 248)
MUTED = (170, 178, 186)
ACCENT = (0, 200, 255)
ACCENT_DARK = (0, 140, 200)
RED = (230, 80, 80)

BOARD_PAD = 30        # padding around the board area
CELL_MARGIN = 10      # space between cards
CARD_ASPECT = 5/7     # width:height ratio for scaling

# Folders
IMG_FOLDER = "images"
SND_FOLDER = "sounds"
AST_FOLDER = "assets"
SCORES_FILE = os.path.join(AST_FOLDER, "high_scores.json")

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match — 32 Levels")
clock = pygame.time.Clock()

# -----------------------------
# Helpers: safe asset loading
# -----------------------------
def load_image(path):
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"[warn] Could not load image: {path} -> {e}")
        # Fallback: simple placeholder surface
        surf = pygame.Surface((100, 140), pygame.SRCALPHA)
        surf.fill((60, 60, 80))
        pygame.draw.line(surf, (120, 120, 160), (0,0), (100,140), 3)
        pygame.draw.line(surf, (120, 120, 160), (100,0), (0,140), 3)
        return surf

def load_sound(name):
    path = os.path.join(SND_FOLDER, name)
    try:
        return pygame.mixer.Sound(path)
    except Exception as e:
        print(f"[warn] Could not load sound: {path} -> {e}")
        class _NullSound:
            def play(self): pass
        return _NullSound()

def load_font(size):
    # Try assets/font.ttf, otherwise default
    path = os.path.join(AST_FOLDER, "font.ttf")
    try:
        return pygame.font.Font(path, size)
    except Exception:
        return pygame.font.SysFont(None, size)

# -----------------------------
# Assets
# -----------------------------
# Images
back_raw = load_image(os.path.join(IMG_FOLDER, "back.png"))
face_raws = [load_image(os.path.join(IMG_FOLDER, f"{i}.png")) for i in range(1, 33)]

# Sounds (optional)
snd_flip = load_sound("flip.wav")
snd_match = load_sound("match.wav")
snd_mismatch = load_sound("mismatch.wav")
snd_win = load_sound("win.wav")
snd_button = load_sound("button.wav")

# Music (optional)
try:
    pygame.mixer.music.load(os.path.join(AST_FOLDER, "bg_music.mp3"))
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)
except Exception as e:
    print(f"[warn] No/invalid bg music -> {e}")

# Fonts
FONT_LG = load_font(56)
FONT_MD = load_font(36)
FONT_SM = load_font(24)
FONT_XS = load_font(18)

# Optional logo
try:
    LOGO = load_image(os.path.join(AST_FOLDER, "logo.png"))
except Exception:
    LOGO = None

# -----------------------------
# High scores (per-level best time in seconds)
# -----------------------------
def load_scores():
    try:
        if not os.path.exists(AST_FOLDER):
            os.makedirs(AST_FOLDER, exist_ok=True)
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, "r") as f:
                data = json.load(f)
                # ensure keys are strings "1".."32"
                return {str(k): int(v) for k, v in data.items()}
    except Exception as e:
        print(f"[warn] load_scores: {e}")
    return {}

def save_scores(scores):
    try:
        with open(SCORES_FILE, "w") as f:
            json.dump(scores, f, indent=2)
    except Exception as e:
        print(f"[warn] save_scores: {e}")

scores = load_scores()

# -----------------------------
# UI helpers
# -----------------------------
def draw_text_center(text, font, color, center, surface=screen):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=center)
    surface.blit(surf, rect)
    return rect

def draw_text_left(text, font, color, topleft, surface=screen):
    surf = font.render(text, True, color)
    rect = surf.get_rect(topleft=topleft)
    surface.blit(surf, rect)
    return rect

def draw_button(label, rect, hover, font=FONT_MD):
    pygame.draw.rect(screen, ACCENT if hover else ACCENT_DARK, rect, border_radius=16)
    draw_text_center(label, font, (10, 14, 18), rect.center)

def make_button(x, y, w, h):
    return pygame.Rect(int(x), int(y), int(w), int(h))

# -----------------------------
# Card + Grid
# -----------------------------
class Card:
    def __init__(self, rect, face_idx, face_img_scaled, back_img_scaled):
        self.rect = rect
        self.face_idx = face_idx   # identify matches by index
        self.face_img = face_img_scaled
        self.back_img = back_img_scaled
        self.flipped = False
        self.matched = False

    def draw(self, surf):
        if self.matched or self.flipped:
            surf.blit(self.face_img, self.rect)
        else:
            surf.blit(self.back_img, self.rect)
        # subtle border
        pygame.draw.rect(surf, (0,0,0), self.rect, 2, border_radius=10)

def compute_grid(num_cards):
    # Try to make it as square as possible
    cols = ceil(sqrt(num_cards))
    rows = ceil(num_cards / cols)
    return cols, rows

def compute_card_size(cols, rows):
    # Fit within the board area considering margins
    # Board area = screen with top HUD strip
    top_hud = 90
    board_w = WIDTH - 2*BOARD_PAD
    board_h = HEIGHT - top_hud - BOARD_PAD

    avail_w = board_w - (cols - 1) * CELL_MARGIN
    avail_h = board_h - (rows - 1) * CELL_MARGIN

    # Based on aspect ratio (w:h = CARD_ASPECT)
    # So h = w / CARD_ASPECT
    max_w_by_width = avail_w / cols
    max_h_by_height = avail_h / rows

    # Convert height constraint into width via aspect
    max_w_from_h = max_h_by_height * CARD_ASPECT

    card_w = min(max_w_by_width, max_w_from_h)
    card_h = card_w / CARD_ASPECT

    # Cap sizes to something reasonable
    card_w = max(40, min(180, card_w))
    card_h = max(56, min(260, card_h))
    return int(card_w), int(card_h), top_hud

def layout_cards(level):
    # Level N => N pairs => N*2 cards, use faces 1..N
    pairs = level
    num_cards = pairs * 2
    cols, rows = compute_grid(num_cards)
    card_w, card_h, top_hud = compute_card_size(cols, rows)

    # Scale images to card size
    back_img = pygame.transform.smoothscale(back_raw, (card_w, card_h))
    faces_scaled = [
        pygame.transform.smoothscale(face_raws[i], (card_w, card_h)) for i in range(pairs)
    ]

    # Prepare shuffled deck as indices (two of each)
    deck = []
    for idx in range(pairs):
        deck.append(idx)
        deck.append(idx)
    random.shuffle(deck)

    board_w = cols * card_w + (cols - 1) * CELL_MARGIN
    board_h = rows * card_h + (rows - 1) * CELL_MARGIN
    start_x = (WIDTH - board_w) // 2
    start_y = top_hud + (HEIGHT - top_hud - board_h) // 2

    cards = []
    i = 0
    for r in range(rows):
        for c in range(cols):
            if i >= len(deck): break
            x = start_x + c * (card_w + CELL_MARGIN)
            y = start_y + r * (card_h + CELL_MARGIN)
            idx = deck[i]
            rect = pygame.Rect(x, y, card_w, card_h)
            cards.append(Card(rect, idx, faces_scaled[idx], back_img))
            i += 1

    return cards, (cols, rows), (card_w, card_h), top_hud

# -----------------------------
# Screens: Home / High Scores / Game
# -----------------------------
def home_screen():
    # Buttons
    btn_w, btn_h = 260, 60
    gap = 18
    center_x = WIDTH // 2
    top_y = HEIGHT // 2 - btn_h - gap

    btn_start = make_button(center_x - btn_w//2, top_y, btn_w, btn_h)
    btn_scores = make_button(center_x - btn_w//2, top_y + btn_h + gap, btn_w, btn_h)
    btn_quit = make_button(center_x - btn_w//2, top_y + 2*(btn_h + gap), btn_w, btn_h)

    while True:
        mx, my = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    snd_button.play()
                    return "start"
                if event.key == pygame.K_h:
                    snd_button.play()
                    return "scores"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        screen.fill(BG_COLOR)

        # Title/logo
        title_rect = draw_text_center("Memory Match", FONT_LG, ACCENT, (WIDTH//2, 120))
        draw_text_center("32 Levels • Save Best Times", FONT_SM, MUTED, (WIDTH//2, title_rect.bottom + 26))

        if LOGO:
            logo_scaled_w = 120
            ratio = LOGO.get_width() / LOGO.get_height() if LOGO.get_height() else 1
            logo_scaled_h = int(logo_scaled_w / ratio)
            logo = pygame.transform.smoothscale(LOGO, (logo_scaled_w, logo_scaled_h))
            logo_rect = logo.get_rect(center=(WIDTH//2, title_rect.top - logo_scaled_h//2 - 10))
            screen.blit(logo, logo_rect)

        # Buttons
        for rect, label in [(btn_start, "Start Game"),
                            (btn_scores, "High Scores"),
                            (btn_quit, "Quit")]:
            hover = rect.collidepoint(mx, my)
            draw_button(label, rect, hover)

        # Quick best for Level 1
        best1 = scores.get("1", None)
        tip = "Tip: Press H for Scores" if best1 is None else f"Best Level 1: {best1}s"
        draw_text_center(tip, FONT_XS, MUTED, (WIDTH//2, btn_quit.bottom + 30))

        if click:
            if btn_start.collidepoint(mx, my):
                snd_button.play(); return "start"
            if btn_scores.collidepoint(mx, my):
                snd_button.play(); return "scores"
            if btn_quit.collidepoint(mx, my):
                snd_button.play(); pygame.quit(); sys.exit()

        pygame.display.flip()
        clock.tick(FPS)

def scores_screen():
    # Back button
    btn_back = make_button(BOARD_PAD, HEIGHT - BOARD_PAD - 48, 160, 48)
    scroll = 0
    items_per_col = 16
    col_w = 300
    cols = 2
    start_x = (WIDTH - (cols * col_w)) // 2

    while True:
        mx, my = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                snd_button.play(); return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        screen.fill(BG_COLOR)
        draw_text_center("High Scores", FONT_LG, ACCENT, (WIDTH//2, 90))

        # Grid of scores
        # Levels 1..32
        for i in range(32):
            level = i + 1
            col = i // items_per_col
            row = i % items_per_col
            x = start_x + col * col_w
            y = 160 + row * 30
            label = f"Level {level:>2}:"
            best = scores.get(str(level))
            value = f"{best}s" if best is not None else "—"
            draw_text_left(label, FONT_SM, WHITE, (x, y))
            draw_text_left(value, FONT_SM, ACCENT if best is not None else MUTED, (x + 150, y))

        # Back
        hover = btn_back.collidepoint(mx, my)
        draw_button("Back", btn_back, hover)

        if click and btn_back.collidepoint(mx, my):
            snd_button.play(); return

        pygame.display.flip()
        clock.tick(FPS)

def game_screen(level):
    cards, (cols, rows), (cw, ch), top_hud = layout_cards(level)
    flipped = []
    matches = 0
    total_pairs = level
    moves = 0
    start_ts = time.time()

    # Pause after win
    post_win_ms = 2200

    running = True
    while running:
        dt = clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                # Return to home
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Flip logic
                for card in cards:
                    if card.rect.collidepoint(event.pos) and not card.flipped and not card.matched:
                        if len(flipped) < 2:
                            snd_flip.play()
                            card.flipped = True
                            flipped.append(card)
                        break

        # Check pair
        if len(flipped) == 2:
            pygame.display.flip()
            pygame.time.delay(350)
            moves += 1
            a, b = flipped
            if a.face_idx == b.face_idx:
                snd_match.play()
                a.matched = b.matched = True
                matches += 1
            else:
                snd_mismatch.play()
                a.flipped = b.flipped = False
            flipped.clear()

        # Draw background and HUD panel
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, PANEL_COLOR, (0, 0, WIDTH, top_hud))

        # HUD
        elapsed = int(time.time() - start_ts)
        best = scores.get(str(level))
        draw_text_left(f"Level {level}", FONT_MD, WHITE, (BOARD_PAD, 26))
        draw_text_left(f"Moves: {moves}", FONT_MD, WHITE, (BOARD_PAD + 220, 26))
        draw_text_left(f"Time: {elapsed}s", FONT_MD, WHITE, (BOARD_PAD + 420, 26))
        if best is not None:
            draw_text_left(f"Best: {best}s", FONT_MD, ACCENT, (BOARD_PAD + 620, 26))
        else:
            draw_text_left("Best: —", FONT_MD, MUTED, (BOARD_PAD + 620, 26))
        draw_text_left("ESC: Home", FONT_SM, MUTED, (WIDTH - 150, 30))

        # Draw cards
        for c in cards:
            c.draw(screen)

        # Win condition
        if matches == total_pairs:
            snd_win.play()
            elapsed = int(time.time() - start_ts)
            # Save best if improved
            prev = scores.get(str(level))
            if prev is None or elapsed < prev:
                scores[str(level)] = elapsed
                save_scores(scores)

            # Overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            draw_text_center(f"Level {level} Complete!", FONT_LG, ACCENT, (WIDTH//2, HEIGHT//2 - 20))
            draw_text_center(f"Time {elapsed}s • Moves {moves}", FONT_MD, WHITE, (WIDTH//2, HEIGHT//2 + 40))
            pygame.display.flip()
            pygame.time.delay(post_win_ms)
            return True  # proceed to next level

        pygame.display.flip()

# -----------------------------
# Main loop
# -----------------------------
def main():
    while True:
        action = home_screen()
        if action == "scores":
            scores_screen()
            continue
        if action == "start":
            # Play through levels 1..32, allow exit back to Home
            for lv in range(1, 33):
                proceed = game_screen(lv)
                if not proceed:
                    break
            # After finishing or exiting, loop back to Home

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()
