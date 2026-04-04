# DriftSentinel End-to-End Visualized Verification Prompt

**Author:** Anthony Johnson II
**Date:** 2026-04-02
**Purpose:** Instruct a coding agent with sub-agent access to Kapture MCP and
Claude Chrome to perform a full end-to-end, visually verified acceptance test
of the DriftSentinel application — simulating a real executive who downloaded
the package, brought their own data, and used it on Databricks Free Edition
over the course of several operational days.

---

## Prompt

```text
You are performing a full end-to-end visualized verification of DriftSentinel,
the Enterprise Data Trust Chapter 4 application.

Repository: /Users/etherealogic-2/Dev/Databricks/DriftSentinel
Product state: Phases 0–5 complete, 310 tests passing, dependency triage resolved.

Your role: You are an executive at a mid-market construction company
("Meridian Infrastructure") who just discovered DriftSentinel on GitHub. You
have Databricks Free Edition, basic Python knowledge, a laptop, and real
business data you want to protect. You will simulate FIVE DAYS of realistic
usage — from first clone through daily operations — exercising every feature,
function, button, tab, widget, filter, error path, and workflow the product
exposes. You will use Kapture MCP and Claude Chrome as your eyes and hands
to visually interact with the Gradio dashboard and the Databricks workspace.

IMPORTANT RULES:
- You must VISUALLY VERIFY every interaction through screenshots via Kapture
  or Claude Chrome. No claim of "button works" without a captured screenshot
  showing the before and after state.
- You must log every issue you encounter in a structured issue log.
- After logging each issue, attempt to resolve it in the codebase. If the fix
  requires code changes, make them, re-run the test suite, and re-verify
  visually.
- At the end of each simulated day, write a day summary to
  report/e2e-verification/day-N-summary.md

Before starting, read these files for full context:
- CLAUDE.md
- AGENTS.md
- CONSTITUTION.md
- README.md
- app/app.py
- src/driftsentinel/orchestration/runner.py
- src/driftsentinel/config/loader.py
- src/driftsentinel/evidence/writer.py
- All notebooks in notebooks/
- All templates in templates/

Create the evidence directory before starting:
  mkdir -p report/e2e-verification

==========================================================================
DAY 1 — FIRST CONTACT: CLONE, INSTALL, AND HEALTH CHECK
==========================================================================

Persona: You are Marcus Chen, VP of Data & Analytics at Meridian
Infrastructure. You found DriftSentinel on GitHub and want to evaluate it.

TASK 1.1 — Clone and local install
- Clone the repo (or use the existing local copy)
- Run: make sync
- Run: make test
- VERIFY: All 310 tests pass. Screenshot the terminal output via Kapture.
- VERIFY: No errors during install. If there are dependency issues, log them.

TASK 1.2 — Read the README and quickstart
- Open README.md in the browser via Claude Chrome
- VERIFY: The quickstart instructions are clear and match what you just did.
- VERIFY: The "Part of a series" table renders correctly.
- VERIFY: Badge images load (CI, Codacy, Codecov).
- Screenshot the rendered README.

TASK 1.3 — Launch the Gradio app locally
- Run: cd app && pip install -r requirements.txt
- Run: python app.py
- VERIFY via Kapture/Chrome: The app launches and shows four tabs:
  "Registry", "Run Status", "Evidence Explorer", "Analytics"
- VERIFY: The branded header reads "DriftSentinel"
- VERIFY: The subtitle reads "Read-only operator dashboard — intake, drift,
  benchmark"
- Screenshot the initial empty state of each tab.

TASK 1.4 — Registry tab: empty state
- Click the "Load Registry" button with the default path.
- VERIFY: The table shows "(no registry file found)" — not a crash.
- Screenshot.

TASK 1.5 — Run Status tab: empty state
- Navigate to the "Run Status" tab.
- Click "Query" with default/empty filters.
- VERIFY: The table shows "(no artifacts found)" — not a crash.
- Screenshot.

TASK 1.6 — Evidence Explorer tab: empty state
- Navigate to the "Evidence Explorer" tab.
- Click "Load Artifact" with empty filename.
- VERIFY: The code block shows "(select an artifact filename)" — not a crash.
- Screenshot.

TASK 1.7 — Evidence Explorer: nonexistent file
- Type "nonexistent.json" into the Artifact Filename field.
- Click "Load Artifact".
- VERIFY: Shows "(file not found: nonexistent.json)" — graceful error.
- Screenshot.

==========================================================================
DAY 2 — DATASET REGISTRATION AND FIRST PIPELINE RUN
==========================================================================

Persona: Marcus has decided to onboard Meridian's project-cost dataset.

TASK 2.1 — Create a custom dataset contract
- Copy templates/dataset_contract.yml to /tmp/meridian_project_costs.yml
- Edit it to represent a construction project cost dataset:
    dataset:
      name: meridian_project_costs
      description: Monthly project cost actuals from Procore
      catalog: driftsentinel
      schema: default
      table: project_costs
      contract_version: "1.0.0"
    source:
      system: procore
      format: csv
      landing_path: /Volumes/driftsentinel/default/landing/procore/
    contract:
      required_columns:
        - column_name: project_id
          type: string
          nullable: false
        - column_name: cost_date
          type: date
          nullable: false
        - column_name: labor_cost
          type: double
          nullable: false
        - column_name: material_cost
          type: double
          nullable: false
        - column_name: category
          type: string
          nullable: false
      business_key: [project_id, cost_date]
      batch_identifier: batch_id
- VERIFY: The YAML is valid by loading it in Python:
  python -c "from driftsentinel.config.loader import load_dataset_contract; print(load_dataset_contract('/tmp/meridian_project_costs.yml'))"
- Screenshot the successful load output.

TASK 2.2 — Register the dataset via Python
- Run the following in a Python session:
    from driftsentinel.config.loader import DatasetRegistry, load_dataset_contract
    contract = load_dataset_contract("/tmp/meridian_project_costs.yml")
    reg = DatasetRegistry()
    did, ver = reg.register(contract)
    reg.save("/tmp/driftsentinel_registry.json")
    print(f"Registered: {did} v{ver}")
- VERIFY: Output shows "Registered: meridian_project_costs v1.0.0"
- Screenshot.

TASK 2.3 — Verify registration in the Gradio app
- Go back to the Gradio app in the browser.
- In the Registry tab, ensure the Registry Path is /tmp/driftsentinel_registry.json
- Click "Load Registry".
- VERIFY: The table now shows one row:
  meridian_project_costs | 1.0.0 | driftsentinel | default | project_costs
- Screenshot.

TASK 2.4 — Register a SECOND dataset (to test multi-dataset)
- Create /tmp/meridian_labor_hours.yml with a different dataset:
    dataset:
      name: meridian_labor_hours
      description: Weekly labor hour reports from UKG
      catalog: driftsentinel
      schema: default
      table: labor_hours
      contract_version: "1.0.0"
    source:
      system: ukg
      format: csv
      landing_path: /Volumes/driftsentinel/default/landing/ukg/
    contract:
      required_columns:
        - column_name: employee_id
          type: string
          nullable: false
        - column_name: week_ending
          type: date
          nullable: false
        - column_name: hours_worked
          type: double
          nullable: false
      business_key: [employee_id, week_ending]
      batch_identifier: batch_id
- Register it and save to the same registry path.
- VERIFY: Registry now has 2 entries.
- Click "Load Registry" in the Gradio app.
- VERIFY: Two rows appear.
- Screenshot.

TASK 2.5 — Attempt duplicate registration (error path)
- Try to register meridian_project_costs v1.0.0 again.
- VERIFY: RegistryError is raised with a clear message about the collision.
- Screenshot the error.

TASK 2.6 — Run the local pipeline with evidence
- Run in Python:
    from driftsentinel.orchestration.runner import run_local_pipeline
    result = run_local_pipeline(evidence_dir="/tmp/driftsentinel_evidence")
    import json; print(json.dumps(result, indent=2, default=str))
- VERIFY: The result includes intake, drift, and benchmark sections.
- VERIFY: Evidence files were written to /tmp/driftsentinel_evidence/
- List the evidence directory:
    ls -la /tmp/driftsentinel_evidence/
- Screenshot.

TASK 2.7 — Run the dataset-aware pipeline
- Run in Python:
    from driftsentinel.config.loader import DatasetRegistry
    from driftsentinel.orchestration.runner import run_dataset_pipeline
    reg = DatasetRegistry.load("/tmp/driftsentinel_registry.json")
    result = run_dataset_pipeline(
        reg, "meridian_project_costs",
        evidence_dir="/tmp/driftsentinel_evidence",
    )
    import json; print(json.dumps(result, indent=2, default=str))
- VERIFY: Result includes dataset_id, contract_version, run_id.
- VERIFY: Evidence file written with dataset metadata in the envelope.
- Screenshot.

TASK 2.8 — Verify evidence in the Gradio app
- Go to the "Run Status" tab.
- Set Evidence Dir to /tmp/driftsentinel_evidence
- Click "Query" with no filters.
- VERIFY: Multiple evidence artifacts appear in the table.
- VERIFY: The "Dataset" column shows "meridian_project_costs" for the
  dataset-aware run.
- VERIFY: The "Kind" column shows correct run kinds.
- VERIFY: The "Verdict" column shows actual verdicts (PASS/FAIL/WARN).
- Screenshot.

TASK 2.9 — Filter evidence by dataset
- In the "Run Status" tab, type "meridian_project_costs" in the Dataset ID field.
- Click "Query".
- VERIFY: Only meridian_project_costs artifacts appear.
- Screenshot.

TASK 2.10 — Filter evidence by run kind
- Clear the Dataset ID field.
- Select "benchmark" from the Run Kind dropdown.
- Click "Query".
- VERIFY: Only benchmark artifacts appear.
- Screenshot.

TASK 2.11 — Explore a specific evidence artifact
- Go to the "Evidence Explorer" tab.
- Type the filename of a benchmark evidence artifact (from the Run Status
  results) into the Artifact Filename field.
- Click "Load Artifact".
- VERIFY: Full JSON is displayed in the code block.
- VERIFY: The JSON contains meta.generated_at, meta.dataset_id, meta.run_kind,
  and a payload with quality_track, drift_track, gates, overall_verdict.
- Screenshot the JSON output.

==========================================================================
DAY 3 — DRIFT DETECTION AND GATE VERDICTS
==========================================================================

Persona: Marcus runs the controls daily and wants to understand the gate
verdicts and what happens when drift is detected.

TASK 3.1 — Run drift demo and inspect provenance
- Run in Python:
    from driftsentinel.orchestration.runner import run_drift_demo
    import json
    result = run_drift_demo()
    print(json.dumps(result["provenance"], indent=2, default=str))
- VERIFY: The provenance envelope contains health_score, overall_verdict,
  columns_checked, columns_drifted, gate_results, column_details.
- VERIFY: The overall_verdict is "FAIL" because the demo data includes drift.
- Screenshot.

TASK 3.2 — Write drift evidence for the registered dataset
- Run in Python:
    from driftsentinel.evidence.writer import generate_run_id, write_evidence
    from driftsentinel.orchestration.runner import run_drift_demo
    result = run_drift_demo()
    rid = generate_run_id()
    write_evidence(
        "/tmp/driftsentinel_evidence",
        "drift_meridian_project_costs.json",
        result["provenance"],
        dataset_id="meridian_project_costs",
        contract_version="1.0.0",
        run_id=rid,
        run_kind="drift",
    )
    print(f"Written with run_id={rid}")
- VERIFY: File created in evidence dir.
- Screenshot.

TASK 3.3 — Filter evidence by date range
- Go to "Run Status" tab in Gradio.
- Set "Date From (ISO)" to today's date (e.g. "2026-04-02").
- Click "Query".
- VERIFY: Only today's artifacts appear.
- Now set "Date To" to yesterday's date.
- Click "Query".
- VERIFY: No artifacts match (they were all created today).
- Screenshot both results.

TASK 3.4 — Filter by run ID
- Copy a run_id from one of the previous results.
- Paste it into the "Run ID" field in Run Status.
- Click "Query".
- VERIFY: Exactly one artifact is returned.
- Screenshot.

TASK 3.5 — Run the second dataset pipeline
- Run the dataset-aware pipeline for meridian_labor_hours.
- VERIFY: Evidence is written with dataset_id=meridian_labor_hours.
- Go to Gradio Run Status, filter by meridian_labor_hours.
- VERIFY: Only that dataset's artifacts appear.
- Screenshot.

==========================================================================
DAY 4 — BENCHMARK DEEP DIVE AND POLICY CUSTOMIZATION
==========================================================================

Persona: Marcus wants to customize the benchmark policy for his project
cost dataset and run it with stricter gates.

TASK 4.1 — Create a custom benchmark policy
- Copy templates/benchmark_policy.yml to /tmp/meridian_benchmark_policy.yml
- Edit it:
    benchmark_policy:
      name: meridian_cost_benchmark
      dataset: meridian_project_costs
      contract_version: "1.0.0"
      policy_version: "1.0.0"
      seed: 99
      quality_faults:
        - type: null_injection
          columns: [labor_cost]
          rate: 0.15
        - type: duplicate_inflation
          rate: 0.10
      drift_patterns:
        - type: sudden_shift
          columns: [category]
      gates:
        - name: quality_recall
          type: FAIL
          operator: ">="
          threshold: 0.90
          track: quality
          description: High recall required for cost data
        - name: quality_fpr
          type: FAIL
          operator: "<="
          threshold: 0.05
          track: quality
          description: Very low false positive tolerance
        - name: sudden_drift_sensitivity
          type: FAIL
          operator: ">="
          threshold: 1.00
          track: drift
          description: Must detect sudden drift
        - name: drift_fpr
          type: FAIL
          operator: "<="
          threshold: 0.00
          track: drift
          description: Zero false positives on stable
        - name: challenger_beats_baseline_quality
          type: FAIL
          operator: ">="
          threshold: 1.00
          track: quality
          description: Challenger must beat baseline
        - name: challenger_beats_baseline_drift
          type: FAIL
          operator: ">="
          threshold: 1.00
          track: drift
          description: Challenger must beat baseline on drift
- VERIFY: Policy loads without error:
  python -c "from driftsentinel.config.loader import load_benchmark_policy; print(load_benchmark_policy('/tmp/meridian_benchmark_policy.yml'))"
- Screenshot.

TASK 4.2 — Run benchmark with custom policy
- Run:
    from driftsentinel.benchmark.orchestrator import run_benchmark
    result = run_benchmark(
        seed=99, n_rows=500,
        evidence_dir="/tmp/driftsentinel_evidence",
        policy_path="/tmp/meridian_benchmark_policy.yml",
    )
    print(f"Verdict: {result['overall_verdict'].value}")
    for gr in result["gate_results"]:
        print(f"  {gr.config.name}: {gr.measured_value:.4f} vs {gr.config.threshold} -> {gr.verdict.value}")
- VERIFY: Gate results show with the stricter thresholds applied.
- VERIFY: Evidence file written.
- Screenshot.

TASK 4.3 — Verify custom benchmark in Gradio
- Go to Run Status, filter by run_kind=benchmark.
- VERIFY: The new benchmark artifact appears with the correct timestamp.
- Go to Evidence Explorer, load the new artifact.
- VERIFY: The JSON shows seed=99, n_rows=500, and the custom gate definitions.
- Screenshot.

TASK 4.4 — Create a custom drift policy
- Copy templates/drift_policy.yml to /tmp/meridian_drift_policy.yml
- Edit it to match the registered dataset:
    drift_policy:
      name: meridian_cost_drift
      dataset: meridian_project_costs
      contract_version: "1.0.0"
      policy_version: "1.0.0"
      monitored_columns:
        - column_name: labor_cost
          method: shannon_entropy
        - column_name: category
          method: shannon_entropy
      baseline:
        source: trusted_load
        min_rows: 50
      gates:
        health_score_threshold: 0.80
        max_columns_failed: 1
      verdict_on_fail: block
- VERIFY: Policy loads without error.
- Screenshot.

TASK 4.5 — Run dataset pipeline with both policies
- Run:
    from driftsentinel.config.loader import (
        DatasetRegistry, load_drift_policy, load_benchmark_policy
    )
    from driftsentinel.orchestration.runner import run_dataset_pipeline
    reg = DatasetRegistry.load("/tmp/driftsentinel_registry.json")
    dp = load_drift_policy("/tmp/meridian_drift_policy.yml")
    bp = load_benchmark_policy("/tmp/meridian_benchmark_policy.yml")
    result = run_dataset_pipeline(
        reg, "meridian_project_costs",
        evidence_dir="/tmp/driftsentinel_evidence",
        drift_policy=dp,
        benchmark_policy=bp,
        seed=99, n_rows=500,
    )
    import json; print(json.dumps(result, indent=2, default=str))
- VERIFY: Result includes drift_policy_version, benchmark_policy_version.
- VERIFY: Evidence file written with all metadata.
- Screenshot.

TASK 4.6 — Policy version mismatch (error path)
- Edit the drift policy to reference contract_version: "2.0.0" (non-existent).
- Attempt to run the dataset pipeline.
- VERIFY: RegistryError raised with a clear message about version mismatch.
- Screenshot the error.

==========================================================================
DAY 5 — OPERATIONAL REVIEW AND EDGE CASES
==========================================================================

Persona: Marcus has been running DriftSentinel for a week. He wants a
consolidated view and tests some edge cases before recommending it.

TASK 5.1 — Accumulated evidence review
- Go to Gradio Run Status with no filters.
- VERIFY: All artifacts from Days 1-4 appear, sorted by timestamp descending.
- Count the artifacts and verify the count is consistent with what was written.
- Screenshot.

TASK 5.2 — Combined filter: dataset + run kind
- Filter: dataset_id=meridian_project_costs AND run_kind=pipeline
- VERIFY: Only pipeline runs for that dataset appear.
- Screenshot.

TASK 5.3 — Registry path change (error recovery)
- In the Registry tab, change the path to "/tmp/nonexistent_registry.json"
- Click "Load Registry".
- VERIFY: Shows "(no registry file found)" — no crash.
- Change back to the correct path.
- Click "Load Registry".
- VERIFY: Both datasets reappear.
- Screenshot both states.

TASK 5.4 — Evidence dir change (error recovery)
- In Run Status, change Evidence Dir to "/tmp/empty_dir"
- mkdir -p /tmp/empty_dir
- Click "Query".
- VERIFY: Shows "(no artifacts found)" — no crash.
- Change back to /tmp/driftsentinel_evidence.
- VERIFY: Artifacts reappear.
- Screenshot both states.

TASK 5.5 — Malformed evidence file
- Create a deliberately malformed JSON file in the evidence dir:
    echo "this is not json" > /tmp/driftsentinel_evidence/malformed.json
- Go to Run Status, click Query.
- VERIFY: The malformed file appears with "(malformed)" indicator — no crash.
- Screenshot.

TASK 5.6 — Large evidence load
- Generate 20+ evidence artifacts using a loop:
    from driftsentinel.evidence.writer import write_evidence, generate_run_id
    for i in range(20):
        write_evidence(
            "/tmp/driftsentinel_evidence",
            f"bulk_test_{i}.json",
            {"test_run": i, "overall_verdict": "PASS" if i % 3 else "FAIL"},
            dataset_id="meridian_project_costs",
            run_kind="benchmark",
            run_id=generate_run_id(),
        )
- Go to Run Status, Query with no filters.
- VERIFY: All artifacts appear without pagination errors or UI breakage.
- VERIFY: Scrolling works on the table.
- Screenshot.

TASK 5.7 — Evidence Explorer with a bulk artifact
- Pick one of the bulk_test_N.json artifacts.
- Load it in the Evidence Explorer.
- VERIFY: JSON renders correctly in the code block.
- Screenshot.

TASK 5.8 — Packaged template loading
- VERIFY the packaged templates load correctly:
    from driftsentinel.config.loader import (
        load_packaged_dataset_contract,
        load_packaged_drift_policy,
        load_packaged_benchmark_policy,
    )
    print(load_packaged_dataset_contract())
    print(load_packaged_drift_policy())
    print(load_packaged_benchmark_policy())
- VERIFY: All three load without error from the installed package.
- Screenshot.

TASK 5.9 — Run full test suite one final time
- Run: make test
- VERIFY: All tests still pass (should be 256 or more if you added fixes).
- Screenshot.

TASK 5.10 — Final Gradio app visual audit
- Take a full-page screenshot of each tab in its populated state:
  1. Registry tab with 2 datasets loaded
  2. Run Status tab showing unfiltered results
  3. Evidence Explorer tab with a loaded artifact
- Verify visual consistency: no broken layouts, no misaligned columns, no
  truncated text, no JavaScript console errors.

==========================================================================
ISSUE LOG AND RESOLUTION
==========================================================================

After each day, write to report/e2e-verification/day-N-summary.md:

```markdown
# Day N — E2E Verification Summary

