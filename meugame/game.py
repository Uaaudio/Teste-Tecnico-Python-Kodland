import pgzrun
from pygame import Rect
import random

WIDTH, HEIGHT = 800, 600
GRAVITY, JUMP_FORCE = 0.5, -10
game_state = "menu"
music_playing = False
sound_enabled = True
score = 0
scroll_x = 0
WORLD_WIDTH = 100000

dragao_anim = [images.dragao_atacando1, images.dragao_atacando2, images.dragao_atacando3, images.dragao_atacando4]

class Cloud:
    def __init__(self):
        self.width = random.randint(80, 150)
        self.height = random.randint(30, 50)
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(50, 200)
        self.speed = random.uniform(0.5, 1.5)
        self.color = (255, 255, 255)

    def update(self):
        self.x -= self.speed
        if self.x + self.width < 0:
            self.x = WIDTH
            self.y = random.randint(50, 200)
            self.speed = random.uniform(0.5, 1.5)
            self.width = random.randint(80, 150)
            self.height = random.randint(30, 50)

    def draw(self):
        screen.draw.filled_rect(Rect(int(self.x), int(self.y), self.width, self.height), self.color)

clouds = [Cloud() for _ in range(6)]

class Player:
    def __init__(self):
        self.reset()

    def reset(self):
        self.rect = Rect(100, HEIGHT - 100, 40, 60)
        self.vel_y = 0
        self.on_ground = False
        self.anim_parado = [images.gato_parado1, images.gato_parado2, images.gato_parado3]
        self.anim_andando = [images.gato_andando1, images.gato_andando2, images.gato_andando3]
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.15
        self.facing_right = True
        self.current_anim = self.anim_parado

    def move(self):
        moving = False
        if keyboard.d:
            self.rect.x += 5
            self.facing_right = True
            moving = True
        if keyboard.a:
            self.rect.x -= 5
            self.facing_right = False
            moving = True
        if keyboard.space and self.on_ground:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            if sound_enabled:
                sounds.player_jump.play()
        return moving

    def apply_gravity(self):
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

    def check_collision(self, platforms):
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p) and self.vel_y > 0:
                self.rect.bottom = p.top
                self.vel_y = 0
                self.on_ground = True

    def update(self, platforms):
        moving = self.move()
        self.apply_gravity()
        self.check_collision(platforms)
        self.anim_timer += self.anim_speed
        if self.anim_timer >= 1:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 3
        self.current_anim = self.anim_andando if moving else self.anim_parado

    def draw(self, offset_x):
        r = self.rect.copy()
        r.x -= offset_x
        img = self.current_anim[self.anim_frame]
        if self.facing_right:
            screen.blit(img, (r.x, r.y))
        else:
            screen.blit(img, (r.x + r.width, r.y), transform="flipx")

class Enemy:
    def __init__(self, x, y, flying=False):
        self.flying = flying
        if self.flying:
            self.rect = Rect(x, y, 100, 40)
            self.speed = -1.5
            self.anim = dragao_anim
        else:
            self.rect = Rect(x, base_platform.top - 50, 30, 50)
            self.speed = -1
            self.anim = [images.cavaleirowalk1, images.cavaleirowalk2, images.cavaleirowalk3, images.cavaleirowalk4]

        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.15

    def update(self):
        self.rect.x += self.speed
        if not self.flying:
            self.rect.bottom = base_platform.top
        self.anim_timer += self.anim_speed
        if self.anim_timer >= 1:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % len(self.anim)

    def draw(self, offset_x):
        r = self.rect.copy()
        r.x -= offset_x
        screen.blit(self.anim[self.anim_frame], (r.x, r.y))

    def collides(self, player_rect):
        return self.rect.colliderect(player_rect)

class MonedaD:
    def __init__(self, x, y):
        self.rect = Rect(x, y, 20, 20)
        self.collected = False
        self.anim_frames = [images.moeda]
        self.anim_frame = 0
        self.anim_timer = 0
        self.anim_speed = 0.2

    def update(self):
        if not self.collected:
            self.anim_timer += self.anim_speed
            if self.anim_timer >= 1:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % len(self.anim_frames)

    def draw(self, offset_x):
        if not self.collected:
            r = self.rect.copy()
            r.x -= offset_x
            screen.blit(self.anim_frames[self.anim_frame], (r.x, r.y))

    def collect(self, player_rect):
        if not self.collected and self.rect.colliderect(player_rect):
            self.collected = True
            if sound_enabled:
                sounds.sfx_coin.play()
            return True
        return False

base_platform = Rect(0, HEIGHT - 40, WORLD_WIDTH, 40)
dynamic_platforms = []
enemies = []
monedasD = []
player = Player()

