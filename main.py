import pygame
import random
import sys
import os
import json
import time
import datetime
from math import ceil, sqrt

# =============================
# Boot & constants
# =============================
pygame.init()
try:
    pygame.mixer.init()
except Exception:
    pass

WIDTH, HEIGHT = 900, 640
FPS = 60

# Colors
BG_COLOR = (12, 14, 22)
PANEL_COLOR = (22, 26, 36)
WHITE = (240, 244, 248)
MUTED = (170, 178, 186)
ACCENT = (0, 200, 255)
ACCENT_DARK = (0, 140, 200)
GOLD = (255, 215, 0)
RED = (230, 80, 80)

# Layout
BOARD_PAD = 24
CELL_MARGIN = 9
TOP_HUD = 96
CARD_ASPECT = 5/7
CARD_MIN_W, CARD_MIN_H = 40, 48
CARD_MAX_W, CARD_MAX_H = 220, 320

# Files/folders
ROOT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
IMG_FOLDER = os.path.join(ROOT, "images")
SND_FOLDER = os.path.join(ROOT, "sounds")
AST_FOLDER = os.path.join(ROOT, "assets")
SCORES_FILE = os.path.join(AST_FOLDER, "high_scores.json")
PROFILE_FILE = os.path.join(AST_FOLDER, "profile.json")
DAILY_SCORES_FILE = os.path.join(AST_FOLDER, "daily_scores.json")

if not os.path.exists(AST_FOLDER):
    os.makedirs(AST_FOLDER, exist_ok=True)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Memory Match — Ultra")
clock = pygame.time.Clock()

# =============================
# Safe loads
# =============================
def load_image(path):
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception:
        surf = pygame.Surface((100, 140), pygame.SRCALPHA)
        surf.fill((60, 60, 80))
        pygame.draw.line(surf, (120, 120, 160), (0,0), (100,140), 3)
        pygame.draw.line(surf, (120, 120, 160), (100,0), (0,140), 3)
        return surf

def load_sound(name):
    path = os.path.join(SND_FOLDER, name)
    try:
        s = pygame.mixer.Sound(path)
        return s
    except Exception:
        class _Null:
            def play(self):
                pass
        return _Null()

def load_font(size):
    try:
        return pygame.font.Font(os.path.join(AST_FOLDER, "font.ttf"), size)
    except Exception:
        return pygame.font.SysFont(None, size)

# Fonts
FONT_XL = load_font(64)
FONT_LG = load_font(48)
FONT_MD = load_font(32)
FONT_SM = load_font(22)
FONT_XS = load_font(16)

# Sounds/music
snd_flip = load_sound("flip.wav")
snd_match = load_sound("match.wav")
snd_mismatch = load_sound("mismatch.wav")
snd_win = load_sound("win.wav")
snd_button = load_sound("button.wav")

try:
    pygame.mixer.music.load(os.path.join(AST_FOLDER, "bg_music.mp3"))
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play(-1)
except Exception:
    pass

# =============================
# Data persistence
# =============================
def _read_json(path, default):
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        print("[warn] read_json", path, e)
    return default

def _write_json(path, data):
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("[warn] write_json", path, e)

# High scores (single-player levels 1..32)
_scores = _read_json(SCORES_FILE, {})

# Daily challenge scores keyed by date string
_daily_scores = _read_json(DAILY_SCORES_FILE, {})

# Profile: xp, streaks, powerups, achievements, collection, settings
_profile_default = {
    "xp": 0,
    "level": 1,
    "streak": 0,
    "best_streak": 0,
    "powerups": {"shuffle": 1, "bomb": 1, "freeze": 1},
    "achievements": {"flawless": False, "speed_runner": False, "collector": False},
    "collection": [],  # list of image IDs (filenames)
    "settings": {"music": True, "sfx": True, "fullscreen": False}
}
_profile = _read_json(PROFILE_FILE, _profile_default)
# ensure keys exist
for k, v in _profile_default.items():
    if k not in _profile:
        _profile[k] = v

