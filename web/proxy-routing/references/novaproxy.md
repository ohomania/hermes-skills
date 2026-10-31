# NovaProxy — read credentials programmatically

Public API: `https://public-api.novaproxy.io`. Auth: `Authorization: Bearer <token>`
(the token is a UUID; dashboard → API section).

- `GET /orders` → array of orders, each with `uuid`, `username`, `password`,
  `plan.slug`, `connection.host.value` + `connection.protocols[]`
  (`{code:"http"|"socks5"|"udp", port}`), `expires_at`, `status`,
  `initial/remaining_bandwidth_in_bytes`.
- Proxy URL = `protocol://username:password@host:port` — same creds for http and
  socks5, different ports (Residential Budget = `residential-budget.novaproxy.io`,
  http 6969 / socks5 9696).
- Rotating by default; sticky/geo via modifiers appended to the username or
  password (see the order's `connection.modifiers` — target, separator, token shape).

The dashboard order page is a JS SPA (`no content extracted` via curl); always
read creds through this API with the Bearer token, never by scraping the page.
