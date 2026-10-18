"""OEIS-style closed forms for the arrangement columns of the Hardin family, built directly from the
exact EGF expansion (a, k, c): a(n) = Sum_k [Sum_a c*(n+s)_a*k^(s-a)] k^n, n >= n0. Each text is
parsed back and checked against the exact counts."""
import json, sys
from fractions import Fraction
from math import lcm
import sympy as sp
src = open('oeis_hardin_family.py', encoding='utf-8').read(); src = src[:src.index('report = []')]
ns = {}; exec(src, ns); n = ns['n']
rep = {r['id']: r for r in json.load(open('../data/profiles/family_report.json', encoding='utf-8'))}

def poly_text(P):
    terms = []
    for (d,), c in sorted(sp.Poly(P, n).terms(), key=lambda t: -t[0][0]):
        c = int(c); mono = '' if d == 0 else ('n' if d == 1 else 'n^%d' % d)
        mag = abs(c); body = str(mag) if not mono else (mono if mag == 1 else '%d*%s' % (mag, mono))
        terms.append(('-' if c < 0 else '+') + body)
    s = ''.join(terms); return s[1:] if s.startswith('+') else s

def closed_text(q, s):
    tot = ns['egf_total'](q, s)
    byk = {}
    for (a, k), c in tot.items():
        if k:
            ff = sp.Integer(1)
            for i in range(a):
                ff *= (n + s - i)
            byk[k] = byk.get(k, 0) + sp.Rational(c.numerator, c.denominator) * ff * sp.Rational(k) ** (s - a)
    pieces = []
    for k in sorted(byk, reverse=True):
        P = sp.expand(byk[k])
        if P == 0:
            continue
        den = lcm(*[int(sp.Rational(v).q) for v in sp.Poly(P, n).coeffs()])
        Pi = sp.expand(P * den); j = 0
        if k > 1:
            while den % k == 0:
                den //= k; j -= 1
            g = sp.Poly(Pi, n)
            if g.degree() == 0:
                cst = int(g.coeffs()[0])
                while cst % k == 0:
                    cst //= k; j += 1
                Pi = sp.Integer(cst)
            else:
                cont = sp.gcd_list([int(v) for v in g.coeffs()])
                while cont % k == 0 and den == 1:
                    cont //= k; Pi = sp.expand(Pi / k); j += 1
        sign = '+'
        if sp.Poly(Pi, n).LC() < 0:
            Pi = sp.expand(-Pi); sign = '-'
        pt = poly_text(Pi)
        kp = '' if k == 1 else ('%d^n' % k if j == 0 else '%d^(n%+d)' % (k, j))
        if k == 1:
            term = '(%s)' % pt if (sign == '-' and any(ch in pt[1:] for ch in '+-') and den == 1) else pt
        elif pt == '1':
            term = kp
        elif pt == '-1':
            term = '-' + kp
        elif any(ch in pt[1:] for ch in '+-'):
            term = '(%s)*%s' % (pt, kp)
        else:
            term = '%s*%s' % (pt, kp)
        if den != 1:
            term = '(%s)/%d' % (term, den) if k == 1 else '%s/%d' % (term, den)
        pieces.append((sign, term))
    txt = ''.join(' %s %s' % (sg, t) for sg, t in pieces).strip()
    txt = txt[2:] if txt.startswith('+ ') else '-' + txt[2:]
    return txt, tot

out = {}
for aid in sys.argv[1:]:
    r = rep[aid]; q, s, n0 = r['q'], r['s'], r['closed_form_from_n']
    txt, tot = closed_text(q, s)
    expr = sp.sympify(txt.replace('^', '**'), locals={'n': n})
    ok = all(expr.subs(n, kk) == sp.Rational(ns['arr_count'](tot, kk + s)) for kk in range(n0, n0 + 80))
    bad = [kk for kk in range(1, n0) if expr.subs(n, kk) != sp.Rational(ns['arr_count'](tot, kk + s))]
    out[aid] = dict(text='a(n) = %s for n >= %d.' % (txt, n0), verified=ok, fails_below=bad)
    print('%s q=%d s=%d %s fails at n=%s\n   a(n) = %s for n >= %d.' % (aid, q, s, 'verified' if ok else 'MISMATCH', bad, txt, n0))
json.dump(out, open('../rebuilt/new_formulas.json', 'w'), indent=1)
