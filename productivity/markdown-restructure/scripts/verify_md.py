#!/usr/bin/env python3
"""Verify a restructured Markdown doc.

Usage:
  python verify_md.py NEW.md
  python verify_md.py NEW.md --base ORIG.md
  python verify_md.py NEW.md --base ORIG.md --require "weeds.bat,socks5://"
  python verify_md.py NEW.md --require-file needed.txt

Hard checks (exit 1 on failure): TOC anchors resolve, code fences balanced,
every table block has a consistent column count and a valid separator row,
all --require tokens present.

Warnings only: inline code spans present in --base but missing from NEW,
word/byte delta.
"""
import argparse
import re
import sys

FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
ANCHOR_RE = re.compile(r"\]\(#([^)\s]+)\)")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
SEP_CELL_RE = re.compile(r"^:?-{2,}:?$")
CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.S)


def split_fences(md):
    """Return (lines_outside_fences, fenced_blocks, fences_balanced)."""
    outside, blocks, cur = [], [], []
    in_f, marker = False, None
    balanced = True
    for line in md.splitlines():
        m = FENCE_RE.match(line)
        if m:
            tok = m.group(1)[0]
            if not in_f:
                in_f, marker, cur = True, tok, []
            elif tok == marker:
                in_f = False
                blocks.append(cur)
                cur = []
                marker = None
            continue
        (cur if in_f else outside).append(line)
    if in_f:
        balanced = False
        blocks.append(cur)
    return outside, blocks, balanced


def slug(text):
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s.strip("-")


def check_headings(outside):
    heads, counts = [], {}
    for line in outside:
        m = HEADING_RE.match(line)
        if m and m.group(2):
            heads.append(m.group(2))
    slugs = set()
    for h in heads:
        s = slug(h)
        counts[s] = counts.get(s, 0) + 1
        slugs.add(s if counts[s] == 1 else "%s-%d" % (s, counts[s] - 1))
    return heads, slugs


def table_cells(row):
    """Split one GFM table row into cells, ignoring escaped pipes.

    A cell like `GET /api/market?asset=relic\|loom` contains an escaped pipe
    that keeps the code span intact; splitting on every "|" would report the
    row as ragged.
    """
    r = row.strip()
    if r.startswith("|"):
        r = r[1:]
    if r.endswith("|") and not r.endswith("\\|"):
        r = r[:-1]
    return [c.strip() for c in CELL_SPLIT_RE.split(r)]


def check_tables(outside):
    problems, blocks, cur = [], [], []
    for line in outside:
        if line.strip().startswith("|"):
            cur.append(line.strip())
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    for i, block in enumerate(blocks, 1):
        if len(block) < 2:
            problems.append("table %d: fewer than 2 rows" % i)
            continue
        widths = [len(table_cells(r)) for r in block]
        if len(set(widths)) != 1:
            problems.append("table %d: ragged columns %s" % (i, sorted(set(widths))))
        sep_cells = table_cells(block[1])
        if not all(SEP_CELL_RE.match(c) for c in sep_cells):
            problems.append("table %d: row 2 is not a valid separator" % i)
    return problems, len(blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("new")
    ap.add_argument("--base")
    ap.add_argument("--require", default="")
    ap.add_argument("--require-file")
    ap.add_argument("--strict-lost", action="store_true")
    ap.add_argument("--frontmatter", action="store_true",
                    help="require a YAML frontmatter block identical to --base")
    args = ap.parse_args()

    md = open(args.new, encoding="utf-8").read()
    base_md = open(args.base, encoding="utf-8").read() if args.base else None
    outside, blocks, balanced = split_fences(md)
    heads, slugs = check_headings(outside)
    table_problems, n_tables = check_tables(outside)

    fm_note, fm_problem = "-", None
    if args.frontmatter:
        m_new = FM_RE.match(md)
        if m_new is None:
            fm_problem = "no YAML frontmatter block found"
            fm_note = "missing"
        elif base_md is None:
            fm_note = "present (no --base to compare)"
        else:
            m_base = FM_RE.match(base_md)
            if m_base is None:
                fm_problem = "--base has no frontmatter block to compare"
                fm_note = "uncompared"
            else:
                a, b = m_base.group(1), m_new.group(1)
                try:
                    import yaml
                    same = yaml.safe_load(a) == yaml.safe_load(b)
                    how = "parsed YAML"
                except Exception:
                    same = a.strip() == b.strip()
                    how = "raw text"
                fm_note = "identical=%s (%s)" % (same, how)
                if not same:
                    fm_problem = "frontmatter changed vs --base"

    link_targets = set(ANCHOR_RE.findall(md))
    broken = sorted(t for t in link_targets if t not in slugs)

    required = [t.strip() for t in args.require.split(",") if t.strip()]
    if args.require_file:
        required += [l.strip() for l in open(args.require_file, encoding="utf-8") if l.strip()]
    missing_required = [t for t in required if t not in md]

    lost = []
    if base_md is not None:
        base_tokens = {t.strip() for t in INLINE_CODE_RE.findall(base_md)}
        base_tokens = {t for t in base_tokens if len(t) >= 4 and not t.startswith("#")}
        for tok in sorted(base_tokens):
            if tok not in md:
                lost.append(tok)

    print("file    : %s" % args.new)
    print("lines   : %d   bytes: %d" % (len(md.splitlines()), len(md.encode("utf-8"))))
    print("headings: %d   anchors linked: %d" % (len(heads), len(link_targets)))
    print("tables  : %d" % n_tables)
    print("fences  : %d blocks, balanced=%s" % (len(blocks), balanced))
    print("required: %d given, %d missing" % (len(required), len(missing_required)))
    if args.frontmatter:
        print("frontmt : %s" % fm_note)

    fails = []
    if not balanced:
        fails.append("unbalanced code fences")
    if broken:
        fails.append("broken anchors: %s" % ", ".join("#" + b for b in broken))
    if table_problems:
        fails.append("tables: " + "; ".join(table_problems))
    if missing_required:
        fails.append("missing required tokens: %s" % ", ".join(missing_required))
    if fm_problem:
        fails.append("frontmatter: %s" % fm_problem)

    if lost:
        tag = "FAIL" if args.strict_lost else "WARN"
        print("%s    : %d inline code tokens from base are gone: %s"
              % (tag, len(lost), ", ".join(lost[:25])))
        if args.strict_lost:
            fails.append("lost code tokens")

    if base_md is not None:
        bw = len(base_md.split())
        nw = len(md.split())
        print("words   : %d -> %d (%+d)  [growth is expected; shrinkage means lost content]"
              % (bw, nw, nw - bw))

    if fails:
        print("RESULT  : FAIL")
        for f in fails:
            print("  - %s" % f)
        return 1
    print("RESULT  : PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