# =============================
# Face library (IDs = filenames)
# =============================
# Expect images/1.png .. images/32.png (or more). You can add any number.
FACE_LIBRARY = []  # list of (id, surface)
for fname in sorted(os.listdir(IMG_FOLDER)) if os.path.exists(IMG_FOLDER) else []:
    low = fname.lower()
    if low.endswith((".png", ".jpg", ".jpeg")):
        FACE_LIBRARY.append((fname, load_image(os.path.join(IMG_FOLDER, fname))))

if not FACE_LIBRARY:
    # Fallback to generated placeholders so the game still runs
    for i in range(1, 33):
        surf = pygame.Surface((100, 140), pygame.SRCALPHA)
        surf.fill(((i*37)%255, (i*73)%255, (i*19)%255, 255))
        FACE_LIBRARY.append((f"{i}.png", surf))

# card back
BACK_IMAGE = load_image(os.path.join(IMG_FOLDER, "back.png")) if os.path.exists(os.path.join(IMG_FOLDER, "back.png")) else load_image("")

# =============================
# UI helpers
# =============================
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

def button(rect, label, hover, font=FONT_MD):
    pygame.draw.rect(screen, ACCENT if hover else ACCENT_DARK, rect, border_radius=16)
    draw_text_center(label, font, (10, 14, 18), rect.center)

# =============================
# Card object with flip anim
# =============================
class Card:
    def __init__(self, rect, face_idx, face_id, face_img, back_img):
        self.rect = rect
        self.face_idx = face_idx   # index inside selected set (0..pairs-1)
        self.face_id = face_id     # global ID (filename)
        self.face_img = face_img
        self.back_img = back_img
        self.flipped = False
        self.matched = False
        self.anim = 1.0
        self.bump = 0.0  # small bounce on click

    def draw(self, surf):
        img = self.face_img if (self.flipped or self.matched) else self.back_img
        scale_x = abs(self.anim - 0.5) * 2
        w = max(1, int(self.rect.width * scale_x))
        temp = pygame.transform.smoothscale(img, (w, self.rect.height))
        temp_rect = temp.get_rect(center=self.rect.center)
        # bump scale
        if self.bump > 0:
            bump_scale = 1.0 + 0.06 * self.bump
            temp = pygame.transform.smoothscale(temp, (int(temp_rect.width * bump_scale), int(temp_rect.height * bump_scale)))
            temp_rect = temp.get_rect(center=self.rect.center)
        surf.blit(temp, temp_rect)
        pygame.draw.rect(surf, (0,0,0), self.rect, 2, border_radius=10)

    def update(self):
        if self.anim < 1.0:
            self.anim += 0.18
            if self.anim > 1.0: self.anim = 1.0
        if self.bump > 0:
            self.bump -= 0.12
            if self.bump < 0: self.bump = 0

    def flip_visual(self):
        self.flipped = not self.flipped
        self.anim = 0.0
        self.bump = 1.0

# =============================
# Layout helpers
# =============================
def compute_grid(num_cards):
    cols = ceil(sqrt(num_cards))
    rows = ceil(num_cards / cols)
    return cols, rows

def compute_card_size(cols, rows):
    board_w = WIDTH - 2 * BOARD_PAD
    board_h = HEIGHT - TOP_HUD - BOARD_PAD
    avail_w = board_w - (cols - 1) * CELL_MARGIN
    avail_h = board_h - (rows - 1) * CELL_MARGIN
    max_w_by_width = avail_w / cols
    max_h_by_height = avail_h / rows
    max_w_from_h = max_h_by_height * CARD_ASPECT
    card_w = min(max_w_by_width, max_w_from_h)
    card_h = card_w / CARD_ASPECT
    card_w = max(CARD_MIN_W, min(CARD_MAX_W, card_w))
    card_h = max(CARD_MIN_H, min(CARD_MAX_H, card_h))
    return int(card_w), int(card_h)

