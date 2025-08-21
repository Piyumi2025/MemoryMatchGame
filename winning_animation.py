import pygame
pygame.init()
# Global variables
particles = []

# Particle class
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.color = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
        self.lifetime = random.randint(30, 60)  # Frames

# In update_loop (when setting GAME_OVER)
if len(matched_pairs) == (difficulty * difficulty) // 2:
    score = calculate_score()
    high_scores[difficulty] = min(high_scores[difficulty], score)
    game_state = GAME_OVER
    if win_sound:
        win_sound.play()
    # Generate particles
    particles.clear()
    for _ in range(100):
        particles.append(Particle(WIDTH // 2, HEIGHT // 2))

# In update_loop (during GAME_OVER, before drawing text)
new_particles = []
for p in particles:
    p.x += p.vx
    p.y += p.vy
    p.lifetime -= 1
    if p.lifetime > 0:
        new_particles.append(p)
        pygame.draw.circle(screen, p.color, (int(p.x), int(p.y)), 3)
particles = new_particles