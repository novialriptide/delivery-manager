import pygame


class Connection:
    def __init__(self, node1, node2, distance, blocked=False, bumpy=False):
        self.node1 = node1
        self.node2 = node2
        self.distance = distance
        self.blocked = blocked
        self.bumpy = bumpy

    def draw(self, surface, color, width=1, offset=pygame.Vector2(0, 0)):
        pygame.draw.line(
            surface,
            color,
            self.node1.position - offset,
            self.node2.position - offset,
            width,
        )
