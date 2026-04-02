# verify

Independently verify a DriftSentinel subject against primary evidence.

## Workflow

1. Identify what must be verified.
2. Read the primary sources directly: `specs/`, implementation or config files,
   notebooks, bundle files, or evidence artifacts.
3. Trace dependencies and supporting surfaces.
4. Run relevant commands that produce observable proof.
5. Separate verified facts, issues found, and inconclusive items.

## Principles

- evidence over inference
- canonical spec over narrative summary
- no file modification during verification
- no PASS claim without replayable proof
