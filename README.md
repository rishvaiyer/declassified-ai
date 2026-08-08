# 🗂️ Declassified AI — The Secret Rulebooks of the Machines

Every AI chatbot is handed a hidden list of rules before it ever talks to you —
who it is, what it must never say. This project takes **229 leaked system prompts
from 53 companies**, pulls them apart, lays them side by side, and then flips the
dossier over to look at the **jailbreaks built to break them**. One interactive,
self-contained page.

**▶ Live demo:** https://rishvaiyer.github.io/declassified-ai/

> **Data credit.** System prompts come from two public archives: **[CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)**
> and the jailbreak archive **[L1B3RT4S](https://github.com/elder-plinius/L1B3RT4S)**, both by
> **[Pliny · @elder-plinius](https://github.com/elder-plinius)**, plus **[leaked-system-prompts](https://github.com/jujumilk3/leaked-system-prompts)**
> by **[@jujumilk3](https://github.com/jujumilk3)**. This project only *visualizes* their public
> collections — all credit for gathering the prompts is theirs.

---

## What it shows

Six "exhibits," styled as a declassified intelligence file:

- **A · Who Says No To What** — a company × topic heat map of what each lab's rulebooks
  keep raising (weapons, self-harm, copyright, elections, "don't reveal this prompt"…).
- **B · Who Writes The Most** — length leaderboard, toggling raw word count vs.
  *bossiness* (must/never/always commands per 1,000 words).
- **C · Who Copied Whose Homework** — an interactive **force-directed web** of all 229
  rulebooks (drag the nodes!), plus a **Map** view that settles them by overall similarity.
  Hover any node for its closest cousin from a *different* company.
- **D · The Archive** — every file, searchable, each linking back to its source repo.
- **E · The Diff Machine** — line-by-line diff between any two rulebooks; watch a model's
  prompt balloon from one version to the next.
- **F · The Counter-Spells** — the *attack* side. Pliny's L1B3RT4S jailbreaks read only in
  the **aggregate**: which techniques (persona, token injection, encoding…) show up most.
  No exploit text is reproduced — just the shape of the attack surface.

## A few things it surfaces

- **Coding agents copy each other** across company lines (Windsurf ↔ Cursor and friends
  cluster tightly in the web).
- **Cross-company twins:** Anthropic's "Claude Design" prompt and Meta's "Muse Spark"
  share ~74% of their vocabulary.
- **Frontier chat models write novels** — the longest rulebooks run past 25,000 words.
- **Jailbreaks lean on structure:** token/format injection and persona-roleplay dominate
  L1B3RT4S; encoding tricks are rare.
- **667,000 words** of hidden instruction across the whole corpus.

> **Read the tallies as _emphasis_, not verdicts.** Category and technique scores are keyword
> mentions — a longer document mentions more of everything. Similarity is TF-IDF (word
> bigrams + character n-grams), not neural embeddings.

## How it's built

- **Zero-dependency to view.** `index.html` is fully self-contained — all data baked in,
  no server, no external requests, no build step to run it. The similarity web is a
  hand-rolled canvas force simulation (no D3).
- **Pipeline** (`src/`, needs only `numpy`):
  `build_data.py` merges + de-dupes both rulebook archives → `embed.py` computes the
  TF-IDF similarity graph → `jailbreaks.py` builds the aggregate counter-spells taxonomy →
  `build.py` inlines everything into the page (escaping `<` so embedded `</script>` can't
  break it).

## Regenerating the data

```bash
# from the repo root — clone the three public archives
git clone --depth 1 https://github.com/elder-plinius/CL4R1T4S.git       CL4R1T4S
git clone --depth 1 https://github.com/jujumilk3/leaked-system-prompts.git juju
git clone --depth 1 https://github.com/elder-plinius/L1B3RT4S.git       L1B3RT4S
pip install numpy
python src/build_data.py    # -> data/data.json + data/texts.json  (merged, de-duped)
python src/embed.py         # -> similarity map + force-graph edges
python src/jailbreaks.py    # -> aggregate jailbreak taxonomy
python src/build.py         # -> rebuild index.html
```
The pre-built `data/` and `index.html` are committed, so this is optional.

## License

Analysis code and visualization: **MIT** (see `LICENSE`). The upstream prompt text remains
subject to each source archive's own license.
