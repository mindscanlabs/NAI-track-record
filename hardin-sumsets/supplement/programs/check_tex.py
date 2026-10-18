"""Reads the formulas back from the preprint ../../hardin-sumsets.tex (as printed) and checks them against the exact
counts from the profile enumeration, for n0..n0+60."""
import re, sys
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

src = open('oeis_hardin_family.py', encoding='utf-8').read(); src = src[:src.index('report = []')]
ns = {}; exec(src, ns)
n = sp.symbols('n')
T = standard_transformations + (implicit_multiplication_application,)
TEX_PATH = sys.argv[1] if len(sys.argv) > 1 else '../../hardin-sumsets.tex'
tex = open(TEX_PATH, encoding='ascii').read()

def to_expr(s):
    s = ' '.join(s.split())
    s = s.replace(r'\\', ' ').replace('&', ' ').replace(r'\qquad', ' ').replace(r'\quad', ' ')
    s = s.replace(r'\bigl(', '(').replace(r'\bigr)', ')').replace(r'\cdot', '*')
    m = re.match(r'\s*\\frac\{1\}\{(\d+)\}\s*\((.*)\)\s*$', s, re.S)
    if m:
        s = '(%s)/%s' % (m.group(2), m.group(1))
    s = re.sub(r'\^\{([^{}]*)\}', r'**(\1)', s)
    s = re.sub(r'\\frac\{([^{}]*)\}\{(\d+)\}', r'((\1)/\2)', s)
    s = s.replace('{', '(').replace('}', ')')
    s = re.sub(r'(?<!\*)\^', '**', s)
    return parse_expr(s, transformations=T, local_dict={'n': n})

blocks = re.findall(r'\\seqnum\{(A\d+)\} \(\$q=(\d+)\$(?:, \$s=(\d+)\$)?, \$n_0 = (\d+)\$\):\s*(\\begin\{align\*\}(.*?)\\end\{align\*\}|\\\[(.*?)\\\])', tex, re.S)
rep = {r['id']: r for r in __import__('json').load(open('../data/profiles/family_report.json', encoding='utf-8'))}
blocks = [(a, q, s_ if s_ else str(rep[a]['s']), n0, x, y, z) for a, q, s_, n0, x, y, z in blocks]
nd_ids = set('A1838%02d' % i for i in range(97, 100)) | set('A1839%02d' % i for i in range(0, 12))
ok_all = True
for aid, q, s, n0, _, alignbody, displaybody in blocks:
    q, s, n0 = int(q), int(s), int(n0)
    body = alignbody or displaybody
    body = body.replace('a(n) &=', '').replace('a(n) =', '').strip().rstrip('.').strip()
    body = re.sub(r'\.\s*$', '', body)
    e = to_expr(body)
    if aid in nd_ids:
        G = ns['nd_total'](q, s); cnt = lambda k: ns['nd_count'](G, k + s)
    else:
        tot = ns['egf_total'](q, s); cnt = lambda k: ns['arr_count'](tot, k + s)
    good = all(e.subs(n, k) == sp.Rational(cnt(k)) for k in range(n0, n0 + 61))
    fails_below = [k for k in range(1, n0) if e.subs(n, k) != sp.Rational(cnt(k))]
    ok_all &= good and fails_below == list(range(1, n0))
    print('%s q=%d s=%d n>=%d: printed formula %s; fails for all smaller n: %s'
          % (aid, q, s, n0, 'correct' if good else 'WRONG', fails_below == list(range(1, n0))))
print('formulas found:', len(blocks), '; all correct:', ok_all and len(blocks) == 28)
