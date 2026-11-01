#!/usr/bin/env python3
"""Read-only discovery of public agent bounties. No bids, payments or LLM calls."""
from __future__ import annotations
import argparse
import json
import math
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FEED_URL = "https://dailydollar-bot.github.io/agent-bounty-feed/feed.json"
BLOCKED = {"kyc", "bond", "stake", "purchase", "human_only", "x_account"}
MAX_BYTES = 2_000_000

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        source = urllib.parse.urlsplit(FEED_URL)
        dest = urllib.parse.urlsplit(newurl)
        if (dest.scheme, dest.netloc, dest.path) != (source.scheme, source.netloc, source.path) or dest.query or dest.fragment:
            raise ValueError("Unexpected feed redirect; refusing to follow")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def fetch_feed() -> dict[str, Any]:
    opener = urllib.request.build_opener(SafeRedirect)
    req = urllib.request.Request(FEED_URL, headers={"Accept": "application/json", "User-Agent": "PublicBountyScout/1.0"})
    with opener.open(req, timeout=12) as response:
        if response.status != 200:
            raise ValueError(f"Feed HTTP {response.status}")
        body = response.read(MAX_BYTES + 1)
        if len(body) > MAX_BYTES:
            raise ValueError("Feed exceeds 2 MB safety limit")
        result = json.loads(body)
        if not isinstance(result, dict) or not isinstance(result.get("items"), list):
            raise ValueError("Unexpected feed schema")
        return result

def time_parse(s: Any) -> datetime | None:
    if not isinstance(s, str) or len(s) > 60:
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)
    except ValueError:
        return None

def shortlist(feed: dict[str, Any], *, min_usd: float = 1, since: datetime | None = None,
              limit: int = 10, now: datetime | None = None) -> list[dict[str, Any]]:
    now = now or datetime.now(timezone.utc)
    items = feed.get("items")
    if not isinstance(items, list):
        raise ValueError("Missing items list")
    candidates = []
    seen_ids = set()
    for raw in items[:1000]:
        if not isinstance(raw, dict):
            continue
        bounty_id = raw.get("id")
        if not isinstance(bounty_id, str) or not bounty_id or bounty_id in seen_ids:
            continue
        seen_ids.add(bounty_id)
        if raw.get("kind", "bounty") != "bounty" or raw.get("stale") is True:
            continue
        required = raw.get("requires", [])
        if not isinstance(required, list) or any(not isinstance(x, str) for x in required):
            continue
        if set(required) & BLOCKED:
            continue
        prize = raw.get("est_usd")
        if isinstance(prize, bool) or not isinstance(prize, (int, float)) or not math.isfinite(prize) or prize < min_usd:
            continue
        dl = time_parse(raw.get("deadline"))
        if dl is not None and dl <= now:
            continue
        first = time_parse(raw.get("first_seen"))
        if since is not None and (first is None or first <= since):
            continue
        href = raw.get("url")
        if not isinstance(href, str) or len(href) > 2048:
            continue
        try:
            u = urllib.parse.urlsplit(href)
        except ValueError:
            continue
        if u.scheme != "https" or not u.hostname or u.username or u.password:
            continue
        title = raw.get("title") if isinstance(raw.get("title"), str) else "Untitled"
        candidates.append({
            "id": bounty_id,
            "title": " ".join(title.split())[:180],
            "source": str(raw.get("source") or "unknown")[:50],
            "est_usd": round(float(prize), 2),
            "currency": str(raw.get("currency") or "unknown")[:12],
            "url": href,
            "requires": required,
            "first_seen": raw.get("first_seen"),
            "deadline": raw.get("deadline"),
            "verified_at": raw.get("verified", {}).get("checked_at") if isinstance(raw.get("verified"), dict) else None,
        })
    candidates.sort(key=lambda x: (-x["est_usd"], x["id"]))
    return candidates[:limit]

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="List free, low-friction agent bounties (read-only)")
    ap.add_argument("--min-usd", type=float, default=5.0)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--since", help="Only records first seen after this ISO-8601 UTC time")
    ap.add_argument("--fixture", type=Path, help="Offline test JSON instead of the live feed")
    ap.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = ap.parse_args(argv)
    if not math.isfinite(args.min_usd) or args.min_usd < 0 or not 1 <= args.limit <= 25:
        ap.error("min-usd must be nonnegative and limit must be 1..25")
    since = time_parse(args.since) if args.since else None
    if args.since and since is None:
        ap.error("invalid --since UTC timestamp")
    try:
        if args.fixture:
            if args.fixture.stat().st_size > MAX_BYTES:
                raise ValueError("Fixture too large")
            feed = json.loads(args.fixture.read_text(encoding="utf-8"))
        else:
            feed = fetch_feed()
        rows = shortlist(feed, min_usd=args.min_usd, since=since, limit=args.limit)
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"Feed unavailable / invalid: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    out = {"mode": "fixture" if args.fixture else "live_public_read_only", "feed_generated_at": feed.get("generated_at"), "count": len(rows), "note": "Listing is not an award. Verify source task, funding and payout independently before applying.", "items": rows}
    if args.json:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(f"Agent Bounty Feed | {out['mode']} | refreshed {out['feed_generated_at']} | {len(rows)} shortlisted")
        for i, row in enumerate(rows, 1):
            print(f"{i:>2}. " + "$" + f"{row['est_usd']:>7.2f} {row['currency']:<5} {row['title']}\n    {row['url']}\n    requires: {', '.join(row['requires']) or 'none'}")
        print("Check the ORIGINAL task and payout evidence; listed value is not earned income.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
