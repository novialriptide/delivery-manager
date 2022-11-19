import pygame


class BaseButton:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_clicked = False

    def on_hover(self, mouse_pos):
        """MUST OVERRIDE"""
        pass

    def on_click(self, mouse_pos):
        """MUST OVERRIDE"""
        pass

    def is_hovering(self, mouse_pos):
        """DO NOT OVERRIDE"""
        return self.rect.collidepoint(mouse_pos)

    def update(self, mouse_pos, mouse_activity):
        """DO NOT OVERRIDE"""
        if self.is_hovering(mouse_pos):
            self.on_hover(mouse_pos)
            if mouse_activity and not self.is_clicked:
                self.on_click(mouse_pos)
                self.is_clicked = True

        if not mouse_activity:
            self.is_clicked = False