menu_buttons = {
    "Start": Rect(WIDTH // 2 - 75, 200, 150, 50),
    "Music": Rect(WIDTH // 2 - 75, 280, 150, 50),
    "Sound": Rect(WIDTH // 2 - 75, 360, 150, 50),
    "Exit": Rect(WIDTH // 2 - 75, 440, 150, 50),
}

PLATFORM_WIDTH = 100
PLATFORM_HEIGHT = 20
PLATFORM_GAP_MIN = 150
PLATFORM_GAP_MAX = 300
last_platform_x = 0

def generate_platforms_and_objects(player_x):
    global last_platform_x
    while last_platform_x < player_x + WIDTH * 2:
        gap = random.randint(PLATFORM_GAP_MIN, PLATFORM_GAP_MAX)
        plat_x = last_platform_x + gap
        plat_y = random.randint(HEIGHT - 300, HEIGHT - 100)
        plat = Rect(plat_x, plat_y, PLATFORM_WIDTH, PLATFORM_HEIGHT)
        dynamic_platforms.append(plat)

        if random.random() < 0.5:
            enemies.append(Enemy(plat_x, 0, flying=False))
        if random.random() < 0.5:
            fly_x = plat_x + random.randint(0, 100)
            fly_y = random.randint(HEIGHT - 400, HEIGHT - 300)
            enemies.append(Enemy(fly_x, fly_y, flying=True))
        if random.random() < 0.8:
            for i in range(random.randint(1, 3)):
                monedasD.append(MonedaD(plat_x + i * 25, plat_y - 25))

        last_platform_x = plat_x

def update():
    global game_state, score, scroll_x
    if game_state != "playing":
        return

    generate_platforms_and_objects(player.rect.x)

    platforms = [base_platform] + [p for p in dynamic_platforms if abs(p.x - player.rect.x) < WIDTH]
    player.update(platforms)

    scroll_x = max(0, min(player.rect.x - WIDTH // 2, WORLD_WIDTH - WIDTH))

    for e in enemies:
        if abs(e.rect.x - player.rect.x) < WIDTH:
            e.update()
            if e.collides(player.rect):
                game_state = "game_over"

    for m in monedasD:
        if abs(m.rect.x - player.rect.x) < WIDTH:
            m.update()
            if m.collect(player.rect):
                score += 1

    for cloud in clouds:
        cloud.update()

def draw():
    screen.clear()
    if game_state == "menu":
        screen.fill((25, 50, 100))
        screen.draw.text("Cat Rush\nBy Wendell Jesus", center=(WIDTH // 2, 100), fontsize=50, color="white")
        for label, rect in menu_buttons.items():
            screen.draw.filled_rect(rect, "white")
            screen.draw.text(label, center=rect.center, fontsize=30, color="black")
        sound_text = "Sound: ON" if sound_enabled else "Sound: OFF"
        sound_color = "green" if sound_enabled else "red"
        screen.draw.text(sound_text, center=menu_buttons["Sound"].center, fontsize=25, color=sound_color)
        for cloud in clouds:
            cloud.draw()

    elif game_state == "playing":
        screen.fill((135, 206, 235))
        for cloud in clouds:
            cloud.draw()

        block_img = images.block_green
        block_w = block_img.get_width()

        x = base_platform.x - scroll_x
        while x < base_platform.right - scroll_x:
            screen.blit("block_green", (x, base_platform.y))
            x += block_w

        for plat in dynamic_platforms:
            if abs(plat.x - player.rect.x) < WIDTH:
                x = plat.x - scroll_x
                while x < plat.right - scroll_x:
                    screen.blit("block_green", (x, plat.y))
                    x += block_w

        player.draw(scroll_x)

        for e in enemies:
            if abs(e.rect.x - player.rect.x) < WIDTH:
                e.draw(scroll_x)

        for m in monedasD:
            if abs(m.rect.x - player.rect.x) < WIDTH:
                m.draw(scroll_x)

        screen.draw.text(f"Score: {score}", (10, 10), fontsize=30, color="black")

    elif game_state == "game_over":
        screen.fill((100, 0, 0))
        screen.draw.text("Fim De Jogo", center=(WIDTH // 2, HEIGHT // 2 - 50), fontsize=60, color="white")
        screen.draw.text(f"Pontuação Final: {score}", center=(WIDTH // 2, HEIGHT // 2 + 10), fontsize=40, color="white")
        screen.draw.text("Click para ir para o menu", center=(WIDTH // 2, HEIGHT // 2 + 70), fontsize=30, color="white")

def on_mouse_down(pos):
    global game_state, score, scroll_x, music_playing, sound_enabled, dynamic_platforms, enemies, monedasD, last_platform_x
    if game_state == "menu":
        if menu_buttons["Start"].collidepoint(pos):
            game_state = "playing"
            score = 0
            scroll_x = 0
            dynamic_platforms.clear()
            enemies.clear()
            monedasD.clear()
            last_platform_x = 0
            player.reset()
            if music_playing:
                music.stop()
                music_playing = False
        elif menu_buttons["Music"].collidepoint(pos):
            if not music_playing and sound_enabled:
                music.play("menu_music")
                music_playing = True
            else:
                music.stop()
                music_playing = False
        elif menu_buttons["Sound"].collidepoint(pos):
            sound_enabled = not sound_enabled
            if not sound_enabled:
                music.stop()
                music_playing = False
        elif menu_buttons["Exit"].collidepoint(pos):
            exit()
    elif game_state == "game_over":
        game_state = "menu"

pgzrun.go()
