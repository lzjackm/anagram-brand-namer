# Anagram Brand Namer

A naming tool for marketers. Feed it letters (or the words behind an acronym)
and it finds **real, brandable names that are anagrams of your letters** —
rearranged to use them all, or with a single letter added or removed. Every
match is tagged with the brandable categories it belongs to (mythology,
celestial, gemstones, creatures, Latin/Greek roots), so you can spot evocative,
ownable names fast.

It runs entirely **offline** against local word lists — no API keys, no rate
limits, no network. Pure Python standard library, nothing to `pip install`.

```
  → STALA
  EXACT ANAGRAM — uses all your letters (2)
    ATLAS  TALAS
  EXACT ANAGRAM — uses all your letters — NAMES (1)
    ATLAS = Atlas (Greek myth)
  PLUS ONE LETTER — your letters + 1 (13)
    ALANTS  ALATES  ALTARS  ASLANT  ASTRAL  BASALT  ...
```

## Why marketers use it

- **Turn loose letters into a real word.** Rearrange the letters you've got into
  pronounceable, ownable names — the classic branding trick (`STALA` → `ATLAS`).
- **Anagram an acronym's initials.** Feed the words behind an acronym; it takes
  the initials and finds the real words they can spell.
- **Stretch by one letter.** "Plus one" and "minus one" surface brandable
  variants you'd never reach by hand.
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
| **↑ ↓ / PgUp / PgDn** | scroll long result lists |
| **Ctrl-U** | clear the active field |
| **Ctrl-Q** | quit |

### Plain interactive prompt

```bash
python3 acronym_finder.py
```

Then type at the prompt:

- `STALA` — letters mode (anagrams them → `ATLAS`, ...)
- `Also True Later Amazing Salsa` — phrase mode (first letter of each word →
  `ATLAS`, then anagrammed)
- `start T` / `start off` — only show results beginning with `T`
- `end X` / `end off` — only show results ending with `X`
- `quit` — exit

### One-shot (scriptable)

```bash
python3 acronym_finder.py STALA                  # letters -> ATLAS, ...
python3 acronym_finder.py "Also True Later"      # phrase -> ATL, then anagrammed
python3 acronym_finder.py --start T --end S STALA  # pinned start/end
```

## How matching works

Results are real words and names that are **anagrams of your letters**, grouped
into three buckets:

- **EXACT ANAGRAM** — uses all your letters, rearranged (`STALA` → `ATLAS`)
- **PLUS ONE LETTER** — your letters plus one more
- **MINUS ONE LETTER** — your letters with one removed

The `start` / `end` pins filter every bucket.

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
