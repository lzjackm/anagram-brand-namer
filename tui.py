#!/usr/bin/env python3
"""
tui.py — a lightweight terminal GUI for acronym_finder.

Live, as-you-type search built on the standard-library `curses` module.
No third-party packages. Run via:

    python3 tui.py
    python3 acronym_finder.py --gui
"""

import curses

import acronym_finder as af


def build_lines(query, prefix, suffix, mode, max_x):
    """Return (acronym, rows) where rows are (text, attr_key) for the current state."""
    width = max(20, max_x - 2)
    word = af.to_acronym(query)
    rows = []

    if not word:
        rows.append(("Start typing letters, or a phrase like "
                     "'Also True Later Amazing Salsa'.", "dim"))
        return word, rows

    sections = af.find(word, prefix, suffix, mode)
    if not sections:
        label = "anagram" if mode == "anagram" else "1-letter"
        rows.append((f"No {label} matches for '{word}'.", "dim"))
        return word, rows

    for sec in sections:
        rows.extend(af.section_to_rows(sec, width))
    return word, rows


def run(stdscr):
    curses.curs_set(1)
    stdscr.keypad(True)
    if curses.has_colors():
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)     # label
        curses.init_pair(2, curses.COLOR_GREEN, -1)    # hit
        curses.init_pair(3, curses.COLOR_YELLOW, -1)   # title/focus

    attrs = {
        "label": curses.color_pair(1) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD,
        "hit": curses.color_pair(2) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD,
        "plain": curses.A_NORMAL,
        "dim": curses.A_DIM,
    }

    query, prefix, suffix = "", "", ""
    focus_order = ["query", "start", "end"]
    focus = "query"
    mode = "edit"
    scroll = 0

    def safe(y, x, text, attr=curses.A_NORMAL):
        h, w = stdscr.getmaxyx()
        if 0 <= y < h and x < w:
            stdscr.addstr(y, x, text[: max(0, w - x - 1)], attr)

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        # title bar
        title = " ACRONYM FINDER · brandable name generator "
        safe(0, 0, title.ljust(w - 1), curses.A_REVERSE)

        # mode indicator
        mode_desc = ("ANAGRAM (uses your letters, ±1, any order)"
                     if mode == "anagram"
                     else "1-LETTER (add / remove / swap, in place)")
        safe(1, 0, f"  Mode: {mode_desc}   ·   Ctrl-A to toggle", attrs["dim"])

        # input fields
        m = {f: ("▸" if focus == f else " ") for f in focus_order}
        safe(2, 0, f"{m['query']} Letters/phrase: ", attrs["label"])
        safe(2, 18, query)
        safe(3, 0, f"{m['start']} Pin start with: ", attrs["label"])
        safe(3, 18, prefix if prefix else "(none)",
             curses.A_NORMAL if prefix else attrs["dim"])
        safe(4, 0, f"{m['end']} Pin end with:   ", attrs["label"])
        safe(4, 18, suffix if suffix else "(none)",
             curses.A_NORMAL if suffix else attrs["dim"])

        word, rows = build_lines(query, prefix, suffix, mode, w)
        if word and word != query.strip().upper():
            safe(5, 0, f"  → acronym: {word}", attrs["dim"])

        # results area
        top = 7
        avail = h - top - 1
        scroll = max(0, min(scroll, max(0, len(rows) - avail)))
        view = rows[scroll: scroll + avail]
        for i, (text, key) in enumerate(view):
            safe(top + i, 0, text, attrs[key])
        if len(rows) > scroll + avail:
            safe(h - 2, 0, f"  ↓ {len(rows) - scroll - avail} more "
                           f"(PgDn/↓ to scroll)", attrs["dim"])

        # footer
        footer = (" Tab: field   Ctrl-A: mode   ↑↓/PgUp/PgDn: scroll   "
                  "Ctrl-U: clear   Ctrl-Q: quit ")
        safe(h - 1, 0, footer.ljust(w - 1), curses.A_REVERSE)

        # park cursor in the active field
        row = {"query": 2, "start": 3, "end": 4}[focus]
        cur = {"query": query, "start": prefix, "end": suffix}[focus]
        stdscr.move(row, min(18 + len(cur), w - 1))
        stdscr.refresh()

        ch = stdscr.getch()

        if ch in (17,):                       # Ctrl-Q
            break
        elif ch == 1:                          # Ctrl-A: toggle match mode
            mode = "anagram" if mode == "edit" else "edit"
            scroll = 0
        elif ch == 9:                          # Tab: cycle fields
            focus = focus_order[(focus_order.index(focus) + 1) % len(focus_order)]
        elif ch == 21:                         # Ctrl-U: clear active field
            if focus == "query":
                query = ""
            elif focus == "start":
                prefix = ""
            else:
                suffix = ""
            scroll = 0
        elif ch in (curses.KEY_BACKSPACE, 127, 8):
            if focus == "query":
                query = query[:-1]
            elif focus == "start":
                prefix = prefix[:-1]
            else:
                suffix = suffix[:-1]
            scroll = 0
        elif ch in (curses.KEY_DOWN,):
            scroll += 1
        elif ch in (curses.KEY_UP,):
            scroll = max(0, scroll - 1)
        elif ch == curses.KEY_NPAGE:           # Page Down
            scroll += max(1, (h - 8))
        elif ch == curses.KEY_PPAGE:           # Page Up
            scroll = max(0, scroll - max(1, (h - 8)))
        elif ch == curses.KEY_RESIZE:
            pass
        elif 32 <= ch <= 126:                  # printable
            c = chr(ch)
            if focus == "query":
                if c.isalpha() or c == " ":
                    query += c
            elif focus == "start":
                if c.isalpha():
                    prefix += c.upper()
            else:
                if c.isalpha():
                    suffix += c.upper()
            scroll = 0
        # ignore everything else


def main():
    af.load_words()
    af.load_names()
    curses.wrapper(run)


if __name__ == "__main__":
    main()
