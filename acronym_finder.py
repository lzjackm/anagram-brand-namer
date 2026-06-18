#!/usr/bin/env python3
"""
acronym_finder — interactive lookup with fuzzy (edit-distance-1) matching.

Given letters (or a phrase), it finds matches that are:
  * an exact match, OR
  * exactly one letter away: a single insertion, deletion, OR substitution.

It checks local lists (instant, offline, no rate limits):
  * words.txt              — an English word list (ENABLE1, public domain, ~173k)
  * named pools below      — brandable name categories, matched on LAST NAME,
                             each match tagged with its category

No third-party packages required — standard library only.
"""

import os
import sys

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MIN_LEN = 2  # ignore 1-letter candidates (too noisy)
HERE = os.path.dirname(os.path.abspath(__file__))
WORDLIST = os.path.join(HERE, "words.txt")

# Each pool: (filename, category label, subgroup style)
#   subgroup style: "pantheon" -> "Greek myth", "meaning" -> "myth: x", None -> just label
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


def load_words(path=WORDLIST):
    """Load the Scrabble word list into an uppercase set."""
    global WORDS
    with open(path, encoding="utf-8") as fh:
        WORDS = {line.strip().upper() for line in fh if line.strip()}
    return WORDS


def _make_tag(category, subgroup, style):
    if not subgroup:
        return category
    if style == "pantheon":
        return f"{subgroup} {category}"      # "Greek myth"
    if style == "meaning":
        return f"{category}: {subgroup}"     # "root: light"
    return f"{category}: {subgroup}"


def load_names(pools=POOLS):
    """Load all named pools, keyed by the LAST word of each name (uppercased)."""
    global NAMES, CAT_COUNTS
    NAMES, CAT_COUNTS = {}, {}
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


def edit_distance_1(word):
    """All distinct strings exactly one edit (ins/del/sub) from `word`, uppercased."""
    word = word.upper()
    out = set()
    for i in range(len(word)):                      # deletions
        out.add(word[:i] + word[i + 1:])
    for i in range(len(word)):                      # substitutions
        for c in ALPHABET:
            if c != word[i]:
                out.add(word[:i] + c + word[i + 1:])
    for i in range(len(word) + 1):                  # insertions
        for c in ALPHABET:
            out.add(word[:i] + c + word[i:])
    out.discard(word)
    return out


# ---- anagram index (built lazily on first anagram lookup) ----
_ANA_WORDS = None
_ANA_NAMES = None


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


def find(word, prefix="", suffix="", mode="edit"):
    """Return a list of result sections. mode: 'edit' (1 letter away) or 'anagram'."""
    word = word.strip().upper()
    prefix = prefix.strip().upper()
    suffix = suffix.strip().upper()
    if mode == "anagram":
        return _find_anagram(word, prefix, suffix)
    return _find_edit(word, prefix, suffix)


def _find_edit(word, prefix, suffix):
    candidates = {word} | edit_distance_1(word)
    candidates = {c for c in candidates if len(c) >= MIN_LEN}
    if prefix:
        candidates = {c for c in candidates if c.startswith(prefix)}
    if suffix:
        candidates = {c for c in candidates if c.endswith(suffix)}

    word_hits = {c for c in candidates if c in WORDS}
    name_hits = {c for c in candidates if c in NAMES}

    sections = []
    if word in word_hits:
        sections.append(_section("EXACT WORD", "words", [word], highlight=True))
    if word in name_hits:
        sections.append(_section("EXACT NAME", "names",
                                 [(word, NAMES[word])], highlight=True))
    wf = sorted(c for c in word_hits if c != word)
    if wf:
        sections.append(_section(f"WORDS ONE LETTER AWAY ({len(wf)})", "words", wf))
    nf = sorted((c, NAMES[c]) for c in name_hits if c != word)
    if nf:
        sections.append(_section(f"NAMES ONE LETTER AWAY ({len(nf)})", "names", nf))
    return sections


def _find_anagram(word, prefix, suffix):
    _build_anagram_index()
    letters = "".join(ch for ch in word if ch.isalpha())
    if not letters:
        return []

    def words_for(keys):
        out = set()
        for k in keys:
            out.update(_ANA_WORDS.get(k, ()))
        out = [w for w in out if len(w) >= MIN_LEN]
        return sorted(_apply_pins(out, prefix, suffix))

    def names_for(keys):
        out = set()
        for k in keys:
            out.update(_ANA_NAMES.get(k, ()))
        return sorted((k, NAMES[k]) for k in _apply_pins(list(out), prefix, suffix))

    exact_keys = [_canon(letters)]
    plus_keys = [_canon(letters + c) for c in ALPHABET]
    minus_keys = [_canon(letters[:i] + letters[i + 1:]) for i in range(len(letters))]

    buckets = [
        ("EXACT ANAGRAM — uses all your letters", exact_keys, True),
        ("PLUS ONE LETTER — your letters + 1", plus_keys, False),
        ("MINUS ONE LETTER — your letters − 1", minus_keys, False),
    ]
    sections = []
    for title, keys, hl in buckets:
        w = words_for(keys)
        if w:
            sections.append(_section(f"{title} ({len(w)})", "words", w, highlight=hl))
        n = names_for(keys)
        if n:
            sections.append(_section(f"{title} — NAMES ({len(n)})", "names", n, highlight=hl))
    return sections


