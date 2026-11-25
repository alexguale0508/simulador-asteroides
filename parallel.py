"""Particion y adaptadores de ejecucion secuencial/paralela."""
from itertools import accumulate
from multiprocessing.pool import Pool
from typing import Callable

from physics import process_chunk


def partition(items: tuple, n: int) -> tuple:
    """Divide items en n segmentos contiguos y balanceados (diferencia <= 1)."""
    if n < 1:
        raise ValueError("El numero de segmentos debe ser mayor que cero")
    q, r = divmod(len(items), n)
    sizes = tuple(q + (1 if i < r else 0) for i in range(n))
    starts = tuple(accumulate((0,) + sizes[:-1]))
    return tuple(items[start:start + size] for start, size in zip(starts, sizes))


def sequential_mapper(tasks: tuple) -> tuple:
    """Ejecuta las mismas tareas en el proceso principal, como linea base."""
    return tuple(map(process_chunk, tasks))


def make_parallel_mapper(pool: Pool) -> Callable[[tuple], tuple]:
    """Pool.map bloquea hasta completar todas las tareas y conserva su orden."""
    return lambda tasks: tuple(pool.map(process_chunk, tasks, chunksize=1))
