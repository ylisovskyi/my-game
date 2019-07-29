import pygame
import re
import os
import time

WIDTH = 800
HEIGHT = 800
sizes = [WIDTH, HEIGHT]


# Load images
bg = pygame.image.load(os.path.join('media', 'bg.jpg'))
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))
char = pygame.image.load(os.path.join('media', 'standing.png'))

# Initialisation
pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE)
pygame.display.set_caption('First game')
clock = pygame.time.Clock()

# Load sounds
bullet_sound = pygame.mixer.Sound(os.path.join('media', 'bullet.wav'))
hit_sound = pygame.mixer.Sound(os.path.join('media', 'hit.wav'))
music = pygame.mixer.music.load(os.path.join('media', 'music.mp3'))

pygame.mixer.music.play(-1)


def load_media_by_pattern(pattern):
    output_list = []
    for file in os.listdir('media'):
        if re.match(pattern, file):
            output_list.append(pygame.image.load(os.path.join('media', file)))
    return output_list


def redraw():
    global goblins, goblin_spawn_clock, level, goblin_counter, WIDTH, HEIGHT
    win.blit(pygame.transform.scale(bg, (sizes[0], sizes[1])), (0, 0))
    text = font.render('Score: {}'.format(score), 1, (0, 0, 0))
    win.blit(text, (WIDTH * 0.75, 10))
    character.draw(win)
    for gob in goblins:
        gob.draw(win)
    if (time.time() - goblin_spawn_clock) // level > 1:
        goblins.append(Enemy(0, HEIGHT * 0.9, 64, 64, WIDTH - 50))
        goblin_spawn_clock = time.time()
        goblin_counter += 1
        if goblin_counter % 5 == 0 and level != 0:
            level -= 1
    for bul in bullets:
        bul.draw(win)
    pygame.display.update()


