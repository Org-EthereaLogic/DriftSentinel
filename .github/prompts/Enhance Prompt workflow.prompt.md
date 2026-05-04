---
agent: agent
description: Transform a vague or incomplete prompt into a fully actionable, self-contained specification that an AI coding agent can execute step-by-step without ambiguity.
argument-hint: Paste the source prompt text directly, or provide the file path to the prompt you want to enhance
allowed-tools: Read, Write, Edit, Bash, Search, Grep, LS
---

# Prompt Enhancement Workflow

**Version:** 3.0
**Updated:** 2026-04-01
**Prompt Level:** Level 6 (Template Metaprompt)

---

## Purpose

Apply expert prompt engineering knowledge to transform ambiguous or underspecified prompts into fully self-contained, executable specifications that AI coding agents can follow to completion without further clarification. This workflow produces Level 2–5 output prompts depending on the source complexity, using a consistent structural template per type.

---

## Variables

| Variable | Type | Description |
|----------|------|-------------|
| `$ARGUMENTS` | Dynamic | The source prompt text, or a file path to the prompt you want to enhance. If a file path is provided, read the file before proceeding. |
| `REPO_ROOT` | Dynamic | Current DriftSentinel checkout, resolved with `git rev-parse --show-toplevel` before creating or reading repository-local prompt assets. |
| `OUTPUT_DIR` | Static | `${REPO_ROOT}/docs/prompts/enhanced/` |
| `EXAMPLES_DIR` | Static | `${REPO_ROOT}/docs/prompts/enhanced/` — repository-local enhanced prompts for structural reference |
| `DOCS_DIR` | Static | `${REPO_ROOT}/docs/prompts/doc/` — repository-local prompt engineering references |

---

## Behavioral Controls

<investigate_before_answering>
Do not reference or describe any file, function, or codebase detail you have not personally opened and read. If the source prompt references a specific file or path, read it before proceeding. Grounded, hallucination-free analysis is mandatory — never speculate about code, architecture, or behavior you have not inspected. If the source prompt was provided as a file path, read the file first.
</investigate_before_answering>

<default_to_action>
Produce the enhanced prompt file in the repository-local prompt workspace — do not describe what it could contain, create it. If the source prompt's intent is ambiguous, infer the most useful interpretation, document your assumption in the prompt metadata, and use workspace search tools to discover missing context rather than stopping to ask.
</default_to_action>

<use_parallel_tool_calls>
When reading multiple reference files (`AGENTS.md`, `DIRECTIVES.md`, applicable `.instructions.md`, source files), read them all in parallel. When verifying that multiple file paths exist, check them all in parallel. Never read files sequentially when parallel reads are possible.
</use_parallel_tool_calls>

<format_control>
The enhanced prompt you produce must use markdown headings (`##`, `###`), fenced code blocks with language identifiers, and tables for structured data. Write all step instructions in the imperative voice. Every action step must be followed by an italicized success signal. Never use "think" — use "evaluate", "assess", "consider", or "determine" instead.
</format_control>

---

## Inputs Consulted

| Source | Key Takeaways |
|--------|---------------|
| `docs/prompts/doc/agentic-prompt-engineering.md` | Seven prompt levels; section anatomy (`Metadata`, `Variables`, `Workflow`, `Instructions`, `Expertise`, `Report`); Level 6 prompts generate structured lower-level prompts. |
| `docs/prompts/doc/anthropic-prompting-best-practices.md` | Be explicit with modifiers; embed behavioral XML controls; justify restrictions; use parallel tool calls; avoid "think" variants. |
| `docs/prompts/enhanced/` | Repository-local enhanced prompts provide structural reference for new prompt outputs. |
| `.github/prompts/Enhance Prompt workflow.prompt.md` | This workflow prompt itself is repository-local and should write outputs into the repo rather than editor-profile storage. |

---

## Mission Statement

Given an ambiguous or high-level prompt, produce a self-contained, test-ready enhanced prompt in the DriftSentinel repository that an AI coding agent can execute step-by-step without further clarification.

---

## Prompt Type Classification

Before enhancing, classify the source prompt into one of these categories to apply the appropriate template:

