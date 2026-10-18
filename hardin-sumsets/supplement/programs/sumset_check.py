"""Section "Which exponentials occur": compares the exponentials k^m (k < q) that occur in W_{q,s}(m)
with the k for which some k-element set B of residues has sB != Z_q (s-fold sumset with repetitions).
Theorem (proved): no k^m with K(q,s) < k < q. Conjecture: the k^m with k <= K(q,s) all occur.
Uses the profile histograms ../data/profiles/hist_q{q}_s{s}.txt.
Run from supplement/programs/:  python sumset_check.py"""
from itertools import combinations

src = open('oeis_hardin_family.py', encoding='utf-8').read(); src = src[:src.index('report = []')]
ns = {}; exec(src, ns)

def sumset(B, s, q):
    S = {0}
    for _ in range(s):
        S = {(x + b) % q for x in S for b in B}
    return S

def K(q, s):
    return max([k for k in range(1, q) if any(len(sumset(B, s, q)) < q for B in combinations(range(q), k))] or [0])

all_ok = True
for s, qs in ((2, range(2, 15)), (3, range(2, 12))):
    for q in qs:
        tot = ns['egf_total'](q, s)
        occur = sorted({k for (a, k), c in tot.items() if k and k < q and c != 0})
        k_max = K(q, s)
        theorem_ok = all(k <= k_max for k in occur)
        conj_ok = occur == list(range(1, k_max + 1))
        all_ok &= theorem_ok and conj_ok
        print('s=%d q=%2d: proper exponentials %s, K(q,s) = %d, theorem %s, conjecture %s'
              % (s, q, occur, k_max, 'ok' if theorem_ok else 'VIOLATED', 'holds' if conj_ok else 'FAILS'))
print('theorem and conjecture hold in all cases:', all_ok)