def get_scaled_images(card_w, card_h, back_raw, selected_faces):
    back_img = pygame.transform.smoothscale(back_raw, (card_w, card_h))
    faces = [(fid, pygame.transform.smoothscale(img, (card_w, card_h))) for fid, img in selected_faces]
    return back_img, faces

def layout_cards(pairs, rng):
    num_cards = pairs * 2
    cols, rows = compute_grid(num_cards)
    cw, ch = compute_card_size(cols, rows)

    # choose faces
    selected = rng.sample(FACE_LIBRARY, pairs)
    back_img, faces_scaled = get_scaled_images(cw, ch, BACK_IMAGE, selected)

    deck = [i for i in range(pairs) for _ in (0,1)]
    rng.shuffle(deck)

    board_w = cols * cw + (cols - 1) * CELL_MARGIN
    board_h = rows * ch + (rows - 1) * CELL_MARGIN
    start_x = (WIDTH - board_w) // 2
    start_y = TOP_HUD + (HEIGHT - TOP_HUD - board_h) // 2

    cards = []
    for idx, face_idx in enumerate(deck):
        r, c = divmod(idx, cols)
        x = start_x + c * (cw + CELL_MARGIN)
        y = start_y + r * (ch + CELL_MARGIN)
        rect = pygame.Rect(x, y, cw, ch)
        face_id, face_img = faces_scaled[face_idx]
        cards.append(Card(rect, face_idx, face_id, face_img, back_img))
    return cards, (cols, rows)

# =============================
# Screens
# =============================

def fade_fill(alpha=180):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0,0,0,alpha))
    screen.blit(overlay, (0,0))


def draw_hud_single(level, moves, elapsed, best, powerups=None, mode="single", extra=""):
    pygame.draw.rect(screen, PANEL_COLOR, (0,0,WIDTH,TOP_HUD))
    draw_text_left(f"Mode: {mode.title()}", FONT_SM, MUTED, (BOARD_PAD, 10))
    draw_text_left(f"Level {level}", FONT_MD, WHITE, (BOARD_PAD, 40))
    draw_text_left(f"Moves: {moves}", FONT_MD, WHITE, (BOARD_PAD+200, 40))
    draw_text_left(f"Time: {elapsed}s", FONT_MD, WHITE, (BOARD_PAD+400, 40))
    if best is not None:
        draw_text_left(f"Best: {best}s", FONT_MD, ACCENT, (BOARD_PAD+620, 40))
    else:
        draw_text_left("Best: —", FONT_MD, MUTED, (BOARD_PAD+620, 40))
    if extra:
        draw_text_left(extra, FONT_SM, MUTED, (BOARD_PAD, 70))

    # Power-ups HUD
    if powerups:
        x = WIDTH - 260
        y = 16
        for key in ("shuffle", "bomb", "freeze"):
            rect = pygame.Rect(x, y, 76, 28)
            pygame.draw.rect(screen, (40,60,80), rect, border_radius=10)
            draw_text_center(f"{key[:1].upper()}:{powerups.get(key,0)}", FONT_XS, WHITE, rect.center)
            powerups[f"_{key}_rect"] = rect
            x += 84


def draw_hud_multi(p1, p2, cur, moves, elapsed):
    pygame.draw.rect(screen, PANEL_COLOR, (0,0,WIDTH,TOP_HUD))
    draw_text_left("Mode: Multiplayer", FONT_SM, MUTED, (BOARD_PAD, 10))
    draw_text_left(f"P1: {p1}", FONT_MD, WHITE, (BOARD_PAD, 40))
    draw_text_left(f"P2: {p2}", FONT_MD, WHITE, (BOARD_PAD+220, 40))
    turn_col = GOLD if cur==1 else WHITE
    draw_text_left(f"Turn: P{cur}", FONT_MD, turn_col, (BOARD_PAD+420, 40))
    draw_text_left(f"Moves: {moves}", FONT_MD, WHITE, (BOARD_PAD+600, 40))
    draw_text_left(f"Time: {elapsed}s", FONT_MD, WHITE, (BOARD_PAD+760, 40))


