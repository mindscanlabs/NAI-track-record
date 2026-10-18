"""A183881, A183887 (and A183880): arrangements of m numbers in 0..q-1, each the sum mod q of s others
(s other distinct positions). Exact closed form by a finite enumeration of profiles.

Whether a word qualifies depends only on the profile: for each residue v, its count is 0, 1, ..., s,
or >= s+1 (a sum of s others plus the position itself needs at most s+1 copies of one residue).
The number of words of length m with a given profile is m! [t^m] Prod_v f_v(t), with
f = t^k/k! for an exact count k and f = e^t - Sum_{j<=s} t^j/j! for ">= s+1". Summing over the
valid profiles gives Sum c[a,k] t^a e^(k t), so count(m) = Sum_{k>=1} c[a,k] (m)_a k^(m-a) plus
c[a,0] a! for m = a. The script compares this with the conjectured closed form.
"""
from fractions import Fraction
from itertools import product, combinations_with_replacement
from math import factorial
import sympy as sp

def valid(profile, q, s):
    T = s + 1
    for v in range(q):
        if profile[v] == 0:
            continue
        ok = False
        for ms in combinations_with_replacement(range(q), s):
            if sum(ms) % q != v:
                continue
            need = {}
            for a in ms:
                need[a] = need.get(a, 0) + 1
            need[v] = need.get(v, 0) + 1          # the position itself
            if all(profile[a] >= c or profile[a] == T for a, c in need.items()):
                ok = True
                break
        if not ok:
            return False
    return True

def polymul(A, B):
    C = {}
    for (a1, k1), c1 in A.items():
        for (a2, k2), c2 in B.items():
            key = (a1 + a2, k1 + k2)
            C[key] = C.get(key, 0) + c1 * c2
    return {k: v for k, v in C.items() if v != 0}

def closed_form(q, s):
    T = s + 1
    f = {}
    for k in range(T):
        f[k] = {(k, 0): Fraction(1, factorial(k))}
    f[T] = {(0, 1): Fraction(1)}
    for j in range(T):
        f[T][(j, 0)] = f[T].get((j, 0), 0) - Fraction(1, factorial(j))
    total = {}
    nvalid = 0
    for prof in product(range(T + 1), repeat=q):
        if not valid(prof, q, s):
            continue
        nvalid += 1
        P = {(0, 0): Fraction(1)}
        for v in range(q):
            P = polymul(P, f[prof[v]])
        for key, c in P.items():
            total[key] = total.get(key, 0) + c
    total = {k: v for k, v in total.items() if v != 0}
    return total, nvalid

def count(total, m):
    r = Fraction(0)
    for (a, k), c in total.items():
        if m < a:
            continue
        if k == 0:
            r += c * factorial(a) if m == a else 0
        else:
            r += c * Fraction(factorial(m), factorial(m - a)) * k ** (m - a)
    return r

def bfile(aid):
    b = {}
    for line in open('../data/bfiles/b%s.txt' % aid[1:], encoding='utf-8'):
        p = line.split()
        if len(p) >= 2 and not line.startswith('#'):
            b[int(p[0])] = int(p[1])
    return b

n = sp.symbols('n')
cases = [
    ('A183881', 7, 2, 2, lambda n: 7**(n+2) - (28*n**2+252*n+554)*3**n + (9*n**3+201*n**2+1044*n+1668)*2**(n-1)
                                    + 6*n**4+19*n**3-45*n**2-274*n-342),
    ('A183887', 5, 3, 3, lambda n: 5**(n+3) - (3*n+13)*2**(n+3) - sp.Rational(1, 3)*(17*n**4+182*n**3+733*n**2+1312*n+864)),
]
for aid, q, s, shift, conj in cases:
    total, nvalid = closed_form(q, s)
    b = bfile(aid)
    ns = sorted(b)
    agree_b = all(count(total, nn + shift) == b[nn] for nn in ns[:200])
    # symbolic closed form in n (k >= 1 part), m = n + shift
    m = n + shift
    expr = 0
    for (a, k), c in total.items():
        if k >= 1:
            ff = sp.Integer(1)
            for i in range(a):
                ff *= (m - i)
            expr += sp.Rational(c.numerator, c.denominator) * ff * sp.Integer(k)**(m - a)
    diff = sp.simplify(sp.expand(sp.powsimp(sp.expand_power_exp(sp.expand(expr - conj(n))))))
    k0 = sorted(a for (a, k), c in total.items() if k == 0)
    print('%s: q=%d, s=%d; valid profiles %d; exact count = b-file for the first %d terms: %s'
          % (aid, q, s, nvalid, min(200, len(ns)), agree_b))
    print('   exponentials present (k with nonzero terms): %s'
          % sorted({k for (a, k) in total if k >= 1}))
    print('   closed form (k >= 1 part) minus the conjecture, simplified: %s' % diff)
    print('   polynomial-only terms t^a with a in %s, so the closed form holds for m > %s, i.e. n >= %s'
          % (k0, max(k0) if k0 else '-', (max(k0) - shift + 1) if k0 else 0))
    first_fail = [nn for nn in ns[:20] if conj(nn) != b[nn]]
    print('   conjecture fails at n = %s (b-file)' % first_fail)
