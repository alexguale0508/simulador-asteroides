"""Compara rendimiento secuencial y paralelo. Ejecutar desde la carpeta del proyecto."""
import argparse
import os
import time
from dataclasses import replace
from multiprocessing import Pool

from game import calculate_frame, new_game, update
from models import Inputs, Params
from parallel import make_parallel_mapper, sequential_mapper


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("el valor debe ser mayor que cero")
    return number


def non_negative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("el valor no puede ser negativo")
    return number


def measure_fps(n: int, mapper, workers: int, frames: int, warmup: int, p: Params) -> float:
    state = replace(new_game(n, 1, p), lives=10**9)
    idle = Inputs()
    for _ in range(warmup):
        result = calculate_frame(state, idle, p, mapper, workers)
        state = update(state, idle, p, result)
    start = time.perf_counter()
    for _ in range(frames):
        result = calculate_frame(state, idle, p, mapper, workers)
        state = update(state, idle, p, result)
    elapsed = time.perf_counter() - start
    return frames / elapsed if elapsed else float("inf")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", type=positive_int, nargs="+", default=[1000, 3000, 5000])
    parser.add_argument("--frames", type=positive_int, default=120)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--workers", type=non_negative_int, default=0,
                        help="numero de procesos; 0 = automatico (hasta 8)")
    args = parser.parse_args()
    if args.warmup < 0:
        parser.error("--warmup no puede ser negativo")

    p = Params()
    cores = os.cpu_count() or 1
    workers = min(args.workers or min(cores, 8), 8)
    rows = []
    with Pool(processes=workers) as pool:
        parallel_mapper = make_parallel_mapper(pool)
        for count in args.counts:
            sequential = measure_fps(count, sequential_mapper, 1, args.frames, args.warmup, p)
            parallel = measure_fps(count, parallel_mapper, min(workers, count), args.frames, args.warmup, p)
            rows.append((count, sequential, parallel))

    lines = [
        "| Cantidad de entidades | Secuencial (1 proceso) | Paralelo ({} workers max.) | Speedup |".format(workers),
        "|---:|---:|---:|---:|",
    ]
    lines.extend(
        f"| {count:,} | {seq:.2f} FPS | {par:.2f} FPS | {par / seq:.2f}x |"
        for count, seq, par in rows
    )
    lines.extend([
        "",
        f"- Nucleos logicos detectados por os.cpu_count(): {cores}",
        f"- Workers configurados: {workers}",
        "- Particion: segmentos contiguos balanceados por indice; sus tamanos difieren como maximo en una entidad.",
        f"- Medicion: {args.frames} frames por modo y carga, despues de {args.warmup} frames de calentamiento.",
        "- Alcance: mide calculo, serializacion y sincronizacion; no incluye renderizado de Pygame.",
        "- Los resultados dependen del hardware, version de Python y carga del sistema.",
    ])
    report = "\n".join(lines)
    print(report)
    with open("benchmark_results.md", "w", encoding="utf-8") as output:
        output.write(report + "\n")


if __name__ == "__main__":
    main()