# -----------------------------
# Utility: profile save helpers
# -----------------------------
def save_profile():
    _write_json(PROFILE_FILE, _profile)

def save_scores():
    _write_json(SCORES_FILE, _scores)

def save_daily_scores():
    _write_json(DAILY_SCORES_FILE, _daily_scores)

# -----------------------------
# Game logic core
# -----------------------------

def apply_shuffle(cards, rng):
    # Shuffle only unmatched cards' positions
    free = [c for c in cards if not c.matched]
    poses = [c.rect.topleft for c in free]
    rng.shuffle(poses)
    for c, pos in zip(free, poses):
        c.rect.topleft = pos


def apply_bomb(cards, rng, pairs_to_clear=1):
    # Clear random unmatched pair(s)
    remaining = {}
    for c in cards:
        if not c.matched:
            remaining.setdefault(c.face_idx, []).append(c)
    keys = [k for k, v in remaining.items() if len(v)>=2]
    rng.shuffle(keys)
    cleared = 0
    for k in keys:
        a, b = remaining[k][:2]
        a.matched = b.matched = True
        cleared += 1
        if cleared >= pairs_to_clear:
            break
    return cleared

# -----------------------------
# Game screens
# -----------------------------

def game_screen(level=1, mode="single"):
    # RNG: normal vs daily seeded
    if mode == "daily":
        seed = datetime.date.today().isoformat()
        rng = random.Random(seed)
    else:
        rng = random.Random()

    cards, (cols, rows) = layout_cards(level, rng)
    flipped = []
    matches = 0
    total_pairs = level
    moves = 0
    mismatches = 0

    start_ts = time.time()
    frozen_accum = 0.0
    freeze_left_ms = 0

    # Multiplayer state
    p_scores = [0, 0]
    cur_player = 1

    # Training: reveal at start for 4s
    training_reveal_ms = 0
    if mode == "training":
        for c in cards:
            c.flipped = True
        training_reveal_ms = 4000

    running = True
    while running:
        dt = clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()

        # Timer freeze accumulation
        if freeze_left_ms > 0:
            freeze_left_ms = max(0, freeze_left_ms - dt)
            frozen_accum += dt/1000.0

        # Handle events
        click = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                return False
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                click = True

        # Training hide after reveal timeout
        if training_reveal_ms > 0:
            training_reveal_ms -= dt
            if training_reveal_ms <= 0:
                for c in cards:
                    c.flipped = False

        # Card clicks
        if click and training_reveal_ms <= 0:
            for card in cards:
                if card.rect.collidepoint((mx, my)) and not card.flipped and not card.matched:
                    if len(flipped) < 2:
                        snd_flip.play() if _profile["settings"].get("sfx", True) else None
                        card.flip_visual()
                        flipped.append(card)
                    break

        # Power-up clicks (single/daily/training only)
        pu_hud = None
        if mode in ("single", "daily", "training"):
            pu_hud = {
                "shuffle": _profile["powerups"].get("shuffle", 0),
                "bomb": _profile["powerups"].get("bomb", 0),
                "freeze": _profile["powerups"].get("freeze", 0)
            }
            # On click, check rects set later during draw
            if click:
                # Defer processing until after drawing when rects exist
                pass

        # Pair resolution
        if len(flipped) == 2:
            pygame.display.flip()
            pygame.time.delay(380)
            moves += 1
            a, b = flipped
            if a.face_idx == b.face_idx:
                snd_match.play() if _profile["settings"].get("sfx", True) else None
                a.matched = b.matched = True
                matches += 1
                if mode == "multi":
                    p_scores[cur_player-1] += 1
                # Add to collection
                if a.face_id not in _profile["collection"]:
                    _profile["collection"].append(a.face_id)
                    save_profile()
            else:
                snd_mismatch.play() if _profile["settings"].get("sfx", True) else None
                mismatches += 1
                a.flip_visual(); b.flip_visual()
                if mode == "multi":
                    cur_player = 2 if cur_player == 1 else 1
            flipped.clear()

        # Drawing
        screen.fill(BG_COLOR)

        elapsed = int(max(0, (time.time() - start_ts) - frozen_accum))

        if mode == "multi":
            draw_hud_multi(p_scores[0], p_scores[1], cur_player, moves, elapsed)
        else:
            best = None
            label_mode = mode
            if mode == "single":
                best = _scores.get(str(level))
            elif mode == "daily":
                dkey = datetime.date.today().isoformat()
                best = _daily_scores.get(dkey, {}).get("best_time")
                label_mode = f"daily {dkey}"
            draw_hud_single(level, moves, elapsed, best, powerups=pu_hud, mode=label_mode, extra="Click power-ups on right")

        # Draw cards
        for c in cards:
            c.update(); c.draw(screen)

        # Now that HUD is drawn, handle power-up clicks if any
        if pu_hud and click:
            # shuffle
            r = pu_hud.get("_shuffle_rect")
            if r and r.collidepoint((mx,my)) and _profile["powerups"].get("shuffle",0) > 0:
                apply_shuffle(cards, rng)
                _profile["powerups"]["shuffle"] -= 1
                save_profile()
            r = pu_hud.get("_bomb_rect")
            if r and r.collidepoint((mx,my)) and _profile["powerups"].get("bomb",0) > 0:
                cleared = apply_bomb(cards, rng, 1)
                if cleared>0:
                    matches += cleared
                    _profile["powerups"]["bomb"] -= 1
                    save_profile()
            r = pu_hud.get("_freeze_rect")
            if r and r.collidepoint((mx,my)) and _profile["powerups"].get("freeze",0) > 0:
                freeze_left_ms = max(freeze_left_ms, 10000)
                _profile["powerups"]["freeze"] -= 1
                save_profile()

        # Win condition
        if matches >= total_pairs:
            snd_win.play() if _profile["settings"].get("sfx", True) else None
            elapsed = int(max(0, (time.time() - start_ts) - frozen_accum))

            # Stats/achievements (single only affects level scores & streak)
            if mode == "single":
                prev = _scores.get(str(level))
                if prev is None or elapsed < prev:
                    _scores[str(level)] = elapsed
                    save_scores()
                # XP & streak
                gain = 10*level + max(0, (total_pairs*2 - moves))
                _profile["xp"] += max(5, gain)
                _profile["streak"] += 1
                _profile["best_streak"] = max(_profile["best_streak"], _profile["streak"])
                # Achievements
                if mismatches == 0:
                    _profile["achievements"]["flawless"] = True
                if elapsed <= 20:
                    _profile["achievements"]["speed_runner"] = True
                if len(_profile["collection"]) >= min(32, len(FACE_LIBRARY)):
                    _profile["achievements"]["collector"] = True
                save_profile()

            elif mode == "daily":
                dkey = datetime.date.today().isoformat()
                entry = _daily_scores.get(dkey, {"best_time": None, "best_moves": None})
                if entry["best_time"] is None or elapsed < entry["best_time"]:
                    entry["best_time"] = elapsed
                if entry["best_moves"] is None or moves < entry["best_moves"]:
                    entry["best_moves"] = moves
                _daily_scores[dkey] = entry
                save_daily_scores()

            # Multiplayer: just show winner banner
            fade_fill(180)
            if mode == "multi":
                if p_scores[0] > p_scores[1]:
                    msg = "Player 1 Wins!"
                elif p_scores[1] > p_scores[0]:
                    msg = "Player 2 Wins!"
                else:
                    msg = "Draw!"
                draw_text_center(msg, FONT_LG, GOLD, (WIDTH//2, HEIGHT//2 - 10))
                draw_text_center(f"Time {elapsed}s • Moves {moves}", FONT_MD, WHITE, (WIDTH//2, HEIGHT//2 + 40))
            else:
                draw_text_center(f"Level {level} Complete!", FONT_LG, ACCENT, (WIDTH//2, HEIGHT//2 - 30))
                draw_text_center(f"Time {elapsed}s • Moves {moves}", FONT_MD, WHITE, (WIDTH//2, HEIGHT//2 + 20))
            pygame.display.flip()
            pygame.time.delay(2200)
            return True

        pygame.display.flip()

# -----------------------------
# Other Screens
# -----------------------------

def scores_screen():
    btn_back = pygame.Rect(BOARD_PAD, HEIGHT-BOARD_PAD-48, 160, 48)
    while True:
        mx, my = pygame.mouse.get_pos()
        click = False
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                click = True

        screen.fill(BG_COLOR)
        draw_text_center("High Scores", FONT_LG, ACCENT, (WIDTH//2, 80))
        for i in range(32):
            level = i+1
            x = WIDTH//2 - 240 + (i//16)*300
            y = 150 + (i%16)*26
            draw_text_left(f"Level {level:>2}:", FONT_SM, WHITE, (x, y))
            best = _scores.get(str(level))
            val = f"{best}s" if best is not None else "—"
            draw_text_left(val, FONT_SM, ACCENT if best is not None else MUTED, (x+140, y))

        h = btn_back
        button(h, "Back", h.collidepoint((mx,my)))
        if click and h.collidepoint((mx,my)):
            return
        pygame.display.flip(); clock.tick(FPS)


def settings_screen():
    items = [
        ("Music", "music"),
        ("SFX", "sfx"),
        ("Fullscreen", "fullscreen"),
        ("+1 Shuffle", "add_shuffle"),
        ("+1 Bomb", "add_bomb"),
        ("+1 Freeze", "add_freeze"),
    ]
    rects = []
    back = pygame.Rect(BOARD_PAD, HEIGHT-BOARD_PAD-56, 180, 48)
    while True:
        mx, my = pygame.mouse.get_pos(); click=False
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE): return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: click=True
        screen.fill(BG_COLOR)
        draw_text_center("Settings", FONT_LG, ACCENT, (WIDTH//2, 90))
        rects.clear()
        for i, (label, key) in enumerate(items):
            r = pygame.Rect(WIDTH//2-180, 160+i*60, 360, 44)
            rects.append((r, key))
            on = None
            if key in ("music","sfx","fullscreen"):
                on = _profile["settings"].get(key, False)
            elif key.startswith("add_"):
                on = None
            pygame.draw.rect(screen, (40,60,80), r, border_radius=12)
            draw_text_left(label + (f": {'ON' if on else 'OFF'}" if on is not None else ""), FONT_MD, WHITE, (r.x+16, r.y+8))
        button(back, "Back", back.collidepoint((mx,my)))

        if click:
            if back.collidepoint((mx,my)): return
            for r, key in rects:
                if r.collidepoint((mx,my)):
                    if key in ("music","sfx","fullscreen"):
                        val = not _profile["settings"].get(key, False)
                        _profile["settings"][key] = val
                        if key == "music":
                            try:
                                if val:
                                    pygame.mixer.music.unpause()
                                else:
                                    pygame.mixer.music.pause()
                            except Exception:
                                pass
                        if key == "fullscreen":
                            if val:
                                pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
                            else:
                                pygame.display.set_mode((WIDTH, HEIGHT))
                        save_profile()
                    elif key == "add_shuffle":
                        _profile["powerups"]["shuffle"] = _profile["powerups"].get("shuffle",0)+1; save_profile()
                    elif key == "add_bomb":
                        _profile["powerups"]["bomb"] = _profile["powerups"].get("bomb",0)+1; save_profile()
                    elif key == "add_freeze":
                        _profile["powerups"]["freeze"] = _profile["powerups"].get("freeze",0)+1; save_profile()
        pygame.display.flip(); clock.tick(FPS)


def collection_screen():
    # Simple scroll grid of collected cards (by filename)
    collected = _profile.get("collection", [])
    thumbs = []
    for fid in collected:
        img = load_image(os.path.join(IMG_FOLDER, fid))
        thumbs.append((fid, pygame.transform.smoothscale(img, (90, 126))))
    back = pygame.Rect(BOARD_PAD, HEIGHT-BOARD_PAD-56, 180, 48)

    scroll = 0
    while True:
        mx, my = pygame.mouse.get_pos(); click=False
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE): return
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: click=True
            if e.type == pygame.MOUSEWHEEL:
                scroll += e.y*24
        screen.fill(BG_COLOR)
        draw_text_center("Collection", FONT_LG, ACCENT, (WIDTH//2, 80))
        cols = 8
        gap = 16
        start_x = (WIDTH - cols*(90) - (cols-1)*gap)//2
        y0 = 140 + scroll
        for i, (fid, th) in enumerate(thumbs):
            r, c = divmod(i, cols)
            x = start_x + c*(90+gap)
            y = y0 + r*(126+gap)
            screen.blit(th, (x, y))
            draw_text_left(os.path.splitext(fid)[0], FONT_XS, MUTED, (x, y+126+2))
        button(back, "Back", back.collidepoint((mx,my)))
        if click and back.collidepoint((mx,my)):
            return
        pygame.display.flip(); clock.tick(FPS)

# -----------------------------
# Home/menu
# -----------------------------

def home_screen():
    labels = [
        ("Single Player", "single"),
        ("Multiplayer", "multi"),
        ("Daily Challenge", "daily"),
        ("Training Mode", "training"),
        ("High Scores", "scores"),
        ("Collection", "collection"),
        ("Settings", "settings"),
        ("Quit", "quit"),
    ]
    rects = [pygame.Rect(WIDTH//2-170, 190+i*56, 340, 46) for i in range(len(labels))]

    while True:
        mx, my = pygame.mouse.get_pos(); click=False
        for e in pygame.event.get():
            if e.type == pygame.QUIT: pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1: click=True

        screen.fill(BG_COLOR)
        draw_text_center("Memory Match — Ultra", FONT_XL, ACCENT, (WIDTH//2, 96))
        draw_text_center("Now with Multiplayer, Daily, Training, Power-ups, XP & Collection", FONT_SM, MUTED, (WIDTH//2, 136))

        for (label, key), r in zip(labels, rects):
            hover = r.collidepoint((mx,my))
            button(r, label, hover)
            if click and hover:
                snd_button.play() if _profile["settings"].get("sfx", True) else None
                return key

        pygame.display.flip(); clock.tick(FPS)

# -----------------------------
# Main loop
# -----------------------------

def main():
    level_cap = 32
    while True:
        action = home_screen()
        if action == "quit":
            pygame.quit(); sys.exit()
        elif action == "scores":
            scores_screen()
        elif action == "settings":
            settings_screen()
        elif action == "collection":
            collection_screen()
        elif action in ("single", "multi", "daily", "training"):
            # Loop through levels 1..32 for single/multi; for daily/training we just play level 8 default
            if action in ("single", "multi"):
                for lv in range(1, level_cap+1):
                    cont = game_screen(level=lv, mode=action)
                    if not cont:
                        # reset streak if exited early in single
                        if action == "single":
                            _profile["streak"] = 0; save_profile()
                        break
            else:
                # preset level size (pairs)
                cont = game_screen(level=8, mode=action)
                # no streak updates for these modes
        else:
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit(); sys.exit()