def _fmt_names(entries):
    """entries -> 'Atlas (Greek myth), Atlas (celestial)'."""
    return ", ".join(f"{name} ({tag})" for name, tag in entries)


def section_to_rows(section, width):
    """Convert a section to a list of (text, attr_key) rows. Shared by CLI + GUI."""
    rows = [(section["title"], "label")]
    hl = "hit" if section["highlight"] else "plain"
    if section["kind"] == "words":
        items = section["items"]
        cw = max(len(w) for w in items) + 2
        per_row = max(1, (max(20, width) - 2) // cw)
        for i in range(0, len(items), per_row):
            rows.append(("  " + "".join(w.ljust(cw) for w in items[i:i + per_row]), hl))
    else:  # names
        for key, entries in section["items"]:
            if section["highlight"]:
                rows.append((f"  {key} = {_fmt_names(entries)}", "hit"))
            else:
                rows.append((f"  {key:<11} {_fmt_names(entries)}", "plain"))
    return rows


def render(word, prefix="", suffix="", mode="edit"):
    sections = find(word, prefix, suffix, mode)
    pins = []
    if prefix:
        pins.append(f"start '{prefix.upper()}'")
    if suffix:
        pins.append(f"end '{suffix.upper()}'")
    label = "anagram" if mode == "anagram" else "1-letter"
    extra = f"  [{label}]"
    if pins:
        extra += f"  (pinned: {', '.join(pins)})"
    print(f"\n  → {word}{extra}")

    if not sections:
        print(f"  No {label} matches for '{word}'.\n")
        return
    for sec in sections:
        for text, _ in section_to_rows(sec, 74):
            print("  " + text)
    print()


def _banner():
    cats = ", ".join(f"{c} ({n})" for c, n in sorted(CAT_COUNTS.items()))
    return f"""\
============================================================
 ACRONYM FINDER  ·  brandable name generator
============================================================
 Type some letters (or a phrase) and it finds matches that
 are an EXACT match or exactly ONE LETTER AWAY -- a single
 letter added, removed, or swapped.

 It searches local lists (offline, no rate limits):
   - {len(WORDS):,} Scrabble words (words.txt)
   - brandable name pools, each match TAGGED by category:
     {cats}
   (names match on LAST NAME only, e.g. "Zeus", "Nova")

 INPUT MODES
   letters   ATLAS
   phrase    Also True Later Amazing Salsa   -> first letter
             of each word becomes ATLAS, then searched

 MATCH MODE
   anagram       switch to anagram mode: real words/names that use your
                 letters exactly, or with one letter added/removed (any order)
   edit          switch back to 1-letter mode (default: add/remove/swap, in place)
   (one-shot: add --anagram before your input)

 PIN A STARTING / ENDING LETTER (optional filters, work in both modes)
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
    mode = "edit"
    args = list(argv)
    while args and args[0] in ("--start", "--end", "--anagram"):
        flag = args[0]
        if flag == "--anagram":
            mode = "anagram"
            args = args[1:]
            continue
        val = args[1] if len(args) > 1 else ""
        if flag == "--start":
            prefix = val
        else:
            suffix = val
        args = args[2:]
    render(to_acronym(" ".join(args)), prefix, suffix, mode)


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
    mode = "edit"
    try:
        while True:
            raw = input("letters/phrase> ").strip()
            if not raw:
                continue
            if raw.lower() in {"quit", "exit", "q"}:
                break

            tokens = raw.split()
            cmd = tokens[0].lower()
            if cmd in ("anagram", "edit", "mode"):
                arg = tokens[1].lower() if len(tokens) > 1 else ""
                if cmd == "edit" or arg == "off":
                    mode = "edit"
                else:
                    mode = "anagram"
                print(f"  match mode: {mode}\n")
                continue
            if cmd in ("start", "end"):
                arg = tokens[1] if len(tokens) > 1 else ""
                edge = "start" if cmd == "start" else "end"
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
            render(word, prefix, suffix, mode)
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
