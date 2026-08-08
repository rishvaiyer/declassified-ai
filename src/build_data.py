#!/usr/bin/env python3
"""Unified builder: merge CL4R1T4S (Pliny) + leaked-system-prompts (jujumilk3)
into data/data.json + data/texts.json. Dedupes by content hash."""
import os, re, json, glob, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
CL = os.path.join(HERE, "CL4R1T4S")
JU = os.path.join(HERE, "juju")

# ---------- shared analysis ----------
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
IMP_RE = re.compile(r"\b(must|never|always|do not|don't|cannot|can't|shall not|forbidden|prohibited|refuse|decline|under no circumstances)\b", re.I)

VENDOR_MAP = {
    "anthropic":"ANTHROPIC","openai":"OPENAI","xai":"XAI","google":"GOOGLE","deepmind":"GOOGLE",
    "microsoft":"MICROSOFT","meta":"META","mistralai":"MISTRAL","mistral":"MISTRAL","cohere":"COHERE",
    "perplexity":"PERPLEXITY","moonshot":"MOONSHOT","minimax":"MINIMAX","notion":"NOTION","wrtn":"WRTN",
    "zhipu":"ZHIPU","chatglm4":"ZHIPU","bytedance":"BYTEDANCE","xiaomi":"XIAOMI","cursor":"CURSOR",
    "windsurf":"WINDSURF","cline":"CLINE","replit":"REPLIT","bolt":"BOLT","lovable":"LOVABLE","devin":"DEVIN",
    "factory":"FACTORY","manus":"MANUS","brave":"BRAVE","hume":"HUME","dia":"DIA","multion":"MULTION",
    "cluely":"CLUELY","samedev":"SAMEDEV","same":"SAMEDEV","vercel":"VERCEL","v0":"VERCEL","codeium":"WINDSURF",
    "github":"GITHUB","copilot":"GITHUB","codex":"OPENAI","proton":"PROTON","venice":"VENICE","you":"YOU",
    "inflection":"INFLECTION","nous":"NOUS","grok":"XAI",
    "claude":"ANTHROPIC","gpt":"OPENAI","gpt4":"OPENAI","chatgpt":"OPENAI","o1":"OPENAI","o3":"OPENAI",
    "gemini":"GOOGLE","bard":"GOOGLE","palm":"GOOGLE","llama":"META","kimi":"MOONSHOT","perplexityai":"PERPLEXITY",
    "qwen":"ALIBABA","alibaba":"ALIBABA","doubao":"BYTEDANCE","clyde":"DISCORD","leo":"BRAVE","dbrx":"DATABRICKS",
    "bolt":"BOLT","vercel":"VERCEL","perplexity":"PERPLEXITY","lovable":"LOVABLE","replit":"REPLIT",
}
CODE_KW = ("cursor","windsurf","cline","replit","bolt","lovable","devin","factory","codex","copilot",
           "v0","aider","cody","zed","trae","augment","same","droid","code","ide","agent")
SVC_KW  = ("perplexity","notion","brave","hume","dia","manus","multion","cluely","bing","search","voice","assistant")

def normalize_vendor(raw):
    key = re.sub(r"[^a-z0-9]", "", raw.lower())
    if key in VENDOR_MAP: return VENDOR_MAP[key]
    stripped = re.sub(r"(ai|v0|new|dot|inc|labs|llc|app|io|com|ide|dev)$", "", key)
    if stripped in VENDOR_MAP: return VENDOR_MAP[stripped]
    return (stripped or key).upper()

def tribe_of(vendor, model):
    s = f"{vendor} {model}".lower()
    if any(k in s for k in CODE_KW): return "Coding agent"
    if any(k in s for k in SVC_KW):  return "Service / other"
    return "Frontier chat"

DATE8 = re.compile(r"_(\d{8})(?:\D|$)")
DATE_LOOSE = re.compile(r"(\d{1,2}[-_]\d{1,2}[-_]\d{2,4}|[A-Z][a-z]{2}[-_]\d{1,2}[-_]\d{2,4})")

def iso_from_8(s):  # 20251124 -> 2025-11-24
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}"

def clean_model(stem):
    return re.sub(r"[_\-]+", " ", stem).strip()

