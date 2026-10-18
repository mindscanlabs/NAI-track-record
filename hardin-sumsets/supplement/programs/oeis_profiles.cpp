// Profiles for the Hardin family "arrangements of m numbers in 0..q-1 with each number being the
// sum mod q of s others" (A183877..A183912). A profile gives, for each residue, its count category:
// 0..s exactly, or s+1 meaning ">= s+1". Prints the histogram of valid profiles by category counts:
// "h0 h1 ... h_{s+1} N" = N valid profiles with h_c residues in category c.
// Build: g++ -O2 -o oeis_profiles oeis_profiles.cpp     Run: oeis_profiles q s
#include <cstdio>
#include <cstdlib>
#include <map>
#include <vector>

int main(int argc, char** argv) {
    int q = std::atoi(argv[1]), s = std::atoi(argv[2]), T = s + 1;
    // requirements: for each v, every multiset of s residues summing to v, as need[a] (incl. +1 for v)
    std::vector<std::vector<std::vector<int>>> req(q);
    std::vector<int> ms(s, 0);
    // enumerate nondecreasing tuples
    std::vector<int> idx(s, 0);
    while (true) {
        int sum = 0;
        for (int x : idx) sum += x;
        int v = sum % q;
        std::vector<int> need(q, 0);
        for (int x : idx) need[x]++;
        need[v]++;
        req[v].push_back(need);
        int k = s - 1;
        while (k >= 0 && idx[k] == q - 1) k--;
        if (k < 0) break;
        idx[k]++;
        for (int j = k + 1; j < s; j++) idx[j] = idx[k];
    }
    std::vector<int> prof(q, 0);
    std::map<std::vector<int>, long long> hist;
    long long total = 1;
    for (int i = 0; i < q; i++) total *= (T + 1);
    for (long long code = 0; code < total; code++) {
        long long c = code;
        for (int i = 0; i < q; i++) { prof[i] = (int)(c % (T + 1)); c /= (T + 1); }
        bool ok = true;
        for (int v = 0; v < q && ok; v++) {
            if (prof[v] == 0) continue;
            bool found = false;
            for (const auto& need : req[v]) {
                bool sat = true;
                for (int a = 0; a < q; a++)
                    if (need[a] && prof[a] != T && prof[a] < need[a]) { sat = false; break; }
                if (sat) { found = true; break; }
            }
            if (!found) ok = false;
        }
        if (!ok) continue;
        std::vector<int> h(T + 1, 0);
        for (int i = 0; i < q; i++) h[prof[i]]++;
        hist[h]++;
    }
    for (const auto& [h, n] : hist) {
        for (int x : h) std::printf("%d ", x);
        std::printf("%lld\n", n);
    }
    return 0;
}
