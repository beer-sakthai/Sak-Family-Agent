# SakThai 11-Phase Development Cycle Reference

Detailed phase breakdown, command mappings, and execution checklists for model and agent lifecycles.

## 1. The 11-Phase Cycle
1. **Data**: Augmentation, cleaning, and versioning.
2. **Train**: QLoRA / rsLoRA execution on Kaggle T4 ($0) or free tiers.
3. **Eval**: Two-tier evaluation (BFCL benchmark + BenchmarkQED / LLM-as-judge).
4. **Error Analysis**: Diagnostic taxonomy (Wrong tool, Hallucinated arg, Parallel context loss).
5. **Publish**: Merge LoRA, quantize to GGUF, generate rich model card with limits.
6. **Deploy**: Gradio Space, Ollama Modelfile, Hugging Face Endpoint.
7. **Discoverability**: Metadata tags (`conversational`), interactive playground, cross-linking.
8. **Monitor & Security**: Download analytics, secret scans, token audit.
9. **Release**: Release notes, semantic tag, social broadcast.
10. **Feedback Loop**: Community feedback ingestion, issue triage.
11. **Continuous Learning**: Journal entry and skill evolution.

## 2. Command Lookup Table
| Phase | Core Commands | Validation Trigger |
|---|---|---|
| Data | `sakthai dataset audit` | Schema and format validation |
| Train | `sakthai train run` | Checkpoint loss convergence |
| Eval | `sakthai eval audit` | Target score threshold |
| Publish | `sakthai publish model` | GGUF artifact generation |
| Deploy | `sakthai space deploy` | Healthcheck 200 OK |
| Monitor | `sakthai doctor` | System heartbeat |
