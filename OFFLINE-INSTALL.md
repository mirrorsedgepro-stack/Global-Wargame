# Global Wargame — Offline Install

A self-contained tabletop wargame engine. **No installer, no internet, no
account.** Just unzip and open.

## What's in the package

- `home.html` — start here
- `index.html` — Operations Center (browse / filter all 147 cards)
- `engine.html` — adjudicator, scoring, hot-seat play
- `globe.html` — live 3D Earth with arcs and DIME compass roses
- `card-builder.html` — author new cards, exports to a standalone .html
- `diagnostics.html` — verify the install
- `theme.css`, `theme.js` — shared styling and light/dark theme toggle
- `engine-data.js` — bundled card and country data
- 147 `*-*-*.html` files — one per action card

## Install

1. Copy the entire folder to the destination machine (USB stick, network
   share, anywhere). Keep the file names — the engine resolves cards by
   filename pattern.
2. Double-click `home.html`. It opens in the default browser.
3. From there, every link works without a server.

## How to play

- **Browse cards** → click `Operations Center` from the home page.
- **Score / play hands** → click `Engine`. Hot-seat 2–4 players supported.
- **See it live** → click `Open Globe View` from the engine. Engine actions
  push to the globe via `postMessage`, no server in the loop.
- **Toggle dark mode** → sun/moon button, top-right of every page. Choice
  persists in `localStorage` per machine.

## If `Diagnostics` shows red

`diagnostics.html` verifies all 147 cards are present and reachable. It
uses `fetch()` first, then falls back to `XMLHttpRequest` if the browser
blocks `fetch()` on `file://` URLs.

If diagnostics still fails, run a tiny static server in the folder:

```sh
python3 -m http.server 8000     # then open http://localhost:8000/home.html
```

Any browser-based static server works (Caddy, `npx serve`, IIS Express,
etc.). No network access required — it serves from the local folder.

## Caveats

- The `Globe View` opens in a popup window — the destination browser must
  allow popups for `file://` URLs (most do by default; some Chrome
  policies block it). If popups are blocked, open `globe.html` manually
  in another tab — the engine will still post state to it through
  `window.opener`.
- All preferences (theme, last-played hand) live in browser
  `localStorage`. Clearing the browser's site data resets them.

## Update / re-export

To take a fresh snapshot from this same machine, just rezip the folder.
Nothing in the package phones home, fetches a CDN, or writes outside
`localStorage`.
