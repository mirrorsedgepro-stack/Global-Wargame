#!/usr/bin/env python3
"""Regenerate the wargame sidecars from cards/ and the globe sources.

Run from the repository root (or from anywhere — paths are relative to this file):

    python3 pack/build.py

Writes:
  engine-data.js     card metadata + counter graph consumed by engine.html,
                     index.html, card-builder.html, and diagnostics.html
  globe.html         pack/globe.template.html with pack/continents.json and
                     pack/borders.json injected verbatim
  world-geo-data.js  the same coastlines and borders as a JS sidecar for
                     tactical.html

globe.html is left untouched when pack/globe.template.html is missing and
the current globe.html has no extractable coastline JSON. Card regeneration
still runs.

The adjudication formula lives in engine.html and is not touched here.

Actor shorthand on a card (US, UK, United Arab Emirates, European Union) is
rewritten to the canonical COUNTRY_BASES name, in the HTML and in
engine-data.js. Each card's prev/next list is rewritten to every card file,
in alphabetical order, so the original pages reach the later cards.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACK = Path(__file__).resolve().parent
CARDS_DIR = ROOT / "cards"
ENGINE_DATA = ROOT / "engine-data.js"
GLOBE_HTML = ROOT / "globe.html"
WORLD_GEO = ROOT / "world-geo-data.js"
TEMPLATE = PACK / "globe.template.html"
CONTINENTS_JSON = PACK / "continents.json"
BORDERS_JSON = PACK / "borders.json"

# Summaries in the existing catalogue are the Action prose, collapsed
# whitespace, cut at 200 characters (JS String.slice + trimEnd) plus "...".
# Keep 200 so keyword scoring, which reads card.summary, stays stable.
SUMMARY_LIMIT = 200

# Canonical actor names are the keys of COUNTRY_BASES in engine.html.
# Aliases are rewritten at build time so the engine never grows a second
# ledger for "US" beside "United States".
ACTOR_ALIASES = {
    "US": "United States",
    "UK": "United Kingdom",
    "United Arab Emirates": "UAE",
    "European Union": "EU",
}
CANONICAL_ACTORS = {
    "United States", "China", "Russia", "Japan", "India", "Australia",
    "United Kingdom", "South Korea", "Taiwan", "Philippines", "Singapore",
    "Malaysia", "Canada", "New Zealand", "DPRK", "France", "ASEAN Member",
    "IEA", "Israel", "Iran", "Saudi Arabia", "UAE", "Turkey", "Egypt",
    "Qatar", "Nigeria", "South Africa", "Ethiopia", "Kenya", "Morocco",
    "DRC", "Pakistan", "Bangladesh", "Sri Lanka", "Afghanistan",
    "Kazakhstan", "Uzbekistan", "Germany", "Poland", "Ukraine", "Italy",
    "Spain", "Netherlands", "Norway", "EU", "NATO", "Belgium",
}

CARD_NAME = re.compile(r"^([A-Z]+)-([A-Z])-(\d+)-.+\.html$")
CARD_ID = re.compile(r"^([A-Z]+-[A-Z]-\d+)")
PHASES = {"COM", "CON", "CRI"}
DOMAINS = {"D", "I", "M", "E"}
RISK_RE = re.compile(r"\b(LOW|MEDIUM|HIGH|EXTREME|CRITICAL|STRATEGIC)\b")

CONTINENTS_OPEN = '<script id="continents-data" type="application/json">'
BORDERS_OPEN = '<script id="borders-data" type="application/json">'
CONTINENTS_MARK = "__CONTINENTS_JSON__"
BORDERS_MARK = "__BORDERS_JSON__"
ACTOR_PILL = re.compile(r'(<span class="actor-pill"[^>]*>)(.*?)(</span>)', re.S)
NAV_LIST = re.compile(r"var CARDS = \[.*?\];", re.S)


def collapse(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", "", fragment)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def summarise(action: str) -> str:
    if len(action) > SUMMARY_LIMIT:
        return action[:SUMMARY_LIMIT].rstrip() + "..."
    return action


def canonical_actor(name: str) -> str:
    return ACTOR_ALIASES.get(name, name)


def counter_ids(raw: str) -> list[str]:
    """Card ids linked from the Counter-Cards block, in document order.

    A repeated target is dropped. isCounter only tests membership, and a
    second chip for the same card is the duplicate-edge bug.
    """
    block = re.search(r'<div class="counters">(.*?)</div>', raw, re.S)
    if not block:
        return []
    ids: list[str] = []
    seen: set[str] = set()
    for tag in re.findall(r"<a\b[^>]*>", block.group(1), re.S):
        if not re.search(r'class="[^"]*\bcounter-tag\b', tag):
            continue
        href = re.search(r'href="([^"]*)"', tag)
        if not href:
            continue
        base = href.group(1).split("?", 1)[0].split("#", 1)[0].rstrip("/").split("/")[-1]
        match = CARD_ID.match(base)
        if not match or match.group(1) in seen:
            continue
        seen.add(match.group(1))
        ids.append(match.group(1))
    return ids


def rewrite_actor_pills(raw: str) -> tuple[str, list[tuple[str, str]]]:
    """Replace shorthand actor pills with canonical names. Idempotent."""
    changed: list[tuple[str, str]] = []

    def repl(match: re.Match) -> str:
        text = collapse(match.group(2))
        canon = canonical_actor(text)
        if canon == text:
            return match.group(0)
        changed.append((text, canon))
        return match.group(1) + html.escape(canon) + match.group(3)

    return ACTOR_PILL.sub(repl, raw), changed


def rewrite_navigation(names: list[str]) -> list[str]:
    """Point every card's prev/next list at the full alphabetical deck."""
    literal = "var CARDS = " + json.dumps(names, ensure_ascii=True) + ";"
    warnings: list[str] = []
    for name in names:
        path = CARDS_DIR / name
        raw = path.read_text(encoding="utf-8")
        if not NAV_LIST.search(raw):
            warnings.append(f"{name}: no prev/next CARDS list to update")
            continue
        updated = NAV_LIST.sub(lambda _match: literal, raw, count=1)
        if updated != raw:
            path.write_text(updated, encoding="utf-8")
    return warnings


