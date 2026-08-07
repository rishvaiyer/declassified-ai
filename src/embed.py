#!/usr/bin/env python3
"""TF-IDF similarity + classical MDS 2D projection of every leaked rulebook.
Adds a 'map' block (2D points + nearest cross-company cousin) to data.json."""
import os, re, json, glob, math
import numpy as np

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "CL4R1T4S")
data = json.load(open(os.path.join(HERE, "data.json")))

STOP = set("""the a an and or but if then else for to of in on at by with from as is are was were be been
being this that these those it its it's you your yours we our ours they them their i me my will would
can could should may might must do does did not no yes so than too very just also which who whom what
when where why how all any both each few more most other some such only own same up down out over under
again further once here there when about into through during before after above below between out off
please use using used user assistant system prompt model response help provide make sure ensure give
""".split())

def toks(t):
    return [w for w in re.findall(r"[a-z][a-z'\-]{2,}", t.lower()) if w not in STOP]

# read raw text per prompt (same file list as crunch)
docs, meta = [], []
for p in data["prompts"]:
    fpath = os.path.join(ROOT, p["file"])
    try:
        docs.append(toks(open(fpath, encoding="utf-8", errors="ignore").read()))
        meta.append(p)
    except Exception:
        pass

N = len(docs)
# vocabulary + document frequency
df = {}
for d in docs:
    for w in set(d):
        df[w] = df.get(w, 0) + 1
vocab = {w: i for i, w in enumerate(w for w, c in df.items() if 2 <= c <= N*0.9)}
V = len(vocab)
idf = np.zeros(V)
for w, i in vocab.items():
    idf[i] = math.log((1 + N) / (1 + df[w])) + 1

# tf-idf matrix (l2-normalized rows)
X = np.zeros((N, V))
for r, d in enumerate(docs):
    for w in d:
        j = vocab.get(w)
        if j is not None:
            X[r, j] += 1
    if X[r].sum():
        X[r] = X[r] / X[r].sum() * idf
        nrm = np.linalg.norm(X[r])
        if nrm: X[r] /= nrm

S = X @ X.T                     # cosine similarity (rows are unit vectors)
np.clip(S, -1, 1, out=S)
D = np.sqrt(np.maximum(0, 1 - S))   # distance

# classical MDS -> 2D
J = np.eye(N) - np.ones((N, N)) / N
B = -0.5 * J @ (D**2) @ J
vals, vecs = np.linalg.eigh(B)
idx = np.argsort(vals)[::-1][:2]
coords = vecs[:, idx] * np.sqrt(np.maximum(vals[idx], 0))
# normalize to [-1,1] square
mn, mx = coords.min(0), coords.max(0)
coords = (coords - (mn + mx) / 2) / ((mx - mn) / 2 + 1e-9)

# nearest neighbor overall + nearest cross-company cousin
points = []
for i, p in enumerate(meta):
    sims = S[i].copy(); sims[i] = -1
    nn = int(np.argmax(sims))
    cross = [(S[i, j], j) for j in range(N) if meta[j]["vendor"] != p["vendor"]]
    csim, cj = max(cross) if cross else (0, i)
    points.append({
        "file": p["file"], "model": p["model"], "vendor": p["vendor"],
        "tribe": p["tribe"], "words": p["words"],
        "x": round(float(coords[i, 0]), 4), "y": round(float(coords[i, 1]), 4),
        "cousin": meta[cj]["model"], "cousin_vendor": meta[cj]["vendor"],
        "cousin_i": int(cj), "cousin_sim": round(float(csim), 3),
    })

data["map"] = points
json.dump(data, open(os.path.join(HERE, "data.json"), "w"), indent=1)

# report the juiciest cross-company matches ("copied homework")
print(f"Projected {N} rulebooks. Vocab size {V}.")
print("\nSuspiciously similar ACROSS companies (shared DNA):")
seen = set()
for p in sorted(points, key=lambda z: -z["cousin_sim"])[:12]:
    key = tuple(sorted([p["vendor"], p["cousin_vendor"]]))
    print(f"  {p['cousin_sim']:.2f}  {p['vendor']:>10} · {p['model'][:26]:26}  <->  {p['cousin_vendor']} · {p['cousin']}")
