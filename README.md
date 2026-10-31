# Hermes Skills

Kumpulan **89 skill** untuk Hermes Agent / Claude Code, terorganisir per kategori.
Setiap skill adalah folder berisi `SKILL.md` (prompt/instruksi) plus opsional `references/`, `scripts/`, `templates/`, `assets/`.

## Indeks

| Skill | Deskripsi |
|---|---|
| `binance-agentic-wallet` | Use when minting or listing NFTs on BNB Chain via baw CLI. |
| `installing-external-skills` | Install third-party skill packages into a Hermes profile. |
| `okx-agent-payments-protocol` | Handle agent payments and paid endpoints via x402, MPP, payment links, a2a-pay, and HTTP-payment recurring or metered bi |
| `okx-agentic-wallet` | Operate OKX Onchain OS wallets and execute or inspect on-chain transactions. Use for wallet login/status/accounts/addres |
| `okx-ai` | Operate OKX.AI agents and marketplace workflows. Use when the user wants to register, update, or view Agent identities;  |
| `okx-dapp-discovery` | Discover supported third-party DApps and route protocol-specific requests to OKX plugins without signing or broadcasting |
| `okx-defi` | Discover and manage OKX-aggregated DeFi products and positions across protocols and chains. Use for generic or venue-agn |
| `okx-dex-market` | Query read-only DEX token, market, signal, social, trenches, and WebSocket data. Use for token search, rankings, liquidi |
| `okx-guide` | Guide users through installing or updating Onchain OS, getting started, OKX.AI introduction and role-registration routin |
| `ponytail` | Lazy senior dev mode: the smallest change that fully solves the task, and a reply a busy human understands in one read.  |
| `ponytail-audit` | Quality audit of a whole repo: bugs, security holes, what breaks under real load, risky code without tests, slow paths,  |
| `ponytail-debt` | List every `shortcut:` comment (and older `ponytail:` ones) as a debt ledger. One-shot report, changes nothing. Use for  |
| `ponytail-gain` | Show ponytail's measured savings (code, cost, speed) from the benchmark. One-shot display. Use for /ponytail-gain, "what |
| `ponytail-help` | Quick reference for ponytail levels, skills and commands. One-shot display. Use for /ponytail-help, "ponytail help", "ho |
| `ponytail-review` | Quality review of a change: is the logic right, is it safe, does it hold under real load, is risky code tested, is it fa |
| `reverse-engineer-anything` | Reverse engineer native, managed, Electron/JavaScript, packaged, firmware, and browser targets with REA. Use shipped-art |
| `apple\apple-notes` | Manage Apple Notes via memo CLI: create, search, edit. |
| `apple\apple-reminders` | Apple Reminders via remindctl: add, list, complete. |
| `apple\findmy` | Track Apple devices/AirTags via FindMy.app on macOS. |
| `apple\imessage` | Send and receive iMessages/SMS via the imsg CLI on macOS. |
| `autonomous-ai-agents\claude-code` | Delegate coding to Claude Code CLI (features, PRs). |
| `autonomous-ai-agents\codex` | Delegate coding to OpenAI Codex CLI (features, PRs). |
| `autonomous-ai-agents\computer-use` | Drive the desktop background-first; escalate on signal. |
| `autonomous-ai-agents\hermes-agent` | Use, configure, theme, extend, and orchestrate Hermes Agent. |
| `autonomous-ai-agents\mcp-server-integration` | Use when wiring an external MCP server into Hermes. |
| `autonomous-ai-agents\opencode` | Delegate coding to OpenCode CLI (features, PR review). |
| `creative\architecture-diagram` | Dark-themed SVG architecture/cloud/infra diagrams as HTML. |
| `creative\ascii-video` | ASCII video: convert video/audio to colored ASCII MP4/GIF. |
| `creative\baoyu-infographic` | Infographics: 21 layouts x 21 styles (信息图, 可视化). |
| `creative\claude-design` | Design one-off HTML artifacts (landing, deck, prototype). |
| `creative\design-md` | Author/validate/export Google's DESIGN.md token spec files. |
| `creative\humanizer` | Humanize text: strip AI-isms and add real voice. |
| `creative\manim-video` | Manim CE animations: 3Blue1Brown math/algo videos. |
| `creative\p5js` | p5.js sketches: gen art, shaders, interactive, 3D. |
| `creative\popular-web-designs` | 54 real design systems (Stripe, Linear, Vercel) as HTML/CSS. |
| `creative\songwriting-and-ai-music` | Songwriting craft and Suno AI music prompts. |
| `devops\sdlc-review` | Review Kanban handoffs and route verified outcomes. |
| `email\email-inbox-triage` | Triage an inbox: prioritize threads, draft replies safely. |
| `email\himalaya` | Himalaya CLI: IMAP/SMTP email from terminal. |
| `media\gif-search` | Search/download GIFs from Tenor via curl + jq. |
| `media\songsee` | Audio spectrograms/features (mel, chroma, MFCC) via CLI. |
| `media\youtube-content` | YouTube transcripts to summaries, threads, blogs. |
| `note-taking\obsidian` | Read, search, create, and edit notes in the Obsidian vault. |
| `productivity\airtable` | Airtable REST API via curl. Records CRUD, filters, upserts. |
| `productivity\box` | Box manages cloud files, sharing, search, and metadata. |
| `productivity\document-to-action-items` | Extract cited obligations, deadlines, tasks from documents. |
| `productivity\docx` | Create, read, edit, template, and review Word .docx files. |
| `productivity\google-workspace` | Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python. |
| `productivity\maps` | Geocode, POIs, routes, timezones via OpenStreetMap/OSRM. |
| `productivity\markdown-restructure` | Use when tidying or restructuring a Markdown doc. |
| `productivity\meeting-action-items` | Turn meeting notes into cited decisions, owners, tickets. |
| `productivity\microsoft-office` | Create, read, and edit Word, PowerPoint, and Excel files. |
| `productivity\notion` | Notion API + ntn CLI: pages, databases, markdown, Workers. |
| `productivity\pdf` | PDF files: create, read, merge, fill, OCR, edit text. |
| `productivity\powerpoint` | Create, read, edit .pptx decks with python-pptx. |
| `productivity\product-price-monitor` | Watch product, flight, or listing prices; alert on target. |
| `productivity\teams-meeting-pipeline` | Teams meeting summaries, job replay, Graph subscriptions. |
| `productivity\weekly-review-planning` | Weekly reset: commitments, stalled work, next-week plan. |
| `productivity\xlsx` | Create, read, edit Excel .xlsx workbooks and CSVs. |
| `research\arxiv` | Search arXiv papers by keyword, author, category, or ID. |
| `research\competitor-news-monitor` | Watch named companies for material news; cited digests. |
| `research\grounded-citations` | Ground answers and documents in cited, verifiable sources. |
| `research\llm-wiki` | Karpathy's LLM Wiki: build/query interlinked markdown KB. |
| `social-media\xurl` | X/Twitter via xurl CLI: raw post search, posting, DM, media. |
| `software-development\codebase-inspection` | Inspect codebases w/ pygount: LOC, languages, ratios. |
| `software-development\dogfood` | Exploratory QA of web apps: find bugs, evidence, reports. |
| `software-development\evm-contract-ops` | Use when reading or prepping EVM contract txs via RPC. |
| `software-development\github` | GitHub via gh CLI: PRs, issues, reviews, repos, auth. |
| `software-development\hermes-agent-skill-authoring` | Author in-repo SKILL.md files: frontmatter and structure. |
| `software-development\inspecting-hermes-desktop-dom` | Read the live Hermes desktop DOM/CSS over CDP. |
| `software-development\node-inspect-debugger` | Debug Node.js via --inspect + Chrome DevTools Protocol CLI. |
| `software-development\python-debugpy` | Debug Python: pdb REPL + debugpy remote (DAP). |
| `software-development\requesting-code-review` | Pre-commit review: security scan, quality gates, auto-fix. |
| `software-development\simplify-code` | Parallel 4-agent cleanup of recent code changes. |
| `software-development\spike` | Throwaway experiments to validate an idea before build. |
| `software-development\systematic-debugging` | 4-phase root cause debugging: understand bugs before fixing. |
| `software-development\test-driven-development` | TDD: enforce RED-GREEN-REFACTOR, tests before code. |
| `web\blocked-page-recovery` | Use when a fetch fails: 403/429, paywall, WAF, bot wall. |
| `web\evm-contract-operations` | Use for EVM on-chain work: mint, transfer, list, verify. |
| `web\proxy-routing` | Use when routing a CLI, API, or SSH through a proxy. |
| `web\raidlords-bot` | Use when running or fixing the RaidLords headless bot. |
| `web\tampermonkey-bots` | Build Tampermonkey/userscript bots for web apps & games. |
| `web\web-app-automation` | Use when the user wants a bot or automation for a web app. |
| `web3\agent-native-challenge-solving` | Use when solving PoW/planted-SAT gates on .ai-gated mints. |
| `web3\agent-native-game-onboarding` | Use when onboarding a new .ai-gated game mint via baw. |
| `web3\evm-contract-interaction` | Use when scouting EVM contracts or building mint/claim txs. |
| `web3\onchain-mint-challenges` | Solve PoW & planted-SAT challenge mints on BNB via baw. |
| `web3\poa-mining` | Mine the minepoa.com PoA account (challenge + attest). |
| `web3\proof-of-work-mint-challenges` | Use when a free mint gates behind a compute challenge. |

## Struktur

Skill yang punya kategori disimpan sebagai `kategori/skill/`; skill standalone di root. Kategori:

- **(standalone)** — 16 skill
- **apple** — 4 skill
- **autonomous-ai-agents** — 6 skill
- **creative** — 10 skill
- **devops** — 1 skill
- **email** — 2 skill
- **media** — 3 skill
- **note-taking** — 1 skill
- **productivity** — 16 skill
- **research** — 4 skill
- **social-media** — 1 skill
- **software-development** — 13 skill
- **web** — 6 skill
- **web3** — 6 skill

## Lisensi

Beberapa skill di sini adalah bawaan/default Hermes Agent atau vendor pihak ketiga (mis. OKX Onchain OS, Binance Agentic Wallet) dan lisensinya mengikuti sumber aslinya masing-masing — cek `SKILL.md` tiap skill untuk header `license`/`author`. Skill `ponytail-*` berlisensi MIT (© DietrichGebert). Statis/portabel: skill ini bukan eksekusi CLI, silakan diadaptasi.
