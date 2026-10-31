---
name: markdown-restructure
description: Use when tidying or restructuring a Markdown doc.
version: 1.0.0
metadata:
  hermes:
    tags: [markdown, readme, docs, formatting, verification]
---

# Markdown Restructure

Tidying a document is a **content-preserving rewrite**, not a re-authoring. The deliverable is the same facts in a better shape, proven by checks rather than by impression.

## When to Use

- "rapiin md-nya", "tidy this README", "restructure the docs", "format this properly", "make this readable".
- A doc arrived as a paste or extract (downloaded zip, shared folder, hand-written notes) and still reads like raw notes.
- Any request to reformat a `.md` while keeping its meaning.

Not this skill: writing new documentation from scratch, or extracting tasks/citations from a doc.

## Non-negotiables

1. **Nothing is deleted.** Tidying may reorder, relabel, split into tables, add a TOC and a TL;DR — never drop a step, warning, path, flag, or error string. If a fact looks wrong, keep it and flag it in the reply; do not silently "fix" behavior you cannot run.
2. **Back up before the first write, outside the folder.** Copy into a sibling `md-backup/` directory instead of leaving `README.original.md` beside the file:

   ```bash
   mkdir -p ~/Downloads/md-backup
   cp "$DIR/README.md" ~/Downloads/md-backup/<folder>_README.original.md
   ```

   Extracted/downloaded folders are usually not git repos, so this copy is the only undo — but a stray `*.original.md` inside the folder pollutes one whose own README enumerates its files, and it rides along in the zip the user forwards to someone else. Prefix each backup with its source folder name so several coexist; name the path in the reply.
3. **Never invent commands, flags, menu items, or numbers.** The doc is the spec for a program you did not run. A tidy that invents `--force` is worse than the original. When the doc documents a runnable command that produces a number, run it and keep the number only if it matches — a `# 38 cek` comment earned its place once `python fs_audit.py` printed `38 cek: 36 ok, 2 warn, 0 bad`. If the number no longer matches, keep the doc's claim and flag the mismatch in the reply instead of silently rewriting the count.
4. **Keep every secrets warning, in place.** Docs that carry cookies, private keys, or API keys usually have a "jangan dibagikan / do not share" line near the config file. Losing that line during a cosmetic pass is real harm.
5. **Verify before reporting, and quote the numbers.** Run `scripts/verify_md.py`, report counts (tables, fences, anchors, preserved facts). "Looks cleaner" is not a result.
6. **Answer in the user's language, casually, without narrating the process.** For this user: Bahasa Indonesia, short, no play-by-play of which tool you called.

## Procedure

1. **Find candidates.** Do not guess which file "the md" means.
   ```bash
   cd ~ && find . -maxdepth 4 -name '*.md' \
     -not -path '*/node_modules/*' -not -path '*/.git/*' \
     -printf '%TY-%Tm-%Td %TH:%TM  %8s  %p\n' | sort -r | head -20
   ```
2. **Read the plausible ones in parallel** (`read_file`), so the clarify question and the rewrite are both informed.
3. **Disambiguate with one `clarify`** when more than one file is plausible: put the candidates in `choices`, newest first, and add a "do all of them" option. Then act without further questions.
4. **Back up** the chosen file.
5. **Rewrite** the whole file with `write_file` (a tidy touches most lines; piecemeal `patch` calls leave the shape half-converted). Apply the house style below.
6. **Verify** with the script, plus a key-fact list for domain strings (`AUTH MATI`, `0x`, `socks5://`, every filename). Pass `--frontmatter` when the doc carries a YAML block.
7. **Clean up what verification left behind.** Running a documented script inside the target folder can drop `__pycache__/`, cache dirs, or log files — delete them before reporting, or the "tidied" folder ships dirtier than it arrived.
8. **Report** as a before/after table of the changes, then the verification numbers, then offer the sibling candidates you found in step 1.

## "Rapi" — the house style

What the user actually accepts as tidy, in the order it matters:

