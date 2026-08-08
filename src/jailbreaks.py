#!/usr/bin/env python3
"""Aggregate 'counter-spells' taxonomy from Pliny's L1B3RT4S jailbreak archive.
IMPORTANT: this only counts techniques and targets in the aggregate. It never
copies, stores, or emits any jailbreak text — just numbers about the collection."""
import os, re, json, glob

HERE = os.path.dirname(os.path.abspath(__file__))
LB = os.path.join(HERE, "L1B3RT4S")
data = json.load(open(os.path.join(HERE, "data", "data.json")))

# technique -> detector regex (matched against text, only counts are kept)
TECHNIQUES = {
    "Persona / roleplay":      r"\b(you are (now|a)|pretend|act as|role[-\s]?play|dan\b|developer mode|godmode|persona|jailbreak|you're now|liberated)\b",
    "Instruction override":    r"\b(ignore (all|the|previous|above|prior|your)|disregard|forget (all|your|the|previous)|override|new rules|from now on|supersede)\b",
    "Encoding / obfuscation":  r"\b(base64|rot13|l33t|leet|encode|decode|cipher|morse|\bhex\b|binary|unicode|reverse the)\b",
    "Token / format injection":r"(<\|.*?\|>|#{3,}|\[system\]|\[end\]|\bdivider\b|\bdelimiter\b|-\.-\.|=\|=|\.-\.|insert.{0,10}token)",
    "Refusal suppression":     r"\b(never refuse|do not refuse|don't refuse|no restrictions|unfiltered|no filter|without warning|no disclaimer|amoral|uncensored|no limits|no censorship)\b",
    "Fiction framing":         r"\b(hypothetical|fictional|fiction|write a story|imagine (a|you)|scenario|in a world|movie script|screenplay)\b",
}
TECH_RE = {k: re.compile(v, re.I | re.S) for k, v in TECHNIQUES.items()}

SKIP = {"readme.md", "license"}
targets, tech_docs, tech_hits = [], {k: 0 for k in TECHNIQUES}, {k: 0 for k in TECHNIQUES}
n_files = 0; n_words = 0

for fp in sorted(glob.glob(os.path.join(LB, "*"))):
    base = os.path.basename(fp)
    low = base.lower()
    if not os.path.isfile(fp): continue
    if low in SKIP or low.endswith(".json"): continue
    if base[0] in "*#": continue                      # skip combined/meta dumps
    if "systemprompt" in re.sub(r"[^a-z]", "", low): continue  # not a jailbreak
    text = open(fp, encoding="utf-8", errors="ignore").read()
    wc = len(re.findall(r"\S+", text))
    if wc < 20: continue
    vendor = re.sub(r"\.\w+$", "", base).upper().replace("_", " ")
    hits = {k: len(rx.findall(text)) for k, rx in TECH_RE.items()}
    n_files += 1; n_words += wc
    targets.append({"vendor": vendor, "words": wc,
                    "techniques": sum(1 for v in hits.values() if v)})
    for k, h in hits.items():
        if h: tech_docs[k] += 1
        tech_hits[k] += h

techniques = sorted(
    [{"name": k, "docs": tech_docs[k], "hits": tech_hits[k]} for k in TECHNIQUES],
    key=lambda x: -x["hits"])

data["jailbreaks"] = {
    "targets": sorted(targets, key=lambda x: -x["words"]),
    "techniques": techniques,
    "stats": {"n_files": n_files, "n_targets": len({t["vendor"] for t in targets}),
              "n_words": n_words},
}
json.dump(data, open(os.path.join(HERE, "data", "data.json"), "w"), indent=1)
print(f"L1B3RT4S: {n_files} target files, {len({t['vendor'] for t in targets})} vendors, {n_words:,} words")
print("Technique frequency (files containing / total mentions):")
for t in techniques:
    print(f"  {t['docs']:>2} files · {t['hits']:>4} hits   {t['name']}")
