import pygame
from settings import SHADOW_COLOR, ACCENT_COLOR, ROUNDED_RADIUS


def _draw_shadow(surface, rect, offset=(6, 6), radius=None):
    if radius is None:
        radius = ROUNDED_RADIUS

    shadow = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(shadow, SHADOW_COLOR, shadow.get_rect(), border_radius=radius)
    surface.blit(shadow, (rect.x + offset[0], rect.y + offset[1]))


def draw_panel(surface, rect, fill_color, border_color=None, border_width=2, radius=None, shadow=True):
    """Draw a rounded panel with an optional subtle shadow and border.

    All parameters are visual-only; does not affect layout.
    """
    if radius is None:
        radius = ROUNDED_RADIUS

    if shadow:
        _draw_shadow(surface, rect, radius=radius)

    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    if border_width and border_color:
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)


def draw_button(surface, rect, label, font, fill_color, text_color, border_color=None, radius=None, shadow=True):
    if radius is None:
        radius = ROUNDED_RADIUS

    if shadow:
        _draw_shadow(surface, rect, offset=(4, 4), radius=radius)

    pygame.draw.rect(surface, fill_color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=radius)

    text_surface = font.render(label, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)
