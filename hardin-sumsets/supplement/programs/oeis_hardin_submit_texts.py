"""OEIS texts (FORMULA + Discussion) for the Hardin columns, from verified data. Prints Markdown
sections."""
import json
import sympy as sp

src = open('oeis_hardin_family.py', encoding='utf-8').read(); src = src[:src.index('report = []')]
ns = {}; exec(src, ns); n = ns['n']
arr = json.load(open('../data/profiles/arr_formulas.json'))
rep = {r['id']: r for r in json.load(open('../data/profiles/family_report.json', encoding='utf-8'))}
X = sp.symbols('x')
DATE = 'Oct 18 2026'

def params(aid):
    r = rep[aid]; q, s = r['q'], r['s']; n0 = r['closed_form_from_n']
    nvalid = sum(int(l.split()[-1]) for l in open('../data/profiles/hist_q%d_s%d.txt' % (q, s)))
    tot = ns['egf_total'](q, s)
    byk = {}
    for (a, k), c in tot.items():
        if k:
            ff = sp.Integer(1)
            for i in range(a):
                ff *= (n + s - i)
            byk[k] = byk.get(k, 0) + sp.Rational(c.numerator, c.denominator) * ff * sp.Rational(k) ** (s - a)
    degs = {k: int(sp.degree(sp.expand(v), n)) for k, v in byk.items() if sp.expand(v) != 0}
    order = sum(d + 1 for d in degs.values())
    cpt = '*'.join(('(x-%d)' % k) + ('^%d' % (d + 1) if d > 0 else '') for k, d in sorted(degs.items(), reverse=True))
    k0 = max(a for (a, k), c in tot.items() if k == 0)
    return dict(q=q, s=s, n0=n0, nvalid=nvalid, nprof=(s + 2) ** q, cp=cpt, rec=n0 + order, k0=k0, text=arr[aid]['text'])

def frequent(s):
    terms = ['1', 't'] + ['t^%d/%d' % (j, sp.factorial(j)) if j > 1 else '' for j in range(2, s + 1)]
    return 'e^t - ' + ' - '.join(t for t in terms if t)

def section(aid, title, new):
    p = params(aid)
    s, q = p['s'], p['q']
    word = {2: 'two', 3: 'three'}[s]
    lead = ('The closed form is obtained and proved as follows. ' if new else
            'The closed form was found by guessing from the terms. Proof: ')
    out = []
    out.append('## %s (%s)\n' % (aid, title))
    out.append('**FORMULA**\n```')
    out.append('From _Mikhail Smirnov_, %s: (Start)' % DATE)
    out.append(p['text'])
    out.append('a(n) satisfies a linear recurrence with constant coefficients with characteristic polynomial %s for n >= %d. (End)' % (p['cp'], p['rec']))
    out.append('```')
    out.append('**Discussion**\n```')
    out.append((lead + 'Whether a word of length m = n+%d qualifies depends only on how many times each residue occurs, '
                'counted as %s or at least %d (%s other positions and the position itself need at most %d copies of one residue). '
                'I checked the condition for all %d^%d = %d such profiles; the number of words with a given profile is m!*[t^m] of the product over the residues of '
                't^k/k! (count k <= %d) or %s (count >= %d). Summing over the %d valid profiles gives the closed form above; the terms without an exponential '
                'have degree at most %d in t, so they affect only m <= %d, i.e., n <= %d. The recurrence follows for n >= %d. '
                "This is the same idea as Israel's proof in A183912.")
               % (s, ', '.join(str(i) for i in range(s + 1)), s + 1, word, s + 1, s + 2, q, p['nprof'], s,
                  frequent(s), s + 1, p['nvalid'], p['k0'], p['k0'], p['k0'] - s, p['rec']))
    out.append('```\n')
    return '\n'.join(out), p

if __name__ == '__main__':
    import sys
    for spec in sys.argv[1:]:
        aid, title, new = spec.split(':')
        txt, p = section(aid, title, new == 'new')
        print(txt)
