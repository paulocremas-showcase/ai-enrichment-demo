🟡 Portfolio demo, runnable locally, not deployed

# ai-enrichment-demo

Fills in missing product attributes with an LLM call, generalized to any OpenAI-compatible endpoint. One piece of a small multi-service platform demo, see [Related repos](#related-repos) for the rest.

This is a sanitized, generic rebuild for portfolio purposes. No real vendor, client, or company data is used anywhere in this repo. More context: [paulocremas-showcase](https://github.com/paulocremas-showcase). Full portfolio: [paulocremas.github.io](https://paulocremas.github.io). Built to the standard defined in my [Constitution](https://github.com/paulocremas/paulocremas-method).

## Table of contents
- [What this is](#what-this-is)
- [Flow](#flow)
- [Running it](#running-it)
- [Design notes](#design-notes)
- [Rules](#rules)
- [Related repos](#related-repos)

## What this is

Records land via [data-extraction-demo](https://github.com/paulocremas-showcase/data-extraction-demo) or [data-etl-demo](https://github.com/paulocremas-showcase/data-etl-demo) with gaps in them, category, material, color, whatever the source didn't provide. This fills those gaps with a single LLM call per record, structured as JSON so it's directly usable downstream, not free text that needs its own parser.

## Flow

```mermaid
flowchart LR
    A[Record with missing fields] --> B[enrichment/enrich.py]
    B -->|structured JSON response| C[Enriched record]
```

1. [enrichment/enrich.py](enrichment/enrich.py)'s `enrich_product()` takes a product name, returns a JSON object with the missing fields filled in.
2. `--dry-run` needs no API key: it returns a deterministic placeholder so the code path and its shape are reviewable without credentials.
3. `--live` calls a real OpenAI-compatible endpoint via `OPENAI_API_KEY`.

## Running it

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m enrichment.enrich --product "Wireless Charging Pad"
```

Smoke tests: `python tests/test_enrich.py`

## Design notes

- **Structured output, not free text.** `response_format={"type": "json_object"}` means the model's output is directly usable by the next pipeline stage, no regex or "hope it followed the format" parsing.
- **Model choice lives in an env var** (`ENRICHMENT_MODEL`, defaults to a small fast model), not hardcoded, because the cheapest model that gets the job done changes faster than the code around it should.
- **Generalized to "any OpenAI-compatible endpoint,"** not tied to one vendor's SDK quirks, because the actual production version of this needed to be portable across providers without a rewrite.

## Rules

- `--dry-run` must never require an API key or network access.
- The real API call path stays real, working code, not a stub, even though the demo defaults to dry-run.
- No real vendor, client, or company names or data anywhere in this repo.

## Related repos

- [data-extraction-demo](https://github.com/paulocremas-showcase/data-extraction-demo)
- [data-etl-demo](https://github.com/paulocremas-showcase/data-etl-demo)
- [inventory-sync-demo](https://github.com/paulocremas-showcase/inventory-sync-demo)
- [ops-dashboard-demo](https://github.com/paulocremas-showcase/ops-dashboard-demo) — monitors this alongside the rest
