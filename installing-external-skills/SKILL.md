---
name: installing-external-skills
description: Install third-party skill packages into a Hermes profile.
---

# Installing External Skill Packages into Hermes

Third-party "skills" packages (OKX Onchain OS, vercel-labs `skills` ecosystem, agent-native game helpers) ship as a GitHub repo with `skills/<name>/SKILL.md` plus `references/` and sometimes `_shared/`. Their stock installers target Claude/Cursor/Codex agent directories, NOT this Hermes profile — so bypass the installer and copy the skill directories straight into the profile's skill dir.

## When to Use

- User asks to install an external/agent-native skill package, or to run `npx ... install` that installs "skills".
- A README says `npx skills add <repo> -g` or `npx @scope/installer install`.
- Don't use for: authoring a NEW skill (see `hermes-agent-skill-authoring`) or rewriting vendor skill content.

## Procedure

1. **Resolve the real source.** A spec like `@file:okxweb3/onchainos-installer` is a broken `@file` reference, not a package name. Confirm the npm package with `npm view <name>`; find the skills' GitHub repo (e.g. `okx/onchainos-skills`) from the package's `repository`/README. The SKILL.md files live in the repo, not in the npm tarball.
2. **Shallow-clone the repo:** `git clone --depth 1 <repo-url>`.
3. **Locate `skills/`.** Each entry is `<name>/` with `SKILL.md` + `references/` + optional `_shared/`.
4. **Copy each `skills/<name>/` into the profile skill dir** with `cp -r`:
   - Windows: `C:\Users\<user>\AppData\Local\hermes\profiles\<profile>\skills\<name>/`
   - Keep the dirs **flat siblings** — some SKILL.md files cross-reference `../<sibling>/_shared/<file>.md`, which only resolves when siblings share one parent.
5. **Verify:** each copied dir has `SKILL.md`, and its `references/` file count matches the source (`find`).
6. **Reload note:** the current session's loader is snapshotted at start; new skills surface only after a reload/new session.

## Pitfalls

- `npx skills add <repo> -g` (the vercel-labs `skills` CLI) installs to Claude/Cursor/etc. agent dirs, not this Hermes profile. Copy the dirs yourself rather than trusting the installer's skills step.
- Installer wrappers often also install a CLI binary through a separate `.ps1`/`.sh` step. When the goal is only the SKILL files, skip that step — the binary is separate from the skills and not needed to load them.
- Windows PowerShell 5.1 reads a `.ps1` with no UTF-8 BOM as ANSI (cp1252), so non-ASCII chars like em-dash (`—`) or smart quotes get mangled and can break parsing (`ParserError`, `MissingEndCurlyBrace`). A `.ps1` containing such characters must be saved as UTF-8 **with** BOM (+ CRLF) to run. OKX's `install.ps1` ships with em-dashes and no BOM, which triggers exactly this.
