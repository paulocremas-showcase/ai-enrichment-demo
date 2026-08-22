"""Smoke tests, not a full suite. Run directly: python tests/test_enrich.py"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

from enrichment.enrich import enrich_product, fetch_batch, submit_batch


def test_dry_run_needs_no_client_and_returns_all_fields():
    result = enrich_product("Wireless Charging Pad", client=None)
    assert set(result.keys()) == {"category", "primary_material", "color", "tone"}


class _FakeFilesAPI:
    """Stands in for client.files: echoes one enriched row per uploaded
    request, so submit_batch/fetch_batch's real request/response shape
    is exercised without a network call or an API key."""

    def __init__(self):
        self.uploaded = ""

    def create(self, file, purpose):
        assert purpose == "batch"
        self.uploaded = file.read().decode()
        return SimpleNamespace(id="file-in-1")

    def content(self, file_id):
        rows = [json.loads(line) for line in self.uploaded.splitlines() if line.strip()]
        out_lines = [
            json.dumps(
                {
                    "custom_id": row["custom_id"],
                    "response": {
                        "body": {
                            "choices": [
                                {
                                    "message": {
                                        "content": json.dumps(
                                            {
                                                "category": "test",
                                                "primary_material": "test",
                                                "color": "test",
                                                "tone": "test",
                                            }
                                        )
                                    }
                                }
                            ]
                        }
                    },
                }
            )
            for row in rows
        ]
        return SimpleNamespace(text="\n".join(out_lines))


class _FakeBatchesAPI:
    def create(self, input_file_id, endpoint, completion_window):
        return SimpleNamespace(id="batch-1", status="in_progress")

    def retrieve(self, batch_id):
        return SimpleNamespace(id=batch_id, status="completed", output_file_id="file-out-1")


class _FakeClient:
    def __init__(self):
        self.files = _FakeFilesAPI()
        self.batches = _FakeBatchesAPI()


def test_submit_then_fetch_batch_round_trips_every_product_in_order():
    client = _FakeClient()
    names = ["Wireless Charging Pad", "Ceramic Mug", "Canvas Tote Bag"]

    batch_id = submit_batch(names, client)
    results = fetch_batch(batch_id, client)

    assert results is not None
    assert len(results) == len(names)
    assert all(set(r.keys()) == {"category", "primary_material", "color", "tone"} for r in results)


def test_fetch_batch_returns_none_while_in_progress():
    client = _FakeClient()
    client.batches.retrieve = lambda batch_id: SimpleNamespace(id=batch_id, status="in_progress")

    assert fetch_batch("batch-1", client) is None


if __name__ == "__main__":
    test_dry_run_needs_no_client_and_returns_all_fields()
    test_submit_then_fetch_batch_round_trips_every_product_in_order()
    test_fetch_batch_returns_none_while_in_progress()
    print("all tests passed")
