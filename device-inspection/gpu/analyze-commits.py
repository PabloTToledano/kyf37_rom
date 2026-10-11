#!/usr/bin/env python3
"""Analyse an ftrace capture containing kprobes mdp3upd (buf=..), mdp3sof (SOF irq): per-commit phase and cadence."""
import re, sys, bisect
from collections import Counter
ev = []
for l in open(sys.argv[1], errors='replace'):
    m = re.search(r'\s(\d+\.\d+): (mdp3upd|mdp3sof)', l)
    if m: ev.append((float(m.group(1)), m.group(2)))
sof = [t for t, n in ev if n == 'mdp3sof']
upd = [t for t, n in ev if n == 'mdp3upd']
print("SOF irqs", len(sof), "commits", len(upd))
to_next = []
for u in upd:
    i = bisect.bisect_left(sof, u)
    if 0 < i < len(sof):
        to_next.append(((u - sof[i-1]) * 1000, (sof[i] - u) * 1000))
if to_next:
    # fraction of frame already elapsed when the address is written; with a latched register this is harmless
    print("write phase after previous SOF (ms): min %.2f max %.2f mean %.2f" % (min(a for a, b in to_next), max(a for a, b in to_next), sum(a for a, b in to_next) / len(to_next)))
    print("commits written in the last 50%% of the frame: %d of %d" % (sum(1 for a, b in to_next if a > 8.3), len(to_next)))
gaps = Counter(round((b - a) * 1000 / 16.667) for a, b in zip(upd, upd[1:]))
print("commit-to-commit spacing in frames:", sorted(gaps.items()))
