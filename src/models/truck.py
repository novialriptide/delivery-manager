from common import *
import math


class DeliveryTruck:
    def __init__(self):
        self.path = []
        self.path_index = 1
        self.current_conn = None
        self.current_node_index = 0
        self.current_conn_progress = 0
        self.package = None
        self.destroying = False

    @property
    def is_active(self):
        return len(self.path) != 0

    @property
    def pos(self):
        return self.path[self.path_index - 1].position.lerp(
            self.path[self.path_index].position, self.current_conn_progress
        )

    def dist_traveled(self, map_level):
        _sum = 0

        if self.current_conn is None:
            return math.inf

        for x in self.path:
            conn = map_level.find_conn(
                self.path[self.path_index - 1], self.path[self.path_index]
            )
            if x == self.path[self.path_index - 1]:
                break
            _sum += conn.distance
        return _sum + self.current_conn.distance * self.current_conn_progress

    def reset_delivery(self):
        self.path = []
        self.path_index = 1
        self.current_conn = None
        self.current_node_index = 0
        self.current_conn_progress = 0
        self.package = None
        self.destroying = False

    def update(self, delta_time, map_level):
        if self.is_active:
            conn = map_level.find_conn(
                self.path[self.path_index - 1], self.path[self.path_index]
            )
            self.current_conn = conn
            self.current_conn_progress += delta_time / conn.distance / SPEED_MODIFIER
            if self.current_conn_progress >= 1:
                self.current_conn_progress = 0
                self.path_index += 1
                if self.path_index >= len(self.path):
                    self.reset_delivery()
                    return True

        return False
