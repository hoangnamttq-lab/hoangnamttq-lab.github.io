import unittest
import sys
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agent_bounty_scout import shortlist

class ScoutTests(unittest.TestCase):
    def test_excludes_fee_kyc_stale_expired_human(self):
        data = {"items": [
            {"id":"good","kind":"bounty","est_usd":10,"url":"https://example.org/1","requires":[],"title":"Good"},
            {"id":"kyc","est_usd":20,"url":"https://example.org/2","requires":["kyc"]},
            {"id":"bond","est_usd":20,"url":"https://example.org/3","requires":["bond"]},
            {"id":"stale","est_usd":30,"url":"https://example.org/4","requires":[],"stale":True},
            {"id":"expired","est_usd":50,"url":"https://example.org/5","requires":[],"deadline":"2020-01-01T00:00:00Z"},
            {"id":"human","kind":"audit_contest","est_usd":50,"url":"https://example.org/6","requires":[]},
        ]}
        out = shortlist(data, now=datetime(2026,11,1,tzinfo=timezone.utc))
        self.assertEqual([r["id"] for r in out], ["good"])
    def test_dedupe_and_filter_unsafe_links(self):
        rows=[{"id":"x","est_usd":9,"url":"https://example.com/","requires":[]},
              {"id":"x","est_usd":999,"url":"https://other.com/","requires":[]},
              {"id":"bad","est_usd":100,"url":"file:///etc/passwd","requires":[]}]
        self.assertEqual([r["id"] for r in shortlist({"items":rows})], ["x"])
    def test_since_and_sort(self):
        rows=[{"id":"a","est_usd":12,"url":"https://a.org/","requires":[],"first_seen":"2026-11-01T01:00:00Z"},
              {"id":"b","est_usd":20,"url":"https://b.org/","requires":[],"first_seen":"2026-11-01T03:00:00Z"}]
        result=shortlist({"items":rows},since=datetime(2026,11,1,2,tzinfo=timezone.utc))
        self.assertEqual([r["id"] for r in result],["b"])
    def test_invalid_reward_values(self):
        rows=[{"id":"x","est_usd":float('nan'),"url":"https://a.org/","requires":[]},
              {"id":"y","est_usd":False,"url":"https://a.org/","requires":[]},
              {"id":"z","est_usd":8,"url":"https://a.org/","requires":[]}]
        self.assertEqual([r["id"] for r in shortlist({"items":rows})],["z"])
if __name__=="__main__": unittest.main()
