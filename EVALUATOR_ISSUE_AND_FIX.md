# Debugging and Fix for `evaluator.py`

This document explains in detail the problem encountered in `evaluator.py`, shows the parts of the code that were affected, and describes how the issue was diagnosed and resolved.

---

## 1. Background

The `PromptEvaluator` class in `evaluator.py` is responsible for evaluating a RAG bot’s system prompt and a sample interaction. It loads a template prompt from `memory-bank/sys_prompt_enhanced.md` containing placeholder tags:

```text
- User_Query: {{user_query}}
- Retrieved_Context: {{retrieved_context}}
- Bot_Response: {{bot_response}}
- Bot_Instructions: {{bot_instructions}}
```

These placeholders were expected to be replaced at runtime with actual values before sending to the Azure OpenAI chat completion API.

---

## 2. Issue Description

### Symptom

The evaluator repeatedly produced confusing feedback, such as:

> *“Notify Insufficient Context: Add a rule instructing the bot to explicitly notify users when the context is insufficient…”*

even though the user’s prompt already included that rule. The evaluation model appeared unaware of the existing instructions.

### Root Cause

When inspecting the logs, it became clear that:

- **Placeholders were never replaced.**  
- The template was sent _verbatim_ as the system message, and the actual data was sent separately in the user message.  
- The evaluation LLM saw `{{user_query}}`, `{{retrieved_context}}`, etc., instead of actual content.

This mismatch led the model to operate on an unfilled template, causing it to ignore the real instructions and produce irrelevant feedback.

---

## 3. Diagnostic Steps

1. **Added Diagnostic Logging**  
   We instrumented `evaluate()` with logging to capture:
   - The raw system prompt template (`prompt_to_use`)
   - The user content string (`user_content`)
2. **Ran `python test_evaluator.py`**  
   Observed logs:
   ```text
   --- EVALUATOR SYSTEM PROMPT (what the model is told to be) ---
   # The Prompt Diagnostician’s Mandate
   ...
   - User_Query: {{user_query}}
   - Retrieved_Context: {{retrieved_context}}
   ...
   ```
   and the separate user message containing the real values.

---

## 4. Solution

### 4.1 Placeholder Replacement

Modify `evaluate()` so that before sending the prompt, we:

1. Load the template (with placeholders).
2. Perform string replacements:
   ```python
   prompt_to_use = template.replace("{{user_query}}", user_query)
   prompt_to_use = prompt_to_use.replace("{{retrieved_context}}", retrieved_context)
   prompt_to_use = prompt_to_use.replace("{{bot_response}}", bot_response)
   prompt_to_use = prompt_to_use.replace("{{bot_instructions}}", bot_instructions)
   ```
3. Send a single system message containing the fully populated prompt.

### 4.2 Final Code Snippet

Below is the critical section of `evaluate()` after the fix:

```python
# Load template or override prompt
prompt_template = system_prompt or self.system_prompt

# Inject values into placeholders
prompt_to_use = prompt_template.replace("{{user_query}}", user_query)
prompt_to_use = prompt_to_use.replace("{{retrieved_context}}", retrieved_context)
prompt_to_use = prompt_to_use.replace("{{bot_response}}", bot_response)
prompt_to_use = prompt_to_use.replace("{{bot_instructions}}", bot_instructions)

# Send only the system message; no separate user content needed
messages = [
    {"role": "system", "content": prompt_to_use},
    {"role": "user", "content": ""}
]

response = self.client.chat.completions.create(
    model=self.deployment,
    messages=messages,
    temperature=0.0,
    max_completion_tokens=1000
)
```

---

## 5. Cleanup

Diagnostic logging added during investigation was removed, restoring clean debug output.

---

## 6. Outcome

With placeholders correctly replaced, the evaluator now:

- Sees the real instructions and context in one coherent prompt.
- Produces accurate, actionable feedback that reflects existing rules.
- No longer flags already-present instructions as missing.

The bug is resolved, and the `PromptEvaluator` behaves as intended.
