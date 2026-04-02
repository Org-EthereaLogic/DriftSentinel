# Agentic Prompt Engineering

> The prompt is THE fundamental unit of engineering.
>
> Invest in your prompts for the trifecta to achieve asymmetric engineering in the age of agents.

## The 7 Levels of Agentic Prompt Formats

### Level 1

High Level Prompt

> Reusable, adhoc, static prompt.

- Sections
  - Title
  - High Level Prompt (required)
  - Purpose

- Example Prompts
  - .claude/commands/all_tools.md
  - .claude/commands/start.md

### Level 2

Workflow Prompt

> Sequential workflow prompt with input, work, and output.

- Sections
  - Metadata
  - Workflow (required)
  - Instructions (secondary)
  - Variables (secondary)
  - Report (secondary)
  - Relevant Files
  - Codebase Structure
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/prime.md`
  - `.claude/commands/build.md`
  - `.claude/commands/quick-plan.md`
  - `.claude/commands/prime_tier_list.md`

### Level 3

Control Flow Prompt

> A prompt that runs conditions or/and loops in the workflow.

- Sections
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/build.md`
  - `.claude/commands/create_image.md`
  - `.claude/commands/edit_image.md`

### Level 4

Delegate Prompt

> A prompt that delegates the work to other agents (primary or subagents).

- Sections
  - Variables w/agent config (model, count, tools, etc)
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/parallel_subagents.md`
  - `.claude/commands/load_ai_docs.md`
  - `.claude/commands/background.md`

### Level 5

Higher Order Prompt

> Accept another reusable prompt (file) as input. Provides consistent structure so the lower level prompt can be changed.

- Sections
  - Variables w/prompt file variable (required)
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/build.md`
  - `.claude/commands/load_bundle.md`

### Level 6

Template Metaprompt

> A prompt that is used to create a new prompt in a specific dynamic format.

- Sections
  - Template (required)
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/t_metaprompt_workflow.md`
  - `.claude/commands/plan_vite_vue.md`

### Level 7

Self Improving Prompt

> A prompt that is updated by itself or another prompt/agent with new information.

- Sections
  - Expertise
  - ...same as previous levels

- Example Prompts
  - `.claude/commands/experts/cc_hook_expert/cc_hook_expert_plan.md`

## Agentic Prompt Sections

> Ordered list of common and rare agentic prompt sections you can use to build a new prompt.

- `Metadata`
- `# Title`
- `## Purpose`
- `## Variables`
- `## Instructions`
- `## Relevant Files`
- `## Codebase Structure`
- `## Workflow`
- `## Expertise`
- `## Template`
- `## Examples`
- `## Report`

### Metadata

Provides configuration and metadata about the prompt using YAML frontmatter. Includes `allowed-tools` to specify which tools the prompt can use, `description` for prompt identification, `argument-hint` to guide user input, and optionally `model` to set the AI model (sonnet/opus).

### Title

The main heading that names the prompt, typically using a clear, action-oriented name. Should immediately communicate what the prompt does.

### Purpose

Describes what the prompt accomplishes at a high level and its primary use case. Sets context for the user about when and why to use this prompt. Often references key sections like Workflow or Instructions to guide the reader.

### Variables

Defines both dynamic variables (using `$1`, `$2`, `$ARGUMENTS`) that accept user input and static variables with fixed values. You can reference these variables throughout the prompt using `{{variable_name}}` syntax. For higher-order prompts, this is where prompt file paths are specified.

### Instructions

Provides specific guidelines, rules, and constraints for executing the prompt. Written as bullet points detailing important behaviors, edge cases to handle, and critical requirements. Acts as the guardrails ensuring consistent and correct execution.

### Relevant Files

Lists specific files or file patterns that the prompt needs to read, analyze, or modify. Helps establish context and ensures the prompt has access to necessary codebase resources. Particularly useful for prompts that work with existing project structures.

### Codebase Structure

Documents the expected directory layout and file organization relevant to the prompt's operation. Shows where files should be created, where to find existing resources, and how components relate to each other. Essential for prompts that generate or modify project structures.

### Workflow

The core execution steps presented as a numbered list detailing the sequence of operations. Each step should be clear and actionable, often including conditional logic for different scenarios. This is where control flow and task delegation to other agents occurs in higher-level prompts.

