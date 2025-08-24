import pygame
from pygame.locals import *
import random
import time
from PIL import Image
from gtts import gTTS
import os
import json
import sys
import tempfile
import os

pygame.init()
pygame.mixer.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mythic Match Quest")
clock = pygame.time.Clock()
FPS = 60

# Load and generate sounds
flip_sound = pygame.mixer.Sound('sounds/flip.mp3')
match_sound = pygame.mixer.Sound('sounds/match.mp3')
mismatch_sound = pygame.mixer.Sound('sounds/mismatch.mp3')
win_sound = pygame.mixer.Sound('sounds/win.mp3')
for file, text in [('match.mp3', 'Match!'), ('tryagain.mp3', 'Try again!'), ('levelup.mp3', 'Level Up!')]:
    if not os.path.exists(f'sounds/{file}'):
        tts = gTTS(text=text, lang='en')
        tts.save(f'sounds/{file}')

# Load image with PIL (random filter)


def load_image(path, size=(100, 150)):
    with Image.open(path) as img:
        img = img.resize(size, Image.Resampling.LANCZOS)  # High-quality resize
        if random.choice([True, False]):
            img = img.convert('L')  # Grayscale
        # Create a temporary file with explicit name and no auto-delete
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            img.save(tmp.name, 'PNG')  # Explicitly save as PNG
            tmp_file = tmp.name
        # Load the image after saving
        surface = pygame.image.load(tmp_file)
        # Clean up the temporary file after loading
        os.unlink(tmp_file)
        return surface

# Card class with animation and particles
class Card(pygame.sprite.Sprite):
    def __init__(self, image_path, pos, id):
        super().__init__()
        self.front = load_image(image_path)
        self.back = load_image('images/back.png')
        self.image = self.back
        self.rect = self.image.get_rect(topleft=pos)
        self.id = id
        self.flipped = False
        self.matched = False
        self.angle = 0
        self.animating = False

    def flip(self):
        if not self.animating:
            flip_sound.play()
            self.animating = True
            for angle in range(0, 181, 18):
                rotated = pygame.transform.rotate(self.front if angle > 90 else self.back, angle)
                rotated_rect = rotated.get_rect(center=self.rect.center)
                screen.blit(rotated, rotated_rect)
                pygame.display.flip()
                clock.tick(FPS)
            self.image = self.front
            self.flipped = True
            self.animating = False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        if self.matched:
            for _ in range(10):
                x = self.rect.centerx + random.randint(-20, 20)
                y = self.rect.centery + random.randint(-20, 20)
                pygame.draw.circle(surface, (0, 191, 255), (x, y), 5)  # Blue particles

