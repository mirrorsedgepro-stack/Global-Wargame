# Global Wargame — Indo-Pacific 2030-2036

A tabletop wargame engine built as a small set of standalone HTML pages. Includes 72 action cards, a card builder, an adjudication engine, statistics, hot-seat multiplayer, and a live 3D globe.

## What's in this folder

- **home.html** — Landing page. Start here.
- **index.html** — Operations Center: catalogue all 72 cards with filters and search.
- **engine.html** — Adjudicator, statistics, hot-seat play. Loads card data from `engine-data.js`.
- **engine-data.js** — Auto-generated sidecar with card metadata + counter graph (do not edit by hand).
- **globe.html** — Live 3D globe popup. Sun-lit Earth with real GSHHS coastlines and political borders. Receives state from the engine via postMessage.
- **card-builder.html** — Authoring tool for new cards.
- **theme.css** — Shared design tokens used by `home.html`.
- **cards/** — Action card `.html` files, one per card, named `PHASE-DOMAIN-NN-slug.html`.

## Quick start

Open **home.html** in any modern browser. From there:

1. **Operations Center** — browse all 72 cards.
2. **Engine** → Play Game tab → add 2–4 players → Start Game → click ◉ Open Globe View.
3. **Card Builder** — author new cards, download as `.html`, drop into the `cards/` folder.

No install, no server, no network. Everything runs locally.

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

Each card also carries a **risk score** (LOW / MEDIUM / HIGH / CRITICAL) and one or more primary actor countries.

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

The variance term is seeded by the card ids plus turn number, so replays are reproducible.

## World state and favourability

47 actor countries are tracked across:
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

## Creating new cards

1. Open **card-builder.html**.
2. Fill in title, actor, phase, domain, risk, and the action/effect/counter blocks.
3. Click **Download** to save the `.html` file.
4. Drop the file into the `cards/` folder.
5. Re-run `python3 pack/build.py` so the engine picks it up.

## Rebuilding sidecars

After adding/editing cards or globe rendering code:

```bash
cd /sessions/exciting-bold-clarke
python3 pack/build.py
```

This regenerates two derived files:
- `engine-data.js` — fresh card + counter payload for the engine.
- `globe.html` — `pack/globe.template.html` with `pack/continents.json` and `pack/borders.json` injected.

## Troubleshooting

- **Globe stays on "Waiting for game to start…"** — make sure you opened it via the engine's ◉ Open Globe View button (not as a sibling window). The globe announces ready to its `window.opener`.
- **Engine shows "No card data loaded"** — `engine-data.js` is missing or out of date. Run `python3 pack/build.py`.
- **Import adds a card but the summary looks wrong** — the card's "Action" section needs a `.section-label` and `.section-text` pair. Check an existing card for structure.
- **Adjudicate returns BACKFIRE every time** — the defender likely has a much stronger posture in that domain. Try a card in a different DIME lane.

## Credits

Wargame system designed for Indo-Pacific scenario planning, 2030–2036 timeframe. Card structure, adjudication formula, and world model are original. Built as a Claude Cowork artifact.
