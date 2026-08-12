"""Dependency-free exact arithmetic for short Weierstrass curves over prime fields."""

from __future__ import annotations

from dataclasses import dataclass

Point = tuple[int, int] | None


@dataclass(frozen=True)
class Curve:
    p: int
    a: int
    b: int

    def on_curve(self, point: Point) -> bool:
        if point is None:
            return True
        x, y = point
        return (y * y - (x * x * x + self.a * x + self.b)) % self.p == 0

    def neg(self, point: Point) -> Point:
        return None if point is None else (point[0], (-point[1]) % self.p)

    def add(self, left: Point, right: Point) -> Point:
        if left is None:
            return right
        if right is None:
            return left
        x1, y1 = left
        x2, y2 = right
        if x1 == x2 and (y1 + y2) % self.p == 0:
            return None
        if left == right:
            if y1 == 0:
                return None
            slope = (3 * x1 * x1 + self.a) * pow(2 * y1, -1, self.p) % self.p
        else:
            slope = (y2 - y1) * pow(x2 - x1, -1, self.p) % self.p
        x3 = (slope * slope - x1 - x2) % self.p
        return x3, (slope * (x1 - x3) - y1) % self.p

    def mul(self, scalar: int, point: Point) -> Point:
        if scalar < 0:
            return self.mul(-scalar, self.neg(point))
        result = None
        addend = point
        while scalar:
            if scalar & 1:
                result = self.add(result, addend)
            addend = self.add(addend, addend)
            scalar >>= 1
        return result


def nontrivial_cube_root(modulus: int) -> int:
    """Return a deterministic nontrivial cube root of one (mod a prime)."""
    if modulus % 3 != 1:
        raise ValueError("modulus must be 1 mod 3")
    exponent = (modulus - 1) // 3
    for base in range(2, 1000):
        root = pow(base, exponent, modulus)
        if root != 1:
            assert pow(root, 3, modulus) == 1
            return root
    raise RuntimeError("cube root search failed")


def legendre(a: int, p: int) -> int:
    value = pow(a % p, (p - 1) // 2, p)
    return -1 if value == p - 1 else value


def sqrt_mod(a: int, p: int) -> int | None:
    """Tonelli--Shanks square root, deterministically choosing the smaller root."""
    a %= p
    if a == 0:
        return 0
    if legendre(a, p) != 1:
        return None
    if p % 4 == 3:
        root = pow(a, (p + 1) // 4, p)
        return min(root, p - root)
    q, s = p - 1, 0
    while q % 2 == 0:
        q //= 2
        s += 1
    z = 2
    while legendre(z, p) != -1:
        z += 1
    m, c, t, r = s, pow(z, q, p), pow(a, q, p), pow(a, (q + 1) // 2, p)
    while t != 1:
        i, tt = 1, t * t % p
        while tt != 1:
            tt = tt * tt % p
            i += 1
        b = pow(c, 1 << (m - i - 1), p)
        r, t, c, m = r * b % p, t * b * b % p, b * b % p, i
    return min(r, p - r)


def lift_x(curve: Curve, x: int, parity: int = 0) -> Point:
    y = sqrt_mod((x * x * x + curve.a * x + curve.b) % curve.p, curve.p)
    if y is None:
        return None
    if y & 1 != parity:
        y = curve.p - y
    return x, y


def is_probable_prime(n: int) -> bool:
    """Deterministic Miller--Rabin for n < 2^128 (bases are ample for this project)."""
    if n < 2:
        return False
    small = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
    for prime in small:
        if n % prime == 0:
            return n == prime
    d, s = n - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for base in small:
        x = pow(base, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True
