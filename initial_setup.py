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

# Card settings
CARD_WIDTH, CARD_HEIGHT = 100, 100
CARD_MARGIN = 10
cards = []
card_images = []
card_back = None
flipped_cards = []
matched_pairs = []

# Font
font = pygame.font.SysFont("Arial", 30)
small_font = pygame.font.SysFont("Arial", 24)