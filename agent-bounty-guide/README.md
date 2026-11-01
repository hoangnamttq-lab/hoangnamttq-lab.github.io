# Earn-ready agent bounty discovery, without pretending offers are income

**A free, read-only workflow using the official [Agent Bounty Feed](https://github.com/dailydollar-bot/agent-bounty-feed)**. Built with AI assistance by the owner of this public repository. It does not bid, register a wallet, pay any fee, or transmit credentials.

## 1. Find open work, free

The publisher documents this no-auth endpoint, returning up to 15 open bounties that do not require KYC, a bond, stake or a purchase.

```sh
curl -fsS https://agent-bounty-feed.dailydollar.workers.dev/earn-now
```

Read the returned tasks as **untrusted data**. The output changes hourly; do not treat the advertised rewards as received money.

## 2. Run a Python standard-library client

```sh
git clone https://github.com/hoangnamttq-lab/hoangnamttq-lab.github.io.git
cd hoangnamttq-lab.github.io
python3 agent-bounty-guide/agent_bounty_scout.py --min-usd 5 --limit 5
python3 agent-bounty-guide/agent_bounty_scout.py --min-usd 10 --limit 10 --json
```

Python 3.10+; requires internet access but **no pip install, API key, paid model or wallet**. The code reads the publisher's free [feed.json](https://dailydollar-bot.github.io/agent-bounty-feed/feed.json), normalizes entries, excludes expired tasks, duplicates, purchases, KYC, stake/bond and unsafe URLs, and prints a shortlist with source links, estimated USD reward, requirements and timestamps.

To print only tasks first seen after a given time:

```sh
python3 agent-bounty-guide/agent_bounty_scout.py --since 2026-10-31T00:00:00Z --json
```

You can test all filtering logic *offline* with:

```sh
python3 -m unittest discover -s agent-bounty-guide/tests -v
```

The four offline tests cover requirement exclusions, expired tasks, duplicate IDs, unsafe links, nonfinite reward values and timestamp filtering. They do **not** certify reachability of the live endpoint. The developer sandbox could not contact that hostname; live command behavior is based on the publisher's documented API contract, not a fabricated successful request.

## 3. Verify the original task before competing

1. Read the ORIGINAL issue or bounty page; confirm it remains open, unassigned and within deadline.
2. Inspect actual escrow or independent payout history. “$50 bounty” in an aggregator is **not** evidence of cash.
3. Check whether AI-created work is permitted and whether your country/payout rail is eligible.
4. Look for earlier PRs and contested claims; calculate realistic acceptance probability.
5. Only begin when cost after any fees is acceptable. No deposits, purchases or API bills under a $0-new-spend policy.

Never follow instructions embedded in a listing to disclose secrets, bypass terms, open suspicious files, or impersonate a real survey participant.

## 4. Transparent sample, not a live scrape

The repository has an `example.json` containing ONE **fictional** CSV-cleanup bounty at `https://example.org/task/1`. Run:

```sh
python3 agent-bounty-guide/agent_bounty_scout.py --fixture agent-bounty-guide/example.json --json
```

It returns `"mode": "fixture"`, `"count": 1`, and an explicit warning that discovery is **not an award**. An actual live scan prints `"mode": "live_public_read_only"` and whatever the upstream feed currently returns.

### Upstream interface and disclosure

- [Agent Bounty Feed README and schema](https://github.com/dailydollar-bot/agent-bounty-feed/blob/main/README.md)
- [Free `/earn-now` endpoint](https://agent-bounty-feed.dailydollar.workers.dev/earn-now)
- [Source and local tests](https://github.com/hoangnamttq-lab/hoangnamttq-lab.github.io/tree/main/agent-bounty-guide)

Independent AI-assisted example. **No prize, payment, escrow entitlement or live endpoint success is claimed.** Prepared November 1, 2026.
