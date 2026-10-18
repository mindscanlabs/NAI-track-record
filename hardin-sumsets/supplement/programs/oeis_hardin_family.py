"""Exact formulas for the Hardin family A183877..A183912 from the profile histograms of
oeis_profiles.exe (../data/profiles/hist_q{q}_s{s}.txt).

arrangements:  a(n) = m! [t^m] Sum_hist N Prod_c f_c^h_c, m = n + s, f_c = t^c/c! (c <= s),
               f_{s+1} = e^t - Sum_{j<=s} t^j/j!   ->  Sum_k P_k(n) k^n for n >= n0
nondecreasing: a(n) = [y^m] Sum_hist N y^(sum c*h_c) / (1-y)^h_{s+1}   ->  polynomial for n >= n0

Each formula is checked against the whole b-file (or the data) and against the formulas already
in the entry ("Empirical", "Conjectures"), parsed from the entry text.
"""
import re, sys, json
from fractions import Fraction
from math import factorial, comb
import sympy as sp

n, x = sp.symbols('n x')
R = '../data/profiles'

def read_hist(q, s):
    H = []
    for line in open('%s/hist_q%d_s%d.txt' % (R, q, s), encoding='utf-8'):
        p = [int(v) for v in line.split()]
        H.append((p[:-1], p[-1]))
    return H

def polymul(A, B):
    C = {}
    for (a1, k1), c1 in A.items():
        for (a2, k2), c2 in B.items():
            C[(a1 + a2, k1 + k2)] = C.get((a1 + a2, k1 + k2), 0) + c1 * c2
    return {k: v for k, v in C.items() if v}

def polypow(A, e):
    P = {(0, 0): Fraction(1)}
    for _ in range(e):
        P = polymul(P, A)
    return P

def egf_total(q, s):
    T = s + 1
    f = [{(c, 0): Fraction(1, factorial(c))} for c in range(T)]
    fT = {(0, 1): Fraction(1)}
    for j in range(T):
        fT[(j, 0)] = fT.get((j, 0), 0) - Fraction(1, factorial(j))
    f.append(fT)
    total = {}
    for h, N in read_hist(q, s):
        P = {(0, 0): Fraction(N)}
        for c in range(T + 1):
            if h[c]:
                P = polymul(P, polypow(f[c], h[c]))
        for key, v in P.items():
            total[key] = total.get(key, 0) + v
    return {k: v for k, v in total.items() if v}

def arr_count(total, m):
    r = Fraction(0)
    for (a, k), c in total.items():
        if m < a:
            continue
        r += c * factorial(a) if k == 0 and m == a else 0
        if k:
            r += c * Fraction(factorial(m), factorial(m - a)) * k ** (m - a)
    return r

def arr_formula(total, s):
    m = n + s
    expr = 0
    for (a, k), c in total.items():
        if k:
            ff = sp.Integer(1)
            for i in range(a):
                ff *= (m - i)
            expr += sp.Rational(c.numerator, c.denominator) * ff * sp.Integer(k) ** (m - a)
    by_k = {}
    for (a, k), c in total.items():
        if k:
            by_k.setdefault(k, 0)
    terms = []
    expr = sp.expand(sp.powsimp(sp.expand_power_exp(sp.expand(expr))))
    for k in sorted(by_k, reverse=True):
        coef = sp.expand(sp.simplify(expr.coeff(sp.Integer(k) ** n)) if k > 1 else 0)
        terms.append((k, coef))
    # the k = 1 part is the remainder
    rest = sp.expand(expr - sum(c * sp.Integer(k) ** n for k, c in terms if k > 1))
    terms = [(k, c) for k, c in terms if k > 1] + [(1, rest)]
    return terms

def nd_total(q, s):
    T = s + 1
    G = {}   # (e, h) -> N : N y^e/(1-y)^h
    for hist, N in read_hist(q, s):
        e = sum(c * hist[c] for c in range(T + 1))
        G[(e, hist[T])] = G.get((e, hist[T]), 0) + N
    return G

def nd_count(G, m):
    r = 0
    for (e, h), N in G.items():
        if h == 0:
            r += N if m == e else 0
        elif m >= e:
            r += N * comb(m - e + h - 1, h - 1)
    return r

def nd_formula(G, s):
    m = n + s
    expr = 0
    for (e, h), N in G.items():
        if h:
            expr += N * sp.binomial(m - e + h - 1, h - 1)
    return sp.expand(sp.expand_func(expr))

def bfile(aid):
    b = {}
    try:
        for line in open('../data/bfiles/b%s.txt' % aid[1:], encoding='utf-8'):
            p = line.split()
            if len(p) >= 2 and not line.startswith('#'):
                b[int(p[0])] = int(p[1])
    except FileNotFoundError:
        pass
    return b

def entry_data(lines):
    s = ''.join(l[11:].strip() for l in lines if l[:2] in ('%S', '%T', '%U'))
    return [int(v) for v in s.split(',') if v.strip()]

