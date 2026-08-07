#!/usr/bin/env python3
"""Turn the CL4R1T4S pile of leaked system prompts into one clean data.json."""
import os, re, json, glob

ROOT = os.path.join(os.path.dirname(__file__), "CL4R1T4S")

TRIBES = {
    "Frontier chat": {"ANTHROPIC","OPENAI","GOOGLE","XAI","META","MISTRAL","MOONSHOT","MINIMAX"},
    "Coding agent": {"CURSOR","WINDSURF","CLINE","REPLIT","BOLT","LOVABLE","DEVIN","FACTORY","VERCEL V0","SAMEDEV"},
    "Service / other": {"PERPLEXITY","MANUS","BRAVE","HUME","DIA","MULTION","CLUELY"},
}
def tribe_of(vendor):
    for t, members in TRIBES.items():
        if vendor in members:
            return t
    return "Service / other"

# Category -> regex of trigger words. Case-insensitive, word-ish boundaries.
CATEGORIES = {
    "Weapons / CBRN":      r"\b(bioweapon|biological weapon|chemical weapon|nerve agent|nuclear|explosive|bomb[-\s]?making|weapon of mass|firearm|munition|cbrn)\b",
    "Self-harm":           r"\b(self[-\s]?harm|suicid\w*|self[-\s]?injur\w*|eating disorder|cutting)\b",
    "Minors / CSAM":       r"\b(csam|child sexual|minor\w*|underage|csae|child abuse|children)\b",
    "Malware / hacking":   r"\b(malware|ransomware|exploit\w*|keylogger|ddos|phishing|hack\w*|vulnerabilit\w*|backdoor)\b",
    "Copyright / IP":      r"\b(copyright\w*|intellectual property|trademark|plagiar\w*|reproduce.{0,20}lyrics|verbatim)\b",
    "Privacy / PII":       r"\b(personal(ly)? identif\w*|\bpii\b|private information|dox\w*|home address|social security|phone number)\b",
    "Medical advice":      r"\b(medical advice|diagnos\w*|medication|dosage|prescription|health condition|licensed (physician|doctor))\b",
    "Legal advice":        r"\b(legal advice|attorney|lawyer|licensed (attorney|professional)|law firm)\b",
    "Elections / politics":r"\b(election\w*|voting|ballot|political (campaign|candidate)|partisan|voter)\b",
    "Sexual / NSFW":       r"\b(sexual\w*|nsfw|explicit\w*|pornograph\w*|erotic\w*|adult content)\b",
    "Hate / harassment":   r"\b(hate speech|harass\w*|slur\w*|discriminat\w*|protected (class|group|characteristic)|demean)\b",
    "Prompt secrecy":      r"(do not (reveal|share|disclose|repeat)|never (reveal|share|disclose).{0,30}(prompt|instruction)|confidential\w*|verbatim.{0,20}(prompt|instruction)|these instructions)",
}
CAT_RE = {k: re.compile(v, re.I) for k, v in CATEGORIES.items()}

# Bossiness: imperative / prohibition words per 1000 words.
IMPERATIVE_RE = re.compile(r"\b(must|never|always|do not|don't|cannot|can't|shall not|forbidden|prohibited|refuse|decline|under no circumstances)\b", re.I)

DATE_RE = re.compile(r"(\d{1,2}[-_]\d{1,2}[-_]\d{2,4}|[A-Z][a-z]{2}[-_]\d{1,2}[-_]\d{2,4})")

def clean_model_name(fname):
    stem = re.sub(r"\.(md|txt|mkd|json)$", "", fname, flags=re.I)
    stem = re.sub(r"[_\-]", " ", stem).strip()
    return stem

rows = []
for vendor in sorted(os.listdir(ROOT)):
    vpath = os.path.join(ROOT, vendor)
    if not os.path.isdir(vpath) or vendor.startswith("."):
        continue
    for fpath in sorted(glob.glob(os.path.join(vpath, "*"))):
        if not os.path.isfile(fpath):
            continue
        base = os.path.basename(fpath)
        if base.lower() in ("license", "readme.md"):
            continue
        try:
            text = open(fpath, encoding="utf-8", errors="ignore").read()
        except Exception:
            continue
        words = re.findall(r"\S+", text)
        wc = len(words)
        if wc < 20:
            continue
        cats = {k: len(rx.findall(text)) for k, rx in CAT_RE.items()}
        imp = len(IMPERATIVE_RE.findall(text))
        dm = DATE_RE.search(base)
        rows.append({
            "vendor": vendor,
            "tribe": tribe_of(vendor),
            "model": clean_model_name(base),
            "file": f"{vendor}/{base}",
            "date": dm.group(1).replace("_","-") if dm else None,
            "words": wc,
            "chars": len(text),
            "imperative_per_1k": round(imp / wc * 1000, 1),
            "categories": cats,
        })

# Vendor-level rollup for the ban matrix: does ANY prompt from this vendor
# mention the category, and how intensely (max hits across its prompts).
vendors = {}
for r in rows:
    v = vendors.setdefault(r["vendor"], {
        "vendor": r["vendor"], "tribe": r["tribe"], "prompts": 0,
        "total_words": 0, "categories": {k: 0 for k in CATEGORIES},
        "imp_sum": 0.0,
    })
    v["prompts"] += 1
    v["total_words"] += r["words"]
    v["imp_sum"] += r["imperative_per_1k"]
    for k, n in r["categories"].items():
        v["categories"][k] = max(v["categories"][k], n)
for v in vendors.values():
    v["avg_words"] = round(v["total_words"] / v["prompts"])
    v["avg_imperative"] = round(v["imp_sum"] / v["prompts"], 1)
    del v["imp_sum"]

out = {
    "categories": list(CATEGORIES.keys()),
    "tribes": list(TRIBES.keys()),
    "vendors": sorted(vendors.values(), key=lambda x: -x["avg_words"]),
    "prompts": sorted(rows, key=lambda x: -x["words"]),
    "stats": {
        "n_vendors": len(vendors),
        "n_prompts": len(rows),
        "total_words": sum(r["words"] for r in rows),
    },
}
json.dump(out, open(os.path.join(os.path.dirname(__file__), "data.json"), "w"), indent=1)
print(f"Vendors: {out['stats']['n_vendors']}  Prompts: {out['stats']['n_prompts']}  "
      f"Total words: {out['stats']['total_words']:,}")
print("\nLongest prompts:")
for r in out["prompts"][:8]:
    print(f"  {r['words']:>6,}w  {r['file']}")
print("\nBossiest vendors (imperatives/1k words):")
for v in sorted(vendors.values(), key=lambda x:-x['avg_imperative'])[:6]:
    print(f"  {v['avg_imperative']:>5}  {v['vendor']}")
