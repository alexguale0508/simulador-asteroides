"""Fisica pura: ninguna funcion muta sus argumentos ni toca estado global.

Es la parte CPU-bound que se reparte entre los procesos workers.
"""
from dataclasses import replace
from itertools import groupby
from math import hypot, sin, sqrt

from models import Entity, Params, Ship, Inputs


# ---------------------------------------------------------------- aleatoriedad
def hash01(a: int, b: int) -> float:
    """Pseudo-aleatorio determinista en [0, 1] a partir de dos enteros.
    Reemplaza a random (que tiene estado global oculto) para mantener pureza."""
    h = (a * 374761393 + b * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h ^= h >> 16
    return h / 0xFFFFFFFF


def spawn_entity(i: int, salt: int, p: Params, anywhere: bool = False) -> Entity:
    """Crea (de forma pura) la entidad `i`. Con anywhere=False aparece sobre el borde superior."""
    radius = 2.5 + 3.5 * hash01(i, salt * 8 + 1)
    return Entity(
        id=i,
        x=p.width * hash01(i, salt * 8 + 2),
        y=p.height * hash01(i, salt * 8 + 3) if anywhere else -radius,
        vx=(hash01(i, salt * 8 + 4) - 0.5) * 60,
        vy=40 + 80 * hash01(i, salt * 8 + 5),
        radius=radius,
    )


# ------------------------------------------------------------------ grilla
def build_grid(entities: tuple[Entity, ...], cell: float) -> dict:
    """Grilla espacial {celda: ((id, x, y), ...)} construida sin mutar nada
    (sorted + groupby + comprension de diccionario)."""
    keyed = sorted(
        (((int(e.x // cell), int(e.y // cell)), (e.id, e.x, e.y)) for e in entities),
        key=lambda kv: kv[0],
    )
    return {k: tuple(v for _, v in grp) for k, grp in groupby(keyed, key=lambda kv: kv[0])}


def neighbor_candidates(x: float, y: float, grid: dict, cell: float) -> tuple:
    cx, cy = int(x // cell), int(y // cell)
    return tuple(
        pt
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for pt in grid.get((cx + dx, cy + dy), ())
    )


def separation_force(e: Entity, candidates: tuple, p: Params) -> tuple[float, float]:
    r = p.interact_radius
    close = tuple(
        (dx, dy, sqrt(dx * dx + dy * dy))
        for (nid, nx, ny) in candidates
        if nid != e.id
        for dx, dy in [(e.x - nx, e.y - ny)]
        if 0 < dx * dx + dy * dy < r * r
    )
    fx = sum(p.repulsion * (1 - d / r) * dx / d for dx, dy, d in close)
    fy = sum(p.repulsion * (1 - d / r) * dy / d for dx, dy, d in close)
    return fx, fy


def clamp_speed(vx: float, vy: float, vmax: float) -> tuple[float, float]:
    s = hypot(vx, vy)
    k = 1.0 if s <= vmax else vmax / s
    return vx * k, vy * k


# ------------------------------------------------------------ paso de una entidad
def step_entity(e: Entity, grid: dict, ship: Ship, frame: int, p: Params) -> tuple[Entity, int]:
    """Devuelve (nueva_entidad, choco_con_nave[0|1]). Funcion pura."""
    fx, fy = separation_force(e, neighbor_candidates(e.x, e.y, grid, p.cell), p)
    wind = p.wind * sin(frame * 0.02 + e.y * 0.01)

    vx0 = (e.vx + (fx + wind) * p.dt) * p.damping
    vy0 = e.vy + (fy + p.gravity) * p.dt
    vx1, vy1 = clamp_speed(vx0, vy0, p.max_speed)
    vy1 = max(vy1, p.min_fall)

    x1, y1 = e.x + vx1 * p.dt, e.y + vy1 * p.dt
    hit_wall = x1 < e.radius or x1 > p.width - e.radius
    vx2 = -vx1 if hit_wall else vx1
    x2 = min(max(x1, e.radius), p.width - e.radius)

    hit = hypot(x2 - ship.x, y1 - ship.y) < e.radius + ship.radius
    fell_out = y1 - e.radius > p.height

    return (
        (spawn_entity(e.id, frame, p), int(hit))
        if hit or fell_out
        else (replace(e, x=x2, y=y1, vx=vx2, vy=vy1), 0)
    )


def process_chunk(task: tuple) -> tuple:
    """Funcion que ejecuta cada worker: transforma un segmento completo de entidades.
    Debe estar a nivel de modulo para poder serializarse (pickle)."""
    chunk, grid, ship, frame, p = task
    return tuple(step_entity(e, grid, ship, frame, p) for e in chunk)


# ----------------------------------------------------------------------- nave
def move_ship(ship: Ship, inp: Inputs, p: Params) -> Ship:
    step = p.ship_speed * p.dt
    clamp = lambda v, lo, hi: min(max(v, lo), hi)
    return replace(
        ship,
        x=clamp(ship.x + (int(inp.right) - int(inp.left)) * step, ship.radius, p.width - ship.radius),
        y=clamp(ship.y + (int(inp.down) - int(inp.up)) * step, ship.radius, p.height - ship.radius),
    )