- **TOC with anchor links** at the top when the doc has ~5+ sections; every anchor must resolve (the script checks slugs).
- **One `---` between top-level sections, none inside.** Original files often put a rule after every heading, which reads as noise.
- **Every fenced block gets a language tag** — `bat`, `bash`, `text`, `json`, `powershell`. A bare fence renders unhighlighted.
- **Symptom→solution prose becomes a 2-column table** (`| Gejala | Penyebab & solusi |`). This is the single biggest readability win in install/troubleshooting READMEs.
- **Promote bold lead-ins to real headings.** `**Cara paling gampang:**` → `### Cara paling gampang`.
- **Tables aligned**, one header row, separator with matching column count.
- **Bold only for UI labels, values, and warnings** — not whole sentences, not every other word.
- **Fix typos and localize numbers** (`Resiko`→`Risiko`, `1.5`→`1,5` for an Indonesian doc). Localization is a formatting change, not a content change.
- **Add a "cara tercepat" one-liner** at the top when the doc opens with a long install path: the shortest path from zero to working, in one line.
- **Keep the author's ordering of steps.** Reordering inside a procedure breaks prerequisites.

## Front-matter docs (SKILL.md, Jekyll/Hugo, mkdocs)

A leading `---` block is machine-read, not prose — treat it as untouchable.

- Leave key order, quoting, anchors and comments exactly as the author wrote them. Reformatting `tags: [a, b]` into a bullet list looks equivalent and is not guaranteed to parse the same.
- Prove equality instead of asserting it: `--frontmatter` compares the block parsed with `yaml.safe_load` on both files and fails on any difference.
- For a skill doc, the `name`/`description` pair *is* the trigger. Rewriting the body is the job; shortening the description quietly changes when the skill fires, so copy it through character for character.
- Every rule in this skill still applies to the body below the block.

## Verify

```bash
python scripts/verify_md.py README.md --base README.original.md \
  --require "weeds.bat,socks5://,AUTH MATI,config.json"
```

Hard checks (non-zero exit): TOC anchors resolve to real headings, fences balanced, every table block has a consistent column count and a valid separator row, every `--require` token present. Warnings: inline `code` tokens from `--base` that vanished, word/byte delta. Treat a vanished token as a prompt to look, not proof of loss — reformatting legitimately drops some spans.

## Pitfalls

- **`search_files(target=files, order=modified)` drowns in `node_modules`.** It returns dependency READMEs before the doc you meant. Use the `find` command above with the two `-not -path` filters instead.
- **`hermes_tools.read_file` inside `execute_code` dedups.** If the file was already read this session, the result has no `content` key and `.get("content","")` silently yields `""` — the verifier then reports everything as lost. Use plain `open(path, encoding="utf-8").read()` in the verification script.
- **Do not summarize the delta as a quality metric.** A good tidy usually grows the file (TOC + tables + fences); a shrinking doc is the suspicious one, because it means content went missing.
- **Do not chase decorative styling in the author's warnings.** Convert `→` arrows and `⚠` only if the doc's own tone supports it; keep the warning text verbatim.
- **A single-file rewrite is not a refactor of the sibling docs.** If you noticed other unpolished `.md` files while searching, list them at the end as an offer, do not touch them unasked.
- **A `|` inside a code span is escaped (`\|`) and is not a column break.** Split table rows on unescaped pipes only; a naive `split('|')` calls a valid GFM row like `` `GET /api/market?asset=relic\|loom` `` ragged and sends you chasing a table that was already correct.
- **Rendering is a second opinion, not a replacement for the token checks.** With `markdown_it` available, `MarkdownIt('commonmark').enable('table')` renders the doc and you can count `<table>` blocks; the `gfm-like` preset raises without the optional `linkify` package installed, which reads like a doc defect and is not one.
- **A folder that documents its own file list must not gain a file.** If the doc has an "isi folder" / files table, the backup belongs outside it (rule 2) — otherwise you owe the table a row.

## Files

- `scripts/verify_md.py` — anchor/fence/table/required-token/silent-content-loss checker for a rewritten doc; `--frontmatter` adds a parsed-YAML equality check for SKILL.md-style docs.
