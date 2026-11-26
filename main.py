"""Simulador interactivo de lluvia de asteroides / enjambre.

Controles: flechas/WASD mover | ESPACIO paralelo<->secuencial | 1/2/3 = 1k/3k/5k
           R reiniciar | ESC salir
"""
import argparse
import os
from multiprocessing import Pool
from types import MappingProxyType

import pygame

from game import calculate_frame, new_game, update
from models import Inputs, Params
from parallel import make_parallel_mapper, sequential_mapper
from renderer import draw_hud, draw_world

COUNTS = MappingProxyType({pygame.K_1: 1000, pygame.K_2: 3000, pygame.K_3: 5000})


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


def read_inputs(keys) -> Inputs:
    return Inputs(
        left=keys[pygame.K_LEFT] or keys[pygame.K_a],
        right=keys[pygame.K_RIGHT] or keys[pygame.K_d],
        up=keys[pygame.K_UP] or keys[pygame.K_w],
        down=keys[pygame.K_DOWN] or keys[pygame.K_s],
    )


def run(args) -> None:
    p = Params()
    cores = os.cpu_count() or 1
    workers = min(args.workers or min(cores, 8), 8)

    pygame.init()
    screen = pygame.display.set_mode((p.width, p.height))
    pygame.display.set_caption("Simulador de enjambre - Paralelismo + Programacion Funcional")
    font = pygame.font.SysFont("consolas", 16)
    clock = pygame.time.Clock()

    n, parallel_on = args.entities, not args.sequential
    state = new_game(n, args.seed, p)

    try:
        with Pool(processes=workers) as pool:
            par_mapper = make_parallel_mapper(pool)
            running = True
            while running:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                        running = False
                    elif ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_SPACE:
                            parallel_on = not parallel_on
                        elif ev.key == pygame.K_r:
                            state = new_game(n, args.seed, p)
                        elif ev.key in COUNTS:
                            n = COUNTS[ev.key]
                            state = new_game(n, args.seed, p)

                inp = read_inputs(pygame.key.get_pressed())
                active_workers = min(workers, max(1, len(state.entities))) if parallel_on else 1
                mapper = par_mapper if parallel_on else sequential_mapper
                if state.lives > 0:
                    frame_result = calculate_frame(state, inp, p, mapper, active_workers)
                    state = update(state, inp, p, frame_result)

                draw_world(screen, state, p)
                draw_hud(screen, font, (
                    f"Modo: {'PARALELO' if parallel_on else 'SECUENCIAL'}  (workers activos: {active_workers} / nucleos: {cores})",
                    f"Entidades: {len(state.entities)}   FPS: {clock.get_fps():5.1f}",
                    f"Vidas: {max(state.lives, 0)}   Puntaje: {state.score}" + ("   GAME OVER (R)" if state.lives <= 0 else ""),
                ))
                pygame.display.flip()
                clock.tick(args.fps_cap)
    finally:
        pygame.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulador 2D con multiprocessing")
    parser.add_argument("--entities", type=positive_int, default=3000)
    parser.add_argument("--workers", type=non_negative_int, default=0,
                        help="0 = automatico (hasta 8 workers)")
    parser.add_argument("--sequential", action="store_true", help="iniciar en modo secuencial")
    parser.add_argument("--fps-cap", type=non_negative_int, default=0,
                        help="limite de FPS; 0 = sin limite")
    parser.add_argument("--seed", type=int, default=1)
    run(parser.parse_args())
