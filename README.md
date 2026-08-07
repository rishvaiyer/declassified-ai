# 🗂️ Declassified AI — The Secret Rulebooks of the Machines

Every AI chatbot is handed a hidden list of rules before it ever talks to you —
who it is, what it must never say. This project takes **67 of those leaked system
prompts, from 25 companies**, pulls them apart, and lays them side by side as an
interactive, single-page data dossier.

**▶ Live demo:** https://rishvaiyer.github.io/declassified-ai/ &nbsp;·&nbsp; _(enable GitHub Pages — see below)_

---

## What it shows

Five "exhibits," styled as a declassified intelligence file:

- **A · Who Says No To What** — a vendor × topic heat map of what each lab's rulebooks
  keep bringing up (weapons, self-harm, copyright, elections, "don't reveal this prompt"…).
- **B · Who Writes The Most** — length leaderboard, toggling between raw word count and
  *bossiness* (must/never/always commands per 1,000 words).
- **C · Who Copied Whose Homework** — every rulebook plotted by the words it uses
  (TF-IDF + classical MDS). Hover any dot to see its closest cousin from a *different* company.
- **D · The Archive** — all 67 files, searchable, each linking to the raw source.
- **E · The Diff Machine** — line-by-line diff between any two rulebooks; watch a model's
  prompt balloon from one version to the next.

## A few things it surfaces

- **Coding agents copy each other.** Windsurf, Replit, Cursor, Same.dev, Cline and Manus
  cluster tightly (up to ~69% shared vocabulary) — they clearly didn't write these from scratch.
- **Frontier chat models write novels.** The longest rulebooks here run past 25,000 words.
- **266,000 words** of hidden instruction across the whole pile.

> **Read the heat as _emphasis_, not policy.** Category scores are keyword mentions, so a
> longer rulebook naturally mentions more of everything. This is a lens, not a verdict.

## How it's built

- **Zero-dependency to view.** `index.html` is fully self-contained — all data is baked in,
  no server, no build step, no external requests. Open it and it works.
- **Pipeline** (`src/`): `crunch.py` parses the archive → `embed.py` computes the TF-IDF
  similarity map → `build.py` inlines the data into the page template. Only `numpy` is needed
  to regenerate.
- **Design:** hand-rolled HTML/CSS/JS, theme-aware (light/dark), a "declassified dossier" look.

## Regenerating the data

```bash
# from the repo root
git clone --depth 1 https://github.com/elder-plinius/CL4R1T4S.git
pip install numpy
python src/crunch.py      # -> data/data.json  (word counts, categories, bossiness)
python src/embed.py       # -> adds the 2-D similarity map
python src/build.py       # -> rebuilds index.html
```
The pre-built `data/` and `index.html` are committed, so this is optional.

## Data source & credit

System prompts come from the public **[CL4R1T4S](https://github.com/elder-plinius/CL4R1T4S)**
archive by [@elder-plinius](https://github.com/elder-plinius) (AGPL-3.0). These are the
*instructions* given to models — not training data, not anything private. All credit for the
underlying collection goes there.

## License

Analysis code and visualization: **MIT** (see `LICENSE`). The upstream prompt text is subject
to CL4R1T4S's own license.
