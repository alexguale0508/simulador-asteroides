"""Pruebas de inmutabilidad, pureza y equivalencia secuencial/paralela.
Ejecutar: python -m unittest -v
"""
import unittest
from dataclasses import FrozenInstanceError
from multiprocessing import Pool

from game import calculate_frame, new_game, update
from models import Inputs, Params
from parallel import make_parallel_mapper, partition, sequential_mapper

P = Params()


class PurityTests(unittest.TestCase):
    def test_estado_y_entidades_congelados(self):
        state = new_game(10)
        with self.assertRaises(FrozenInstanceError):
            state.frame = 5
        with self.assertRaises(FrozenInstanceError):
            state.entities[0].x = 0.0

    def test_update_es_pura_y_no_muta_estado_original(self):
        original = new_game(300)
        snapshot = (original.entities, original.ship, original.frame,
                    original.score, original.lives, original.invuln)
        inputs = Inputs(left=True)
        result = calculate_frame(original, inputs, P, sequential_mapper, 1)
        updated = update(original, inputs, P, result)
        self.assertIsNot(original, updated)
        self.assertEqual(snapshot, (original.entities, original.ship, original.frame,
                                    original.score, original.lives, original.invuln))
        self.assertEqual(updated.frame, original.frame + 1)

    def test_update_determinista(self):
        state_a = new_game(300)
        state_b = new_game(300)
        inputs = Inputs()
        result_a = calculate_frame(state_a, inputs, P, sequential_mapper, 1)
        result_b = calculate_frame(state_b, inputs, P, sequential_mapper, 1)
        self.assertEqual(update(state_a, inputs, P, result_a),
                         update(state_b, inputs, P, result_b))

    def test_particion_completa_y_balanceada(self):
        items = tuple(range(103))
        parts = partition(items, 8)
        self.assertEqual(tuple(item for part in parts for item in part), items)
        self.assertLessEqual(max(map(len, parts)) - min(map(len, parts)), 1)

    def test_particion_rechaza_cero_workers(self):
        with self.assertRaises(ValueError):
            partition((1, 2, 3), 0)

    def test_paralelo_igual_a_secuencial(self):
        with Pool(2) as pool:
            parallel_mapper = make_parallel_mapper(pool)
            sequential_state = parallel_state = new_game(400)
            for _ in range(15):
                inputs = Inputs()
                seq_result = calculate_frame(sequential_state, inputs, P, sequential_mapper, 1)
                par_result = calculate_frame(parallel_state, inputs, P, parallel_mapper, 2)
                sequential_state = update(sequential_state, inputs, P, seq_result)
                parallel_state = update(parallel_state, inputs, P, par_result)
        self.assertEqual(sequential_state, parallel_state)

    def test_game_over_no_avanza(self):
        state = new_game(5)
        from dataclasses import replace
        finished = replace(state, lives=0)
        self.assertIs(update(finished, Inputs(), P, None), finished)


if __name__ == "__main__":
    unittest.main()
