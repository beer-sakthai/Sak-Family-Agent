# Template: REFERENCES.md

Copy this file into your project's `references/` directory as `REFERENCES.md`
and fill in one section per paper. Relevance notes are mandatory — they
connect each paper back to your project's specific decisions.

---

## 1. [Paper Title]

- **arXiv:** [2312.10793](https://arxiv.org/abs/2312.10793)
- **PDF:** `references/2312.10793.pdf`
- **Authors:** Author One, Author Two, Author Three
- **Published:** 2023-12-17
- **Categories:** cs.CL, cs.AI

### Relevance to [Project Name]

[2-4 sentences explaining why this paper matters for YOUR project's specific
decisions. Example:]

This paper categorizes instruction types into NLP tasks, coding, and general
chat, and studies how mixing ratios affect fine-tuning performance. Key finding:
instruction types compete — coding data improves coding but harms general chat.
This informed [Project Name]'s strategy of balancing [N] tool schemas across
[category count] categories to minimize cross-task interference.

### BibTeX

```bibtex
@article{author2023title,
  title     = {Full Paper Title},
  author    = {Author One and Author Two and Author Three},
  year      = {2023},
  eprint    = {2312.10793},
  archivePrefix = {arXiv},
  primaryClass = {cs.CL},
  url       = {https://arxiv.org/abs/2312.10793}
}
```

---

## Summary Matrix

For the project README, use a compact table:

| arXiv ID | Topic | Project Impact |
|----------|-------|----------------|
| [2312.10793](https://arxiv.org/abs/2312.10793) | Short topic | One-line project impact |
| [2601.19280](https://arxiv.org/abs/2601.19280) | Short topic | One-line project impact |

See `references/REFERENCES.md` for full summaries and BibTeX.
