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

WIDTH, HEIGHT = 900, 640
FPS = 60

BG_COLOR = (12, 14, 22)
PANEL_COLOR = (22, 26, 36)
WHITE = (240, 244, 248)
MUTED = (170, 178, 186)
ACCENT = (0, 200, 255)
ACCENT_DARK = (0, 140, 200)
RED = (230, 80, 60)

# --- window & layout constants ---
BOARD_PAD = 24
CELL_MARGIN = 8
TOP_HUD = 90
CARD_ASPECT = 5 / 7
CARD_MIN_W, CARD_MIN_H = 40, 48
CARD_MAX_W, CARD_MAX_H = 220, 320

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
    path = os.path.join(AST_FOLDER, "font.ttf")
    try:
        return pygame.font.Font(path, size)
    except Exception:
        return pygame.font.SysFont(None, size)

# -----------------------------
# Assets
# -----------------------------
back_raw = load_image(os.path.join(IMG_FOLDER, "back.png"))
face_raws = [load_image(os.path.join(IMG_FOLDER, f"{i}.png")) for i in range(1, 33)]

snd_flip = load_sound("flip.wav")
snd_match = load_sound("match.wav")
snd_mismatch = load_sound("mismatch.wav")
snd_win = load_sound("win.wav")
snd_button = load_sound("button.wav")

try:
    pygame.mixer.music.load(os.path.join(AST_FOLDER, "bg_music.mp3"))
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)
except Exception as e:
    print(f"[warn] No/invalid bg music -> {e}")

FONT_LG = load_font(56)
FONT_MD = load_font(36)
FONT_SM = load_font(24)
FONT_XS = load_font(18)

try:
    LOGO = load_image(os.path.join(AST_FOLDER, "logo.png"))
except Exception:
    LOGO = None

# -----------------------------
# High scores
# -----------------------------
def load_scores():
    try:
        if not os.path.exists(AST_FOLDER):
            os.makedirs(AST_FOLDER, exist_ok=True)
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, "r") as f:
                data = json.load(f)
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
# Card class
# -----------------------------
class Card:
    def __init__(self, rect, face_idx, face_img_scaled, back_img_scaled):
        self.rect = rect
        self.face_idx = face_idx
        self.face_img = face_img_scaled
        self.back_img = back_img_scaled
        self.flipped = False
        self.matched = False

    def draw(self, surf):
        if self.matched or self.flipped:
            surf.blit(self.face_img, self.rect)
        else:
            surf.blit(self.back_img, self.rect)
        pygame.draw.rect(surf, (0,0,0), self.rect, 2, border_radius=10)

# -----------------------------
# Layout helpers
# -----------------------------
def compute_grid(num_cards):
    cols = ceil(sqrt(num_cards))
    rows = ceil(num_cards / cols)
    return cols, rows

def compute_card_size(cols, rows, width=WIDTH, height=HEIGHT,
                      padding=BOARD_PAD, cell_margin=CELL_MARGIN,
                      top_hud=TOP_HUD, aspect=CARD_ASPECT):
    board_w = width - 2 * padding
    board_h = height - top_hud - padding

    avail_w = board_w - (cols - 1) * cell_margin
    avail_h = board_h - (rows - 1) * cell_margin

    max_w_by_width = avail_w / cols
    max_h_by_height = avail_h / rows
    max_w_from_h = max_h_by_height * aspect

    card_w = min(max_w_by_width, max_w_from_h)
    card_h = card_w / aspect

    card_w = max(CARD_MIN_W, min(CARD_MAX_W, card_w))
    card_h = max(CARD_MIN_H, min(CARD_MAX_H, card_h))

    return int(card_w), int(card_h)

def get_scaled_images(card_w, card_h, back_raw, face_raws):
    back_img = pygame.transform.smoothscale(back_raw, (card_w, card_h))
    faces = [pygame.transform.smoothscale(img, (card_w, card_h)) for img in face_raws]
    return back_img, faces

def layout_cards(level, back_raw=back_raw, face_raws=face_raws):
    pairs = level
    num_cards = pairs * 2
    cols, rows = compute_grid(num_cards)
    card_w, card_h = compute_card_size(cols, rows)

    # --- Randomly pick 'pairs' images from all 32 ---
    selected_faces = random.sample(face_raws, pairs)
    back_img_scaled, faces_scaled = get_scaled_images(card_w, card_h, back_raw, selected_faces)

    # Create deck indices (0..pairs-1, twice)
    deck = [i for i in range(pairs) for _ in (0,1)]
    random.shuffle(deck)

    board_w = cols * card_w + (cols - 1) * CELL_MARGIN
    board_h = rows * card_h + (rows - 1) * CELL_MARGIN
    start_x = (WIDTH - board_w) // 2
    start_y = TOP_HUD + (HEIGHT - TOP_HUD - board_h) // 2

    cards = []
    for idx_pos, face_idx in enumerate(deck):
        r = idx_pos // cols
        c = idx_pos % cols
        x = start_x + c * (card_w + CELL_MARGIN)
        y = start_y + r * (card_h + CELL_MARGIN)
        rect = pygame.Rect(x, y, card_w, card_h)
        cards.append(Card(rect, face_idx, faces_scaled[face_idx], back_img_scaled))

    return cards, (cols, rows), (card_w, card_h)

