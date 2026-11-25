"""Logica del juego: separa el despacho de procesos de la actualizacion pura."""
from dataclasses import replace

from models import GameState, Inputs, Params, Ship
from parallel import partition
from physics import build_grid, move_ship, process_chunk, spawn_entity


def new_game(n_entities: int, seed: int = 1, p: Params = Params()) -> GameState:
    """Construye un estado inicial nuevo y determinista."""
    if n_entities < 0:
        raise ValueError("La cantidad de entidades no puede ser negativa")
    return GameState(
        entities=tuple(spawn_entity(i, seed, p, anywhere=True) for i in range(n_entities)),
        ship=Ship(x=p.width / 2, y=p.height - 60, radius=p.ship_radius),
        frame=0,
        score=0,
        lives=p.start_lives,
        invuln=0,
    )


def calculate_frame(state: GameState, inp: Inputs, p: Params, mapper, workers: int):
    """Frontera de ejecucion: prepara tareas y obtiene resultados de los workers.

    Esta funcion coordina multiprocessing y, por tanto, no se considera pura.
    No modifica el estado recibido; devuelve datos inmutables para `update`.
    """
    if workers < 1:
        raise ValueError("workers debe ser un entero mayor que cero")
    ship = move_ship(state.ship, inp, p)
    chunks = partition(state.entities, min(workers, max(1, len(state.entities))))
    grid = build_grid(state.entities, p.cell)
    tasks = tuple((chunk, grid, ship, state.frame, p) for chunk in chunks)
    results = mapper(tasks)
    stepped = tuple(pair for part in results for pair in part)
    return ship, stepped


def update(state: GameState, inp: Inputs, p: Params, frame_result) -> GameState:
    """Actualizacion pura: recibe resultados ya calculados y retorna otro GameState.

    No crea procesos, no dibuja, no lee teclado y no modifica objetos existentes.
    `frame_result` es la tupla (nueva_nave, resultados_de_entidades) calculada
    previamente por `calculate_frame`.
    """
    if state.lives <= 0:
        return state
    ship, stepped = frame_result
    entities = tuple(entity for entity, _ in stepped)
    hits = sum(hit for _, hit in stepped)
    damaged = hits > 0 and state.invuln == 0
    return replace(
        state,
        entities=entities,
        ship=ship,
        frame=state.frame + 1,
        score=state.score + 1,
        lives=state.lives - int(damaged),
        invuln=p.invuln_frames if damaged else max(0, state.invuln - 1),
    )
