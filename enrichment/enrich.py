"""AI-directed product enrichment: fills in missing attributes using an LLM.

Mirrors a real production pattern (batch enrichment via an LLM API against
BigQuery-sourced product records), generalized to any OpenAI-compatible
endpoint. `--dry-run` needs no API key, so the pattern is reviewable without
credentials.
"""
from __future__ import annotations

import argparse
import json
import os

ENRICHMENT_PROMPT = """You are enriching an e-commerce product record. Given the
product name below, return a JSON object with these fields: category,
primary_material, color, tone (one short marketing-friendly phrase).

Product name: {name}

Respond with JSON only."""


def enrich_product(name: str, client=None) -> dict:
    if client is None:
        return {
            "category": "unknown",
            "primary_material": "unknown",
            "color": "unknown",
            "tone": "dry-run placeholder, pass --live with OPENAI_API_KEY set for real enrichment",
        }

    response = client.chat.completions.create(
        model=os.environ.get("ENRICHMENT_MODEL", "gpt-4o-mini"),
        messages=[{"role": "user", "content": ENRICHMENT_PROMPT.format(name=name)}],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="call a real LLM API (needs OPENAI_API_KEY)")
    parser.add_argument("--product", default="Wireless Charging Pad")
    args = parser.parse_args()

    client = None
    if args.live:
        from openai import OpenAI

        client = OpenAI()

    result = enrich_product(args.product, client=client)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