# -----------------------------
# Screens
# -----------------------------
def home_screen():
    btn_w, btn_h = 260, 60
    gap = 18
    center_x = WIDTH // 2

    btn_start = make_button(center_x - btn_w//2, 0, btn_w, btn_h)
    btn_scores = make_button(center_x - btn_w//2, 0, btn_w, btn_h)
    btn_quit = make_button(center_x - btn_w//2, 0, btn_w, btn_h)

    while True:
        mx, my = pygame.mouse.get_pos()
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    snd_button.play(); return "start"
                if event.key == pygame.K_h:
                    snd_button.play(); return "scores"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        screen.fill(BG_COLOR)

        # --- Draw Logo ---
        logo_bottom_y = 40
        if LOGO:
            logo_scaled_w = 120
            ratio = LOGO.get_width() / LOGO.get_height() if LOGO.get_height() else 1
            logo_scaled_h = int(logo_scaled_w / ratio)
            logo_img = pygame.transform.smoothscale(LOGO, (logo_scaled_w, logo_scaled_h))
            logo_rect = logo_img.get_rect(center=(WIDTH//2, logo_bottom_y + logo_scaled_h//2))
            screen.blit(logo_img, logo_rect)
            logo_bottom_y += logo_scaled_h + 20

        # --- Title & subtitle ---
        title_rect = draw_text_center("Memory Match", FONT_LG, ACCENT, (WIDTH//2, logo_bottom_y + FONT_LG.get_height()//2))
        subtitle_rect = draw_text_center("32 Levels • Save Best Times", FONT_SM, MUTED, (WIDTH//2, title_rect.bottom + 14))

        # --- Buttons ---
        btn_start_y = subtitle_rect.bottom + 40
        btn_start.y = btn_start_y
        btn_scores.y = btn_start_y + btn_h + gap
        btn_quit.y = btn_start_y + 2*(btn_h + gap)

        for rect, label in [(btn_start, "Start Game"), (btn_scores, "High Scores"), (btn_quit, "Quit")]:
            hover = rect.collidepoint(mx, my)
            draw_button(label, rect, hover)

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

        hover = btn_back.collidepoint(mx, my)
        draw_button("Back", btn_back, hover)

        if click and btn_back.collidepoint(mx, my):
            snd_button.play(); return

        pygame.display.flip()
        clock.tick(FPS)

# -----------------------------
# Game Screen
# -----------------------------
def game_screen(level):
    cards, (cols, rows), (cw, ch) = layout_cards(level)
    flipped = []
    matches = 0
    total_pairs = level
    moves = 0
    start_ts = time.time()
    post_win_ms = 2200

    running = True
    while running:
        dt = clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for card in cards:
                    if card.rect.collidepoint(event.pos) and not card.flipped and not card.matched:
                        if len(flipped) < 2:
                            snd_flip.play()
                            card.flipped = True
                            flipped.append(card)
                        break

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

        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, PANEL_COLOR, (0, 0, WIDTH, TOP_HUD))
        elapsed = int(time.time() - start_ts)
        best = scores.get(str(level))
        draw_text_left(f"Level {level}", FONT_MD, WHITE, (BOARD_PAD, 26))
        draw_text_left(f"Moves: {moves}", FONT_MD, WHITE, (BOARD_PAD + 220, 26))
        draw_text_left(f"Time: {elapsed}s", FONT_MD, WHITE, (BOARD_PAD + 420, 26))
        if best is not None:
            draw_text_left(f"Best: {best}s", FONT_MD, ACCENT, (BOARD_PAD + 620, 26))
        else:
            draw_text_left("Best: —", FONT_MD, MUTED, (BOARD_PAD + 620, 26))
        draw_text_left("ESC: Home", FONT_SM, MUTED, (WIDTH - 130, 10))

        for c in cards:
            c.draw(screen)

        if matches == total_pairs:
            snd_win.play()
            elapsed = int(time.time() - start_ts)
            prev = scores.get(str(level))
            if prev is None or elapsed < prev:
                scores[str(level)] = elapsed
                save_scores(scores)
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,150))
            screen.blit(overlay, (0,0))
            draw_text_center(f"Level {level} Complete!", FONT_LG, ACCENT, (WIDTH//2, HEIGHT//2 - 20))
            draw_text_center(f"Time {elapsed}s • Moves {moves}", FONT_MD, WHITE, (WIDTH//2, HEIGHT//2 + 40))
            pygame.display.flip()
            pygame.time.delay(post_win_ms)
            return True

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
            for lv in range(1, 33):
                proceed = game_screen(lv)
                if not proceed:
                    break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit()
