import pygame
pygame.init()
# Global variable
theme = "Image"  # Default

# Update draw_menu
def draw_menu():
    screen.fill(BLACK)
    title = font.render("Memory Match Game", True, WHITE)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 50))
    
    buttons = [
        Button(WIDTH // 2 - 100, 200, 200, 50, "Easy (4x4)", lambda: set_difficulty(4)),
        Button(WIDTH // 2 - 100, 270, 200, 50, "Medium (6x6)", lambda: set_difficulty(6)),
        Button(WIDTH // 2 - 100, 340, 200, 50, "Hard (8x8)", lambda: set_difficulty(8)),
        Button(WIDTH // 2 - 100, 410, 200, 50, f"Theme: {theme}", toggle_theme)  # New button
    ]
    
    for button in buttons:
        pygame.draw.rect(screen, BLUE, button.rect)
        text = small_font.render(button.text, True, WHITE)
        screen.blit(text, (button.rect.x + 50, button.rect.y + 15))
    
    return buttons

# New function
def toggle_theme():
    global theme
    theme = "Color" if theme == "Image" else "Image"
    # Note: Call setup() if in game, but for simplicity, it applies on next start

# In setup (before selecting images)
card_images.clear()
if theme == "Image":
    try:
        for i in range(1, 33):
            img = pygame.image.load(f"images/card_{i}.png")
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