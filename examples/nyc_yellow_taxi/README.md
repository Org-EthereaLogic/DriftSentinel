# NYC TLC Yellow Taxi — End-to-End DriftSentinel Demo

This example exercises every DriftSentinel control (intake → drift →
benchmark) against real public data. The included configs are the
production-quality versions from the 2026-05-04 demo replay: an 8-column
composite `business_key` that makes deduplication stable across NYC TLC
parquet shards, `tpep_pickup_datetime` as `batch_identifier`, and gate
thresholds proven against Jan + Feb 2024 data on Databricks Free Edition.

## Files

| File | Purpose |
| --- | --- |
| `dataset_contract.yml` | Schema + `(business_key, batch_identifier)` for `nyc_yellow_taxi` |
| `drift_policy.yml` | Wasserstein + Shannon entropy monitors with `health_score_threshold=0.70` |
| `benchmark_policy.yml` | Quality + drift fault injections with the recall/FPR/sensitivity gate set |

## Replay (one shot)

From the repo root, with Databricks CLI authenticated and OpenTofu installed
(see `docs/deployment_guide.md`):

```bash
make demo-nyc-taxi CATALOG=<your_catalog> PROFILE=<your_profile>
```

That target wraps `scripts/run_nyc_taxi_demo.sh`, which:

1. Downloads NYC TLC Yellow Taxi parquet for January and February 2024.
2. Deduplicates each month with the 8-column composite key.
3. Uploads them to `/Volumes/<catalog>/default/driftsentinel_runtime/{baseline,landing}/yellow_taxi/`.
4. Registers the dataset via `driftsentinel registry add`.
5. Runs `driftsentinel databricks connect --wait` against the resolved configs.
6. Prints the final intake/drift/benchmark verdicts.

## Replay (manual, 9 commands)

```bash
# 1. Download Jan + Feb 2024 from the public CloudFront mirror.
mkdir -p /tmp/nyc_taxi/{baseline,landing}
curl -fL https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet \
  -o /tmp/nyc_taxi/baseline/yellow_tripdata_2024-01.parquet
curl -fL https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-02.parquet \
  -o /tmp/nyc_taxi/landing/yellow_tripdata_2024-02.parquet

# 2. Register the dataset (creates /tmp/nyc_taxi_registry.json on first call).
uv run driftsentinel registry add \
  --contract examples/nyc_yellow_taxi/dataset_contract.yml \
  --registry /tmp/nyc_taxi_registry.json \
  --catalog <your_catalog>

# 3. Run the full pipeline against the resolved configs.
uv run driftsentinel databricks connect \
  --catalog <your_catalog> --profile <your_profile> \
  --dataset-id nyc_yellow_taxi \
  --registry /tmp/nyc_taxi_registry.json \
  --drift-policy examples/nyc_yellow_taxi/drift_policy.yml \
  --benchmark-policy examples/nyc_yellow_taxi/benchmark_policy.yml \
  --landing-path /tmp/nyc_taxi/landing \
  --baseline-path /tmp/nyc_taxi/baseline \
  --wait
```

## Expected verdict

On a clean run with Jan→Feb 2024:

- **Intake**: PASS — schema matches, quarantine ratio is 0 after dedup.
- **Drift**: BLOCK — fare and trip-distance Wasserstein scores cross
  `health_score_threshold=0.70`. This is real seasonal drift between months,
  not a defect, and is the demo's headline finding.
- **Benchmark**: PASS — recall/FPR gates clear at the shipped thresholds.

Replays against other month pairs may yield different verdicts.

## Why these configs matter

| Choice | Reason |
| --- | --- |
| 8-column `business_key` | Single-column keys (e.g. `VendorID`) collide on every shard; the 8-col composite is the minimal set that uniquely identifies a trip in NYC TLC parquet |
| `tpep_pickup_datetime` `batch_identifier` | Trip records do not carry a load-batch column; pickup time is the only deterministic, monotonically-organized field |
| Wasserstein on `fare_amount`, `trip_distance` | Fare changes and seasonal trip length are real, measurable distributional drift |
| Shannon entropy on `payment_type`, `VendorID` | Low-cardinality categorical share shifts (cash share, vendor mix) |
| `min_rows: 100000` baseline | NYC TLC monthly parquet ships ~3M rows; 100k is the minimum for stable Wasserstein at default sample sizes |

See `specs/DS-PATCH-040_nyc_taxi_demo_example.md` for full design context.