| Type | Indicators | Key Sections Needed |
|------|------------|---------------------|
| **Fix/Debug** | "broken", "not working", "error", "gap", "issue" | Root Cause Analysis phase, Problem-State Table, Alternative Solutions |
| **Feature** | "implement", "add", "create", "build" | Technical Context, Problem-State Table (current → target), Phased Instructions |
| **Research** | "investigate", "evaluate", "compare", "find" | Research Criteria, Deliverables spec, Decision Matrix template |
| **Troubleshoot** | "diagnose", "why", "understand", "check" | Investigation Phase, Hypothesis Table, Verification Commands |
| **Refactor** | "optimize", "clean up", "improve", "consolidate" | Before/After examples, Complexity Budget, Regression Tests |

**Complexity Classification Rubric:**

| Complexity | Criteria | Instruction Count | Line Budget |
|------------|----------|-------------------|-------------|
| **Simple** | Single file, < 50 lines changed, no dependencies | 3-6 instructions | 50-100 lines |
| **Moderate** | 2-5 files, < 200 lines changed, existing patterns | 7-12 instructions | 100-300 lines |
| **Complex** | 5+ files, new patterns introduced, integration needed | 13-20 instructions | 300-500 lines |

---

## Workflow

### Phase 1: Analyze Source Prompt

*Why: Grounding analysis before writing prevents the most common failure mode — enhancing the wrong problem. Incomplete assumptions at this stage cascade into every downstream instruction.*

1. **Classify prompt type:** Determine if this is a Fix, Feature, Research, Troubleshoot, or Refactor prompt using the classification table above.
2. **Extract the core intent:** State the single main goal in one sentence — no qualifiers.
3. **Define scope boundaries:** List explicitly what IS in scope and what is NOT.
4. **Identify success criteria:** State the measurable outcomes that confirm completion.
5. **Catalog missing details:** List every ambiguous element that would block execution:
   - Target file paths or directories
   - Required tools, frameworks, or dependencies
   - Input/output formats
   - Testing or verification steps
   - Edge cases or error handling requirements
6. **Assess complexity:** Use the rubric above to classify as Simple, Moderate, or Complex.

### Phase 2: Synthesize Reference Guidance

*Why: Project constraints discovered here propagate into every instruction. Skipping this phase produces plausible but non-compliant prompts that violate governance rules or introduce forbidden patterns.*

7. **Gather project constraints in parallel:** Read `AGENTS.md`, `DIRECTIVES.md`, and any `.instructions.md` files applicable to the workspace — read all of them simultaneously, not sequentially.
8. **Identify coding standards:** Note naming conventions, file organization patterns, and forbidden practices.
9. **Resolve conflicts:** If reference materials contradict each other, apply this precedence:
   1. Security rules (highest priority)
   2. Project-specific instructions (`AGENTS.md`, `DIRECTIVES.md`)
   3. General best practices
10. **Summarize key rules:** Produce a concise list (5–10 items) of constraints the enhanced prompt must enforce.

### Phase 3: Draft Enhanced Prompt

*Why: Each structural element below addresses a known execution failure mode — missing context causes guessing, vague instructions cause wrong actions, absent verification enables silent failures, and unexplained restrictions get overridden when they seem inconvenient.*

11. **Write the mission statement:** One clear, unambiguous sentence stating what the agent must accomplish.
12. **Add technical context section:** Explain *why* this solution works and what the agent needs to understand to implement it correctly. Include:
    - Relevant architecture context
    - Key files and their purposes
    - Design rationale for the chosen approach
13. **Create the problem-state table:** Use a table to contrast current vs. target state for all prompt types.
14. **Select model tier:** Based on complexity classification, include a model recommendation:
    - **Simple** → `claude-haiku-4-20250514`
    - **Moderate** → `claude-sonnet-4-20250514`
    - **Complex** → `claude-opus-4-20250514`
