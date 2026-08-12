import json
import unittest
from pathlib import Path

from src.ec import Curve, is_probable_prime, lift_x, sqrt_mod

ROOT = Path(__file__).resolve().parents[1]


class ExactArithmeticTests(unittest.TestCase):
    def test_square_roots(self):
        for p in (7, 13, 19, 31, 37):
            for x in range(p):
                root = sqrt_mod(x, p)
                self.assertEqual(root is not None, any(y*y % p == x for y in range(p)))

    def test_sec2_orders(self):
        for spec in json.loads((ROOT / "data/sec2_koblitz.json").read_text())["curves"]:
            v = {k: int(spec[k], 16) for k in ("p", "a", "b", "gx", "gy", "n")}
            curve, point = Curve(v["p"], v["a"], v["b"]), (v["gx"], v["gy"])
            self.assertTrue(curve.on_curve(point))
            self.assertIsNone(curve.mul(v["n"], point))

    def test_primality_smoke(self):
        self.assertTrue(is_probable_prime(2**61 - 1))
        self.assertFalse(is_probable_prime((2**31 - 1) * (2**19 - 1)))

if __name__ == "__main__":
    unittest.main()
