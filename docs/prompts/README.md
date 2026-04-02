# Prompt Workspace

Prompt-engineering workspace for DriftSentinel. This directory holds repository-local prompt references, draft prompts, validated enhanced prompts, and prompt-generated support artifacts.

## Directory Map

- `doc/`: reference material on prompt engineering methodology, provider guidance, and DriftSentinel-specific prompt conventions
- `draft/`: work-in-progress prompts under active editing
- `enhanced/`: validated prompts used as higher-quality working versions
- `enhanced/artifacts/`: supporting analysis artifacts generated while refining prompts

## Usage Notes

- Keep repository-specific prompt assets here rather than leaving them only in editor-profile prompt storage.
- Treat prompts in `draft/` as in-progress working material, not validated execution contracts.
- Promote prompts into `enhanced/` only after the prompt structure and acceptance criteria have been checked.
- Store supporting comparisons, inventories, and transformation notes in `enhanced/artifacts/` when a prompt refinement produces extra evidence worth keeping.
- `specs/` remains canonical for product requirements and architecture. This directory supports prompt workflows and does not override canonical specs.

## Current Inventory

- `.github/prompts/Enhance Prompt workflow.prompt.md`: repository-local workflow prompt for turning rough prompts into enhanced prompts stored in this repo
- `doc/agentic-prompt-engineering.md`: reference material on prompt levels, sections, and prompt anatomy
- `doc/anthropic-prompting-best-practices.md`: reference material on Claude 4.x prompt design, tool usage, and state tracking
- `enhanced/DriftSentinel-Phase-1-Repository-Consolidation.enhanced.prompt.md`: repository-local enhanced prompt for the DS-IP-001 Phase 1 consolidation task