def parse_card(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    name = path.name
    match = CARD_NAME.match(name)
    if not match:
        raise ValueError(f"unexpected card filename: {name}")
    phase, domain, number = match.group(1), match.group(2), match.group(3)
    card_id = f"{phase}-{domain}-{number}"

    title_m = re.search(r'class="card-title"[^>]*>(.*?)</div>', raw, re.S)
    title = collapse(title_m.group(1)) if title_m else card_id

    actors = [
        canonical_actor(collapse(piece))
        for piece in re.findall(r'class="actor-pill"[^>]*>(.*?)</span>', raw, re.S)
    ]
    actors = [actor for actor in actors if actor]

    risk = ""
    risk_m = re.search(
        r'class="(?:risk-value|risk-level|card-risk)"[^>]*>(.*?)</div>',
        raw,
        re.S,
    )
    if risk_m:
        found = RISK_RE.search(collapse(risk_m.group(1)).upper())
        if found:
            risk = found.group(1)

    labels = [
        collapse(piece)
        for piece in re.findall(r'class="section-label"[^>]*>(.*?)</div>', raw, re.S)
    ]
    texts = [
        collapse(piece)
        for piece in re.findall(r'class="section-text"[^>]*>(.*?)</div>', raw, re.S)
    ]
    action = ""
    for label, text in zip(labels, texts):
        if label.lower() == "action":
            action = text
            break
    if not action and texts:
        action = texts[0]

    return {
        "id": card_id,
        "phase": phase,
        "domain": domain,
        "file": f"cards/{name}",
        "title": title,
        "actors": actors,
        "risk": risk,
        "summary": summarise(action),
        "_counters": counter_ids(raw),
        "_action_label_ok": any(label.lower() == "action" for label in labels),
    }


def load_cards() -> tuple[list[dict], dict[str, list[str]], list[str]]:
    warnings: list[str] = []
    parsed: list[dict] = []
    seen: dict[str, str] = {}
    for path in sorted(CARDS_DIR.glob("*.html")):
        if not CARD_NAME.match(path.name):
            warnings.append(f"skipped {path.name}: name is not PHASE-DOMAIN-NN-slug.html")
            continue
        card = parse_card(path)
        if card["id"] in seen:
            warnings.append(
                f"duplicate id {card['id']}: {seen[card['id']]} and {path.name}"
            )
            continue
        seen[card["id"]] = path.name
        if card["phase"] not in PHASES or card["domain"] not in DOMAINS:
            warnings.append(f"{card['id']}: unusual phase/domain {card['phase']}-{card['domain']}")
        if not card["title"]:
            warnings.append(f"{card['id']}: missing title")
        if not card["actors"]:
            warnings.append(f"{card['id']}: no actors")
        for actor in card["actors"]:
            if actor not in CANONICAL_ACTORS:
                warnings.append(f"{card['id']}: actor {actor!r} is not a canonical country")
        if not card["risk"]:
            warnings.append(f"{card['id']}: no risk")
        if not card["summary"]:
            warnings.append(f"{card['id']}: no action summary")
        if not card["_action_label_ok"]:
            warnings.append(f"{card['id']}: no Action section; summary fell back to first prose")
        parsed.append(card)

    parsed.sort(key=lambda card: card["id"])
    ids = {card["id"] for card in parsed}
    counters: dict[str, list[str]] = {}
    for card in parsed:
        edges = card.pop("_counters")
        card.pop("_action_label_ok")
        counters[card["id"]] = edges
        for target in edges:
            if target not in ids:
                warnings.append(f"broken counter: {card['id']} -> {target} (no such card)")
    return parsed, counters, warnings


def write_engine_data(cards: list[dict], counters: dict[str, list[str]]) -> None:
    payload = {"cards": cards, "counters": counters}
    body = json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
    text = (
        "// Auto-generated by pack/build.py — do not edit by hand.\n"
        "// Card metadata + counter graph for engine.html, index.html,\n"
        "// card-builder.html, and diagnostics.html. Re-run after card edits:\n"
        "//   python3 pack/build.py\n"
        f"window.__ENGINE_DATA = {body};\n"
    )
    ENGINE_DATA.write_text(text, encoding="utf-8")


def _json_between(page: str, opener: str) -> str:
    start = page.find(opener)
    if start < 0:
        raise ValueError(f"globe.html has no {opener!r}")
    start += len(opener)
    end = page.find("</script>", start)
    if end < 0:
        raise ValueError("globe.html script tag is not closed")
    blob = page[start:end]
    if blob.startswith("__") or not blob.lstrip().startswith("["):
        raise ValueError("globe.html has no inline coastline JSON to extract")
    json.loads(blob)
    return blob


def ensure_globe_sources() -> bool:
    """Make sure the template and geo JSON exist.

    Returns True when globe.html can be regenerated. If the template is
    missing and the current globe has no inline JSON, returns False and
    leaves globe.html alone.
    """
    if TEMPLATE.exists() and CONTINENTS_JSON.exists() and BORDERS_JSON.exists():
        return True
    if not GLOBE_HTML.exists():
        print("globe.html is missing and pack/ has no template; leaving the globe alone")
        return False
    page = GLOBE_HTML.read_text(encoding="utf-8")
    try:
        continents = _json_between(page, CONTINENTS_OPEN)
        borders = _json_between(page, BORDERS_OPEN)
    except ValueError as exc:
        print(f"not regenerating globe.html: {exc}")
        return False
    if CONTINENTS_MARK not in page and BORDERS_MARK not in page:
        template = page.replace(continents, CONTINENTS_MARK, 1).replace(borders, BORDERS_MARK, 1)
    else:
        template = page
    PACK.mkdir(parents=True, exist_ok=True)
    CONTINENTS_JSON.write_text(continents, encoding="utf-8")
    BORDERS_JSON.write_text(borders, encoding="utf-8")
    TEMPLATE.write_text(template, encoding="utf-8")
    print("extracted pack/globe.template.html, continents.json, borders.json from globe.html")
    return True


def _read_geo(path: Path) -> str:
    blob = path.read_text(encoding="utf-8")
    if blob.endswith("\n"):
        blob = blob[:-1]
    json.loads(blob)
    return blob


def write_globe() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    if CONTINENTS_MARK not in template or BORDERS_MARK not in template:
        raise SystemExit(
            "pack/globe.template.html is missing __CONTINENTS_JSON__ or __BORDERS_JSON__"
        )
    continents = _read_geo(CONTINENTS_JSON)
    borders = _read_geo(BORDERS_JSON)
    page = template.replace(CONTINENTS_MARK, continents, 1).replace(BORDERS_MARK, borders, 1)
    if CONTINENTS_MARK in page or BORDERS_MARK in page:
        raise SystemExit("globe placeholders survived injection")
    GLOBE_HTML.write_text(page, encoding="utf-8")
    # tactical.html reads the same polygons as JS constants.
    WORLD_GEO.write_text(
        f"const CONTINENTS_DATA = {continents};\nconst BORDERS_DATA = {borders};\n",
        encoding="utf-8",
    )


def main() -> int:
    if not CARDS_DIR.is_dir():
        print(f"no card directory at {CARDS_DIR}", file=sys.stderr)
        return 1
    names = sorted(
        path.name for path in CARDS_DIR.glob("*.html") if CARD_NAME.match(path.name)
    )
    for name in names:
        path = CARDS_DIR / name
        raw = path.read_text(encoding="utf-8")
        updated, changed = rewrite_actor_pills(raw)
        if changed:
            path.write_text(updated, encoding="utf-8")
            print(f"normalised actors in {name}: " + ", ".join(f"{old} -> {new}" for old, new in changed))
    nav_warnings = rewrite_navigation(names)
    cards, counters, warnings = load_cards()
    warnings = nav_warnings + warnings
    write_engine_data(cards, counters)
    edges = sum(len(targets) for targets in counters.values())
    print(f"engine-data.js: {len(cards)} cards, {edges} counter edges")
    globe_ok = ensure_globe_sources()
    if globe_ok:
        write_globe()
        print("globe.html and world-geo-data.js regenerated from pack/")
    else:
        print("globe.html left unchanged")
    broken = [note for note in warnings if note.startswith("broken counter")]
    for note in warnings:
        print(f"warning: {note}")
    if not cards:
        print("no cards parsed", file=sys.stderr)
        return 1
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
