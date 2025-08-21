import pygame
pygame.init()
# Update Card class
class Card:
    def __init__(self, x, y, image_index):
        self.rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        self.image_index = image_index
        self.flipped = False
        self.matched = False
        self.flip_progress = 0
        self.hover = False  # New: Hover state

# In update_loop (inside PLAYING state, after event handling)
mouse_pos = pygame.mouse.get_pos()
for card in cards:
    if card.rect.collidepoint(mouse_pos) and not card.flipped and not card.matched:
        card.hover = True
    else:
        card.hover = False

# In card drawing loop (modify the blit section)
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
            # Add hover effect: Draw a yellow border
            pygame.draw.rect(screen, (255, 255, 0), card.rect, 2)
            # Optional: Slight scale on hover
            img = pygame.transform.scale(img, (int(CARD_WIDTH * 1.05), int(CARD_HEIGHT * 1.05)))
            x_offset = (CARD_WIDTH - img.get_width()) // 2
        screen.blit(img, (card.rect.x + x_offset, card.rect.y))