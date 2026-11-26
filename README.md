# Simulador de enjambre / asteroides

Proyecto 2D en Python con Pygame, `multiprocessing` y una arquitectura funcional basada en datos inmutables.

## Requisitos

- Python 3.10 o superior.
- Pygame 2.5 o superior.
- Se recomienda probar con 2 o más núcleos lógicos para comparar el paralelismo.

Instalar dependencias:

```bash
python -m pip install -r requirements.txt
```

## Ejecutar el simulador

```bash
python main.py --entities 3000
```

Opciones:

```bash
python main.py --entities 1000 --workers 2
python main.py --entities 5000 --workers 4
python main.py --entities 3000 --sequential
```

Controles: flechas o WASD para mover la nave; ESPACIO cambia entre secuencial y paralelo; teclas 1, 2 y 3 cargan 1.000, 3.000 y 5.000 entidades; R reinicia; ESC sale.

## Arquitectura y responsabilidades

| Archivo | Responsabilidad | Naturaleza |
|---|---|---|
| `models.py` | `GameState`, `Entity`, `Ship`, `Inputs` y `Params` congelados | Datos inmutables |
| `physics.py` | Física determinista y transformación pura de entidades | Funciones puras |
| `parallel.py` | Partición y adaptadores secuencial/paralelo | Coordinación |
| `game.py` | `calculate_frame` despacha el cálculo; `update` consolida un estado nuevo | Frontera y actualización pura |
| `renderer.py` | Dibuja leyendo el estado | Efecto de interfaz |
| `main.py` | Game loop, teclado, pantalla y pool de procesos | Efectos de interfaz |
| `benchmark.py` | Mide rendimiento secuencial y paralelo | Medición |
| `test_purity.py` | Comprueba inmutabilidad y equivalencia | Pruebas |

## Pipeline por frame

1. `main.py` captura las entradas del jugador.
2. `calculate_frame()` calcula la posición de la nave, construye la grilla espacial y segmenta las entidades.
3. En modo secuencial, `sequential_mapper` ejecuta `process_chunk` en el proceso principal. En modo paralelo, `Pool.map` distribuye los segmentos a los procesos hijos.
4. `Pool.map` espera a que terminen todas las tareas y devuelve los resultados en el orden original.
5. `update(state, inputs, params, frame_result)` es la actualización pura: consolida resultados y retorna un `GameState` nuevo con `dataclasses.replace`. No crea procesos, no dibuja y no modifica el estado anterior.

## Partición y workers

Las entidades se dividen en segmentos contiguos y equilibrados por índice. Los tamaños de los segmentos difieren como máximo en una entidad. El programa detecta los núcleos lógicos con `os.cpu_count()` y, en configuración automática, limita el pool a un máximo de 8 workers para evitar crear cientos de procesos innecesarios. Se puede configurar manualmente con `--workers`.

## Pruebas

```bash
python -m unittest -v
```

Las pruebas verifican dataclasses congeladas, ausencia de mutación del estado anterior, determinismo, partición equilibrada, rechazo de cero workers, equivalencia entre los resultados secuenciales y paralelos y comportamiento de Game Over.

## Benchmark

Ejecutar:

```bash
python benchmark.py --workers 4 --frames 120 --warmup 10
```

El programa mide 1.000, 3.000 y 5.000 entidades y crea `benchmark_results.md`. La medición incluye cálculo, serialización y sincronización, pero no el renderizado. Los FPS dependen del hardware, la versión de Python y los procesos en segundo plano: utiliza únicamente los resultados medidos en tu computadora para completar el informe.

## Entrega y GitHub

Sube los archivos del proyecto a un repositorio público. Cada integrante debe realizar aportes reales y progresivos desde su propia cuenta; no se deben fabricar commits ni concentrar todo el trabajo en una sola carga. El PDF de entrega debe contener el enlace del repositorio. El video de defensa debe durar al menos 10 minutos y contar con la participación equitativa del equipo.
