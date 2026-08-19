# Stitch Design Prompt: Semantic Response Caching & Token Cost Optimizer Studio

> **Design Target:** `semantic_cache_token_optimizer_studio`  
> **Theme:** Obsidian Dark with Cyber Amber & Neon Cyan Accents (`#020617`, `#0f172a`, `#1e293b`, `#f59e0b`, `#06b6d4`, `#10b981`)  
> **Layout:** Modern Glassmorphic Operations Dashboard with Live Vector Distance Visualizer  
> **Target Framework:** Next.js 15, Tailwind CSS, Lucide React, SVG Gauge Polygons  

---

## 1. Visual Hierarchy & Overview

A futuristic, high-density AI operations panel designed for monitoring semantic cache efficiency, embedding vector distances, and real-time dollar cost savings across LLM provider inferences (Gemini 1.5 Pro, Claude 3.5 Sonnet, GPT-4o, and SakThai QLoRA).

```
+-----------------------------------------------------------------------------------------------+
|  SEMANTIC CACHE COMMAND BAR: Hit Rate: 84.5% | Tokens Saved: 142.5k | USD Saved: $2.45 | 1.8ms |
+---------------------------------------------------------------+-------------------------------+
|                                                               |                               |
|  INTERACTIVE VECTOR DISTANCE SIMULATOR                        |  LIVE RECENT CACHE ENTRIES    |
|  - Real-time prompt input with quick templates                |  - Dynamic search filter      |
|  - 64-D L2 Normalized Cosine Similarity Meter (0.70 - 0.99)   |  - Persona color badges       |
|  - Radial Hit/Miss SVG Gauge with Glowing Arc                 |  - Model pricing breakdown    |
|  - Side-by-side: Raw Prompt vs Retrieved Cached Output        |  - Instant 1-Click Invalidate |
|                                                               |                               |
+---------------------------------------------------------------+-------------------------------+
|  MODEL PRICING MATRIX & CUMULATIVE TOKEN SAVINGS FORECASTER   |  EXPIRATION TTL TICKER        |
|  [Claude: +$1.42] [Gemini Pro: +$0.68] [GPT-4o: +$0.35]       |  - Automated LRU cleanups     |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Color Palette & Styling Tokens

- **Surface Base:** `bg-slate-950` with subtle dot-grid background overlay.
- **Glass Panels:** `bg-slate-900/80 border border-slate-800/80 backdrop-blur-xl shadow-2xl rounded-2xl`.
- **Accent Radiance:**
  - **Hit Indicator:** `#10b981` (Emerald-500) glowing pulse.
  - **Miss Indicator:** `#f43f5e` (Rose-500) subtle border ring.
  - **Vector Similarity:** `#06b6d4` (Cyan-500) animated fill bar.
  - **Financial Savings:** `#f59e0b` (Amber-500) bold typographic badges.

---

## 3. Interactive Components & Micro-Interactions

### A. Radial Similarity Gauge (`CosineGauge`)
- SVG circular gauge displaying real-time cosine similarity $(0.00 \to 1.00)$ calculated between the user's live keystrokes and existing 64-D L2-normalized vector embeddings.
- Smooth CSS transition `stroke-dashoffset 400ms cubic-bezier(0.4, 0, 0.2, 1)`.

### B. Live Vector Similarity Meter
- Slider control with dynamic step increments $(0.01)$ allowing engineers to tune fuzzy cache matching thresholds without cold restarts.

### C. Persona Partition Filter & TTL Expiration Badges
- Filterable directory displaying hit frequency counts, token approximations ($1\text{ token} \approx 4\text{ chars}$), and countdown timestamps.

---

## 4. Production Tailwind CSS Component Mock

```tsx
<div className="bg-slate-950 text-slate-100 min-h-screen p-6 font-sans">
  {/* Top Metric Strip */}
  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
    <div className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl shadow-lg flex items-center justify-between">
      <div>
        <span className="text-xs text-slate-400 font-mono">CACHE HIT RATIO</span>
        <div className="text-2xl font-bold text-emerald-400 mt-1">84.5%</div>
        <span className="text-[10px] text-slate-500 font-mono">198 hits / 240 queries</span>
      </div>
      <div className="w-10 h-10 rounded-lg bg-emerald-950/60 border border-emerald-800/50 flex items-center justify-center text-emerald-400 font-bold">
        ⚡
      </div>
    </div>
    {/* Dollar Savings, Tokens, Latency */}
  </div>
</div>
```
