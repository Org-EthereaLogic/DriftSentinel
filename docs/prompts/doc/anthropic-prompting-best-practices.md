# Prompting best practices

---

This guide provides specific prompt engineering techniques for Claude 4.x models, with specific guidance for Sonnet 4.5, Haiku 4.5, and Opus 4.5. These models have been trained for more precise instruction following than previous generations of Claude models.

## General principles

### Be explicit with your instructions

Claude 4.x models respond well to clear, explicit instructions. Being specific about your desired output can help enhance results. Customers who desire the above-and-beyond behavior from previous Claude models might need to more explicitly request these behaviors with newer models.

**Less effective:**

```text
Create an analytics dashboard
```

**More effective:**

```text
Create an analytics dashboard. Include as many relevant features and interactions as possible. Go beyond the basics to create a fully-featured implementation.
```

### Add context to improve performance

Providing context or motivation behind your instructions, such as explaining why a behavior is important, can help Claude 4.x models better understand your goals and deliver more targeted responses.

**Less effective:**

```text
NEVER use ellipses
```

**More effective:**

```text
Your response will be read aloud by a text-to-speech engine, so never use ellipses since the text-to-speech engine will not know how to pronounce them.
```

### Be vigilant with examples and details

Claude 4.x models pay close attention to details and examples as part of their precise instruction-following capabilities. Ensure that your examples align with the behaviors you want to encourage and minimize behaviors you want to avoid.

### Long-horizon reasoning and state tracking

Claude 4.5 models excel at long-horizon reasoning tasks with strong state tracking. This especially emerges over multiple context windows or task iterations, where Claude can work on a complex task, save state, and continue with a fresh context window.

#### Context awareness and multi-window workflows

Claude 4.5 models can track remaining context budget throughout a conversation. This enables better execution and state management.

**Managing context limits:**

```text
Your context window will be automatically compacted as it approaches its limit, allowing you to continue working indefinitely from where you left off. Therefore, do not stop tasks early due to token budget concerns. As you approach your token budget limit, save your current progress and state to memory before the context window refreshes. Always be as persistent and autonomous as possible and complete tasks fully, even if the end of your budget is approaching. Never artificially stop any task early regardless of the context remaining.
```

The memory tool pairs naturally with context awareness for seamless context transitions.

#### Multi-context window workflows

For tasks spanning multiple context windows:

1. Use a different prompt for the very first context window.
2. Have the model write tests in a structured format.
3. Set up quality-of-life tools such as startup and test scripts.
4. Consider starting with a fresh context window rather than compacting.
5. Provide verification tools.
6. Encourage complete usage of context.

**State management best practices:**

- Use structured formats such as JSON for state data.
- Use unstructured text for progress notes.
- Use git for checkpoint and state tracking.
- Emphasize incremental progress.

### Communication style

Claude 4.5 models have a more concise and natural communication style than previous models:

- More direct and grounded
- More conversational
- Less verbose unless prompted otherwise

## Guidance for specific situations

### Balance verbosity

If you want more visible progress reporting during tool use, say so explicitly:

```text
After completing a task that involves tool use, provide a quick summary of the work you've done.
```

### Tool usage patterns

Claude 4.5 models are trained for precise instruction following and benefit from explicit direction to use specific tools.

**Less effective:**

```text
Can you suggest some changes to improve this function?
```

**More effective:**

```text
Change this function to improve its performance.
```

Or:

```text
Make these edits to the authentication flow.
```

To make Claude more proactive by default:

```text
<default_to_action>
By default, implement changes rather than only suggesting them. If the user's intent is unclear, infer the most useful likely action and proceed, using tools to discover any missing details instead of guessing. Try to infer the user's intent about whether a tool call is intended or not, and act accordingly.
</default_to_action>
```

To make Claude more conservative by default:

```text
<do_not_act_before_instructions>
Do not jump into implementation or change files unless clearly instructed to make changes. When the user's intent is ambiguous, default to providing information, doing research, and providing recommendations rather than taking action. Only proceed with edits, modifications, or implementations when the user explicitly requests them.
</do_not_act_before_instructions>
```

### Tool usage and triggering

Claude Opus 4.5 is highly responsive to system prompts. If your prompts were designed to reduce undertriggering on tools or skills, Opus 4.5 may overtrigger. Use normal prompting rather than aggressive MUST-style wording unless it is genuinely necessary.

### Control the format of responses

Effective techniques for steering output formatting include:

1. Tell Claude what to do instead of what not to do.
2. Use XML format indicators.
3. Match prompt style to desired output style.
4. Provide detailed prompts for specific formatting preferences.

Example:

