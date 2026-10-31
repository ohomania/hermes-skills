# REA — reverse-engineering MCP server

Vendor: `morluto/rea` (`https://rea.tools`). npm package `rea-agents`, binary `rea`. MIT.

## Install / register

```bash
npm install -g rea-agents          # binary lands on PATH (may live inside the Hermes node dir)
rea --version
rea setup --client hermes --dry-run --format json   # read plannedActions first
rea setup --client hermes --yes
```

`setup` makes two writes into the profile: the `mcp_servers.rea` block in `config.yaml`, and the bundled skill `skills/reverse-engineer-anything/` (SKILL.md + `references/`). `--skill=false` skips the skill; `--install-hopper` is only meaningful together with `--yes`. Supported client IDs include `hermes`, `claude_code`, `codex`, `cursor`, `opencode`, `vscode`, `dsh` and more — read the repo's `docs/installation.md` table instead of guessing.

Verify:

```bash
hermes mcp test rea        # → Connected, Tools discovered: ~200
rea doctor --client hermes # healthy vs environment_healthy
```

## What works with no extra engine

JavaScript/Electron (directory or `.asar`), Go, Rust, IL2CPP metadata, Godot PCK, GGUF/safetensors, WASM (with caller-supplied WABT), PE certificates, ELF notes, SQLite, desktop installs, and the HarmonyOS/Android/iOS project graphs.

## Optional engines (native binaries, decompilation)

| Engine | Enable with |
|---|---|
| Hopper | `rea setup --install-hopper --yes`, or `HOPPER_LAUNCHER_PATH` |
| Ghidra 12.1.x | `GHIDRA_INSTALL_DIR=<extracted dir>` |
| IDA | `REA_IDA_MCP_CONFIG=<upstream IDA MCP registration JSON>` |
| JADX (APK) | JADX on PATH |

Until one exists, `rea doctor` reports `healthy: true` with `environment_healthy: false` — registration is fine, native analysis is not available yet.

## CLI usage worth remembering

```bash
rea analyze-javascript-application "/path/to/app.asar" --json   # Evidence bundle on stdout
rea analyze /path --json
rea --help | head -45                                           # 100+ subcommands
rea update                                                      # then re-run `rea setup`
```

Fields worth quoting from the JSON: `evidence_id`, `normalized_result.summary`, `normalized_result.statistics` (modules, findings, parsed files, `parse_failures`), `normalized_result.graph` (nodes/edges), and `limitations[]`. They make a result auditable instead of a claim.

## Notes

- The MCP surface is large (~207 tools); prune with `hermes mcp configure rea` when context matters.
- Manual registration entry: `<node> <npm root>/rea-agents/scripts/rea.mjs mcp`.
- `setup` rewrites `config.yaml` with LF endings even when the file was CRLF — normalize before diffing, restore endings afterwards.