def parse_existing(F):
    """closed forms 'a(n) = expr for n>k' / 'Empirical (for n>=k): expr' and G.f. lines"""
    out = []
    for f in F:
        g = re.search(r'G\.f\.:\s*(.*?)\.\s*(-|$)', f)
        if g:
            out.append(('gf', g.group(1), f))
            continue
        m1 = re.search(r'Empirical \(for n\s*>=\s*(\d+)\):\s*(.*?)\.\s*-', f)
        m2 = re.search(r'a\(n\)\s*=\s*(.*?)\s+for n\s*>\s*(\d+)', f)
        if m1:
            out.append(('cf', m1.group(2), int(m1.group(1)), f))
        elif m2:
            out.append(('cf', m2.group(1), int(m2.group(2)) + 1, f))
    return out

def to_sympy(t):
    t = t.replace('^', '**')
    return sp.sympify(t, locals={'n': n, 'x': x})

entries = {}
cur = None
for line in open('../data/oeis_entries/search_family.txt', encoding='utf-8'):
    m = re.match(r'%(\w) (A\d+) ?(.*)', line.rstrip('\n'))
    if m:
        entries.setdefault(m.group(2), []).append(line.rstrip('\n'))

ids = {}
for aid, lines in entries.items():
    N = [l[11:] for l in lines if l.startswith('%N')][0]
    mm = re.match(r'Number of (nondecreasing )?arrangements of n\+(\d) numbers in 0\.\.(\d) ', N)
    if mm:
        ids[aid] = (bool(mm.group(1)), int(mm.group(2)), int(mm.group(3)) + 1)

def series_coeffs(expr, N):
    num, den = sp.fraction(sp.together(expr))
    P = sp.Poly(sp.expand(num), x); Q = sp.Poly(sp.expand(den), x)
    pc = [P.coeff_monomial(x**i) for i in range(N)]
    qc = [Q.coeff_monomial(x**i) for i in range(Q.degree() + 1)]
    out = []
    for i in range(N):
        v = pc[i] - sum(qc[j] * out[i - j] for j in range(1, min(i, len(qc) - 1) + 1))
        out.append(sp.Rational(v, qc[0]))
    return out

def check_existing(e, cnt):
    if e[0] == 'gf':
        co = series_coeffs(to_sympy(e[1]), 45)
        return 'g.f. (45 terms): %s' % all(co[k] == cnt(k) for k in range(1, 45))
    text, start = e[1], e[2]
    if 'a(n-' in text.replace(' ', ''):
        t = re.sub(r'a\(\s*n\s*-\s*(\d+)\s*\)', lambda mm: 'A%s' % mm.group(1), text)
        ee = to_sympy(t)
        syms = sorted(ee.free_symbols - {n}, key=str)
        ok = True
        for k in range(start + 12, start + 60):
            sub = {n: k}
            for sy in syms:
                sub[sy] = sp.Rational(cnt(k - int(str(sy)[1:])))
            if ee.subs(sub) != sp.Rational(cnt(k)):
                ok = False; break
        return 'recurrence (checked n = %d..%d): %s' % (start + 12, start + 59, ok)
    ee = to_sympy(text)
    ok = all(ee.subs(n, k) == sp.Rational(cnt(k)) for k in range(start, start + 60))
    return 'closed form for n >= %d: %s' % (start, ok)

report = []
for aid in sorted(ids):
    nd, s, q = ids[aid]
    lines = entries[aid]
    F = [l[11:] for l in lines if l.startswith('%F')]
    b = bfile(aid)
    if not b:
        d = entry_data(lines)
        b = {i + 1: v for i, v in enumerate(d)}
    rng = sorted(b)
    if nd:
        G = nd_total(q, s)
        cnt = lambda k, G=G, s=s: nd_count(G, k + s)
        formula = nd_formula(G, s)
        poly = sp.Poly(formula, n)
        closed = lambda k, poly=poly: poly.eval(k)
    else:
        tot = egf_total(q, s)
        cnt = lambda k, tot=tot, s=s: arr_count(tot, k + s)
        def closed(k, tot=tot, s=s):
            m = k + s; r = Fraction(0)
            for (a, kk), c in tot.items():
                if kk and m >= a:
                    r += c * Fraction(factorial(m), factorial(m - a)) * kk ** (m - a)
            return r
        terms = arr_formula(tot, s)
        formula = sum(c * sp.Integer(k) ** n for k, c in terms)
    exact_ok = all(cnt(k) == b[k] for k in rng)
    fails = [k for k in range(1, 45) if sp.Rational(closed(k)) != sp.Rational(cnt(k))]
    n0 = (max(fails) + 1) if fails else 1
    checks = [check_existing(e, cnt) for e in parse_existing(F)]
    report.append(dict(id=aid, kind='nondecreasing' if nd else 'arrangements', q=q, s=s,
                       bfile_terms=len(rng), exact_equals_data=exact_ok, closed_form_from_n=n0,
                       formula=str(formula), existing=checks))
    print('%s %-8s q=%d s=%d  data %d terms equal: %s  closed form for n >= %d  existing: %s'
          % (aid, 'nondecr' if nd else 'arrange', q, s, len(rng), exact_ok, n0, '; '.join(checks) or '-'),
          flush=True)
json.dump(report, open('%s/family_report.json' % R, 'w', encoding='utf-8'), indent=1)
