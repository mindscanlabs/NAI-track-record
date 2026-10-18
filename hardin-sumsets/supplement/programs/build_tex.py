"""Builds the LaTeX source of the preprint (written to ../rebuilt/hardin-sumsets.tex) from the verified formula files
in ../data/profiles/. Formulas are converted to LaTeX here, never typed by hand.
Checks: ASCII only, no percent sign, balanced braces and environments, labels/cites defined."""
import json, re, sys

R = '../data/profiles'
arr = json.load(open(R + '/arr_formulas.json'))
nd = json.load(open(R + '/nd_formulas.json'))
rep = {r['id']: r for r in json.load(open(R + '/family_report.json', encoding='utf-8'))}
bases_lines = open(R + '/bases_table.txt').read().splitlines()

def top_split(expr):
    """split 'A - B + C' at depth-0 ' + ' / ' - ' into [(sign, term)]"""
    out, depth, cur, sign, i = [], 0, '', '+', 0
    while i < len(expr):
        ch = expr[i]
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if depth == 0 and expr[i:i + 3] in (' + ', ' - '):
            out.append((sign, cur.strip())); sign = expr[i + 1]; cur = ''; i += 3; continue
        cur += ch; i += 1
    out.append((sign, cur.strip()))
    if out and out[0][1].startswith('-'):
        out[0] = ('-', out[0][1][1:])
    return out

def tex_term(t):
    t = re.sub(r'\^\(([^()]*)\)', r'^{\1}', t)          # k^(n+2) -> k^{n+2}
    t = re.sub(r'\^(\d+)', r'^{\1}', t)                  # n^12 -> n^{12}
    t = re.sub(r'\)\*(\d)', r')\\cdot \1', t)            # (...)*3^{n} -> (...) 3^{n}
    t = re.sub(r'\}\*(\d)', r'}\\cdot \1', t)            # (n+4)^{2}*2^{n} -> (n+4)^{2} 2^{n}
    t = t.replace('*', '')
    t = re.sub(r'\)/(\d+)$', r')/\1', t)
    return t

def nice_term(t):
    """factor a parenthesized polynomial coefficient when that is shorter: (2*n+6)*3^(n+3) -> 2*(n+3)*3^(n+3)"""
    import sympy as sp
    m = re.match(r'^\(([^()]*)\)(\*.*)?$', t)
    if not m:
        return t
    poly, rest = m.group(1), m.group(2) or ''
    n_ = sp.symbols('n')
    f = str(sp.factor(sp.sympify(poly.replace('^', '**'), locals={'n': n_}))).replace('**', '^').replace(' ', '')
    if len(f) < len(poly) and re.fullmatch(r'(\d+\*)?\([^()]*\)(\^\d+)?', f):
        return f + rest
    return t

def tex_formula(text):
    m = re.match(r'a\(n\) = (.*) for n >= (\d+)\.$', text)
    body, n0 = m.group(1), int(m.group(2))
    parts = top_split(body)
    lines = []
    for idx, (sg, t) in enumerate(parts):
        tt = tex_term(nice_term(t))
        if idx == 0:
            lines.append(('-' if sg == '-' else '') + tt)
        else:
            lines.append(sg + ' ' + tt)
    return lines, n0

def tex_poly_over(text):
    m = re.match(r'a\(n\) = \((.*)\)/(\d+) for n >= (\d+)\.$', text)
    if m:
        num, den, n0 = m.group(1), m.group(2), int(m.group(3))
        num = re.sub(r'\^(\d+)', r'^{\1}', num).replace('*', '')
        return r'\frac{%s}{%s}' % (num, den), n0
    m = re.match(r'a\(n\) = (.*) for n >= (\d+)\.$', text)
    return re.sub(r'\^(\d+)', r'^{\1}', m.group(1)).replace('*', ''), int(m.group(2))

def bases_rows():
    rows = []
    for line in bases_lines:
        m = re.match(r's=(\d) q=\s*(\d+): (.*?)\s+\|', line)
        s, q, rest = int(m.group(1)), int(m.group(2)), m.group(3)
        items = re.findall(r'(\d+)\^n\(deg (\d+)\)', rest)
        rows.append((s, q, ', '.join('$%s^m$ (%s)' % (k, d) if k != '1' else '$1$ (%s)' % d for k, d in items)))
    return rows

