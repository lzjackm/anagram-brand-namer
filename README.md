# Anagram Brand Namer

A naming tool for marketers. Feed it letters (or the words behind an acronym)
and it finds **real, brandable names** built from those letters: exact matches,
near-misses one letter away, and full anagrams. Every match is tagged with the
brandable categories it belongs to (mythology, celestial, gemstones, creatures,
Latin/Greek roots), so you can spot evocative, ownable names fast.

It runs entirely **offline** against local word lists — no API keys, no rate
limits, no network. Pure Python standard library, nothing to `pip install`.

```
  → NOVA  [1-letter]
  EXACT WORD
    NOVA
  EXACT NAME
    NOVA = Nova (celestial), Nova (root: new)
  WORDS ONE LETTER AWAY (6)
    NOMA   NONA   NOTA   NOVAE  NOVAS  OVA
```

## Why marketers use it

- **Spell a real word from your initials.** Got the words "Also True Later
  Amazing Salsa"? It tells you they spell `ATLAS` — a real word *and* a Greek
  Titan *and* a celestial term. Strong, ownable, memorable.
- **Find near-miss names.** One letter added, removed, or swapped surfaces
  brandable variants you'd never brainstorm by hand.
- **Anagram mode.** Rearrange your letters into real words/names — the classic
  branding trick (`STALA` → `ATLAS`).
- **Category tags = brandability signal.** A candidate that lands in several
  pools (e.g. word + myth + celestial) is usually a stronger name.
- **Pin constraints.** Force results to start or end with chosen letters.

## Install

Requires **Python 3.8+** (already on most macOS/Linux machines). No dependencies.

```bash
git clone https://github.com/lzjackm/anagram-brand-namer.git
cd anagram-brand-namer
python3 acronym_finder.py --gui
```

That's it. The word list (`words.txt`, the public-domain ENABLE1 lexicon) and
the name pools ship with the repo.

## Usage

### Terminal GUI (recommended)

```bash
python3 acronym_finder.py --gui
```

A lightweight full-screen interface (built on Python's `curses`) with live,
as-you-type results.

| Key | Action |
| --- | --- |
| type in **Letters/phrase** | search live |
| **Tab** | cycle fields: query → **Pin start with** → **Pin end with** |
| **Ctrl-A** | toggle match mode (1-letter ↔ anagram) |
| **↑ ↓ / PgUp / PgDn** | scroll long result lists |
| **Ctrl-U** | clear the active field |
| **Ctrl-Q** | quit |

### Plain interactive prompt

```bash
python3 acronym_finder.py
```

Then type at the prompt:

- `ATLAS` — letters mode
- `Also True Later Amazing Salsa` — phrase mode (first letter of each word → `ATLAS`)
- `anagram` / `edit` — switch match mode (default `edit`)
- `start T` / `start off` — only show results beginning with `T`
- `end X` / `end off` — only show results ending with `X`
- `quit` — exit

### One-shot (scriptable)

```bash
python3 acronym_finder.py ATLAS                  # letters
python3 acronym_finder.py "Also True Later"      # phrase -> ATL
python3 acronym_finder.py --anagram STALA        # anagram mode -> ATLAS
python3 acronym_finder.py --start T --end Y BOLD # pinned start/end
```

## Match modes

- **1-letter (default)** — the exact string plus everything one edit away: a
  single letter inserted, deleted, or substituted, *in place*.
  `CAT` → `COT`, `CART`, `SCAT`, `CHAT`, ...
- **anagram** — real words and names that use your letters in *any order*,
  either exactly or with one letter added/removed. Grouped into **EXACT
  ANAGRAM**, **PLUS ONE LETTER**, **MINUS ONE LETTER**. `STALA` → `ATLAS`.

The `start` / `end` pins apply in both modes.

## What it searches

- **`words.txt`** — English word list (ENABLE1, public domain, ~173k words).
- **Brandable name pools**, each match tagged with its category:
  - `mythical_figures.txt` — Greek / Roman / Norse figures (e.g. `Greek myth`)
  - `celestial.txt` — stars, planets, constellations, space phenomena
  - `creatures.txt` — mythical creatures (Phoenix, Hydra, Griffin, ...)
  - `gemstones.txt` — gems and minerals (Onyx, Jade, Opal, ...)
  - `roots.txt` — Latin / Greek roots with meanings (`root: light`)

Name pools are **matched on the last word of each name** ("last name"), so
multi-word entries match on their final token.

## Customize

- **Swap the dictionary:** replace `words.txt` with any newline-delimited word
  list (e.g. a different language, or your industry's term list). The code just
  loads it into a set.
- **Add brandable names:** append lines to any pool file (`Name` or
  `Name|subgroup`), or add a whole new pool by dropping a file in and
  registering it in the `POOLS` list near the top of `acronym_finder.py`.

## Files

| File | Purpose |
| --- | --- |
| `acronym_finder.py` | engine + CLI (one-shot and interactive) |
| `tui.py` | terminal GUI (`--gui`) |
| `words.txt` | English word list (ENABLE1) |
| `*.txt` pools | brandable name categories |

## License

Code released under the MIT License (see `LICENSE`). The bundled `words.txt` is
the ENABLE1 word list, which is in the public domain.
