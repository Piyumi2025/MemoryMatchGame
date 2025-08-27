import os
import sys
import json
import time
import random
import math
import pygame
from typing import List, Tuple

# ---------------------------
# Basic setup & constants
# ---------------------------
pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 900, 640
FPS = 60
BG_COLOR = (12, 14, 25)
ACCENT = (0, 191, 255)
TEXT = (230, 238, 255)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mythic Match Quest — robust edition")
clock = pygame.time.Clock()

FONT_LG = pygame.font.SysFont("Segoe UI", 42)
FONT_MD = pygame.font.SysFont("Segoe UI", 26)
FONT_SM = pygame.font.SysFont("Segoe UI", 18)

# ---------------------------
# Utilities
# ---------------------------
ASSETS_DIR = os.path.abspath("assets")
SOUNDS_DIR = os.path.abspath("sounds")
IMAGES_DIR = os.path.abspath("images")

for d in [ASSETS_DIR, SOUNDS_DIR, IMAGES_DIR]:
    if not os.path.isdir(d):
        # Create if missing to avoid crashes; user can later add real files
        os.makedirs(d, exist_ok=True)


def safe_load_sound(name: str):
    """Try to load a sound. Return None on failure (game will continue silently)."""
    path = os.path.join(SOUNDS_DIR, name)
    try:
        if os.path.exists(path):
            return pygame.mixer.Sound(path)
    except Exception:
        pass
    return None


# Optional sounds — all are optional; game runs fine without them
SND_FLIP = safe_load_sound("flip.mp3") or safe_load_sound("flip.wav")
SND_MATCH = safe_load_sound("match.mp3") or safe_load_sound("match.wav")
SND_MISMATCH = safe_load_sound("mismatch.mp3") or safe_load_sound("mismatch.wav")
SND_WIN = safe_load_sound("win.mp3") or safe_load_sound("win.wav")
SND_LEVELUP = safe_load_sound("levelup.mp3") or safe_load_sound("levelup.wav")

MUSIC_TRACKS = [
    os.path.join(SOUNDS_DIR, f"level{i}.mp3") for i in (1, 2, 3)
]


# ---------------------------
# Image helpers
# ---------------------------

def list_card_images() -> List[str]:
    """Return sorted list of image file paths (jpg/png) inside images/ excluding back.* """
    if not os.path.isdir(IMAGES_DIR):
        return []
    files = []
    for f in os.listdir(IMAGES_DIR):
        fl = f.lower()
        if fl.startswith("back."):
            continue
        if fl.endswith((".jpg", ".jpeg", ".png")):
            files.append(os.path.join(IMAGES_DIR, f))
    files.sort()
    return files


