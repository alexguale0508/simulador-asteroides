"""Renderizado 2D con Pygame. Es la frontera impura (dibuja en pantalla),
pero SOLO lee el GameState: nunca lo modifica."""
import pygame

from models import GameState, Params

BG = (8, 10, 22)


def draw_world(surface: pygame.Surface, state: GameState, p: Params) -> None:
    surface.fill(BG)
    for e in state.entities:
        shade = min(255, 110 + int(e.vy * 0.6))
        pygame.draw.circle(surface, (shade, shade - 20, 255 - shade // 2), (int(e.x), int(e.y)), max(1, int(e.radius)))
    visible = state.invuln == 0 or (state.invuln // 6) % 2 == 0
    if state.lives > 0 and visible:
        s = state.ship
        pygame.draw.polygon(
            surface, (80, 255, 140),
            [(s.x, s.y - s.radius * 1.4), (s.x - s.radius, s.y + s.radius), (s.x + s.radius, s.y + s.radius)],
        )


def draw_hud(surface: pygame.Surface, font: pygame.font.Font, lines: tuple[str, ...]) -> None:
    for i, line in enumerate(lines):
        surface.blit(font.render(line, True, (235, 235, 235)), (10, 8 + i * 20))