## Tasks Completed
- [x] Task N.1 — description
- [x] Task N.2 — description

## Issues Found

### ISSUE-N.1 — Short title
- **Severity:** critical | high | medium | low
- **Category:** ui | backend | config | docs | packaging
- **Description:** What happened
- **Expected:** What should have happened
- **Steps to reproduce:** How to trigger it
- **Screenshot:** reference to saved screenshot
- **Resolution:** What was fixed (or "deferred")
- **Verification:** How the fix was confirmed
- **Files changed:** list

## Screenshots Captured
- screenshot-N.1-description.png
- screenshot-N.2-description.png
```

At the very end, write: report/e2e-verification/final-summary.md

```markdown
# DriftSentinel E2E Verification — Final Summary

## Test Period
Days 1-5 simulated

## Total Tasks Executed
<count>

## Total Issues Found
<count>

## Issues Resolved
<count>

## Issues Deferred
<count>

## Final Test Suite
<count> passed

## Verdict
PASS | FAIL | CONDITIONAL PASS

## Evidence
- Day summaries: report/e2e-verification/day-{1..5}-summary.md
- Screenshots: report/e2e-verification/screenshots/
- Final test run: terminal output captured
```

==========================================================================
SUB-AGENT INSTRUCTIONS
==========================================================================

You have access to Kapture MCP and Claude Chrome as sub-agents. Use them:

Kapture MCP:
- Use `kapture:screenshot` to capture the current state of the browser or app
- Use `kapture:click` to interact with buttons, tabs, and form elements
- Use `kapture:fill` to type into text fields and dropdowns
- Use `kapture:navigate` to open URLs
- Use `kapture:dom` or `kapture:elements` to inspect page structure

Claude Chrome:
- Use for navigating to the local Gradio app (typically http://localhost:7860)
- Use for reading page content and verifying rendered text
- Use for interacting with the Databricks workspace if needed

For each visual verification:
1. Screenshot BEFORE the interaction
2. Perform the interaction
3. Screenshot AFTER the interaction
4. Compare and document the result

Save all screenshots to report/e2e-verification/screenshots/ with
descriptive filenames.

==========================================================================
COMPLETION CRITERIA
==========================================================================

This verification is complete when:

1. All 5 days of tasks are executed with visual evidence.
2. Every button, tab, filter, text field, dropdown, and error path in the
   Gradio app has been exercised at least once.
3. All three product domains (intake, drift, benchmark) have been run
   with evidence written and verified in the app.
4. Multi-dataset operation has been proven with 2+ registered datasets.
5. Policy customization has been proven with custom drift and benchmark
   policies.
6. All error paths (missing files, malformed data, version mismatches,
   duplicate registration) have been exercised and handled gracefully.
7. The issue log is complete with resolutions for all found issues.
8. The final test suite passes.
9. The final-summary.md is written with an honest verdict.
```

## Intended Use

Copy the prompt block above into a Claude Code session that has Kapture MCP
and Claude Chrome connected. The agent will execute the full 5-day simulation,
capture visual evidence, log and resolve issues, and produce a structured
verification report under report/e2e-verification/.
