#!/usr/bin/env python3
"""
anagram_brand_namer — turn letters (or an acronym's words) into brandable names.

Give it some letters, or a phrase whose initials form an acronym, and it finds
real words and names that are ANAGRAMS of those letters:
  * EXACT  — uses all your letters, rearranged
  * PLUS ONE LETTER  — your letters plus one more
  * MINUS ONE LETTER — your letters with one removed

It searches local lists (instant, offline, no rate limits):
  * words.txt              — an English word list (ENABLE1, public domain, ~173k)
  * brandable name pools   — myth / celestial / creatures / gems / roots,
                             matched on LAST NAME, each match tagged by category

No third-party packages required — standard library only.
"""

import os
import sys
from collections import Counter

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MIN_LEN = 2  # ignore 1-letter results (too noisy)
HERE = os.path.dirname(os.path.abspath(__file__))
WORDLIST = os.path.join(HERE, "words.txt")

# Each pool: (filename, category label, subgroup style)
#   subgroup style: "pantheon" -> "Greek myth", "meaning" -> "root: light", None -> label
POOLS = [
    ("mythical_figures.txt", "myth", "pantheon"),
    ("celestial.txt", "celestial", None),
    ("creatures.txt", "creature", None),
    ("gemstones.txt", "gem", None),
    ("roots.txt", "root", "meaning"),
]

WORDS = set()    # uppercase words
NAMES = {}       # uppercase last-name -> list of (display_name, tag)
CAT_COUNTS = {}  # category label -> count

# anagram indexes, built lazily on first lookup
_ANA_WORDS = None
_ANA_NAMES = None


def load_words(path=WORDLIST):
    """Load the English word list into an uppercase set."""
    global WORDS
    with open(path, encoding="utf-8") as fh:
        WORDS = {line.strip().upper() for line in fh if line.strip()}
    return WORDS


def _make_tag(category, subgroup, style):
    if not subgroup:
        return category
    if style == "pantheon":
        return f"{subgroup} {category}"      # "Greek myth"
    return f"{category}: {subgroup}"         # "root: light"


def load_names(pools=POOLS):
    """Load all named pools, keyed by the LAST word of each name (uppercased)."""
    global NAMES, CAT_COUNTS, _ANA_WORDS, _ANA_NAMES
    NAMES, CAT_COUNTS = {}, {}
    _ANA_WORDS = _ANA_NAMES = None  # force index rebuild after a reload
    for filename, category, style in pools:
        path = os.path.join(HERE, filename)
        if not os.path.exists(path):
            continue
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, _, subgroup = line.partition("|")
            name, subgroup = name.strip(), subgroup.strip()
            if not name:
                continue
            tag = _make_tag(category, subgroup, style)
            key = name.split()[-1].upper()  # match on last name only
            NAMES.setdefault(key, []).append((name, tag))
            CAT_COUNTS[category] = CAT_COUNTS.get(category, 0) + 1
    return NAMES


def to_acronym(text):
    """Single token -> taken as-is. Multiple words -> first letter of each word."""
    tokens = text.split()
    if len(tokens) <= 1:
        return text.strip().upper()
    letters = []
    for tok in tokens:
        for ch in tok:
            if ch.isalpha():
                letters.append(ch.upper())
                break
    return "".join(letters)


def _canon(s):
    """Canonical anagram key: letters sorted."""
    return "".join(sorted(s))


def _build_anagram_index():
    global _ANA_WORDS, _ANA_NAMES
    if _ANA_WORDS is not None:
        return
    aw = {}
    for w in WORDS:
        aw.setdefault(_canon(w), []).append(w)
    an = {}
    for key in NAMES:
        an.setdefault(_canon(key), []).append(key)
    _ANA_WORDS, _ANA_NAMES = aw, an


def _apply_pins(words, prefix, suffix):
    if prefix:
        words = [w for w in words if w.startswith(prefix)]
    if suffix:
        words = [w for w in words if w.endswith(suffix)]
    return words


def _section(title, kind, items, highlight=False):
    """kind: 'words' (list of str) or 'names' (list of (key, entries))."""
    return {"title": title, "kind": kind, "items": items, "highlight": highlight}


def _diff_letter(letters, word, kind):
    """The single letter that differs between input `letters` and `word`.

    kind 'plus'  -> the extra letter in `word`        -> '+X'
    kind 'minus' -> the input letter missing in `word` -> '−X'
    kind 'exact' -> '' (no change)
    """
    if kind == "plus":
        diff = Counter(word) - Counter(letters)
    elif kind == "minus":
        diff = Counter(letters) - Counter(word)
    else:
        return ""
    for ch in diff:  # exactly one letter, count 1
        return ("+" if kind == "plus" else "−") + ch
    return ""


