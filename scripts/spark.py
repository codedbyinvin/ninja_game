import math 
import pygame

class Spark:
    """A class to represent a spark particle"""
    def __init__ (self, pos : tuple, angle:float, speed: float):
        """
        Initialize the spark particle
        
        :param pos: The position of the spark  
        :param angle: The angle of the spark
        :param speed: The speed of the spark
        """
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
    
    def update(self) -> None:
        """
        Update the spark's position and speed
        """
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed

        self.speed = max(0, self.speed - 0.1)   
        return not self.speed



    def render(self, surf, offset=(0, 0)):
        """
        Render the spark on the screen
        """
        render_points = [
            (self.pos[0] + math.cos(self.angle)*self.speed*3 - offset[0],self.pos[1] + math.sin(self.angle)*self.speed*3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi/2)*self.speed*0.5 - offset[0],self.pos[1] + math.sin(self.angle + math.pi/2)*self.speed*0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi)*self.speed*3 - offset[0],self.pos[1] + math.sin(self.angle + math.pi)*self.speed*3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi/2)*self.speed*0.5 - offset[0],self.pos[1] + math.sin(self.angle - math.pi/2)*self.speed*0.5 - offset[1])
        ]

        pygame.draw.polygon(surf, (255,255,255), render_points)