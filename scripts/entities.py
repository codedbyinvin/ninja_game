import pygame 
from scripts.particles import Particle
from scripts.spark import Spark
import math
import random

class PhysicsEntity :
    """Classe de base pour les entités physiques du jeu"""

    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        self.action = ''
        self.anim_offset = (-3,-3)
        self.flip= False
        self.set_action('idle')

        self.last_movement = [0, 0]

    def rect(self):
        """
        Retourne un objet pygame.Rect correspondant à la hitbox de l'entité
        """
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
            self.animation.frame = 0

    def update(self, tilemap, movement = [0, 0]):
        # reset des collisions
        self.collisions = {'up': False, 'down': False, 'left': False, 'right': False}

        # calcul du deplacement
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        # deplacement en x
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()  # transfrome les float en int donc 0.1 devient 0 ce qui fait que l'on reste la ligne le temps de passer 0.5
        for rect in tilemap.physics_rect_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                else:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

        # deplacement en y
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rect_around(self.pos):
            # j'utilise ca pour que ca prenne en compte la ligne du bas de l'entité et du haut de la case pcq dans colliderect il la prend pas en compte
            if entity_rect.bottom == rect.top and entity_rect.centerx >= rect.left and entity_rect.centerx <= rect.right:
                self.collisions['down'] = True
            if entity_rect.colliderect(rect):
                if frame_movement[1] == 0:
                    self.collisions['down'] = True
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y
        
        # flip si necessaire

        if movement[0] != 0:
            self.flip = movement[0] < 0

        self.last_movement = movement

        # gravite
        
        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        # reset velocity 
        if self.collisions['down'] or self.collisions['up']:  
            self.velocity[1] = 0

        # update l'animation

        self.animation.update()

    def render(self, surf, offset = (0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(),self.flip,False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))



class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        self.set_action('idle')
        self.walking = 0

    def update(self, tilemap, movement = (0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)  
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
                if (abs(dis[1]) < 16):
                    if (self.flip and dis[0] < 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if (not self.flip and dis[0] > 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        for _ in range(4):
                            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement = movement)

        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.sfx['hit'].play()
                self.game.screen_shake = max(16, self.game.screen_shake)
                for _ in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(self.rect().center, angle, random.random() + 2))
                        self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity = [math.cos(angle + math.pi ) *speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame = random.randint(0, 7)))
                self.game.sparks.append(Spark(self.rect().center,0, 5 + random.random()))
                self.game.sparks.append(Spark(self.rect().center,math.pi, 5 + random.random()))
                return True
            
    def render(self, surf, offset = (0, 0)):
        super().render(surf, offset)

        if self.flip :
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]) )
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]) )
        
       



class Player(PhysicsEntity):

    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.dashing = 0
        

    
    def update(self, tilemap, movement = [0, 0]):
        super().update(tilemap, movement)
        
        self.air_time += 1

        if self.air_time > 120 and self.game.tilemap.physics_rect_around(self.pos) == []:
            self.game.dead += 1

        if self.collisions['down']:
            self.air_time = 0
            self.wall_slide = False
        
        self.wall_slide = False

        if (self.collisions['left'] or self.collisions['right']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(0.5, self.velocity[1])
            if self.collisions['right']:
                self.flip = False
            if self.collisions['left']:
                self.flip = True
            self.set_action('wallslide')

        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')
        
        if abs(self.dashing) in {60,50}:
            for _ in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle)*speed, math.sin(angle)*speed]
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame = random.randint(0, 7)))
        if self.dashing > 0:
            self.dashing = max(self.dashing - 1, 0)
        if self.dashing < 0:
            self.dashing = min(self.dashing + 1, 0)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() *3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame = random.randint(0, 7)))
       
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                return True
        if self.collisions['down']:
            self.velocity[1] = -3
            return True
    
    def dash(self) -> None:
        if not self.dashing:
            self.game.sfx['dash'].play()
            self.dashing = -60 if self.flip else 60

    def render(self, surf, offset = (0,0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset) 
        
