# Dotprompt Evaluation & Dev UI Rubrics

## Structuring `.prompt` Files for Eval
- Keep model and sampling defaults in YAML frontmatter (`model`, `config.temperature`, `input.schema`, `output.format`, `output.schema`).
- Store evaluation provenance under top-level `ext` (e.g., `ext.evalSuite`, `ext.datasetSplit`, `ext.baselineVersion`) rather than inside `input.schema`.
- Use Picoschema (`field?: string`, `items(array): string`, `status(enum): [PASS, FAIL]`) for compact, readable judge output contracts.
- Test prompt iterations side-by-side using Dotprompt variants (`judge.strict.prompt`) and inspect up to 3 runs simultaneously in Genkit Dev UI (`genkit start -- tsx --watch ...`).

## Pairing Deterministic & LLM Evaluators
- **Deterministic (`ai.defineEvaluator`):** Enforce turn budgets, JSON schema validity, `rawToolResponses` parity, and A2UI `validate: 'strict'`.
- **LLM-as-a-Judge (`@genkit-ai/evaluator` + `assets/eval-judge.prompt`):** Score `FAITHFULNESS`, `ANSWER_RELEVANCY`, `MALICIOUSNESS`, and tool-selection precision with explicit `reasoning` fields.