class Person(object):
    def __init__(self, x, y, width, height, end=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.end = end
        self.velocity = 10
        self.left = False
        self.right = False
        self.walk_count = 0
        self.standing = True
        self.walk_right = None
        self.walk_left = None
        self.hit_box = (self.x + 17, self.y + 11, 28, 60)
        self.health = None
        self.start_health = self.health

    def draw(self, window):
        self.hit_box = (self.x + 17, self.y + 11, 28, 60)
        pygame.draw.rect(window, (255, 0, 0), (self.hit_box[0], self.hit_box[1] - 20, 50, 10))
        pygame.draw.rect(
            window,
            (0, 128, 0),
            (self.hit_box[0], self.hit_box[1] - 20, self.health / self.start_health * 50, 10)
        )

    def move_right(self):
        if self.x < WIDTH - self.width - self.velocity:
            self.x += self.velocity
            self.left = False
            self.right = True
            self.standing = False

    def move_left(self):
        if self.x > self.velocity:
            self.x -= self.velocity
            self.left = True
            self.right = False
            self.standing = False

    def hit(self):
        hit_sound.play()
        if self.health > 10:
            self.health -= 10
            return 1
        else:
            return -1


class Player(Person):
    def __init__(self, x, y, width, height):
        super(Player, self).__init__(x, y, width, height)
        self.is_jump = False
        self.jump_count = 10
        self.walk_right = load_media_by_pattern(r'^R\d\.png$')
        self.walk_left = load_media_by_pattern(r'^L\d\.png$')
        self.hit_box = (self.x + 17, self.y + 11, 28, 60)
        self.health = 100
        self.start_health = 100

    def draw(self, window):
        super(Player, self).draw(window)
        side = self.walk_left if self.left else self.walk_right if self.right else [char]
        if self.walk_count + 1 >= 27:
            self.walk_count = 0

        if not self.standing:
            window.blit(side[self.walk_count // 3], (self.x, self.y))
            self.walk_count += 1
        else:
            window.blit(side[0], (self.x, self.y))

    def set_standing(self):
        self.walk_count = 0
        self.standing = True

    def prepare_jump(self):
        self.is_jump = True
        self.right = False
        self.left = False
        self.walk_count = 0

    def jump(self):
        if self.jump_count >= -10:
            self.y -= (self.jump_count ** 2) * (-0.5 if self.jump_count < 0 else 0.5)
            self.jump_count -= 1
        else:
            self.is_jump = False
            self.jump_count = 10

    def hit(self):
        res = super(Player, self).hit()
        if res < 0:
            global score
            score -= 5
            self.__init__(WIDTH * 0.6, HEIGHT * 0.9, self.width, self.height)
            font1 = pygame.font.SysFont('comicsans', 100)
            text = font1.render('-5', 1, (255, 0, 0))
            win.blit(text, (WIDTH / 2 - (text.get_width() / 2), HEIGHT * 0.45))
            pygame.display.update()
            for i in range(0, 300, 10):
                pygame.time.delay(10)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()


class Projectile(object):
    def __init__(self, x, y, radius, color, facing):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.facing = facing
        self.velocity = 12 * facing

    def draw(self, window):
        pygame.draw.circle(window, self.color, (self.x, self.y), self.radius)


class Enemy(Person):

    def __init__(self, x, y, width, height, end):
        super(Enemy, self).__init__(x, y, width, height, end)
        self.velocity = 3
        self.path = [self.x, self.end]
        self.walk_right = load_media_by_pattern(r'^R\d+E\.png$')
        self.walk_left = load_media_by_pattern(r'^L\d+E\.png$')
        self.health = 50
        self.start_health = 50
        self.player_hit = False

    def draw(self, window):
        super(Enemy, self).draw(window)
        self.move()
        side = self.walk_right if self.velocity > 0 else self.walk_left
        if self.walk_count + 1 >= 33:
            self.walk_count = 0

        window.blit(side[self.walk_count // 3], (self.x, self.y))
        self.walk_count += 1

    def move(self):
        if self.velocity > 0:
            if self.x + self.velocity < WIDTH - 50:
                self.x += self.velocity
            else:
                self.velocity *= -1
                self.walk_count = 0
        else:
            if self.x - self.velocity > self.path[0]:
                self.x += self.velocity
            else:
                self.velocity *= -1
                self.walk_count = 0


font = pygame.font.SysFont('comicsans', 30, True)
character = Player(WIDTH * 0.6, HEIGHT * 0.9, 64, 64)
score = 0
shoot_loop = 0
bullets = []
goblins = [Enemy(0, HEIGHT * 0.9, 64, 64, WIDTH - 50)]
run = True
goblin_spawn_clock = time.time()
goblin_counter = 1
level = 5

while run:

    clock.tick(30)  # 30 FPS

    # Goblins collision with player
    for goblin in goblins:
        if (
                goblin and
                character.hit_box[1] < goblin.hit_box[1] + goblin.hit_box[3] and
                character.hit_box[1] + character.hit_box[3] > goblin.hit_box[1] and
                character.hit_box[0] + character.hit_box[2] > goblin.hit_box[0] and
                character.hit_box[0] < goblin.hit_box[0] + goblin.hit_box[2]
        ):
            if not goblin.player_hit:
                goblin.player_hit = True
                character.hit()
        else:
            goblin.player_hit = False

    # Non-spamming shooting
    if shoot_loop > 0:
        shoot_loop += 1
    if shoot_loop > 10:
        shoot_loop = 0

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.VIDEORESIZE:
            sizes[0] = event.dict['size'][0]
            sizes[1] = event.dict['size'][1]

    # Moving/destroying bullets
    for bullet in bullets:
        for goblin in goblins:
            if (
                    goblin and
                    bullet.y - bullet.radius < goblin.hit_box[1] + goblin.hit_box[3] and
                    bullet.y + bullet.radius > goblin.hit_box[1] and
                    bullet.x + bullet.radius > goblin.hit_box[0] and
                    bullet.x - bullet.radius < goblin.hit_box[0] + goblin.hit_box[2]
            ):
                # goblin = None
                if goblin.hit() < 0:
                    goblins.pop(goblins.index(goblin))
                bullets.pop(bullets.index(bullet))
                score += 1

        if 0 < bullet.x < WIDTH:
            bullet.x += bullet.velocity
        else:
            bullets.pop(bullets.index(bullet))

    keys = pygame.key.get_pressed()

    # Shooting
    if keys[pygame.K_SPACE] and shoot_loop == 0:
        bullet_sound.play()
        if len(bullets) < 5:
            bullets.append(Projectile(
                x=round(character.x + character.width // 2),
                y=round(character.y + character.height // 2),
                radius=6,
                color=(0, 0, 0),
                facing=-1 if character.left else 1
            ))

        shoot_loop = 1

    # Go left
    if keys[pygame.K_LEFT]:
        character.move_left()

    # Go right
    elif keys[pygame.K_RIGHT]:
        character.move_right()

    # Stand still
    else:
        character.set_standing()

    # Jumping
    if not character.is_jump:
        if keys[pygame.K_UP]:
            character.prepare_jump()

    else:
        character.jump()

    redraw()

pygame.quit()