def find(word, prefix="", suffix=""):
    """Return anagram result sections for the given letters, honoring start/end pins."""
    word = word.strip().upper()
    prefix = prefix.strip().upper()
    suffix = suffix.strip().upper()

    _build_anagram_index()
    letters = "".join(ch for ch in word if ch.isalpha())
    if not letters:
        return []

    def collect(keys):
        words, names = set(), set()
        for k in keys:
            words.update(_ANA_WORDS.get(k, ()))
            names.update(_ANA_NAMES.get(k, ()))
        words = {w for w in words if len(w) >= MIN_LEN}
        words = set(_apply_pins(list(words), prefix, suffix))
        names = set(_apply_pins(list(names), prefix, suffix))
        return words, names

    exact_keys = [_canon(letters)]
    plus_keys = [_canon(letters + c) for c in ALPHABET]
    minus_keys = [_canon(letters[:i] + letters[i + 1:]) for i in range(len(letters))]

    buckets = [
        ("EXACT ANAGRAM — uses all your letters", exact_keys, "exact", True),
        ("PLUS ONE LETTER — your letters + 1", plus_keys, "plus", False),
        ("MINUS ONE LETTER — your letters − 1", minus_keys, "minus", False),
    ]
    sections = []
    for title, keys, kind, hl in buckets:
        words, names = collect(keys)
        # de-dupe: a string that is also a brandable name shows only in NAMES
        pure_words = sorted(words - names)
        word_items = [(w, _diff_letter(letters, w, kind)) for w in pure_words]
        name_items = [(k, NAMES[k], _diff_letter(letters, k, kind)) for k in sorted(names)]
        if word_items:
            sections.append(_section(f"{title} ({len(word_items)})", "words", word_items, hl))
        if name_items:
            sections.append(_section(f"{title} — NAMES ({len(name_items)})", "names", name_items, hl))
    return sections


def _fmt_names(entries):
    """entries -> 'Atlas (Greek myth), Atlas (celestial)'."""
    return ", ".join(f"{name} ({tag})" for name, tag in entries)


def section_to_rows(section, width):
    """Convert a section to a list of (text, attr_key) rows. Shared by CLI + GUI."""
    rows = [(section["title"], "label")]
    hl = "hit" if section["highlight"] else "plain"
    if section["kind"] == "words":
        cells = [f"{w} ({annot})" if annot else w for w, annot in section["items"]]
        cw = max(len(c) for c in cells) + 2
        per_row = max(1, (max(20, width) - 2) // cw)
        for i in range(0, len(cells), per_row):
            rows.append(("  " + "".join(c.ljust(cw) for c in cells[i:i + per_row]), hl))
    else:  # names
        for key, entries, annot in section["items"]:
            label = f"{key} ({annot})" if annot else key
            if section["highlight"]:
                rows.append((f"  {label} = {_fmt_names(entries)}", "hit"))
            else:
                rows.append((f"  {label:<14} {_fmt_names(entries)}", "plain"))
    return rows


def render(word, prefix="", suffix=""):
    sections = find(word, prefix, suffix)
    pins = []
    if prefix:
        pins.append(f"start '{prefix.upper()}'")
    if suffix:
        pins.append(f"end '{suffix.upper()}'")
    pin = f"  (pinned: {', '.join(pins)})" if pins else ""
    print(f"\n  → {word}{pin}")

    if not sections:
        print(f"  No anagrams found for '{word}'.\n")
        return
    for sec in sections:
        for text, _ in section_to_rows(sec, 74):
            print("  " + text)
    print()


def _banner():
    cats = ", ".join(f"{c} ({n})" for c, n in sorted(CAT_COUNTS.items()))
    return f"""\
============================================================
 ANAGRAM BRAND NAMER
============================================================
 Type some letters (or a phrase) and it finds real words
 and names that are ANAGRAMS of your letters -- rearranged
 to use them all, or with one letter added or removed.

 It searches local lists (offline, no rate limits):
   - {len(WORDS):,} English words (words.txt)
   - brandable name pools, each match TAGGED by category:
     {cats}
   (names match on LAST NAME only, e.g. "Zeus", "Nova")

 INPUT MODES
   letters   ATLAS
   phrase    Also True Later Amazing Salsa   -> first letter
             of each word becomes ATLAS, then anagrammed

 PIN A STARTING / ENDING LETTER (optional filters)
   start T       only show results that begin with T
   start TH      prefixes work too (begin with TH)
   start off     turn the start pin back off
   end X         only show results that end with X (e.g. end LY)
   end off       turn the end pin back off
   (one-shot: add --start T and/or --end X before your input)

 OTHER
   quit / exit   leave the program
============================================================
"""


def run_oneshot(argv):
    prefix = suffix = ""
    args = list(argv)
    while args and args[0] in ("--start", "--end"):
        flag = args[0]
        val = args[1] if len(args) > 1 else ""
        if flag == "--start":
            prefix = val
        else:
            suffix = val
        args = args[2:]
    render(to_acronym(" ".join(args)), prefix, suffix)


def main():
    if not os.path.exists(WORDLIST):
        sys.exit(f"word list not found: {WORDLIST}")

    if len(sys.argv) > 1 and sys.argv[1] in ("--gui", "--tui"):
        import tui
        tui.main()
        return

    load_words()
    load_names()

    if len(sys.argv) > 1:
        run_oneshot(sys.argv[1:])
        return

    print(_banner())

    prefix = suffix = ""
    try:
        while True:
            raw = input("letters/phrase> ").strip()
            if not raw:
                continue
            if raw.lower() in {"quit", "exit", "q"}:
                break

            tokens = raw.split()
            cmd = tokens[0].lower()
            if cmd in ("start", "end"):
                arg = tokens[1] if len(tokens) > 1 else ""
                edge = cmd
                if arg.lower() in {"off", "none", "clear", ""}:
                    if cmd == "start":
                        prefix = ""
                    else:
                        suffix = ""
                    print(f"  {edge} pin cleared.\n")
                elif arg.isalpha():
                    if cmd == "start":
                        prefix = arg.upper()
                    else:
                        suffix = arg.upper()
                    print(f"  pinned: results must {edge} with '{arg.upper()}'.\n")
                else:
                    print(f"  usage: {cmd} <letters> | {cmd} off\n")
                continue

            word = to_acronym(raw)
            if not word.isalpha():
                print("  letters only, please.\n")
                continue
            render(word, prefix, suffix)
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