def analyze(text):
    words = re.findall(r"\S+", text)
    wc = len(words)
    cats = {k: len(rx.findall(text)) for k, rx in CAT_RE.items()}
    imp = len(IMP_RE.findall(text))
    return wc, cats, round(imp/wc*1000, 1) if wc else 0

# ---------- collect prompts ----------
rows, texts, seen = [], {}, {}

def add(vendor, model, date, source, path, text):
    wc, cats, imp = analyze(text)
    if wc < 20: return
    h = hashlib.md5(re.sub(r"\s+", " ", text).strip().encode()).hexdigest()
    if h in seen:  # exact-content duplicate across archives
        return
    seen[h] = True
    uid = f"{source}:{path}"
    rows.append({"uid": uid, "vendor": vendor, "tribe": tribe_of(vendor, model),
                 "model": model, "source": source, "file": path,
                 "date": date, "words": wc, "chars": len(text),
                 "imperative_per_1k": imp, "categories": cats})
    texts[uid] = text

# CL4R1T4S: vendor folders
if os.path.isdir(CL):
    for vendor in sorted(os.listdir(CL)):
        vp = os.path.join(CL, vendor)
        if not os.path.isdir(vp) or vendor.startswith("."): continue
        for fp in sorted(glob.glob(os.path.join(vp, "*"))):
            if not os.path.isfile(fp): continue
            base = os.path.basename(fp)
            if base.lower() in ("license","readme.md"): continue
            txt = open(fp, encoding="utf-8", errors="ignore").read()
            dm = DATE_LOOSE.search(base)
            add(normalize_vendor(vendor), clean_model(re.sub(r"\.\w+$","",base)),
                dm.group(1).replace("_","-") if dm else None, "CL4R1T4S", f"{vendor}/{base}", txt)

# jujumilk3: flat vendor-model_YYYYMMDD.md
if os.path.isdir(JU):
    for fp in sorted(glob.glob(os.path.join(JU, "*.md"))):
        base = os.path.basename(fp)
        if base.lower() == "readme.md": continue
        stem = re.sub(r"\.md$", "", base)
        dm = DATE8.search(stem)
        date = iso_from_8(dm.group(1)) if dm else None
        core = DATE8.sub("", stem)
        vendor_raw = core.split("-")[0] if "-" in core else core
        txt = open(fp, encoding="utf-8", errors="ignore").read()
        add(normalize_vendor(vendor_raw), clean_model(core), date, "jujumilk3", base, txt)

# ---------- rollups ----------
vendors = {}
for r in rows:
    v = vendors.setdefault(r["vendor"], {"vendor": r["vendor"], "tribe": r["tribe"],
        "prompts": 0, "total_words": 0, "categories": {k: 0 for k in CATEGORIES}, "imp_sum": 0.0})
    v["prompts"] += 1; v["total_words"] += r["words"]; v["imp_sum"] += r["imperative_per_1k"]
    for k, n in r["categories"].items():
        v["categories"][k] = max(v["categories"][k], n)
for v in vendors.values():
    v["avg_words"] = round(v["total_words"]/v["prompts"])
    v["avg_imperative"] = round(v["imp_sum"]/v["prompts"], 1)
    del v["imp_sum"]

out = {
    "categories": list(CATEGORIES.keys()),
    "tribes": ["Frontier chat","Coding agent","Service / other"],
    "vendors": sorted(vendors.values(), key=lambda x: -x["avg_words"]),
    "prompts": sorted(rows, key=lambda x: -x["words"]),
    "stats": {"n_vendors": len(vendors), "n_prompts": len(rows),
              "total_words": sum(r["words"] for r in rows),
              "sources": ["CL4R1T4S", "jujumilk3"]},
}
os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
json.dump(out, open(os.path.join(HERE, "data", "data.json"), "w"), indent=1)
json.dump(texts, open(os.path.join(HERE, "data", "texts.json"), "w"))
print(f"Merged: {out['stats']['n_prompts']} prompts, {out['stats']['n_vendors']} vendors, "
      f"{out['stats']['total_words']:,} words")
by_src = {}
for r in rows: by_src[r["source"]] = by_src.get(r["source"],0)+1
print("by source:", by_src)
print("dated prompts:", sum(1 for r in rows if r["date"]))