def arr_block(ids):
    out = []
    for a in ids:
        lines, n0 = tex_formula(arr[a]['text'])
        r = rep[a]
        out.append(r'\noindent\seqnum{%s} ($q=%d$, $n_0 = %d$):' % (a, r['q'], n0))
        if sum(len(l) for l in lines) < 60:
            out.append(r'\[ a(n) = %s. \]' % ' '.join(lines))
            out.append('')
            continue
        out.append(r'\begin{align*}')
        out.append(r'a(n) &= ' + lines[0] + r' \\')
        for l in lines[1:-1]:
            out.append(r'&\quad ' + l + r' \\')
        if len(lines) > 1:
            out.append(r'&\quad ' + lines[-1] + '.')
        else:
            out[-1] = out[-1].rstrip(' \\') + '.'
        out.append(r'\end{align*}')
        out.append('')
    return '\n'.join(out)

def nd_block():
    out = []
    for s_ in (2, 3):
        for a in sorted(nd):
            v = nd[a]
            if v['s'] != s_:
                continue
            f, n0 = tex_poly_over(v['text'])
            out.append(r'\noindent\seqnum{%s} ($q=%d$, $s=%d$, $n_0 = %d$):' % (a, v['q'], v['s'], n0))
            m = re.match(r'\\frac\{(.*)\}\{(\d+)\}$', f)
            if m and len(m.group(1)) > 60:
                terms = re.findall(r'[+-]?[^+-]+', m.group(1))
                rows, cur = [], ''
                for t in terms:
                    if len(cur) + len(t) > 55 and cur:
                        rows.append(cur); cur = ''
                    cur += t
                rows.append(cur)
                out.append(r'\begin{align*}')
                out.append(r'a(n) &= \frac{1}{%s}\bigl(%s \\' % (m.group(2), rows[0]))
                for rr in rows[1:-1]:
                    out.append(r'&\qquad %s \\' % rr)
                out.append(r'&\qquad %s\bigr).' % rows[-1])
                out.append(r'\end{align*}')
            else:
                out.append(r'\[ a(n) = %s. \]' % f)
            out.append('')
    return '\n'.join(out)

def nd_rows(s):
    out = []
    for a in sorted(nd):
        v = nd[a]
        if v['s'] != s:
            continue
        f, n0 = tex_poly_over(v['text'])
        out.append(r'\seqnum{%s} & $%d$ & $\displaystyle %s$ & $%d$ \\[1ex]' % (a, v['q'], f, n0))
    return '\n'.join(out)

SEQS = sorted(set(['A183877', 'A183878', 'A183879', 'A183880', 'A183881', 'A183882', 'A183883', 'A183884',
                   'A183885', 'A183886', 'A183887', 'A183888', 'A183889', 'A183890', 'A183891', 'A183892',
                   'A183897', 'A183898', 'A183899', 'A183900', 'A183901', 'A183902', 'A183903', 'A183904',
                   'A183905', 'A183906', 'A183907', 'A183908', 'A183909', 'A183910', 'A183911', 'A183912',
                   'A000295', 'A005803']))

def concerned():
    s = [r'\seqnum{%s}' % a for a in SEQS]
    return ',\n'.join(s[:-1]) + ', and\n' + s[-1] + '.)\\par}'

