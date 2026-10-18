"""Direct enumeration of s-covered words for small lengths, compared with the OEIS b-files
(Section "Definitions": the reading "s distinct other positions") and with the profile method,
including the q = 2 columns W_{2,2}(m) = 2^m - m - 1 and W_{2,3}(m) = 2^m - 2m.
Run from supplement/programs/:  python brute_force_check.py"""
from itertools import product, combinations

def covered(w, q, s):
    m = len(w)
    for i in range(m):
        others = [w[j] for j in range(m) if j != i]
        if not any(sum(c) % q == w[i] for c in combinations(others, s)):
            return False
    return True

def brute(q, s, m, nondecreasing=False):
    if nondecreasing:
        from itertools import combinations_with_replacement
        words = combinations_with_replacement(range(q), m)
    else:
        words = product(range(q), repeat=m)
    return sum(1 for w in words if covered(w, q, s))

def bfile(aid):
    b = {}
    for line in open('../data/bfiles/b%s.txt' % aid[1:], encoding='utf-8'):
        p = line.split()
        if len(p) >= 2 and not line.startswith('#'):
            b[int(p[0])] = int(p[1])
    return b

ok = True
cases = [('A183881', 7, 2, False, range(1, 6)), ('A183887', 5, 3, False, range(1, 7)),
         ('A183877', 3, 2, False, range(1, 8)), ('A183905', 3, 2, True, range(1, 9)),
         ('A183897', 3, 3, True, range(1, 9))]
for aid, q, s, nd, ns in cases:
    b = bfile(aid)
    res = [(n, brute(q, s, n + s, nd), b[n]) for n in ns]
    good = all(x == y for _, x, y in res)
    ok &= good
    print('%s (q=%d, s=%d, %s): brute force = b-file for n = %d..%d: %s'
          % (aid, q, s, 'nondecreasing' if nd else 'words', ns[0], ns[-1], good))
for s, f in ((2, lambda m: 2**m - m - 1), (3, lambda m: 2**m - 2*m)):
    res = [(m, brute(2, s, m), f(m)) for m in range(s + 1, 13)]
    good = all(x == y for _, x, y in res)
    ok &= good
    print('q=2, s=%d: brute force = closed form for m = %d..12: %s' % (s, s + 1, good))
print('all checks passed:', ok)
