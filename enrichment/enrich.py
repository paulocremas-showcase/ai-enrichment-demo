"""AI-directed product enrichment: fills in missing attributes using an LLM.

Mirrors a real production pattern (batch enrichment via an LLM API against
BigQuery-sourced product records), generalized to any OpenAI-compatible
endpoint. `--dry-run` needs no API key, so the pattern is reviewable without
credentials.
"""
from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path

ENRICHMENT_PROMPT = """You are enriching an e-commerce product record. Given the
product name below, return a JSON object with these fields: category,
primary_material, color, tone (one short marketing-friendly phrase).

Product name: {name}

Respond with JSON only."""


def _model() -> str:
    return os.environ.get("ENRICHMENT_MODEL", "gpt-4o-mini")


def enrich_product(name: str, client=None) -> dict:
    if client is None:
        return {
            "category": "unknown",
            "primary_material": "unknown",
            "color": "unknown",
            "tone": "dry-run placeholder, pass --live with OPENAI_API_KEY set for real enrichment",
        }

    response = client.chat.completions.create(
        model=_model(),
        messages=[{"role": "user", "content": ENRICHMENT_PROMPT.format(name=name)}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def _batch_request_line(index: int, name: str) -> str:
    return json.dumps(
        {
            "custom_id": str(index),
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": _model(),
                "messages": [{"role": "user", "content": ENRICHMENT_PROMPT.format(name=name)}],
                "response_format": {"type": "json_object"},
            },
        }
    )


def submit_batch(names: list[str], client) -> str:
    """Submit one Batch API job enriching many products at once, the same
    pattern the production system this demo mirrors runs against BigQuery.
    Returns immediately with a batch id -- OpenAI's completion window runs
    up to 24h, so this never blocks waiting for it. Poll with fetch_batch()."""
    batch_input = io.BytesIO(
        "\n".join(_batch_request_line(i, name) for i, name in enumerate(names)).encode()
    )
    batch_input.name = "batch_input.jsonl"
    uploaded = client.files.create(file=batch_input, purpose="batch")
    batch = client.batches.create(
        input_file_id=uploaded.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
    )
    return batch.id


def fetch_batch(batch_id: str, client) -> list[dict] | None:
    """Poll a submitted batch once. Returns None while still in progress,
    the enriched records in submission order once completed."""
    batch = client.batches.retrieve(batch_id)
    if batch.status in ("failed", "expired", "cancelled"):
        raise RuntimeError(f"batch {batch_id} ended in status={batch.status!r}")
    if batch.status != "completed":
        return None

    output = client.files.content(batch.output_file_id).text
    by_id = {}
    for line in output.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        content = row["response"]["body"]["choices"][0]["message"]["content"]
        by_id[row["custom_id"]] = json.loads(content)

    return [by_id[str(i)] for i in range(len(by_id))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="call a real LLM API (needs OPENAI_API_KEY)")
    parser.add_argument("--product", default="Wireless Charging Pad")
    parser.add_argument(
        "--batch-submit", metavar="FILE", help="submit a Batch API job for product names, one per line"
    )
    parser.add_argument(
        "--batch-fetch", metavar="BATCH_ID", help="poll a submitted batch and print results once ready"
    )
    args = parser.parse_args()

    client = None
    if args.live:
        from openai import OpenAI

        client = OpenAI()

    if args.batch_fetch:
        if client is None:
            raise SystemExit("--batch-fetch requires --live")
        results = fetch_batch(args.batch_fetch, client)
        print("batch still in progress" if results is None else json.dumps(results, indent=2))
        return

    if args.batch_submit:
        names = [line for line in Path(args.batch_submit).read_text().splitlines() if line.strip()]
        if client is None:
            print(json.dumps([enrich_product(name) for name in names], indent=2))
        else:
            batch_id = submit_batch(names, client)
            print(f"submitted batch {batch_id}, check later with --batch-fetch {batch_id}")
        return

    result = enrich_product(args.product, client=client)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
