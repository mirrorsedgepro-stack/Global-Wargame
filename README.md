# Global Wargame — 2030–2036

A tabletop wargame engine built as standalone HTML pages. The catalogue currently holds **147 action cards** covering the Indo-Pacific, the Middle East, Africa, Europe, and South Asia. It includes a card builder, an adjudication engine, statistics, hot-seat multiplayer, a tactical map, and a live 3D globe.

Displayed card counts on the home page and in the Operations Center are read from `engine-data.js`, so they follow the catalogue instead of a hard-coded 72.

## What's in this folder

- **home.html** — Landing page. Start here.
- **index.html** — Operations Center: filter and search every card. Loads the catalogue from `engine-data.js`.
- **engine.html** — Adjudicator, statistics, hot-seat play. Loads card data from `engine-data.js`.
- **engine-data.js** — Generated sidecar with card metadata and the counter graph. Do not edit by hand.
- **globe.html** — Live 3D globe. Sun-lit Earth with GSHHS coastlines and political borders. Receives state from the engine via `postMessage`. Generated from `pack/` (see below).
- **tactical.html** — Two-player hot-seat map. Hidden movement and engagement orders, resolved with the coastline mask in `world-geo-data.js`.
- **diagnostics.html** — Browser check that the install's pages and sidecars load, then audits the catalogue and counter graph.
- **card-builder.html** — Authoring tool for new cards.
- **theme.css**, **theme.js** — Shared tokens and the light/dark toggle.
- **world-geo-data.js** — Coastline and border arrays used by `tactical.html`. Regenerated with the globe.
- **cards/** — One `.html` file per action card, named `PHASE-DOMAIN-NN-slug.html`.
- **OFFLINE-INSTALL.md** — Copy-and-open instructions for a machine with no network.
- **pack/build.py** — Regenerates `engine-data.js`, `globe.html`, and `world-geo-data.js`.

`PHASE` is `COM` (Competition), `CON` (Conflict), or `CRI` (Crisis). `DOMAIN` is `D`, `I`, `M`, or `E`. The two-digit number is part of the card id; it is not required to be contiguous (several lanes jump from `04` to `11`).

## Quick start

Open **home.html** in any modern browser. From there:

1. **Operations Center** — browse the full catalogue.
2. **Engine** → Play Game tab → add 2–4 players → Start Game → click ◉ Open Globe View.
3. **Tactical Operations** — plot hidden orders on the map.
4. **Diagnostics** — confirm the sidecar and counter graph after copying the folder.
5. **Card Builder** — author a new card, download the `.html`, and drop it into `cards/`.

No install and no network are required. Everything runs locally. `OFFLINE-INSTALL.md` covers a USB-stick copy. Some browsers block `fetch()` on `file://` URLs; a local static server is only needed if Diagnostics cannot see the files.

## Phases and domains

Cards are categorized by **phase**:
- **COM** — Competition (steady-state pressure)
- **CON** — Conflict (kinetic escalation)
- **CRI** — Crisis (high-intensity or post-conflict)

And by **DIME domain**:
- **D** — Diplomatic
- **I** — Informational
- **M** — Military
- **E** — Economic

Each card also carries a **risk score** (LOW / MEDIUM / HIGH / CRITICAL) and one or more primary actor labels. The current catalogue has 47 distinct labels. That count includes organizations (EU, NATO, IEA) and short aliases (`US`, `UK`) as well as country names.

## Adjudication model

Deterministic formula:

```
dime_vector = RISK_MAG[risk] × PHASE_MULT[phase]
             + keyword-weighted secondary domain boosts

net = attacker_base
    + phase_bonus
    + actor_posture_bonus
    - defender_value
    - defender_posture_bonus
    ± variance(hash(ids + turn))
```

**Outcome bands:**
- **BEST** (net ≥ 30) — Full effect applied to world state.
- **PARTIAL** (0 ≤ net < 30) — 40% effect, significant friction.
- **BACKFIRE** (net < 0) — Effect inverts against the attacker, 60% damage to actor.

The variance term is seeded by the card ids plus turn number, so replays are reproducible. Keyword boosts read the card title and the action summary stored in `engine-data.js`.

## World state and favourability

Actor baselines in the engine cover the same 47 labels, tracked across:
- DIME averages (baseline posture, 0–100 each)
- GDP (indexed, 100 = baseline)
- Stockpiles (rare earths, semiconductors, energy, grain)
- Morale (0–100)

**Favourability** = 0.50 × DIMEavg + 0.25 × GDP + 0.15 × StockpileAvg + 0.10 × Morale

The global commodity market tracks Rare Earths, Semiconductors, Energy, and Grain. Each played card applies a supply/demand nudge based on its keywords:

- **Restrictive** plays (sanction, embargo, blockade, strike) drive prices up and drain the **target's** stockpile of that commodity.
- **Expansive** plays (build, expand, partnership, deal) push prices down and raise the **actor's** stockpile.
- BACKFIRE flips the direction.

At end of turn the market settles: net exporters of a commodity gain GDP when its price rises, net importers feel the squeeze. Stockpiles drift slowly toward equilibrium and the Global Risk Index decays toward its 30 baseline.

## Game flow

1. Open **engine.html → Play Game tab**.
2. Pick 2–4 players and assign countries.
3. Click **◉ Open Globe View** to spawn the live 3D globe.
4. Take turns playing cards. Each turn:
   - Attacker plays a card from their hand.
   - If any opponent holds a canonical counter, a prompt lets them pick one to play or pass.
   - Engine rolls adjudication.
   - World state updates, market and stockpiles shift, globe shows attack arcs and DIME deltas.
5. After 5 turns each, highest favourability wins.

## Globe View

A separate browser window that mirrors game state in real time:
- Orthographic Earth with 23.44° axial tilt and live subsolar lighting.
- 1,260 GSHHS coastline polygons + 447 political borders.
- DIME compass roses around each actor country, sized by favourability.
- Attack arcs from attacker to target on each card play.
- Event feed and commodity ticker.

If the popup is blocked, allow popups for the page and click ◉ Open Globe View again.

`tactical.html` uses the same coastline and border vertices via `world-geo-data.js`.

## Creating new cards

1. Open **card-builder.html**.
2. Fill in title, actor, phase, domain, risk, and the action/effect/counter blocks.
3. Click **Download** to save the `.html` file.
4. Drop the file into the `cards/` folder. Name it `PHASE-DOMAIN-NN-slug.html`.
5. From the repository root, run `python3 pack/build.py` so the engine and Operations Center pick it up.

Counter links are the `<a class="counter-tag" href="...">` tags in the card's Counter-Cards section. The build records the target card id (the `PHASE-DOMAIN-NN` prefix of the href). Two labels that point at the same card produce two edges. A tag with no card href is not an edge.

## Rebuilding sidecars

After adding or editing cards, or after editing globe rendering:

```bash
python3 pack/build.py
```

Run that from the repository root. The script uses only the Python 3 standard library.

It rewrites:

- `engine-data.js` — one entry per file in `cards/`, plus the counter graph. Summaries are the Action section, whitespace collapsed, cut at 200 characters.
- `globe.html` — `pack/globe.template.html` with `pack/continents.json` and `pack/borders.json` inserted verbatim into the coastline and border script tags.
- `world-geo-data.js` — the same two JSON arrays as `CONTINENTS_DATA` and `BORDERS_DATA`.

The template and the two JSON files were extracted from the globe that shipped with this repo. Re-running the build reproduces that globe byte for byte until you edit the template or the JSON. Edit `pack/globe.template.html` (the placeholders are `__CONTINENTS_JSON__` and `__BORDERS_JSON__`) when changing globe rendering. Do not hand-edit `globe.html` or `world-geo-data.js`; the next build overwrites them.

If `pack/globe.template.html` is missing and `globe.html` no longer contains inline coastline JSON, the build still rewrites `engine-data.js` and leaves `globe.html` alone.

## Troubleshooting

- **Globe stays on "Waiting for game to start…"** — open it from the engine's ◉ Open Globe View button so the globe can see `window.opener`.
- **Engine or Operations Center shows "No card data loaded"** — `engine-data.js` is missing or failed to load. From the repository root run `python3 pack/build.py`, then reload.
- **Home page counts stay as "—"** — same cause: `engine-data.js` did not load.
- **Import adds a card but the summary looks wrong** — the card's Action section needs a `.section-label` and `.section-text` pair. Check an existing card for structure.
- **Adjudicate returns BACKFIRE every time** — the defender likely has a much stronger posture in that domain. Try a card in a different DIME lane.
- **Diagnostics marks files UNCHECKABLE** — the page was opened as `file://` and this browser blocks local probes. The files may still be present. `python3 -m http.server` from the repository root, then open `http://localhost:8000/diagnostics.html`.

## Credits

Wargame system designed for scenario planning across the Indo-Pacific, Middle East, Africa, Europe, and South Asia, 2030–2036. Card structure, adjudication formula, and world model are original.