```text
<avoid_excessive_markdown_and_bullet_points>
When writing reports, documents, technical explanations, analyses, or any long-form content, write in clear, flowing prose using complete paragraphs and sentences. Use standard paragraph breaks for organization and reserve markdown primarily for inline code, code blocks, and simple headings. Avoid using bold and italics.

Do not use ordered or unordered lists unless the content is truly discrete or the user explicitly requests a list.

Your goal is readable, flowing text that guides the reader naturally through ideas rather than fragmenting information into isolated points.
</avoid_excessive_markdown_and_bullet_points>
```

### Research and information gathering

Claude 4.5 models demonstrate strong agentic search capabilities. For best research results:

1. Provide clear success criteria.
2. Encourage source verification.
3. For complex research tasks, use a structured approach.

```text
Search for this information in a structured way. As you gather data, develop several competing hypotheses. Track your confidence levels in your progress notes to improve calibration. Regularly self-critique your approach and plan. Update a hypothesis tree or research notes file to persist information and provide transparency. Break down this complex research task systematically.
```

### Subagent orchestration

Claude 4.5 models demonstrate improved native subagent orchestration. To benefit from that:

1. Ensure well-defined subagent tools are available.
2. Let Claude orchestrate naturally.
3. Adjust conservativeness if needed.

```text
Only delegate to subagents when the task clearly benefits from a separate agent with a new context window.
```

### Model self-knowledge

If you want Claude to identify itself correctly or use exact model strings:

```text
The assistant is Claude, created by Anthropic. The current model is Claude Sonnet 4.5.
```

### Thinking sensitivity

When extended thinking is disabled, Claude Opus 4.5 is especially sensitive to the word "think" and its variants. Replace "think" with alternatives such as "consider," "believe," or "evaluate."

### Leverage thinking and interleaved thinking capabilities

Claude 4.x models offer strong reasoning capabilities that can help with reflection after tool use or complex multi-step work.

```text
After receiving tool results, carefully reflect on their quality and determine optimal next steps before proceeding. Use your reasoning to plan and iterate based on this new information, and then take the best next action.
```

### Document creation

Claude 4.5 models are strong at creating presentations, animations, and visual documents.

```text
Create a professional presentation on [topic]. Include thoughtful design elements, visual hierarchy, and engaging animations where appropriate.
```

### Improved vision capabilities

Claude Opus 4.5 has improved vision capabilities compared to previous Claude models. A crop tool or skill can further improve image evaluations.

### Optimize parallel tool calling

Claude 4.x models excel at parallel tool execution. You can steer this behavior explicitly.

```text
<use_parallel_tool_calls>
If you intend to call multiple tools and there are no dependencies between the tool calls, make all of the independent tool calls in parallel. Prioritize calling tools simultaneously whenever the actions can be done in parallel rather than sequentially. However, if some tool calls depend on previous calls to inform dependent values like parameters, do not call these tools in parallel and instead call them sequentially. Never use placeholders or guess missing parameters in tool calls.
</use_parallel_tool_calls>
```

### Reduce file creation in agentic coding

Claude 4.x models may create temporary files while iterating. If you want fewer leftover files:

```text
If you create any temporary new files, scripts, or helper files for iteration, clean up these files by removing them at the end of the task.
```

### Overeagerness and file creation

Claude Opus 4.5 can overengineer by creating extra files, abstractions, or configurability that was not requested. Counter that with explicit guidance:

```text
Avoid over-engineering. Only make changes that are directly requested or clearly necessary. Keep solutions simple and focused.

Do not add features, refactor code, or make improvements beyond what was asked. Do not create helpers, utilities, or abstractions for one-time operations. Do not design for hypothetical future requirements.
```

### Frontend design

Claude 4.x models can build strong frontends, but without guidance they may default to generic patterns. Use explicit aesthetics guidance when needed.

### Avoid focusing on passing tests and hard-coding

Encourage general solutions rather than test-only fixes:

```text
Please write a high-quality, general-purpose solution using the standard tools available. Do not create helper scripts or workarounds to accomplish the task more efficiently. Implement a solution that works correctly for all valid inputs, not just the test cases. Do not hard-code values or create solutions that only work for specific test inputs.
```

### Encouraging code exploration

If you notice the model proposing solutions without inspecting code, add explicit guidance:

```text
Always read and understand relevant files before proposing code edits. Do not speculate about code you have not inspected. If the user references a specific file or path, you must open and inspect it before explaining or proposing fixes.
```

### Minimizing hallucinations in agentic coding

To encourage grounded answers:

```text
<investigate_before_answering>
Never speculate about code you have not opened. If the user references a specific file, you must read the file before answering. Make sure to investigate and read relevant files before answering questions about the codebase.
</investigate_before_answering>
```

## Migration considerations

When migrating to Claude 4.5 models:

1. Be specific about desired behavior.
2. Frame instructions with explicit modifiers.
3. Request specific features explicitly when needed.
