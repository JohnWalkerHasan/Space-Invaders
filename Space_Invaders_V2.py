import os
import pygame
import random 
import time
pygame.font.init()

title_font = pygame.font.SysFont("comicsans", 56)

WIDTH, HEIGHT = 1366, 768
WIN = pygame.display.set_mode((WIDTH,HEIGHT))
pygame.display.set_caption("Space Invaders")

# Load Images
RED_SPACE_SHIP = pygame.image.load(os.path.join("assets","image.png"))
GREEN_SPACE_SHIP = pygame.image.load(os.path.join("assets","image1.png"))
BLUE_SPACE_SHIP = pygame.image.load(os.path.join("assets","image2.png"))

# Player ship
YELLOW_SPACE_SHIP = pygame.image.load(os.path.join("assets","pixel_ship_player.png"))

# Lasers
RED_LASER = pygame.image.load(os.path.join("assets","pixel_laser_red.png"))
GREEN_LASER = pygame.image.load(os.path.join("assets","pixel_laser_green.png"))
BLUE_LASER = pygame.image.load(os.path.join("assets","pixel_laser_blue.png"))
YELLOW_LASER = pygame.image.load(os.path.join("assets","pixel_laser_yellow.png"))

# Background
BG = pygame.transform.scale(pygame.image.load(os.path.join("assets","background-black.png")),(WIDTH, HEIGHT))

class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0) 

    def collision(self, obj):
        return collide(self, obj)    


class Ship:
    COOLDOWN= 30

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.cooldown()
        active_lasers = []
        for laser in self.lasers:
            laser.move(vel)
            if not laser.off_screen(HEIGHT) and not laser.collision(obj):
                active_lasers.append(laser)
            elif laser.collision(obj):
                obj.health -= 10
        self.lasers = active_lasers

    def cooldown(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter > 0:
            self.cool_down_counter += 1
    
    def shoot(self):
        if self.cool_down_counter == 0:
            laser =Laser(self.x, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1    

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()


class Player(Ship):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = YELLOW_SPACE_SHIP
        self.laser_img = YELLOW_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health

    def move_lasers(self, vel, objs):
        self.cooldown()
        active_lasers = []
        for laser in self.lasers:
            laser.move(vel)
            if not laser.off_screen(HEIGHT):
                collision = False
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        collision = True
                        break
                if not collision:
                    active_lasers.append(laser)
        self.lasers = active_lasers

    def draw(self, window):
        super().draw(window)
        self.healthbar(window)

    def healthbar(self, window):
        pygame.draw.rect(window, (255,0,0), (self.x,self.y + self.ship_img.get_height() +10, self.ship_img.get_width(), 10))
        pygame.draw.rect(window, (0,255,0), (self.x,self.y + self.ship_img.get_height() +10, self.ship_img.get_width() * (self.health/self.max_health), 10))

class Enemy(Ship):
    COLOR_MAP= {
                "red" : (RED_SPACE_SHIP, RED_LASER),
                "green" : (GREEN_SPACE_SHIP, GREEN_LASER),
                "blue" : (BLUE_SPACE_SHIP, BLUE_LASER)
                }

    def __init__(self, x, y, color, health=100): 
        super().__init__(x, y, health)
        self.ship_img, self.laser_img = self.COLOR_MAP[color]
        self.mask = pygame.mask.from_surface(self.ship_img)

    def move(self,vel):
        self.y += vel

    def shoot(self):
        if self.cool_down_counter == 0:
            laser =Laser(self.x - 10, self.y, self.laser_img)
            self.lasers.append(laser)
            self.cool_down_counter = 1    


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


def game_over_screen():
    run = True
    while run:
        WIN.blit(BG, (0, 0))
        title_label = title_font.render("Game Over", 1, (255, 255, 255))
        retry_label = title_font.render("Press R to Retry or Q to Quit", 1, (255, 255, 255))
        
        WIN.blit(title_label, (WIDTH/2 - title_label.get_width()/2, 260))
        WIN.blit(retry_label, (WIDTH/2 - retry_label.get_width()/2, 320))
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                elif event.key == pygame.K_q:
                    run = False
    pygame.quit()


def main():
    run=True
    FPS = 90
    paused = False
    start_ticks = pygame.time.get_ticks()  
    level = 0 
    lives = 5
    main_font = pygame.font.SysFont("comicsans", 24) 
    lost_font = pygame.font.SysFont("comicsans", 48)
    enemies = []
    wave_length = 5
    enemy_vel = 1
    
    player_vel = 9
    laser_vel = 4

    player = Player(325, 560)
    
    clock = pygame.time.Clock()
    lost = False
    lost_count = 0 

    def redraw_window():
        WIN.blit(BG, (0,0))
        # draw text
        lives_label = main_font.render(f"Lives: {lives}", 1, (255,255,255))
        level_label = main_font.render(f"Level: {level}", 1, (255,255,255))

        WIN.blit(lives_label, (10,10))
        WIN.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))

        for enemy in enemies:
            if enemy.y + enemy.get_height() > 0:
                enemy.draw(WIN) 

        player.draw(WIN)

        if lost:
            lost_label = lost_font.render("You Lost!!", 1, (255,255,255))
            WIN.blit(lost_label, (WIDTH/2 - lost_label.get_width()/2, 340 - lost_label.get_height()/2 ))

        pygame.display.update()

    while run:
        start_ticks = pygame.time.get_ticks()
        while paused:
            WIN.blit(BG, (0, 0))
            elapsed_time = (pygame.time.get_ticks() - start_ticks) / 1000
            WIN.fill((0, 0, 0))
            title_label = title_font.render(f"Paused... {elapsed_time:.2f}s", 1, (255, 255, 255))
            WIN.blit(title_label, (WIDTH / 2 - title_label.get_width() / 2, HEIGHT / 2))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN :
                    paused = False
                    start_ticks = pygame.time.get_ticks()  # Reset timer
                

        clock.tick(90)

        redraw_window()
        
        if lives <= 0 or player.health <= 0 :
            lost = True
            lost_count += 1 

        if lost:
            if lost_count > FPS * 3 :
                game_over_screen()
            else:
                continue

        if len(enemies) == 0 :
            level += 1
            wave_length += 5
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100), random.choice(["red","blue","green"]))
                enemies.append(enemy)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.x - player_vel > 0 : # left
            player.x -= player_vel
        if keys[pygame.K_RIGHT] and player.x + player_vel + player.get_width() < WIDTH: # right
            player.x += player_vel
        if keys[pygame.K_UP] and player.y - player_vel > 0 :  # up
            player.y -= player_vel                                                             # down
        if keys[pygame.K_DOWN] and player.y + player_vel + player.get_height() < HEIGHT:
            player.y += player_vel
        if keys[pygame.K_SPACE]:
            player.shoot()
        if keys[pygame.K_ESCAPE]:
            paused = True

        for enemy in enemies[:]:
            enemy.move(enemy_vel)
            enemy.move_lasers(laser_vel,player)

            if random.randrange(0, 3*60) ==1:
                enemy.shoot()

            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives-= 1
                enemies.remove(enemy) 

            player.move_lasers(-laser_vel,enemies) 

def main_menu():
    run = True   
    while run:
        WIN.blit(BG, (0,0))
        title_label = title_font.render("Press the mouse to begin...", 1, (255,255,255))
        WIN.blit(title_label, (WIDTH/2- title_label.get_width()/2, 312))

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()    

    pygame.quit()

main_menu()
