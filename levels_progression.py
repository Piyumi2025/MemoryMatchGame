import pygame
pygame.init()
# In update_loop (during GAME_OVER, on R key press)
keys = pygame.key.get_pressed()
if keys[pygame.K_r] and game_state == GAME_OVER:
    # Progress to next level
    if difficulty == 4:
        difficulty = 6
    elif difficulty == 6:
        difficulty = 8
    else:
        difficulty = 4  # Loop back
    setup()