🟡 Portfolio demo, runnable locally, not deployed

# ai-enrichment-demo

Fills in missing product attributes with an LLM call, generalized to any OpenAI-compatible endpoint, in real batches via the OpenAI Batch API, not one interactive call per record. One piece of a small multi-service platform demo, see [Related repos](#related-repos) for the rest.

This is a sanitized, generic rebuild for portfolio purposes. No real vendor, client, or company data is used anywhere in this repo. More context: [paulocremas-showcase](https://github.com/paulocremas-showcase). Full portfolio: [paulocremas.github.io](https://paulocremas.github.io). Built to the standard defined in my [Constitution](https://github.com/paulocremas/paulocremas-method).

## Table of contents
- [What this is](#what-this-is)
- [Flow](#flow)
- [Running it](#running-it)
- [Design notes](#design-notes)
- [Rules](#rules)
- [Related repos](#related-repos)

## What this is

Records land via [data-extraction-demo](https://github.com/paulocremas-showcase/data-extraction-demo) or [data-etl-demo](https://github.com/paulocremas-showcase/data-etl-demo) with gaps in them, category, material, color, whatever the source didn't provide. This fills those gaps with an LLM call, structured as JSON so it's directly usable downstream, not free text that needs its own parser. Two paths: `enrich_product()` for one record at a time, and `submit_batch()` / `fetch_batch()` for many records in one OpenAI Batch API job, mirroring how the production system this demo is based on actually runs.

## Flow

```mermaid
flowchart LR
    A[Records with missing fields] --> B[submit_batch]
    B -->|Batch API job, up to 24h window| C[fetch_batch]
    C -->|structured JSON per record| D[Enriched records]
```

1. [enrichment/enrich.py](enrichment/enrich.py)'s `enrich_product()` handles a single record synchronously; `submit_batch()` and `fetch_batch()` handle many records as one Batch API job, submit and poll are separate calls so nothing blocks waiting for the job.
2. `--dry-run` (the default, no `--live`) needs no API key: it returns deterministic placeholders so the code path and its shape are reviewable without credentials.
3. `--live` calls a real OpenAI-compatible endpoint via `OPENAI_API_KEY`.

## Running it

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# single record
python -m enrichment.enrich --product "Wireless Charging Pad"

# batch: one line per product name in the file
python -m enrichment.enrich --batch-submit products.txt --live
python -m enrichment.enrich --batch-fetch <batch_id> --live
```

Smoke tests: `python tests/test_enrich.py`

## Design notes

- **Structured output, not free text.** `response_format={"type": "json_object"}` means the model's output is directly usable by the next pipeline stage, no regex or "hope it followed the format" parsing.
- **Batch submission never blocks on the result.** `submit_batch()` returns a batch id immediately; OpenAI's completion window runs up to 24h, so polling is a separate `fetch_batch()` call, not a sleep loop held open for hours.
- **Model choice lives in an env var** (`ENRICHMENT_MODEL`, defaults to a small fast model), not hardcoded, because the cheapest model that gets the job done changes faster than the code around it should.
- **Generalized to "any OpenAI-compatible endpoint,"** not tied to one vendor's SDK quirks, because the actual production version of this needed to be portable across providers without a rewrite.

## AI-BOM

- **Model**: whatever `ENRICHMENT_MODEL` is set to, default `gpt-4o-mini`.
- **Fine-tuned?** No. This is inference against a frozen pre-trained model with an engineered prompt, no weights are updated and nothing persists between calls.
- **What it touches**: only the OpenAI-compatible chat completions and Batch API endpoints (`--live`); no other API, database, or service.

## Rules

- `--dry-run` must never require an API key or network access.
- The real API call path, both single-record and batch, stays real, working code, not a stub, even though the demo defaults to dry-run.
- `fetch_batch()` must return `None` while a job is in progress, never raise or block waiting for it.
- No real vendor, client, or company names or data anywhere in this repo.

## Related repos

- [data-extraction-demo](https://github.com/paulocremas-showcase/data-extraction-demo)
- [data-etl-demo](https://github.com/paulocremas-showcase/data-etl-demo)
- [inventory-sync-demo](https://github.com/paulocremas-showcase/inventory-sync-demo)
- [ops-dashboard-demo](https://github.com/paulocremas-showcase/ops-dashboard-demo) — monitors this alongside the rest
