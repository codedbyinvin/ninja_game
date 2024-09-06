import sys
import pygame
import random
import math
import os

from scripts.entities  import PhysicsEntity, Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.utils import load_image, load_images, Animation
from scripts.spark import Spark
from scripts.particles import Particle


class Game:
    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            'grass' : load_images('tiles/grass'),
            'stone' : load_images('tiles/stone'),
            'decor' : load_images('tiles/decor'),
            'large_decor' : load_images('tiles/large_decor'),
            'player': load_image('entities/player.png'),
            'background' : load_image('background.png'),
            'clouds' : load_images('clouds'),
            'gun' : load_image('gun.png'),
            'projectile' : load_image('projectile.png'),
            'enemy/idle' : Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run' : Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle' : Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run' : Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump' : Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wallslide': Animation(load_images('entities/player/wall_slide')),
            'particles/leaf' : Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particles/particle' : Animation(load_images('particles/particle'), img_dur=6, loop=False)
        
        }

        self.sfx = {
            'jump' : pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash' : pygame.mixer.Sound('data/sfx/dash.wav'),
            'shoot' : pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience' : pygame.mixer.Sound('data/sfx/ambience.wav'),
            'hit' : pygame.mixer.Sound('data/sfx/hit.wav')
        }

        self.sfx['ambience'].set_volume(0)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)


        self.clouds = Clouds(self.assets['clouds'], count = 8)

        self.player = Player(self, (50, 50), (8,15))
        
        self.tilemap = Tilemap(self,tile_size=16)

        self.level = 0

        self.load_level(self.level)

        self.screen_shake = 0

        
    def load_level(self, map_id = 0):

        try:
            self.tilemap.load('data/maps/'+str(map_id)+'.json')
        except FileNotFoundError:
            print("Map not found !")

        self.leaf_spawners_trees = []
        for tree  in self.tilemap.extract(([('large_decor',2)]),keep= True):
            self.leaf_spawners_trees.append(pygame.Rect(tree['pos'][0] + 4 , tree['pos'][1] + 4, 23, 13))
        
        self.leaf_spawners_bushes = []
        for bush  in self.tilemap.extract(([('large_decor',1)]),keep= True):
            self.leaf_spawners_bushes.append(pygame.Rect(bush['pos'][0] + 3 , bush['pos'][1] + 3, 19, 9))

        self.enemies = []
        for spawner in self.tilemap.extract([('spawners',0),('spawners',1)],keep=False):
            if spawner['variant'] == 0:
                self.player.air_time = 0
                self.player.pos = spawner['pos']
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0

        self.player.velocity = [0,0]

        self.transition = -30


    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx['ambience'].play(-1)
        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))

            self.screen_shake = max(0, self.screen_shake - 1)

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(len(os.listdir('data/maps')) -1 , self.level + 1)
                    self.load_level(self.level)
                elif self.level == len(os.listdir('data/maps')) -1:
                    self.display.fill((0, 0, 0))
                    self.display_2.blit(self.assets['background'], (0, 0))
                    font = pygame.font.Font(None, 50)
                    text = font.render('You win !', True, (255, 255, 255))
                    text_rect = text.get_rect(center=(self.display.get_width()//2, self.display.get_height()//2))
                    self.display.blit(text, text_rect)
                    self.display_2.blit(self.display, (0,0))
                    
            if self.transition < 0:
                self.transition += 1

            
            if self.dead:
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(self.transition + 1, 30)
                self.screen_shake = max(16, self.screen_shake)
                if self.dead > 40:
                    self.load_level(self.level)

            

            self.scroll[0] += (self.player.rect().centerx  - self.display.get_width() / 2 - self.scroll[0]) / 10

            self.scroll[1] += (self.player.rect().centery  - self.display.get_height() / 2 - self.scroll[1]) / 10

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            # ajout des feuilles des arbres
            for rect in self.leaf_spawners_trees:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random()*rect.width, rect.y + random.random()*rect.height)

                    self.particles.append(Particle(self, 'leaf', pos, velocity = [random.randint(-1, 1), random.randint(-2, 6)*0.1], frame = random.randint(0, 20)))
                
                if self.player.rect().colliderect(rect):
                    if random.randint(0,10) < 3:
                        self.particles.append(Particle(self, 'leaf', (rect.x + random.randint(0, rect.width), rect.y + random.randint(0, rect.height)), velocity = [random.randint(-1, 1), random.randint(-2, 6)*0.1],frame = random.randint(0, 20)))


            # ajout des feuilles des buissons
            for rect in self.leaf_spawners_bushes:
                if self.player.rect().colliderect(rect) and (self.player.last_movement[0] != 0 or self.player.velocity[0] != 0):
                    if random.randint(0,10) < 1:
                        self.particles.append(Particle(self, 'leaf', (rect.x + random.randint(0, rect.width), rect.y + random.randint(0, rect.height)), velocity = [random.randint(-1, 1), random.randint(-2, 6)*0.1],frame = random.randint(0, 20)))
                
                if self.player.rect().colliderect(rect) and (self.player.velocity[1] > 0.1 or self.player.velocity[1] < -0.1):
                    if random.randint(0,10) < self.player.velocity[1] * 2:
                        for _ in range(round(self.player.velocity[1] * 3)):
                            self.particles.append(Particle(self, 'leaf', (rect.x + random.randint(0, rect.width), rect.y + random.randint(0, rect.height)), velocity = [random.randint(-1, 1), random.randint(-2, 6)*0.1],frame = random.randint(0, 20)))
                    
            self.clouds.update()
            self.clouds.render(self.display_2, offset = render_scroll)

            self.tilemap.render(self.display, offset = render_scroll)

            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, movement = (0,0))
                enemy.render(self.display, offset = render_scroll)
                if kill:
                    self.enemies.remove(enemy)
                    

            if not self.dead:
                self.player.update(self.tilemap,(self.movement[1] - self.movement[0], 0))
                self.player.render(self.display, offset = render_scroll)  

            # [[x,y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                self.display.blit(img, (projectile[0][0] - render_scroll[0] - img.get_width()/2, projectile[0][1] - render_scroll[1] - img.get_height()/2))
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for _ in range(4):
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 +(+ math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
                elif abs(self.player.dashing) < 50:
                    if self.player.rect().collidepoint(projectile[0]):
                        self.sfx['hit'].play()
                        self.projectiles.remove(projectile)
                        self.dead += 1
                        self.screen_shake = max(16, self.screen_shake)
                        for _ in range(30):
                            angle = random.random() * math.pi * 2
                            speed = random.random()*5
                            self.sparks.append(Spark(self.player.rect().center, angle, random.random() + 2))  
                            self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity = [math.cos(angle + math.pi ) *speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0, 7)))

            
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset = render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0,0,0,180), unsetcolor=(0,0,0,0))
            for offset in [(1,0), (-1,0), (0,1), (0,-1)]:
                self.display_2.blit(display_sillhouette, offset)

            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset = render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_SPACE:
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_z:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_q:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255,255,255), (self.display.get_width()//2, self.display.get_height()//2), (30 - abs(self.transition))*8, 0)
                transition_surf.set_colorkey((255,255,255))
                self.display.blit(transition_surf, (0,0))
            
            self.display_2.blit(self.display, (0,0))

            screenshake_offset = (random.random()*self.screen_shake - self.screen_shake/2, random.random()*self.screen_shake*2 - self.screen_shake)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)
 
Game().run()