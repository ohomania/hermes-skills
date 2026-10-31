# Userscript HUD — foldable panel, toggle switches, live feedback

Concrete patterns that satisfy this user. Copy these decisions.

## Skeleton
- Floating pill, bottom-right, `z-index` >= `2147483000`, a pulsing dot; click
  toggles panel visibility. Pill color encodes RUNNING vs STOPPED / online vs
  offscreen.
- Panel: `position:fixed; max-height:82vh; display:flex; flex-direction:column;
  overflow:hidden`, three rows: drag-handle header, scrollable middle, fixed log.

## Scroll (fixes "tidak bisa discroll")
- The middle content lives in its own wrapper:
  `flex:1 1 auto; min-height:0; overflow-y:auto; overscroll-behavior:contain`.
  Without `min-height:0` a flex child won't shrink below its content height, so
  it overflows a `max-height` panel and gets clipped by `overflow:hidden` —
  lower content is unreachable and nothing scrolls.
- The log is a separate `flex:0 0 <px>; overflow-y:auto` block.
- Rebuilding the log with `innerHTML=''` every tick resets `scrollTop`. Capture
  `follow = (scrollHeight - scrollTop - clientHeight) < 40` BEFORE clearing, then
  only re-snap to bottom when `follow` is true. Forcing bottom every render makes
  the log impossible to scroll up.
- Style the scrollbar thumb to a visible mid-tone, never the browser default — a
  dark default renders black-on-black against the panel and reads as "scroll is
  just black / broken". On the scrollable blocks set
  `::-webkit-scrollbar{width:8px}`,
  `::-webkit-scrollbar-track{background:transparent}`,
  `::-webkit-scrollbar-thumb{background:#4a4360;border-radius:8px;border:2px solid transparent;background-clip:content-box}`,
  plus `scrollbar-width:thin; scrollbar-color:#4a4360 transparent` for Firefox.

## Toggle switch (no checkboxes)
Render a `<span class="sw on|off">` holding a knob + `ON`/`OFF` text; a click
flips the class and label, then calls the change callback. Persist to
localStorage. One master switch at the top, one per rule.

## Live feedback (prevents "bot gak jalan")
Always render: RUNNING/STOPPED, detected (non-disabled) button count, total
clicks, last action + timestamp. When an enabled rule matches nothing for >60s,
log `rule ON tapi tombol tidak ketemu` once a minute — the fastest diagnosis for
a dead bot.

## Button matching + scan
- Candidate selector: `button, [role=button], a, [class*=btn], [class*=button]`;
  skip `disabled` / `aria-disabled=true`.
- Match on `textContent + aria-label + title`, case-insensitive, exact or contains.
- **Always add a generic-element fallback.** Game UI "buttons" (job cards, tier
  chips, tabs, action rows) are frequently `<div>`/`<span>` with a click handler,
  not `<button>` — a `<button>`-only matcher silently finds nothing and the bot
  reads as dead. Fall back to
  `div,span,label,li,[class*=card],[class*=tile],[class*=item],[class*=tab]` and
  return the *smallest* node whose trimmed text matches (shortest text wins), so
  a large container that merely contains the text is skipped. Preact/React
  dispatch `.click()` via delegated listeners, so a found `<div>` clicks fine.
- Provide a "Scan" button that dumps every unique visible button text to console
  (buttons AND leaf `<div>/<span>` text ≤ ~25 chars — those are usually the tabs);
  use the fed-back labels to wire real rules when the UI wasn't visible in recon.
