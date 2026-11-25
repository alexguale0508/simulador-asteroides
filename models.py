"""Modelos de datos inmutables del simulador.

Todo el estado vive en estructuras @dataclass(frozen=True). No hay metodos que
muten instancias: las "modificaciones" se hacen con dataclasses.replace(),
que devuelve una copia nueva.
Requiere Python 3.10+ (slots=True).
"""
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Entity:
    """Un asteroide / miembro del enjambre."""
    id: int
    x: float
    y: float
    vx: float
    vy: float
    radius: float


@dataclass(frozen=True, slots=True)
class Ship:
    x: float
    y: float
    radius: float


@dataclass(frozen=True, slots=True)
class Inputs:
    """Instantanea de la entrada del jugador en un frame."""
    left: bool = False
    right: bool = False
    up: bool = False
    down: bool = False


@dataclass(frozen=True, slots=True)
class Params:
    """Constantes de la simulacion (tambien inmutables)."""
    width: int = 1280
    height: int = 720
    dt: float = 1 / 60          # paso fijo: la fisica no depende del FPS
    cell: float = 60.0          # tamano de celda de la grilla espacial (>= interact_radius)
    interact_radius: float = 50.0
    repulsion: float = 900.0    # fuerza de separacion entre entidades
    gravity: float = 60.0
    wind: float = 25.0
    damping: float = 0.999
    max_speed: float = 240.0
    min_fall: float = 25.0      # velocidad minima de caida (siempre bajan)
    ship_speed: float = 420.0
    ship_radius: float = 10.0
    invuln_frames: int = 90
    start_lives: int = 3


@dataclass(frozen=True, slots=True)
class GameState:
    """Estado unico e inmutable del juego."""
    entities: tuple[Entity, ...]
    ship: Ship
    frame: int
    score: int
    lives: int
    invuln: int