TEX = r'''\documentclass[12pt,reqno]{article}

\usepackage[usenames]{color}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{amsthm}
\usepackage{fullpage}
\usepackage[colorlinks=true,
linkcolor=webgreen,
filecolor=webbrown,
citecolor=webgreen]{hyperref}

\definecolor{webgreen}{rgb}{0,.5,0}
\definecolor{webbrown}{rgb}{.6,0,0}

\setlength{\textwidth}{6.5in}
\setlength{\oddsidemargin}{.1in}
\setlength{\evensidemargin}{.1in}
\setlength{\topmargin}{-.1in}
\setlength{\textheight}{8.4in}

\newcommand{\seqnum}[1]{\href{https://oeis.org/#1}{\rm \underline{#1}}}
\newcommand{\Zq}{\mathbb{Z}_q}

\begin{document}

\theoremstyle{plain}
\newtheorem{theorem}{Theorem}
\newtheorem{lemma}[theorem]{Lemma}
\newtheorem{corollary}[theorem]{Corollary}

\theoremstyle{definition}
\newtheorem{definition}[theorem]{Definition}
\newtheorem{example}[theorem]{Example}
\newtheorem{conjecture}[theorem]{Conjecture}

\begin{center}
\vskip 1cm{\LARGE\bf Hardin's Arrangements in Which Every Number\\
\vskip .1in
Is a Sum of Others: Formulas and Sumsets}
\vskip 1cm
\large
Mikhail Smirnov\\
Independent researcher\\
\href{mailto:lab@mindscan.org}{\tt lab@mindscan.org}\\
\vskip .2in
\normalsize Preprint, October 2026
\end{center}

\vskip .2 in

\begin{abstract}
In 2011 Hardin contributed to the OEIS a family of sequences counting
arrangements of residues modulo a fixed integer in which every entry is
the sum of two, or of three, of the other entries; most of them carry
only empirical formulas or conjectures. We show that whether such an arrangement
qualifies depends only on how often each residue occurs, counted up to
a small threshold, which turns the enumeration into a finite sum of
exponential generating functions. Hence every sequence of the family is
eventually a sum of polynomials times exponentials (for ordered
arrangements) or a polynomial (for nondecreasing ones). We give explicit formulas for all twenty-eight
sequences of the family, prove the empirical formulas and conjectures
recorded in the OEIS that were still open, and show that three of the conjectured recurrences
hold only from one step later than stated. We also show that an
exponential with base smaller than the modulus can occur only if some set
of that many residues fails to produce every residue as a sum of two (or
three) of its elements, and we conjecture that this condition is also
sufficient; the conjecture holds in all cases computed.
\end{abstract}

\section{Introduction}\label{sec:intro}

Fix integers $q \ge 2$ and $s \ge 2$. In January 2011 Hardin contributed to
the On-Line Encyclopedia of Integer Sequences \cite{oeis} a family of
sequences with titles such as ``Number of arrangements of $n+2$ numbers in
$0..6$ with each number being the sum mod $7$ of two others''
(\seqnum{A183881}), for sums of two or of three others and $3 \le q \le 9$,
together with the corresponding ``nondecreasing arrangements'' and four
tables collecting them; see Table~\ref{tab:family}.

\begin{table}[ht]
\begin{center}
\begin{tabular}{llll}
\hline
family & $s$ & $q = 3, 4, \ldots, 9$ & table \\
\hline
arrangements & $2$ & \seqnum{A183877}--\seqnum{A183883} & \seqnum{A183884} \\
arrangements & $3$ & \seqnum{A183885}--\seqnum{A183891} & \seqnum{A183892} \\
nondecreasing arrangements & $3$ & \seqnum{A183897}--\seqnum{A183903} & \seqnum{A183904} \\
nondecreasing arrangements & $2$ & \seqnum{A183905}--\seqnum{A183911} & \seqnum{A183912} \\
\hline
\end{tabular}
\end{center}
\caption{The thirty-two sequences of Hardin's family.}\label{tab:family}
\end{table}

For many of these sequences the OEIS records formulas only as empirical
(found by fitting the terms) or as conjectures: closed forms by Kotesovec
for $q \le 5$ ($s = 2$) and $q \le 4$ ($s = 3$), polynomial formulas by Hardin
for all nondecreasing arrangements, and conjectured generating functions and
recurrences by Barker. Israel proved the conjectures recorded for
\seqnum{A183877}, and he proved that every column of \seqnum{A183912}
(nondecreasing arrangements, $s = 2$) is eventually a polynomial
\cite{israel}. Eight sequences of the family have no formula at all, and
neither do the four tables.

We prove that all these sequences are of a very simple type. The key
observation (Lemma~\ref{lem:profile}) is that whether a word qualifies
depends only on how many times each residue occurs, counted up to the
threshold $s+1$. Counting words with a prescribed number of occurrences of
each letter is classical, and summing over the finitely many admissible
patterns gives the results: the number of ordered arrangements is
eventually a sum of polynomials times exponentials $k^m$
(Theorem~\ref{thm:words}), and the number of nondecreasing arrangements is
eventually a polynomial in $m$ (Theorem~\ref{thm:multisets}). The
finite sum is evaluated by computer; this gives explicit formulas for all
twenty-eight sequences (Section~\ref{sec:formulas}), settles every empirical formula and conjecture
recorded in the OEIS for the family (all are true, except that three
recurrences hold only from one step later than stated), and supplies formulas
for the sequences that had none (Section~\ref{sec:oeis}).

The exponentials that occur are governed by additive structure
(Section~\ref{sec:bases}): $k^m$ with $k < q$ can occur only if some set of
$k$ residues does not produce every residue as a sum of $s$ of its elements
(Theorem~\ref{thm:gap}); in particular $k^m$ never occurs for $q/2 < k < q$.
We conjecture that this condition is also sufficient
(Conjecture~\ref{conj:bases}) and verify it for $q \le 14$ ($s = 2$) and
$q \le 11$ ($s = 3$).

Israel's argument for \seqnum{A183912} also records each residue only up to
three occurrences; it is the case $s = 2$ of Lemma~\ref{lem:profile} for
nondecreasing words, and our Theorem~\ref{thm:multisets} extends his result.
Apart from these results in the OEIS we have not found earlier work on these
counts. In additive combinatorics a
subset of an abelian group is called \emph{sum-full} if every element of it is
a sum of two other elements, possibly equal to each other; Lev, Nagy, and Pach
\cite{lnp} answered a question of Zaimi on such sets. For $s = 2$ the words
counted here are the multiset analogue of sum-full subsets of $\Zq$, with the
two summands taken at distinct positions. Chung, Folkman, and Graham
\cite{cfg} studied a different condition on sequences modulo $n$, namely that
every residue is represented the same number of times as a sum of two entries.

\section{Definitions}\label{sec:defs}

Let $\Zq = \{0, 1, \ldots, q-1\}$ denote the integers modulo $q$.

\begin{definition}
A word $w = w_1 w_2 \cdots w_m$ over $\Zq$ is \emph{$s$-covered} if for every
position $i$ there are $s$ distinct positions $j_1, \ldots, j_s$, all
different from $i$, such that $w_{j_1} + \cdots + w_{j_s} \equiv w_i$ (mod $q$).
\end{definition}

\begin{example}
Over $\mathbb{Z}_7$ the word $112244$ is $2$-covered: $2 = 1 + 1$,
$4 = 2 + 2$, and $1 \equiv 4 + 4$ (mod $7$), each time with two positions
different from the one being covered. The word $001$ is not $2$-covered,
since the only sum of two other entries available for the last position is
$0 + 0 = 0$.
\end{example}

Let $W_{q,s}(m)$ denote the number of $s$-covered words of length $m$, and let
$N_{q,s}(m)$ denote the number of $s$-covered words of length $m$ that are
nondecreasing (equivalently, $s$-covered multisets of size $m$). Hardin's
sequences are $a(n) = W_{q,s}(n+s)$ and $a(n) = N_{q,s}(n+s)$ with offset $1$.
We checked this reading of the definition (``$s$ distinct other positions'')
by brute force against the terms in the OEIS for small $m$.

For a word $w$ and a residue $v$ let $c_v(w)$ be the number of positions $i$
with $w_i = v$. The \emph{profile} of $w$ is the map
$\pi_w \colon \Zq \to \{0, 1, \ldots, s+1\}$,
$\pi_w(v) = \min(c_v(w), s+1)$. We call $v$ \emph{frequent} in $w$ if
$\pi_w(v) = s+1$.

\section{Profiles}\label{sec:profiles}

\begin{lemma}\label{lem:profile}
Whether a word is $s$-covered depends only on its profile.
\end{lemma}

\begin{proof}
Let $w_i = v$. Position $i$ is covered if and only if there is a multiset
$\{a_1, \ldots, a_s\}$ of residues with $a_1 + \cdots + a_s \equiv v$ (mod $q$)
such that for every residue $a$ the multiplicity $\mu_a$ of $a$ in the multiset
satisfies $\mu_a \le c_a(w) - [a = v]$, where $[\cdot]$ is the Iverson
bracket. Since $\mu_a + [a = v] \le s+1$, this inequality holds if and only if
it holds with $c_a(w)$ replaced by $\min(c_a(w), s+1)$. The condition does not
depend on $i$ beyond the letter $w_i$.
\end{proof}

By Lemma~\ref{lem:profile} we may speak of \emph{valid} profiles. Let
$\mathcal{V}_{q,s}$ be the set of valid profiles; it is a subset of the
$(s+2)^q$ maps $\Zq \to \{0, \ldots, s+1\}$.

\begin{lemma}\label{lem:count}
Let $\pi$ be a profile. Put $f_c(t) = t^c/c!$ for $0 \le c \le s$ and
$f_{s+1}(t) = e^t - p_s(t)$, where $p_s(t) = \sum_{j=0}^{s} t^j/j!$. Then the
number of words of length $m$ with profile $\pi$ is
\[
m!\,[t^m] \prod_{v \in \Zq} f_{\pi(v)}(t),
\]
and the number of nondecreasing words of length $m$ with profile $\pi$ is
$[y^m] \prod_{v \in \Zq} g_{\pi(v)}(y)$, where $g_c(y) = y^c$ for $c \le s$ and
$g_{s+1}(y) = y^{s+1}/(1-y)$.
\end{lemma}

\begin{proof}
A word is determined by the sets of positions of its letters, so the
exponential generating function of words with $c_v$ letters $v$, summed over
the allowed values of each $c_v$, is the product of the exponential generating
functions $\sum_c t^c/c!$ over the allowed values \cite[Ch.~II]{fs}. A
nondecreasing word is determined by the counts alone.
\end{proof}

\section{Main results}\label{sec:main}

\begin{theorem}\label{thm:words}
Let $q \ge 2$ and $s \ge 2$. There are polynomials $P_1, \ldots, P_q$ and an
integer $m_0$ such that
\[
W_{q,s}(m) = \sum_{k=1}^{q} P_k(m)\, k^m \qquad (m > m_0).
\]
Moreover $P_q = 1$ and $\deg P_k \le s(q-k)$ whenever $P_k \ne 0$.
Consequently $\sum_{m \ge 0} W_{q,s}(m) x^m$ is a rational function whose
denominator divides $\prod (1 - kx)^{\deg P_k + 1}$, and $W_{q,s}(m)$ satisfies
the linear recurrence with constant coefficients and characteristic polynomial
$\prod (x - k)^{\deg P_k + 1}$ for all sufficiently large $m$, both products
taken over the $k$ with $P_k \ne 0$.
\end{theorem}

\begin{proof}
By Lemmas~\ref{lem:profile} and~\ref{lem:count},
$W_{q,s}(m) = m!\,[t^m] F(t)$ with
$F(t) = \sum_{\pi \in \mathcal{V}_{q,s}} \prod_v f_{\pi(v)}(t)$. A profile
with $r$ frequent residues contributes $(e^t - p_s(t))^r$ times a monomial
of degree at most $s(q-r)$; expanding gives a finite sum
$F(t) = \sum_{a, k} c_{a,k}\, t^a e^{kt}$ with $0 \le k \le q$, and the terms
with a given $k \ge 1$ have $a \le s(q-k)$. Since
$m!\,[t^m]\, t^a e^{kt} = m(m-1)\cdots(m-a+1)\, k^{m-a}$, the terms with
$k \ge 1$ give $P_k(m) k^m$, and the terms with $k = 0$ vanish for $m > m_0$,
where $m_0$ is the largest $a$ with $c_{a,0} \ne 0$. Only the profile in which
every residue is frequent contributes to $e^{qt}$; it is valid, because every
residue is a sum of $s$ residues, which gives $P_q = 1$. The statements on
the generating function and the recurrence follow from the form of
$W_{q,s}(m)$.
\end{proof}

\begin{theorem}\label{thm:multisets}
Let $q \ge 2$ and $s \ge 2$. There is an $m_0$ such that $N_{q,s}(m)$ is a
polynomial in $m$ of degree $q-1$ with leading coefficient $1/(q-1)!$ for
$m > m_0$. Its generating function is rational with denominator dividing
$(1-y)^q$.
\end{theorem}

\begin{proof}
By Lemma~\ref{lem:count} the generating function is
$\sum_{\pi \in \mathcal{V}_{q,s}} y^{e(\pi)}/(1-y)^{r(\pi)}$, where $r(\pi)$ is
the number of frequent residues and $e(\pi) = \sum_v \pi(v)$. For $r \ge 1$
the coefficient of $y^m$ in $y^e/(1-y)^r$ is $\binom{m-e+r-1}{r-1}$, a
polynomial in $m$ of degree $r-1$ for $m \ge e-r+1$; for $r = 0$ it vanishes
for $m > e$. Only the profile in which all residues are frequent has
$r = q$.
\end{proof}

For $s = 2$, the fact that $N_{q,2}(m)$ is eventually a polynomial in $m$ is
due to Israel \cite{israel}, who obtained it from a transfer matrix on the
same states; the degree and the leading coefficient are new.

For a set $B \subseteq \Zq$ let
$sB = \{b_1 + \cdots + b_s : b_1, \ldots, b_s \in B\}$ denote its $s$-fold
sumset (repetitions allowed).

\begin{theorem}\label{thm:gap}
Let $q \ge 2$, $s \ge 2$, and $1 \le k < q$. If $sB = \Zq$ for every set
$B \subseteq \Zq$ of $k$ residues, then $P_k = 0$ in Theorem~\ref{thm:words}.
\end{theorem}

\begin{proof}
Write $f_{s+1} = e^t - p_s$ and expand $F(t)$. A term containing $e^{kt}$
arises from a valid profile together with a set $B$ of $k$ of its frequent
residues, which take the factor $e^t$; every other residue $u \notin B$ takes
the weight $t^j/j!$ if $\pi(u) = j \le s$, and the weight $-p_s(t)$ if $u$ is
frequent. Fix $B$ with $sB = \Zq$ and suppose that all residues of $B$ are
frequent. Every residue $v$ can be written as $b_1 + \cdots + b_s$ with
$b_i \in B$; a residue occurs at most $s$ times among the summands, and at most
$s+1$ times if the covered position is counted, so the frequent residues
supply enough distinct positions. Hence every profile in which $B$ is frequent
is valid, whatever the states of the residues outside $B$, and the total
weight of these states is
$\prod_{u \notin B} \bigl(\sum_{j=0}^{s} t^j/j! - p_s(t)\bigr) = 0$, since
$k < q$. Summing over $B$ gives $P_k = 0$.
\end{proof}

\begin{corollary}\label{cor:gap}
Let $q \ge 2$ and $s \ge 2$.
\begin{enumerate}
\item $P_k = 0$ for $q/2 < k < q$.
\item If $q$ is prime, then $P_k = 0$ for $(q-1)/s + 1 \le k < q$.
\end{enumerate}
\end{corollary}

\begin{proof}
If $|B| = k > q/2$, then for every residue $v$ the sets $B$ and $v - B$ meet,
so $v \in B + B$. Hence $B + B = \Zq$, and $sB = \Zq$ for every $s \ge 2$. If $q$
is prime, the Cauchy--Davenport theorem \cite{dav}, applied $s - 1$ times, gives
$|sB| \ge \min(q, s(k-1)+1)$, which equals $q$ for $k \ge (q-1)/s + 1$. In both
cases Theorem~\ref{thm:gap} applies.
\end{proof}

\section{Explicit formulas}\label{sec:formulas}

In this section $a(n)$ denotes the corresponding OEIS sequence (offset $1$),
that is, $a(n) = W_{q,s}(n+s)$ or $a(n) = N_{q,s}(n+s)$. For each sequence
we give a number $n_0$ and an expression; the statement is that $a(n)$ equals
the expression for all $n \ge n_0$ and differs from it for $1 \le n < n_0$.

\begin{theorem}\label{thm:explicit}
For the arrangements with $s = 2$, the following holds.

ARR_S2
\end{theorem}

\begin{theorem}\label{thm:explicit3}
For the arrangements with $s = 3$, the following holds.

ARR_S3
\end{theorem}

\begin{theorem}\label{thm:explicitnd}
For the nondecreasing arrangements, the following holds.

ND_ALL
\end{theorem}

\begin{proof}[Proof of Theorems~\ref{thm:explicit}--\ref{thm:explicitnd}]
By the proofs of Theorems~\ref{thm:words} and~\ref{thm:multisets}, each
sequence is given by an explicit finite sum over the valid profiles. We
computed the set $\mathcal{V}_{q,s}$ and expanded these sums in exact rational
arithmetic (Section~\ref{sec:computation}); this gives the expressions above,
valid for $n + s > m_0$. For the finitely many remaining $n$ the expressions
were compared with the exact counts, which gives $n_0$.
\end{proof}

\section{Consequences for the OEIS}\label{sec:oeis}

Theorems~\ref{thm:explicit}--\ref{thm:explicitnd} settle the formulas
recorded for the family in the OEIS.

\begin{itemize}
\item The empirical closed forms of Kotesovec for \seqnum{A183877},
\seqnum{A183878}, \seqnum{A183879}, \seqnum{A183885}, and \seqnum{A183886},
the empirical polynomial formulas of Hardin for \seqnum{A183897}--\seqnum{A183903}
and \seqnum{A183905}--\seqnum{A183911}, and the conjectured generating
functions and recurrences of Barker for these sequences (except
\seqnum{A183902} and \seqnum{A183903}, which have none) are all true, with
the ranges of validity stated there, with three exceptions given in the next
item. For \seqnum{A183877} this was already proved by Israel in the OEIS
entry. The description of \seqnum{A183905} as triangular numbers minus $11$ is
also correct: $a(n) = \binom{n+4}{2} - 11$ for $n \ge 2$.
\item The recurrences of Barker for \seqnum{A183908}, \seqnum{A183910}, and
\seqnum{A183911}, stated for $n > 7$, $n > 10$, and $n > 11$, hold exactly for
$n > 8$, $n > 11$, and $n > 12$. This agrees with
Theorem~\ref{thm:explicitnd}: a polynomial formula valid for $n \ge n_0$ of
degree $d - 1$ gives the recurrence of order $d$ for $n \ge n_0 + d$.
\item The conjectured closed form and generating function of
\seqnum{A183880} are true.
\item \seqnum{A183881}--\seqnum{A183883} and \seqnum{A183887}--\seqnum{A183891}
had no formula; Theorems~\ref{thm:explicit} and~\ref{thm:explicit3} supply
one.
\item Every column of the tables \seqnum{A183884}, \seqnum{A183892},
\seqnum{A183904}, and \seqnum{A183912} is described by
Theorem~\ref{thm:words} or Theorem~\ref{thm:multisets}, including the
columns for $q = 2$. For these the same computation gives
$W_{2,2}(m) = 2^m - m - 1$ and $W_{2,3}(m) = 2^m - 2m$ for $m \ge s+1$ (that is,
for all $n \ge 1$ in the OEIS indexing), which
proves that the first columns of \seqnum{A183884} and \seqnum{A183892} are
\seqnum{A000295} and \seqnum{A005803}, as stated in the OEIS.
\end{itemize}

\section{Which exponentials occur}\label{sec:bases}

Table~\ref{tab:bases} lists, for $s \in \{2, 3\}$, the values $k$ with
$P_k \ne 0$ in Theorem~\ref{thm:words} together with $\deg P_k$.

\begin{table}[ht]
\begin{center}
\begin{tabular}{lll}
\hline
$s$ & $q$ & exponentials (degree of $P_k$) \\
\hline
BASES
\hline
\end{tabular}
\end{center}
\caption{Exponentials $k^m$ in $W_{q,s}(m)$.}\label{tab:bases}
\end{table}

Let
\[
K(q,s) = \max\{|B| : B \subseteq \Zq,\ sB \ne \Zq\}.
\]
Every subset of a set $B$ with $sB \ne \Zq$ has the same property, so sets of
every size $k \le K(q,s)$ fail to cover $\Zq$, and by Theorem~\ref{thm:gap} we
have $P_k = 0$ for $K(q,s) < k < q$. For instance $K(q,2) = \lfloor q/2 \rfloor$,
as Corollary~\ref{cor:gap} and the set $\{0, 1, \ldots, \lfloor q/2 \rfloor - 1\}$
show; $K(q,3) = q/2$ for even $q$ (take the even residues); and for prime $q$ the
Cauchy--Davenport bound is attained by arithmetic progressions, so
$K(q,3)$ is the largest $k$ with $3k - 2 < q$. Table~\ref{tab:bases} shows that
the converse of Theorem~\ref{thm:gap} holds in every computed case.

\begin{conjecture}\label{conj:bases}
For $q \ge 2$, $s \ge 2$, and $1 \le k < q$, we have $P_k \ne 0$ if and only if
$k \le K(q,s)$. Equivalently, the exponentials in $W_{q,s}(m)$ are exactly
$q^m$ and $k^m$ for $1 \le k \le K(q,s)$.
\end{conjecture}

We verified Conjecture~\ref{conj:bases} for $q \le 14$ when $s = 2$ and for
$q \le 11$ when $s = 3$; the cases $q = 13$ and $q = 14$ with $s = 2$ were
computed after the pattern had been noticed in the smaller cases. The proved
part, Corollary~\ref{cor:gap}, already explains some absences below $q/2$: for
instance $3^m$ does not occur for $q = 7$ and $s = 3$, although $3 < 7/2$,
because every set of three residues modulo $7$ produces all residues as sums of
three of its elements.

\section{Computation}\label{sec:computation}

The set $\mathcal{V}_{q,s}$ was obtained by testing all $(s+2)^q$ profiles
with Lemma~\ref{lem:profile}; for $q \le 9$ this takes about a second per pair
$(q, s)$ in C++, $40$ seconds for $q = 11$, $s = 3$, and about three minutes
for $q = 14$, $s = 2$. For instance
$|\mathcal{V}_{7,2}| = 13234$ and $|\mathcal{V}_{5,3}| = 2640$. Since the
product in Lemma~\ref{lem:count} depends only on how many residues fall into
each class, it suffices to record the histogram of the valid profiles by the
numbers of residues with each value of $\pi$. The sums were then expanded in
exact rational arithmetic. As checks, the resulting counts agree with all
terms of the OEIS entries (up to $n = 200$), each formula in
Section~\ref{sec:formulas} was evaluated from its printed form and compared
with the exact counts for at least sixty consecutive values of $n$, and the
counts for small $m$ were confirmed by direct enumeration of words. The
programs and the computed data are available at
\href{https://github.com/mindscanlabs/NAI-track-record/tree/main/hardin-sumsets}{\tt github.com/mindscanlabs/NAI-track-record}.

\section{Acknowledgments}\label{sec:ack}

The closed forms for \seqnum{A183880}, \seqnum{A183881}, and
\seqnum{A183887} were first found from linear recurrences guessed by NAI
(No-Ansatz Inference), the author's program for finding formulas that fit
given data without fixing their form in advance; it does not use language
models. The recurrences were guessed from initial terms and checked against
further terms. Claude (Anthropic), an AI
assistant, carried out the computations of this paper, found the profile
argument, and drafted the proofs and the text. The author checked the
results, takes responsibility for the content, and thanks the editors of the
OEIS for their comments on related submissions.

\begin{thebibliography}{9}

\bibitem{cfg} F. Chung, J. Folkman, and R. Graham, Sum sequences modulo $n$,
\emph{J. Combin. Theory Ser. A} {\bf 158} (2018), 290--314.

\bibitem{dav} H. Davenport, On the addition of residue classes,
\emph{J. London Math. Soc.} {\bf 10} (1935), 30--32.

\bibitem{fs} P. Flajolet and R. Sedgewick, \emph{Analytic Combinatorics},
Cambridge University Press, 2009.

\bibitem{israel} R. Israel, Columns of A183912 are eventually polynomials,
manuscript, 2018. Available at \url{https://oeis.org/A183912/a183912.pdf}.

\bibitem{lnp} V. F. Lev, J. Nagy, and P. P. Pach, Sum-full sets are not
zero-sum-free, \emph{Linear Algebra Appl.} {\bf 625} (2021), 241--247.

\bibitem{oeis} OEIS Foundation Inc., \emph{The On-Line Encyclopedia of Integer
Sequences}, 2026. Available at \url{https://oeis.org}.

\end{thebibliography}

\bigskip
\hrule
\bigskip

\noindent 2020 {\it Mathematics Subject Classification}:
Primary 05A15; Secondary 11B75, 11P70.

\noindent \emph{Keywords:} enumeration, word, residue, sum-full set, sumset,
Cauchy--Davenport theorem, exponential generating function, linear recurrence.

\bigskip
\hrule
\bigskip

\noindent {\sloppy (Concerned with sequences
CONCERNED

\end{document}
'''

