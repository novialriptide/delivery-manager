import pygame
import random
import copy
from .node import *
from .connection import *
from common import *


class MapLevel:
    def __init__(self, center, node_count, connections_count, map_radius):
        self.nodes = []
        self.connections = []
        self.center = center

        for _ in range(node_count):
            position = pygame.Vector2(
                random.randrange(-map_radius, map_radius),
                random.randrange(-map_radius, map_radius),
            )
            n = Node(position + center)
            self.nodes.append(n)

            if len(self.nodes) <= 1:
                continue

            for _ in range(connections_count):
                temp_nodes = copy.copy(self.nodes)
                temp_nodes.remove(n)
                node2 = random.choice(temp_nodes)
                self.add_conn(n, node2)

    def add_conn(self, node1, node2):
        if node1 == node2:
            return False

        for c in self.connections:
            if (c.node1 == node1 and c.node2 == node2) or (
                c.node1 == node2 and c.node2 == node1
            ):
                return False

        bumpy = random.random() < BUMPY_CONN_PROB
        c = Connection(
            node1,
            node2,
            random.randint(*CONN_DIST)
            if not bumpy
            else random.randint(*BUMPY_CONN_DIST),
            bumpy=bumpy,
        )
        self.connections.append(c)
        return True

    def find_conn(self, node1, node2):
        for c in self.connections:
            if (c.node1 == node1 and c.node2 == node2) or (
                c.node1 == node2 and c.node2 == node1
            ):
                return c
        return None