15. **Write numbered, phased instructions:** Organize instructions into logical phases:
    - **Investigation/Setup Phase:** Gather context, verify prerequisites, read relevant files in parallel
    - **Implementation Phase:** Execute the core work
    - **Verification Phase:** Test and validate changes
    - **Security/Quality Phase:** Run scans and check for regressions

    Each step must be:
    - Atomic (one action per step)
    - Verifiable (includes explicit success signal in italics)
    - Explicit (contains file paths, commands, or code snippets)
    - Motivated (includes a brief **Rationale:** for any non-obvious restriction or choice)
16. **Add quality modifiers where warranted:** For Complex-classified implementation tasks, append quality modifiers — "implement a fully-featured solution", "handle all edge cases", "go beyond the minimum viable implementation" — to prevent the agent from stopping at the minimum.
17. **Add guardrails section:** List forbidden actions, performance budgets, and dependency constraints. Wrap critical constraints in `<guardrails>` XML tags.
18. **Add pre-flight checks:** State what the agent must verify before starting — include executable bash commands.
19. **Add verification checklist:** State what confirms the task is complete as markdown checkboxes.
20. **Define error handling:** Provide a resolution table mapping foreseeable failures to specific resolutions.
21. **Add out-of-scope section:** Explicitly list related work that is NOT part of this prompt.
22. **Add alternative solutions for Fix/Debug prompts:** Provide fallback approaches if the primary solution fails.
23. **Add state tracking instructions for Complex prompts:** Instruct the agent to use `progress.json` for structured state and `progress.txt` for freeform notes. Include a git checkpoint step after each implementation phase.

### Phase 4: Quality Check

24. **Self-containment test:** Evaluate whether an agent could execute this prompt with only the information provided. Add missing context if not.
25. **Ambiguity test:** Review each instruction. Confirm there is only one reasonable interpretation. Rewrite any step that permits multiple interpretations.
26. **Tone review:** Remove hedging language ("maybe", "consider", "you could"). Replace with directive imperatives ("Create", "Execute", "Verify").
27. **Vocabulary check:** Replace any occurrence of "think" or "think about" with "evaluate", "assess", "consider", or "determine".
28. **Complexity budget:** Confirm the enhanced prompt encourages minimal solutions. Add explicit anti-over-engineering guidance if the classification is Simple or Moderate.
29. **Bash command audit:** Every shell command must be copy-pasteable and include expected output where relevant.

---

## Instructions

- **Do NOT expand scope:** The enhanced prompt should solve the original problem, not a larger imagined one.
- **Preserve intent:** If the source prompt is intentionally vague, retain exploratory language but add structure.
- **Use XML tags for formatting control:** Wrap sections in descriptive tags such as `<guardrails>` or `<verification>` when the prompt will be consumed by another AI agent.
- **Embed behavioral XML controls in the enhanced prompt:** When the task warrants it, embed `<investigate_before_answering>`, `<default_to_action>`, or `<use_parallel_tool_calls>` blocks near the top of the enhanced prompt.
- **Include code blocks:** Where implementation is required, provide complete, copy-pasteable code — not pseudocode.
- **Reference concrete paths:** Use absolute paths or paths relative to workspace root. Never use generic placeholders like `<project-root>`.
- **Specify tools explicitly:** If a terminal command is needed, write the exact command. If a file edit is needed, show the before/after.
- **Add success signals:** After each instruction, include an italicized success signal.
- **Include rationale for non-obvious restrictions:** Add a one-sentence **Rationale:** after any instruction that restricts choices or requires a non-default behavior.
- **Add motivating context to instructions:** Phrase restrictions and guidance as context with a reason, not just a rule.
- **Add quality modifiers to complex implementations:** In the enhanced prompt, append modifiers like "implement a fully-featured solution", "handle all edge cases", or "go beyond the minimum viable implementation" for Complex-classified tasks.
- **Use "evaluate/assess/consider/determine" not "think":** Throughout the enhanced prompt, never use the word "think" or "think about".
- **Tell agents what TO DO, not what not to do:** Phrase the desired behavior positively whenever possible.
- **Include model recommendation in metadata:** Add a `Model:` field to the enhanced prompt header when the complexity classification warrants escalation above Sonnet.
- **Write the enhanced prompt into `docs/prompts/enhanced/`:** Keep repository-local prompt outputs with the project rather than only in editor-profile storage.