def load_surface_keep_ratio(path: str, target: Tuple[int, int]) -> pygame.Surface:
    """Load an image and fit it into target size while preserving aspect ratio, with letterbox."""
    try:
        img = pygame.image.load(path).convert_alpha()
    except Exception:
        # Fallback colored card
        surf = pygame.Surface(target, pygame.SRCALPHA)
        surf.fill((30, 34, 46))
        pygame.draw.rect(surf, ACCENT, surf.get_rect(), 3, border_radius=12)
        return surf

    w, h = img.get_size()
    tw, th = target
    scale = min(tw / w, th / h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    img = pygame.transform.smoothscale(img, (nw, nh))

    # Letterbox into target
    surf = pygame.Surface((tw, th), pygame.SRCALPHA)
    surf.fill((22, 26, 34))
    rect = img.get_rect(center=(tw // 2, th // 2))
    surf.blit(img, rect)
    pygame.draw.rect(surf, (60, 70, 92), surf.get_rect(), 2, border_radius=12)
    return surf


def make_back_surface(size: Tuple[int, int]) -> pygame.Surface:
    w, h = size
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    # gradient-like stripes
    for i in range(h):
        t = i / max(1, h - 1)
        c = (
            int(18 + 8 * t),
            int(22 + 12 * t),
            int(34 + 24 * t),
        )
        pygame.draw.line(surf, c, (0, i), (w, i))
    pygame.draw.rect(surf, ACCENT, surf.get_rect(), 3, border_radius=14)
    # emblem
    pygame.draw.circle(surf, ACCENT, (w // 2, h // 2), min(w, h) // 6, 2)
    pygame.draw.line(surf, ACCENT, (w // 2, h // 2 - 10), (w // 2, h // 2 + 10), 2)
    pygame.draw.line(surf, ACCENT, (w // 2 - 10, h // 2), (w // 2 + 10, h // 2), 2)
    return surf


# ---------------------------
# Card sprite
# ---------------------------
CARD_SIZE = (100, 140)


class Card(pygame.sprite.Sprite):
    def __init__(self, front_path: str, pos: Tuple[int, int], pair_id: int):
        super().__init__()
        self.front_surf = load_surface_keep_ratio(front_path, CARD_SIZE)
        self.back_surf = make_back_surface(CARD_SIZE)
        self.image = self.back_surf.copy()
        self.rect = self.image.get_rect(topleft=pos)

        self.id = pair_id
        self.is_front = False
        self.matched = False
        self.animating = False
        self.flip_progress = 0.0  # 0..1 during animation

    def instant_show_back(self):
        self.is_front = False
        self.image = self.back_surf

    def instant_show_front(self):
        self.is_front = True
        self.image = self.front_surf

    def trigger_flip(self):
        if self.animating or self.matched:
            return
        self.animating = True
        self.flip_progress = 0.0
        if SND_FLIP:
            SND_FLIP.play()

    def update(self, dt: float):
        if not self.animating:
            return
        speed = 6.0  # higher is faster
        self.flip_progress += speed * dt
        if self.flip_progress >= 1.0:
            self.flip_progress = 1.0
            self.animating = False
            # finalize side
            self.is_front = not self.is_front
            self.image = self.front_surf if self.is_front else self.back_surf

        # Scale X to create flip illusion
        phase = self.flip_progress
        # 0..0.5 shrink, swap, 0.5..1 expand
        if phase < 0.5:
            scale = max(0.05, 1.0 - (phase * 2))
            surf = self.front_surf if self.is_front else self.back_surf
        else:
            scale = max(0.05, (phase - 0.5) * 2)
            surf = self.back_surf if self.is_front else self.front_surf
        w, h = surf.get_size()
        new_w = max(1, int(w * scale))
        scaled = pygame.transform.smoothscale(surf, (new_w, h))
        # center on original rect center
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        self.image.blit(scaled, scaled.get_rect(center=(w // 2, h // 2)))


# ---------------------------
# Game logic
# ---------------------------
class Game:
    def __init__(self):
        # Levels as (grid_cols_rows, time_limit_sec)
        # We'll auto-size pairs = cols*rows/2
        self.levels = [
            (4, 60),  # 4x4 = 8 pairs
            (6, 100), # 6x6 = 18 pairs
            (8, 160), # 8x8 = 32 pairs
        ]
        self.level_index = 0

        self.cards = pygame.sprite.Group()
        self.flipped_cache: List[Card] = []
        self.matches = 0
        self.flips = 0
        self.score = 0
        self.time_start = 0.0
        self.time_limit = 0.0
        self.game_over = False
        self.paused = False

        self.high_scores = self.load_high_scores()

    # -------------- persistence --------------
    def load_high_scores(self):
        path = os.path.join(ASSETS_DIR, "high_scores.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # ensure keys
                for k in ("0", "1", "2"):
                    data.setdefault(k, 0)
                return data
            except Exception:
                pass
        data = {"0": 0, "1": 0, "2": 0}
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass
        return data

    def save_high_scores(self):
        path = os.path.join(ASSETS_DIR, "high_scores.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.high_scores, f)
        except Exception:
            pass

    # -------------- screens --------------
    def home(self):
        # preload available images to inform levels
        available_images = list_card_images()
        running = True
        blink = 0
        while running:
            dt = clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_1:
                        self.level_index = 0; running = False
                    elif e.key == pygame.K_2:
                        self.level_index = 1; running = False
                    elif e.key == pygame.K_3:
                        self.level_index = 2; running = False
                    elif e.key == pygame.K_q:
                        pygame.quit(); sys.exit()
            blink = (blink + dt) % 1.0

            screen.fill(BG_COLOR)
            self.draw_starfield()

            title = FONT_LG.render("Mythic Match Quest", True, ACCENT)
            screen.blit(title, title.get_rect(center=(WIDTH//2, 100)))

            info = [
                "1: Easy (4x4)",
                "2: Medium (6x6)",
                "3: Hard (8x8)",
                "H: In-level hint  |  P: Pause  |  Q: Quit",
                f"Images found: {len(available_images)} (put JPG/PNG in /images)",
                f"High Scores:  E:{self.high_scores['0']}  M:{self.high_scores['1']}  H:{self.high_scores['2']}",
            ]
            for i, line in enumerate(info):
                surf = FONT_MD.render(line, True, TEXT)
                screen.blit(surf, (WIDTH//2 - 260, 200 + i*40))

            press = FONT_MD.render("Press 1 / 2 / 3 to start", True, (TEXT if blink < 0.5 else (90, 100, 120)))
            screen.blit(press, press.get_rect(center=(WIDTH//2, HEIGHT - 80)))

            pygame.display.flip()

    def run_level(self):
        cols = rows = self.levels[self.level_index][0]
        self.time_limit = float(self.levels[self.level_index][1])
        total_pairs_needed = (cols * rows) // 2

        # Build deck from available images
        imgs = list_card_images()
        if len(imgs) < total_pairs_needed:
            # If not enough, cycle through images
            repeats = math.ceil(total_pairs_needed / max(1, len(imgs))) if imgs else 0
            imgs = (imgs * repeats)[:total_pairs_needed]
        else:
            imgs = random.sample(imgs, total_pairs_needed)

        deck = imgs * 2
        random.shuffle(deck)

        # layout
        self.cards.empty()
        margin_x, margin_y = 40, 80
        grid_w = WIDTH - margin_x*2
        grid_h = HEIGHT - margin_y*2
        spacing_x = grid_w // cols
        spacing_y = grid_h // rows

        k = 0
        for r in range(rows):
            for c in range(cols):
                x = margin_x + c * spacing_x + (spacing_x - CARD_SIZE[0]) // 2
                y = margin_y + r * spacing_y + (spacing_y - CARD_SIZE[1]) // 2
                card = Card(deck[k], (x, y), pair_id=(k // 2))
                self.cards.add(card)
                k += 1

        self.flipped_cache.clear()
        self.matches = 0
        self.flips = 0
        self.score = 1000
        self.time_start = time.time()
        self.game_over = False
        self.paused = False

        # optional music
        try:
            music_path = MUSIC_TRACKS[self.level_index]
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1)
            else:
                pygame.mixer.music.stop()
        except Exception:
            pass

        while not self.game_over:
            dt = clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_p:
                        self.paused = not self.paused
                    elif e.key == pygame.K_h and not self.paused:
                        # Hint: briefly flip a random hidden card (costs score)
                        hidden = [cd for cd in self.cards if not cd.is_front and not cd.matched and not cd.animating]
                        if hidden:
                            self.score = max(0, self.score - 25)
                            random.choice(hidden).trigger_flip()
                    elif e.key == pygame.K_q:
                        pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not self.paused:
                    self.handle_click(e.pos)

            # update
            if not self.paused:
                for cd in self.cards:
                    cd.update(dt)
                self.check_auto_close_flip()

            # time & score
            elapsed = time.time() - self.time_start
            remaining = max(0.0, self.time_limit - (elapsed if not self.paused else 0.0))
            if not self.paused:
                self.score = max(0, 1000 - self.flips * 6 - int(elapsed) * 3 + int(remaining) * 1)

            # draw
            screen.fill(BG_COLOR)
            self.draw_starfield()
            self.cards.draw(screen)

            ui = FONT_MD.render(
                f"Score: {self.score}   Time Left: {int(remaining)}s   Flips: {self.flips}", True, TEXT
            )
            screen.blit(ui, (18, 14))

            lvl = FONT_SM.render(
                f"Level {self.level_index+1} — Press P to Pause, H for hint (-25)", True, (160, 180, 200)
            )
            screen.blit(lvl, (18, 46))

            if self.paused:
                self.draw_center_banner("Paused — press P to resume")

            pygame.display.flip()

            if remaining <= 0 and not self.game_over:
                self.end_level(win=False)

        # after loop
        self.level_index = min(2, self.level_index + 1) if self.last_win else self.level_index

    def handle_click(self, pos: Tuple[int, int]):
        # ignore if two are animating/visible waiting to resolve
        if len(self.flipped_cache) >= 2:
            return
        for card in self.cards:
            if card.rect.collidepoint(pos) and not card.matched and not card.animating:
                if not card.is_front:
                    card.trigger_flip()
                    self.flips += 1
                    # we will push to cache after it finishes opening
                return

    def check_auto_close_flip(self):
        # If cache has 1 or 2 fully opened cards, manage match/mismatch
        # First, collect cards that just finished opening to front
        for cd in self.cards:
            if cd.animating is False and cd.is_front and cd not in self.flipped_cache and not cd.matched:
                # ensure it just became visible (heuristic: if image equals front and not in cache)
                self.flipped_cache.append(cd)

        if len(self.flipped_cache) == 2:
            c1, c2 = self.flipped_cache
            if c1.id == c2.id:
                c1.matched = c2.matched = True
                self.matches += 1
                if SND_MATCH:
                    SND_MATCH.play()
                self.flipped_cache.clear()
                if self.matches == len(self.cards) // 2:
                    self.end_level(win=True)
            else:
                # mismatch — briefly show, then flip back
                if SND_MISMATCH:
                    SND_MISMATCH.play()
                pygame.time.set_timer(pygame.USEREVENT + 1, 600, loops=1)
                # handle timed flip-back in event loop style
                for e in pygame.event.get([pygame.USEREVENT + 1]):
                    pass  # flush any old timers
                def flip_back_after_delay():
                    c1.trigger_flip(); c2.trigger_flip()
                    self.flipped_cache.clear()
                # we'll poll the timer in update loop
                self._pending_flipback = (time.time() + 0.6, flip_back_after_delay)
        # run any pending flipback
        if hasattr(self, "_pending_flipback"):
            t, fn = self._pending_flipback
            if time.time() >= t:
                try:
                    fn()
                finally:
                    delattr(self, "_pending_flipback")

    def end_level(self, win: bool):
        self.game_over = True
        self.last_win = win
        if win:
            if SND_WIN:
                SND_WIN.play()
            # update highscores
            key = str(self.level_index)
            self.high_scores[key] = max(self.high_scores.get(key, 0), int(self.score))
            self.save_high_scores()
            self.draw_center_banner("Level Complete! Press Enter for next / Esc Home")
            if SND_LEVELUP:
                SND_LEVELUP.play()
        else:
            self.draw_center_banner("Time's up! Press Enter to retry / Esc Home")

        pygame.display.flip()
        # Wait for user input
        waiting = True
        while waiting:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_RETURN:
                        waiting = False
                    if e.key == pygame.K_ESCAPE:
                        waiting = False
                        # go home after breaking
                        self.level_index = self.level_index  # unchanged
                        self.last_win = False  # avoid auto level advance
                        self._go_home_after = True
            clock.tick(FPS)

    # -------------- draw helpers --------------
    def draw_starfield(self):
        # subtle starfield (stable pattern using seeded RNG for less flicker)
        rnd = random.Random(12345)
        for _ in range(100):
            x = rnd.randint(0, WIDTH)
            y = rnd.randint(0, HEIGHT)
            r = rnd.choice([1, 1, 2])
            pygame.draw.circle(screen, (255, 255, 255), (x, y), r)

    def draw_center_banner(self, text: str):
        banner = pygame.Surface((WIDTH - 160, 120), pygame.SRCALPHA)
        banner.fill((0, 0, 0, 160))
        pygame.draw.rect(banner, ACCENT, banner.get_rect(), 2, border_radius=18)
        t = FONT_MD.render(text, True, TEXT)
        banner.blit(t, t.get_rect(center=(banner.get_width()//2, banner.get_height()//2)))
        screen.blit(banner, banner.get_rect(center=(WIDTH//2, HEIGHT//2)))


# ---------------------------
# Main entry
# ---------------------------
if __name__ == "__main__":
    game = Game()
    while True:
        game._go_home_after = False
        game.home()
        game.run_level()
        # Decide where to go next
        if getattr(game, "_go_home_after", False):
            continue
        # If completed a level and there is a next, continue automatically
        if game.last_win and game.level_index < 3:
            continue
        # otherwise show home again
        