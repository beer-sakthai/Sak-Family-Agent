# HF Papers of the Day — 2026-07-23 (Evening)

## Top 3 Picks

### 1. Self Gradient Forcing: Native Long Video Extrapolation
**HF:** https://huggingface.co/papers/2607.20368 · **arXiv:** https://arxiv.org/abs/2607.20368 · ⭐ 17

Autoregressive video diffusion models suffer from a "historical context-gradient gap" — future-frame losses can't supervise how earlier latents encode their KV cache. Self Gradient Forcing (SGF) is a two-pass training strategy: Pass 1 does a no-gradient rollout, recording the exit step's self-generated context and noisy latents. Pass 2 reconstructs context gradients at that step — the model recomputes KV representations with causal attention from future to context, providing missing memory-writing supervision without backprop through the full rollout. **Why it matters:** From just a 5-second training window, SGF extrapolates to multi-minute videos with far better subject identity, background consistency, and temporal stability than standard Self Forcing — a clean fix for the core bottleneck in long-form autoregressive video generation.

### 2. Scaling Laws for Hypernetwork-Based Knowledge Injection in Large Language Models
**HF:** https://huggingface.co/papers/2607.19604 · **arXiv:** https://arxiv.org/abs/2607.19604 · ⭐ 13

Hypernetworks offer a decoupled way to inject factual knowledge into LLMs: train a hypernetwork to generate a fixed LoRA adapter from a corpus of facts, then plug it into the target model. This work provides the first rigorous scaling-law study for this setup, spanning hypernetwork depth, width, and target model size. They introduce MegaWikiQA — tens of millions of multi-hop QA examples across 39 domains from Wikidata5M. Key findings: (i) hypernetwork injection obeys predictive power-law scaling along all architectural axes; (ii) hypernetworks generalize OOD with steeper scaling exponents than LoRA finetuning or full finetuning, making them a principled and scalable substrate for train-time adaptation. **Why it matters:** First empirical scaling laws for hypernetwork-based knowledge injection — suggests this route could outperform traditional fine-tuning as models scale, while keeping the target model's weights frozen.

### 3. SLAI T-Rex: Full-Parameter Post-training of the DeepSeek-V4 Family on Ascend SuperPOD
**HF:** https://huggingface.co/papers/2607.20145 · **arXiv:** https://arxiv.org/abs/2607.20145 · ⭐ 12 — 65 authors

Full-stack optimization for trillion-parameter MoE model post-training on Ascend NPU SuperPOD (not GPU). Hierarchical framework spans model-level parallelism, computation-communication orchestration, and low-level kernel execution — achieving 34.22% MFU (2.93× improvement over baseline). On top of this infra, they build a CPT + SFT pipeline for Operations Research (OR) tasks using DeepSeek-V4-Flash: 10K high-quality SFT samples across 4 task categories and 3 problem representations. The specialized model achieves 71.81% zero-shot Pass@1, outperforming GPT-5.4-Mini by 3.98 pp and base DeepSeek-V4-Flash by 11.27 pp. **Why it matters:** Proof that Ascend NPUs can viably train frontier-scale models with competitive MFU, and that domain-specialized post-training (OR) delivers outsized gains — a full-stack blueprint for non-GPU AI infrastructure.

## Other Notable Papers
- **Beyond Relevance-Centric Retrieval: Rubric-Oriented Document Set Selection and Ranking** (2607.19747) — Rethinks retrieval from single-document relevance to rubric-oriented set selection. ⭐ 1
- **An Exam for Active Observers** (2607.16165) — Probing what active observation means for embodied AI via curated exam scenarios. ⭐ 7
- **Beyond Euclidean Clipping: Overcoming Exploration Collapse in LLM RL via Riemannian Isometric Policy Optimization** (2607.10169) — Addresses exploration collapse in RL for LLMs by moving beyond Euclidean gradient clipping to Riemannian geometry.
- **ATSplat: Compact Feed-forward 3D Gaussian Splatting with Adaptive Token Expansion** (2607.20417) — Feed-forward 3DGS with adaptive token expansion for compact scene representation.
- **SeededGrasp: Language-Guided Grasping in Complex Scenes with Multiple Embodiments** (2607.20207) — Decouples VLM semantic reasoning from low-level grasp execution via seed-point conditioning.

## Meta
- **Generated:** Cron job, 2026-07-23 ~evening
- **Source:** https://huggingface.co/papers