# Game class with home screen and levels
class Game:
    def __init__(self):
        self.levels = [(4, 8, 60), (6, 18, 90), (8, 32, 120)]  # (grid_size, pairs, time_limit)
        self.current_level = 0
        self.cards = pygame.sprite.Group()
        self.flipped_cards = []
        self.matches = 0
        self.flips = 0
        self.start_time = 0
        self.score = 1000
        self.high_scores = self.load_high_scores()
        self.show_home()

    def load_high_scores(self):
        try:
            with open('assets/high_scores.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
        # Create default high scores if file is missing or invalid
            default_scores = {"0": 0, "1": 0, "2": 0}
            with open('assets/high_scores.json', 'w') as f:
                json.dump(default_scores, f)
            return default_scores

    def show_home(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_1:
                        self.current_level = 0
                        running = False
                    elif event.key == K_2:
                        self.current_level = 1
                        running = False
                    elif event.key == K_3:
                        self.current_level = 2
                        running = False
                    elif event.key == K_q:
                        pygame.quit()
                        sys.exit()
            screen.fill((0, 0, 0))
            font = pygame.font.SysFont('Arial', 40)
            screen.blit(font.render("Mythic Match Quest", True, (0, 191, 255)), (150, 100))
            screen.blit(font.render("1: Easy | 2: Medium | 3: Hard | Q: Quit", True, (0, 191, 255)), (150, 200))
            screen.blit(font.render(f"High Scores: {self.high_scores['0']}/{self.high_scores['1']}/{self.high_scores['2']}", True, (0, 191, 255)), (150, 300))
            screen.blit(font.render("Click to flip, H for hint", True, (0, 191, 255)), (150, 400))
            pygame.display.flip()

    def create_board(self, grid_size, pairs):
        self.cards.empty()
        images = ['images/' + str(i) + '.jpg' for i in range(1, pairs + 1)]
        pairs_list = images * 2
        random.shuffle(pairs_list)
        spacing_x = WIDTH // (grid_size + 1)
        spacing_y = HEIGHT // (grid_size + 1)
        for i, img in enumerate(pairs_list):
            row, col = i // grid_size, i % grid_size
            pos = (spacing_x * (col + 1), spacing_y * (row + 1))
            card = Card(img, pos, int(img.split('/')[-1].split('.')[0]))
            self.cards.add(card)

    def handle_click(self, pos):
        if len(self.flipped_cards) < 2 and time.time() - self.start_time < self.levels[self.current_level][2]:
            for card in self.cards:
                if card.rect.collidepoint(pos) and not card.flipped and not card.matched:
                    card.flip()
                    self.flipped_cards.append(card)
                    self.flips += 1
                    if len(self.flipped_cards) == 2:
                        self.check_match()

    def check_match(self):
        card1, card2 = self.flipped_cards
        if card1.id == card2.id:
            match_sound.play()
            card1.matched = card2.matched = True
            self.matches += 1
            if self.matches == len(self.cards) // 2:
                self.game_over = True
                win_sound.play()
                self.high_scores[str(self.current_level)] = max(self.high_scores[str(self.current_level)], self.score)
                self.save_high_scores()
        else:
            mismatch_sound.play()
            pygame.time.wait(1000)
            card1.flip()
            card2.flip()
        self.flipped_cards = []

    def update_score(self):
        elapsed = time.time() - self.start_time
        remaining = max(0, self.levels[self.current_level][2] - elapsed)
        self.score = max(0, 1000 - self.flips * 10 - int(elapsed) * 5 + remaining * 2)

    def run_level(self):
        grid_size, pairs, time_limit = self.levels[self.current_level]
        self.create_board(grid_size, pairs)
        self.game_over = False
        self.start_time = time.time()
        pygame.mixer.music.load(f'sounds/level{self.current_level + 1}.mp3')
        pygame.mixer.music.play(-1)
        while not self.game_over and time.time() - self.start_time < time_limit:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    self.handle_click(event.pos)
                if event.type == KEYDOWN and event.key == K_h:  # Hint
                    if not self.flipped_cards and time.time() - self.start_time < time_limit:
                        for card in self.cards:
                            if not card.flipped and not card.matched:
                                card.flip()
                                pygame.time.wait(1000)
                                card.flip()
                                break
            screen.fill((0, 0, 0))  # Dark background
            # Add starry background
            for _ in range(50):
                pygame.draw.circle(screen, (255, 255, 255), (random.randint(0, WIDTH), random.randint(0, HEIGHT)), 1)
            self.cards.draw(screen)
            self.update_score()
            score_text = pygame.font.SysFont('Arial', 20).render(f"Score: {self.score} Time Left: {int(self.levels[self.current_level][2] - (time.time() - self.start_time))}s", True, (0, 191, 255))
            screen.blit(score_text, (10, 10))
            if time.time() - self.start_time >= time_limit:
                self.game_over = True
            pygame.display.flip()
            clock.tick(FPS)
        if self.game_over and self.current_level < 2:
            pygame.mixer.Sound('sounds/levelup.mp3').play()
            self.current_level += 1
            self.run_level()
        elif self.game_over:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run_level()