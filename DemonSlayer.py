import pygame as pg
import time
import os

pg.init()

BackGround = pg.image.load("./assets/bg/background.png")
Screen_W, Screen_H = BackGround.get_width(), BackGround.get_height()

screen = pg.display.set_mode((Screen_W, Screen_H))
pg.display.set_caption('Adventurer vs Demon')

BackGround = pg.transform.scale(BackGround, (Screen_W, Screen_H))

# Constant
FPS = 60

font = pg.font.SysFont("arial", 52)  # Large font for the title
medium_font = pg.font.SysFont("arial", 36)  # Medium font for the start prompt
small_font = pg.font.SysFont("arial", 28)  # Small font for instructions

# Define a Clock
clock = pg.time.Clock()

def start_screen():
    waiting = True
    while waiting:
        # Draw background
        screen.blit(BackGround, (0, 0))

        # Render title text
        title_text = font.render("Demon Slayer", True, (255, 255, 255))
        screen.blit(title_text, (Screen_W // 2 - title_text.get_width() // 2, Screen_H // 3))

        # Render start prompt text
        prompt_text = medium_font.render("Press Space to Start", True, (255, 255, 255))
        screen.blit(prompt_text, (Screen_W // 2 - prompt_text.get_width() // 2, Screen_H // 2))

        # Render movement instructions
        move_text = small_font.render("Use A to move LEFT and D to move RIGHT", True, (255, 255, 255))
        screen.blit(move_text, (Screen_W // 2 - move_text.get_width() // 2, Screen_H - 120))

        # Render jump instruction
        jump_text = small_font.render("Use SPACE to jump", True, (255, 255, 255))
        screen.blit(jump_text, (Screen_W // 2 - jump_text.get_width() // 2, Screen_H - 80))

        # Render attack instruction
        attack_text = small_font.render("Press J to ATTACK", True, (255, 255, 255))
        screen.blit(attack_text, (Screen_W // 2 - attack_text.get_width() // 2, Screen_H - 40))

        # Update the display
        pg.display.flip()

        # Event handling for starting the game
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                quit()
            elif event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                waiting = False  # Exit the start screen loop

# Adventurer and Demon Stats
adventurer_health = 10
demon_health = 25

#loading music and sounds
pg.mixer.music.load("./assets/Sound/Music.mp3")
enemyAttackSound = pg.mixer.Sound("./assets/Sound/Enemy_Attack.mp3")
enemyDeathSound = pg.mixer.Sound("./assets/Sound/Enemy_Death.mp3")
loseSound = pg.mixer.Sound("./assets/Sound/Failure.mp3")
victorySound = pg.mixer.Sound("./assets/Sound/Victory.mp3")
playerAttackSound = pg.mixer.Sound("./assets/Sound/Player_Attack.mp3")
pg.mixer.music.play(loops=-1)
stop = 1


# Adventurer Class
class Adventurer(pg.sprite.Sprite):
    def __init__(self, x, y, scale, speed):
        super().__init__()
        self.character_type = 'Player'
        self.speed = speed
        self.scale = scale
        self.alive = True
        self.death_animation_complete = False
        self.rect = None
        self.direction = 1
        self.flip = False
        self.index = 0
        self.action = 'Idle'
        self.previous_action = 'Idle'
        self.update_timer = pg.time.get_ticks()
        self.jump = False
        self.vel_y = 0
        self.in_air = False
        self.attacking = False
        self.attack_combo_stage = 0
        self.attack_timer = 0
        self.hit_registered = False

        # Initialize the animation list
        self.animation_list = {
            'Idle': self.load_animation('Idle', 4),
            'move': self.load_animation('move', 6),
            'jump': self.load_animation('jump', 4),
            'air-attack': self.load_animation('air-attack', 4),
            'attack1': self.load_animation('attack1', 5),
            'attack2': self.load_animation('attack2', 6),
            'attack3': self.load_animation('attack3', 6),
            'fall': self.load_animation('fall', 2),
            'hurt': self.load_animation('hurt', 3),
            'death': self.load_animation('death', 7)
        }

        # Set initial image and rectangle
        self.image = self.animation_list[self.action][self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def load_animation(self, move, frame_count):
        animation = []
        for i in range(frame_count):
            image_path = f"./assets/{self.character_type}/{move}/{i}.png"
            if os.path.exists(image_path):
                img = pg.image.load(image_path).convert_alpha()
                img = pg.transform.scale(img, (int(img.get_width() * self.scale), int(img.get_height() * self.scale)))
                animation.append(img)
            else:
                print(f"Error: Image {image_path} not found.")
        return animation

    def update_animation(self):
        Animation_cooldown = 100
        if self.index >= len(self.animation_list[self.action]):
            if self.action == 'death':
                self.death_animation_complete = True
                self.index = len(self.animation_list[self.action]) - 1
            elif self.attacking:
                self.attacking = False
                self.hit_registered = False  # Reset hit registration
                if not self.in_air:
                    self.attack_combo_stage = (self.attack_combo_stage + 1) % 3
                self.action = 'Idle'
                self.index = 0
            else:
                self.index = 0

        self.image = self.animation_list[self.action][self.index]

        if pg.time.get_ticks() - self.update_timer > Animation_cooldown:
            self.update_timer = pg.time.get_ticks()
            self.index += 1

    def move(self, move_left, move_right):
        dx = 0
        if move_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if move_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # Prevent moving off-screen
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        elif self.rect.right + dx > Screen_W:
            dx = Screen_W - self.rect.right

        self.rect.x += dx

        if self.jump:
            self.vel_y = -15
            self.jump = False
            self.in_air = True

        self.vel_y += 1
        if self.vel_y > 10:
            self.vel_y = 10
        dy = self.vel_y

        if self.rect.bottom + dy > Screen_H:
            dy = Screen_H - self.rect.bottom
            self.in_air = False
            self.vel_y = 0

        self.rect.y += dy

        # Update action based on state
        if not self.attacking:
            if self.in_air and self.vel_y < 0:
                self.action = 'jump'
            elif self.in_air and self.vel_y >= 0:
                self.action = 'fall'
            elif dx != 0:
                self.action = 'move'
            else:
                self.action = 'Idle'

        if self.action != self.previous_action:
            self.index = 0
            self.previous_action = self.action
        self.rect.x += dx

    def draw(self):
        screen.blit(pg.transform.flip(self.image, self.flip, False), self.rect)

    #def draw_hitbox(self):
        #pg.draw.rect(screen, (255, 0, 0), self.rect, 2)

    def attack(self):
        if not self.attacking:
            self.attacking = True
            self.attack_timer = pg.time.get_ticks()
            self.hit_registered = False
            if self.in_air:
                self.action = 'air-attack'
            else:
                if self.attack_combo_stage == 0:
                    self.action = 'attack1'
                elif self.attack_combo_stage == 1:
                    self.action = 'attack2'
                else:
                    self.action = 'attack3'
            playerAttackSound.play()
            self.index = 0

    def get_attack_hitbox(self):
        attack_rect = self.rect.copy()
        if self.flip:
            attack_rect.left = self.rect.left - self.rect.width // 2
        else:
            attack_rect.right = self.rect.right + self.rect.width // 2
        return attack_rect


# Demon Class
class Demon(pg.sprite.Sprite):
    def __init__(self, x, y, scale, speed):
        super().__init__()
        self.character_type = 'Enemy'
        self.speed = speed
        self.scale = scale
        self.alive = True
        self.death_animation_complete = False
        self.rect = None
        self.direction = 1
        self.flip = False
        self.index = 0
        self.action = 'Idle'
        self.update_timer = pg.time.get_ticks()

        # Initialize the animation list
        self.animation_list = {
            'Idle': self.load_animation('Idle', 6),
            'move': self.load_animation('move', 11),
            'attack': self.load_animation('attack', 15),
            'hurt': self.load_animation('hurt', 5),
            'death': self.load_animation('death', 22)
        }

        # Set initial image and rectangle
        self.image = self.animation_list[self.action][self.index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.create_hitbox()

    def load_animation(self, move, frame_count):
        animation = []
        for i in range(frame_count):
            image_path = f"./assets/{self.character_type}/{move}/{i}.png"
            if os.path.exists(image_path):
                img = pg.image.load(image_path).convert_alpha()
                img = pg.transform.scale(img, (int(img.get_width() * self.scale), int(img.get_height() * self.scale)))
                animation.append(img)
            else:
                print(f"Error: Image {image_path} not found.")
        return animation

    def update_animation(self):
        animation_speed = 100
        animation_frames = len(self.animation_list[self.action])
        current_time = pg.time.get_ticks()
        if current_time - self.update_timer > animation_speed:
            self.update_timer = current_time
            self.index += 1
            if self.index >= animation_frames:
                if self.action == 'death':
                    self.death_animation_complete = True
                    self.index = animation_frames - 1  # Stay on last frame
                elif self.action == 'attack':
                    self.index = 0  # Reset index for attack animation
                    self.action = 'Idle'  # Return to Idle after attack
                else:
                    self.index = 0  # Loop back to first frame
            self.image = self.animation_list[self.action][self.index]


    def create_hitbox(self):
        hitbox_width = int(self.rect.width * 0.5)
        hitbox_height = int(self.rect.height * 0.8)
        hitbox_x = self.rect.centerx - hitbox_width // 2
        hitbox_y = self.rect.bottom - hitbox_height
        self.hitbox = pg.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)


    def draw(self):
        self.create_hitbox()
        flipped_image = pg.transform.flip(self.image, self.flip, False)
        screen.blit(flipped_image, self.rect)

    #def draw_hitbox(self):
        #pg.draw.rect(screen, (255, 0, 0), self.hitbox, 2)


# Function to handle adventurer's attack
def handle_attack():
    global demon_health
    if adventurer.attacking and not adventurer.hit_registered:
        if adventurer.rect.colliderect(demon.rect):
            print("Hit detected!")  # Debug print
            adventurer.hit_registered = True
            damage = 1  # Base damage
            if adventurer.action == 'attack3':
                damage = 3  # Increased damage for the third attack in combo
            demon_health -= damage
            if demon_health <= 0:
                demon.alive = False
                demon.action = 'death'
                demon.index = 0


# Health Bar Drawing
def draw_health_bar(health, max_health, x, y, width, height, color):
    ratio = health / max_health
    pg.draw.rect(screen, (255, 0, 0), (x, y, width, height))  # Background
    pg.draw.rect(screen, color, (x, y, width * ratio, height))  # Health bar


# Demon AI
def demon_ai():
    global adventurer_health
    if demon.alive and adventurer.alive:
        if demon.action != 'attack':
            distance = abs(demon.rect.centerx - adventurer.rect.centerx)
            if distance > 100:
                if demon.rect.centerx < adventurer.rect.centerx:
                    demon.direction = 1
                    demon.flip = True  # Demon is moving right, so don't flip
                else:
                    demon.direction = -1
                    demon.flip = False  # Demon is moving left, so flip

                # Calculate new position
                new_x = demon.rect.x + demon.speed * demon.direction

                # Prevent moving off-screen
                if new_x < 0:
                    new_x = 0
                elif new_x + demon.rect.width > Screen_W:
                    new_x = Screen_W - demon.rect.width

                demon.rect.x = new_x
                demon.action = 'move'
            else:
                demon.action = 'attack'
                demon.index = 0  # Reset the animation index when starting the attack

        if demon.action == 'attack':
            if demon.index == 9:  # The specific frame for the attack hit (10th frame, counting from 0)
                attack_rect = demon.hitbox.copy()
                attack_rect.width = attack_rect.width // 2
                if demon.flip:  # If demon is facing right
                    attack_rect.left = demon.hitbox.centerx
                else:  # If demon is facing left
                    attack_rect.right = demon.hitbox.centerx

                if attack_rect.colliderect(adventurer.rect):
                    adventurer_health -= 1
                    if adventurer_health <= 0:
                        adventurer.alive = False
                        adventurer.action = 'death'
                        adventurer.index = 0

            # Check if the attack animation is complete
            if demon.index >= len(demon.animation_list['attack']) - 1:
                demon.action = 'Idle'  # Reset to Idle after attack animation completes

            # Plays attack sound at end of animation
            if demon.index == 10:
                enemyAttackSound.play()

def check_game_over():
    global run
    if not adventurer.alive:
        pg.mixer.music.stop()
        if adventurer.death_animation_complete:
            game_over_screen("Adventurer Died! Press 1 to Restart or 2 to Quit.")
    elif not demon.alive and not demon.death_animation_complete:
        pg.mixer.music.stop()
        enemyDeathSound.play(0, 100)
    elif not demon.alive and demon.death_animation_complete:
        victorySound.play()
        game_over_screen("Demon Defeated! Press 1 to Restart or 2 to Quit.")


def game_over_screen(message):
    global run
    font = pg.font.SysFont("arial", 36)
    text = font.render(message, True, (255, 255, 255))
    screen.blit(text, (Screen_W // 2 - text.get_width() // 2, Screen_H // 2))
    pg.display.update()
    time.sleep(1)
    waiting = True
    while waiting:
        for event in pg.event.get():
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_1:
                    restart_game()
                    waiting = False
                elif event.key == pg.K_2:
                    run = False
                    waiting = False

# Restart game function
def restart_game():
    global adventurer_health, demon_health, adventurer, demon

    # Reset health
    adventurer_health = 8
    demon_health = 25

    # Reset adventurer
    adventurer.alive = True
    adventurer.death_animation_complete = False
    adventurer.attack_combo_stage = 0
    adventurer.index = 0
    adventurer.action = 'Idle'
    adventurer.rect.x = 100
    adventurer.rect.bottom = Screen_H - 50  # Set bottom of adventurer to 10 pixels above screen bottom

    # Reset demon
    demon.alive = True
    demon.death_animation_complete = False
    demon.index = 0
    demon.action = 'Idle'
    demon.rect.x = 800
    demon.rect.bottom = Screen_H - 50  # Set bottom of demon to 10 pixels above screen bottom

    pg.mixer.music.play(loops=-1)


# Create instances
adventurer = Adventurer(100, Screen_H - 150, 2, 5)
demon = Demon(800, Screen_H - 150, 2, 3)

# Adjust the initial positions
adventurer.rect.bottom = Screen_H - 10
demon.rect.bottom = Screen_H - 10

start_screen()

# Main game loop
run = True
while run:
    clock.tick(FPS)
    screen.blit(BackGround, (0, 0))

    # Event handling
    for event in pg.event.get():
        if event.type == pg.QUIT:
            run = False

    if adventurer.alive:
        keys = pg.key.get_pressed()
        move_left = keys[pg.K_a]
        move_right = keys[pg.K_d]

        # Jump action
        if not adventurer.in_air:
            if keys[pg.K_SPACE]:
                adventurer.jump = True

        # Attack actions
        if keys[pg.K_j] and not adventurer.attacking:
            adventurer.attack()

        # Update and draw the adventurer
        adventurer.move(move_left, move_right)

    adventurer.update_animation()
    current_time = pg.time.get_ticks()
    if adventurer.attacking and current_time - adventurer.attack_timer > 500:  # 500ms attack duration
        adventurer.attacking = False
        adventurer.hit_registered = False
    adventurer.draw()
    if adventurer.attacking:
        attack_hitbox = adventurer.get_attack_hitbox()
        pg.draw.rect(screen, (255, 0, 0), attack_hitbox, 2)  # Draw attack hitbox in red
    adventurer.draw_hitbox()
    if adventurer_health >= 1:
        stop = 1
    if adventurer_health <= 0 and stop == 1:
        loseSound.play()
        stop -=1

    # Update and draw the demon
    demon_ai()
    demon.update_animation()
    demon.draw()
    #demon.draw_hitbox()

    if adventurer.alive:
        handle_attack()

    draw_health_bar(adventurer_health, 8, 10, 10, 200, 20, (0, 255, 0)) # Adventurer health
    draw_health_bar(demon_health, 25, Screen_W - 210, 10, 200, 20, (0, 255, 0)) # Demon health

    check_game_over()

    pg.display.update()

pg.quit()
