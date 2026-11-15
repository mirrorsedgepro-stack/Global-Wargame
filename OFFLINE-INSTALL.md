# Global Wargame — Offline Install

A self-contained tabletop wargame engine. **No installer, no internet, no
account.** Just unzip and open.

## What's in the package

- `home.html` — start here; the whole app, with every tool as a tab
- `overview.html` — the Home tab
- `index.html` — Operations Center (browse / filter the catalogue)
- `engine.html` — adjudicator, scoring, hot-seat play
- `globe.html` — live 3D Earth with arcs and DIME compass roses
- `tactical.html` — two-player hidden-order map
- `card-builder.html` — author new cards, exports to a standalone .html
- `diagnostics.html` — verify the install
- `theme.css`, `theme.js` — shared styling and light/dark theme toggle
- `engine-data.js` — card metadata and counter graph (147 cards in this snapshot)
- `world-geo-data.js` — coastlines and borders for the tactical map
- `cards/` — 147 `PHASE-DOMAIN-NN-slug.html` files, one per action card

## Install

1. Copy the entire folder to the destination machine (USB stick, network
   share, anywhere). Keep the file names — the engine resolves cards by
   filename pattern.
2. Double-click `home.html`. It opens in the default browser.
3. From there, every link works without a server.

## How to play

- **Browse cards** → click `Operations Center` from the home page.
- **Score / play hands** → click `Engine`. Hot-seat 2–4 players supported.
- **See it live** → click `Open Globe View` from the engine, or the Globe
  tab. On a desktop the globe can sit beside the engine (Split button).
  Engine actions push to the globe via `postMessage`, no server in the loop.
- **Tactical map** → open `Tactical Operations` from the home page.
- **Toggle dark mode** → sun/moon button in the top bar (desktop) or
  More menu (phone). Choice
  persists in `localStorage` per machine.

## If `Diagnostics` shows red

`diagnostics.html` checks that the pages and sidecars listed above are
reachable, then audits the catalogue inside `engine-data.js` (card count,
titles, actors, and counter edges). It does not download every file in
`cards/`. It uses `fetch()` first, then falls back to `XMLHttpRequest` if
the browser blocks `fetch()` on `file://` URLs.

If diagnostics still fails, run a tiny static server in the folder:

```sh
python3 -m http.server 8000     # then open http://localhost:8000/home.html
```

Any browser-based static server works (Caddy, `npx serve`, IIS Express,
etc.). No network access required — it serves from the local folder.

## Caveats

- Inside `home.html` the globe is a tab, so no popup is needed. A tool
  opened on its own (`engine.html?standalone=1`) still opens the globe
  in a popup window — the destination browser must
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

After adding or editing cards, regenerate the sidecar before you rezip.
From the folder that contains `pack/` and `cards/`:

```sh
python3 pack/build.py
```

That rewrites `engine-data.js` from `cards/`. It also rewrites `globe.html`
and `world-geo-data.js` from `pack/globe.template.html` plus the coastline
JSON in `pack/`. See `README.md` for what the script leaves alone.