def bases_tex():
    rows = []
    for s, q, txt in bases_rows():
        rows.append(r'$%d$ & $%d$ & %s \\' % (s, q, txt))
    return '\n'.join(rows)

arr2 = [a for a in sorted(arr) if rep[a]['s'] == 2]
arr3 = [a for a in sorted(arr) if rep[a]['s'] == 3]
tex = (TEX.replace('ARR_S2', arr_block(arr2)).replace('ARR_S3', arr_block(arr3))
          .replace('ND_ALL', nd_block())
          .replace('BASES', bases_tex()).replace('CONCERNED', concerned()))

# ---- checks
problems = []
if any(ord(ch) > 127 for ch in tex):
    problems.append('non-ASCII characters')
if '%' in tex:
    problems.append('percent sign present')
depth = 0
for i, ch in enumerate(tex):
    if ch == '{' and tex[i - 1] != '\\':
        depth += 1
    elif ch == '}' and tex[i - 1] != '\\':
        depth -= 1
    if depth < 0:
        problems.append('unbalanced } near %d' % i); break
if depth != 0:
    problems.append('brace depth %d at end' % depth)
begins = re.findall(r'\\begin\{(\w+\*?)\}', tex); ends = re.findall(r'\\end\{(\w+\*?)\}', tex)
for env in set(begins) | set(ends):
    if begins.count(env) != ends.count(env):
        problems.append('environment %s: %d begin, %d end' % (env, begins.count(env), ends.count(env)))
labels = set(re.findall(r'\\label\{([^}]+)\}', tex))
for r_ in re.findall(r'\\ref\{([^}]+)\}', tex):
    if r_ not in labels:
        problems.append('undefined ref ' + r_)
bib = set(re.findall(r'\\bibitem\{([^}]+)\}', tex))
for c in re.findall(r'\\cite(?:\[[^\]]*\])?\{([^}]+)\}', tex):
    for k in c.split(','):
        if k.strip() not in bib:
            problems.append('undefined cite ' + k)
for b in bib:
    if not re.search(r'\\cite(?:\[[^\]]*\])?\{[^}]*\b%s\b' % re.escape(b), tex):
        problems.append('uncited bibitem ' + b)
open('../rebuilt/hardin-sumsets.tex', 'w', encoding='ascii', newline='\n').write(tex)
print('written', len(tex.splitlines()), 'lines;', 'problems: ' + '; '.join(problems) if problems else 'no problems found')
