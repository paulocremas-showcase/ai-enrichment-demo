"""Smoke tests, not a full suite. Run directly: python tests/test_enrich.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from enrichment.enrich import enrich_product


def test_dry_run_needs_no_client_and_returns_all_fields():
    result = enrich_product("Wireless Charging Pad", client=None)
    assert set(result.keys()) == {"category", "primary_material", "color", "tone"}


if __name__ == "__main__":
    test_dry_run_needs_no_client_and_returns_all_fields()
    print("all tests passed")
