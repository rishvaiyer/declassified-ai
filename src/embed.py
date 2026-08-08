#!/usr/bin/env python3
"""TF-IDF (word 1-2 grams + char 4-grams) similarity over every rulebook.
Writes a 'map' block: 2-D MDS coords, cross-company cousin, and a graph
edge-list (top neighbours) for the force-directed web. No heavy deps — numpy only."""
import os, re, json, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "data", "data.json")))
texts = json.load(open(os.path.join(HERE, "data", "texts.json")))

STOP = set("""the a an and or but if then else for to of in on at by with from as is are was were be been
being this that these those it its you your we our they them their i me my will would can could should
may might must do does did not no yes so than too very just also which who what when where why how all
any both each more most other some such only own same up down out over under again here there about into
through please use using used user assistant system prompt model response help provide make sure ensure""".split())

def words(t):
    toks = [w for w in re.findall(r"[a-z][a-z'\-]{2,}", t.lower()) if w not in STOP]
    grams = list(toks)
    grams += [f"{toks[i]}_{toks[i+1]}" for i in range(len(toks)-1)]   # bigrams
    return grams
def chargrams(t):
    s = re.sub(r"\s+", " ", t.lower())
    return [s[i:i+4] for i in range(0, max(0, len(s)-4), 2)]          # char 4-grams, stride 2

meta = data["prompts"]
docs = []
for p in meta:
    t = texts.get(p["uid"], "")
    docs.append(words(t) + chargrams(t))

N = len(docs)
df = {}
for d in docs:
    for w in set(d):
        df[w] = df.get(w, 0) + 1
# keep informative terms: seen in >=3 docs, not in >45% of docs; cap vocab
band = [(w, c) for w, c in df.items() if 3 <= c <= 0.45*N]
band.sort(key=lambda x: x[1])                 # rarer (more specific) first
vocab = {w: i for i, (w, _) in enumerate(band[:14000])}
V = len(vocab)
idf = np.zeros(V)
for w, i in vocab.items():
    idf[i] = math.log((1+N)/(1+df[w])) + 1

X = np.zeros((N, V), dtype=np.float32)
for r, d in enumerate(docs):
    for w in d:
        j = vocab.get(w)
        if j is not None: X[r, j] += 1.0
    row = X[r]
    if row.sum():
        row *= idf
        n = np.linalg.norm(row)
        if n: row /= n

S = (X @ X.T).astype(np.float64)
np.clip(S, -1, 1, out=S)
D = np.sqrt(np.maximum(0, 1 - S))

# classical MDS -> 2D (seed positions)
J = np.eye(N) - np.ones((N, N))/N
B = -0.5 * J @ (D**2) @ J
vals, vecs = np.linalg.eigh(B)
idx = np.argsort(vals)[::-1][:2]
coords = vecs[:, idx] * np.sqrt(np.maximum(vals[idx], 0))
mn, mx = coords.min(0), coords.max(0)
coords = (coords - (mn+mx)/2) / ((mx-mn)/2 + 1e-9)

# graph edges: each node linked to its top-3 neighbours (sim >= 0.14), deduped
edges, eset = [], set()
K, THRESH = 3, 0.14
for i in range(N):
    order = np.argsort(S[i])[::-1]
    kept = 0
    for j in order:
        if j == i: continue
        if S[i, j] < THRESH or kept >= K: break
        a, b = (i, int(j)) if i < j else (int(j), i)
        if (a, b) not in eset:
            eset.add((a, b)); edges.append([a, b, round(float(S[i, j]), 3)])
        kept += 1

nodes = []
for i, p in enumerate(meta):
    sims = S[i].copy(); sims[i] = -1
    # closest DIFFERENT-company doc, skipping >0.97 near-identical re-leaks
    cross = [(S[i, j], j) for j in range(N)
             if meta[j]["vendor"] != p["vendor"] and S[i, j] < 0.97]
    csim, cj = max(cross) if cross else (0.0, i)
    nodes.append({"i": i, "uid": p["uid"], "model": p["model"], "vendor": p["vendor"],
                  "tribe": p["tribe"], "words": p["words"],
                  "x": round(float(coords[i, 0]), 4), "y": round(float(coords[i, 1]), 4),
                  "cousin": meta[cj]["model"], "cousin_vendor": meta[cj]["vendor"],
                  "cousin_i": int(cj), "cousin_sim": round(float(csim), 3)})

data["map"] = {"nodes": nodes, "edges": edges}
json.dump(data, open(os.path.join(HERE, "data", "data.json"), "w"), indent=1)
print(f"Embedded {N} rulebooks | vocab {V} | {len(edges)} graph edges")
print("Tightest cross-company pairs:")
xc = sorted(nodes, key=lambda z: -z["cousin_sim"])[:8]
for p in xc:
    print(f"  {p['cousin_sim']:.2f}  {p['vendor']:>10} · {p['model'][:24]:24} <-> {p['cousin_vendor']} · {p['cousin']}")