### Expertise

Contains accumulated knowledge, best practices, and patterns specific to the prompt's domain. Acts as embedded documentation that evolves over time, making the prompt self-improving. Includes architectural knowledge, discovered patterns, standards, and detailed technical context.

### Template

Provides reusable patterns or boilerplate structures that can be adapted for similar use cases. Often includes code snippets, configuration templates, or structural patterns. Helps users understand how to create variations of the prompt or apply its patterns elsewhere.

### Examples

Demonstrates concrete usage scenarios with actual command invocations and expected outcomes. Shows different parameter combinations and use cases to help users understand the prompt's capabilities. Essential for complex prompts where usage patterns are not immediately obvious.

### Report

Defines how results should be presented back to the user after execution. Specifies the format, structure, and level of detail for output. Can include markdown templates, required sections, metrics to report, or summary formats that best communicate the work completed.

## System Prompts vs User Prompts

> The most important difference is scope and persistence.
>
> System prompts set the rules for all conversations.
>
> User prompts ask for specific tasks.

### System Prompts

System prompts tell the AI who it is and how it should behave in every conversation.

They are the AI's role definition and rule book combined.

**What they do:**

- Set the AI's role
- Define what the AI can and cannot do
- Establish tone and style across interactions
- Create rules that apply to every interaction

**How to write them:**

- Be very clear
- Evaluate edge cases
- Test thoroughly
- Keep them focused
- Use simple, exact language

**Example:**

```text
You are a Python tutor. Always explain code step by step.
Never write code longer than 10 lines without explaining it.
If a user asks about other languages, politely redirect to Python.
```

### User Prompts

User prompts ask the AI to do specific tasks. They work within the rules set by the system prompt.

**What they do:**

- Request specific actions or information
- Provide context for the current task
- Give examples of what you want
- Can be refined based on responses

**How to write them:**

- Be clear about what you want now
- Include relevant details and context
- Show examples if helpful
- Refine with follow-up questions when needed

**Example:**

```text
Write a function that reverses a string. Use a for loop and explain each line.
```

### Key Differences

| System Prompt | User Prompt |
| ------------- | ----------- |
| Sets rules for all conversations | Asks for one specific thing |
| Cannot be changed mid-conversation | Can be refined with follow-ups |
| Needs to handle many scenarios | Focuses on the current task only |
| Mistakes affect everything | Mistakes affect one response |
| Written once, used many times | Written fresh each time |

### Why This Matters

A bad system prompt is like bad instructions for a whole job. A bad user prompt is like unclear directions for one task. System prompts need more testing because they affect everything. User prompts can be improved on the fly.

### Which Sections Work Best for System Prompts

Not all prompt sections make sense for system prompts.

**Essential Sections:**

**Purpose** — define the AI's core identity and role.

**Instructions** — set the behavioral rules that apply to every interaction.

**Examples** — show expected behavior patterns rather than task examples.

**Workflow** — usually too specific, except for a very general operating approach.

**Sections to Avoid:**

- Variables
- Report
- Expertise
- Templates
- Metadata
- Relevant Files
- Codebase Structure

### Common System Prompt Patterns

**Tool Usage Instructions:**

```text
When working with files:
1. Always use Read before Edit
2. Create parent directories before writing files
3. Never use shell commands for file operations - use the provided tools
```

**Behavioral Boundaries:**

```text
If asked to do something harmful or unethical, politely decline and explain why.
Never execute commands that could damage the system.
Always confirm before making destructive changes.
```

**Output Formatting:**

```text
Structure responses as:
- Brief summary of what you'll do
- Execute the task
- Confirm completion with specific details
Keep explanations under 3 sentences unless asked for more detail.
```

## Claude Code Bash Alias

```bash
alias cld="claude"
alias cldp="claude -p"
alias cldo="claude --model opus"
alias clds="claude --model sonnet"
alias cldys="claude --dangerously-skip-permissions --model sonnet"
alias cldy="claude --dangerously-skip-permissions --model sonnet"
alias cldyo="claude --dangerously-skip-permissions --model opus"
alias lfg="claude --dangerously-skip-permissions --model opus"
alias cldpy="claude -p --dangerously-skip-permissions"
alias cldpyo="claude -p --dangerously-skip-permissions --model opus"
alias cldr="claude --resume"
```
