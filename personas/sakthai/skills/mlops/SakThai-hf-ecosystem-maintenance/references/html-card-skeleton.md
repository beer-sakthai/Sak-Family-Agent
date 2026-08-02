# HTML Card Skeleton — Complete Model Card Template

A copy-paste-ready, HTML-based model card skeleton that assembles all enrichment sections into one polished file. Produces the same visual quality as the vision-7b and tts-model cards (~220–320 lines, ~7–13 KB).

```
├── YAML frontmatter (tags, license, model-index, extra.sibling, datasets)
├── Title + badge bar (<h1> + <p align="center">)
├── Blockquote intro (<blockquote>)
├── Try It Now 🚀 (demo Space CTA)
├── Pipeline Integration (ASCII diagram or table)
├── What It Is (file table, bullet highlights)
├── Quick Start (2–3 runtimes: Python, curl, local)
├── Use Cases (table)
├── Intended Use & Limits (✅/⚠️/💻)
├── Family Table (all siblings with download counts)
├── 🌱 Low-Download Gems (under-appreciated siblings)
├── Datasets (all with dl)
├── Spaces (all with role)
├── Ecosystem count line ("N models · M datasets · K Spaces")
├── Links (House of Sak, GitHub, all models, all datasets)
└── License + footer
```

## Template

```markdown
---
license: <license>
language:
- en
- <other_langs>
pipeline_tag: <pipeline-tag>
library_name: <lib>
tags:
- <tag1>
- <tag2>
- sakthai
- house-of-sak
- edge
- cpu-inference
- privacy
extra:
  sibling: <author>/<demo-space>
model-index:
- name: <model-name>
  results:
  - task:
      type: <pipeline-tag>
      name: <task-name>
    dataset:
      name: <eval-dataset>
      type: <dataset-ref>
    metrics:
    - type: <metric-type>
      value: <score>
      name: <metric-label>
      verified: false
---

<h1 align="center">Your Model Name &#x1F3A4;</h1>
<p align="center"><em>One-liner · Key specs · Size GGUF, CPU-only</em></p>
<p align="center">
  <img src="https://img.shields.io/endpoint?url=https://huggingface.co/api/models/<author>/<repo>&label=downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
  <img src="https://img.shields.io/badge/base-<BaseModel>%<Size>B-blueviolet" alt="Base"/>
  <img src="https://img.shields.io/badge/GGUF-<Qtype>%<Size>MB-orange" alt="GGUF"/>
  <img src="https://img.shields.io/badge/License-<license>-green" alt="License"/>
  <a href="https://huggingface.co/collections/<author>/<collection-slug>"><img src="https://img.shields.io/badge/%F0%9F%8F%A0-SakThai%20Family-6644cc" alt="Collection"/></a>
  <a href="https://huggingface.co/spaces/<author>/<demo-space>"><img src="https://img.shields.io/badge/%F0%9F%9A%80-Try%20on%20Spaces-47d147" alt="Spaces"/></a>
</p>

<blockquote>
The <strong>role</strong> of the pipeline — description.
<a href="https://huggingface.co/<author>">House of Sak</a>.
No data leaves your machine.
</blockquote>

<hr />

<h2>Try It Now &#x1F680;</h2>

<p><strong><a href="https://huggingface.co/spaces/<author>/<demo-space>">Demo Name</a></strong> &mdash; short CTA.</p>

<hr />

<h2>Pipeline Integration</h2>

<pre><code>                    &#x250C;... pipeline diagram
...</code></pre>

<h2>What It Is</h2>
<p>A <strong>format</strong> (size) build of <strong>Base Model</strong>.</p>
<ul>
<li><strong>Speed:</strong> ~Nx real-time on a single core (~N MB RAM)</li>
<li><strong>Footprint:</strong> Edge, Raspberry Pi, embedded</li>
<li><strong>Quality:</strong> MOS/value benchmark</li>
<li><strong>Privacy:</strong> All inference local</li>
</ul>

<hr />

<h2>Quick Start</h2>

<h3>Python (HF InferenceClient)</h3>
<pre>from huggingface_hub import InferenceClient
client = InferenceClient()
result = client.<method>(&quot;input&quot;, model=&quot;<author>/<repo>&quot;)
</pre>

<h3>CLI (curl)</h3>
<pre>curl https://api-inference.huggingface.co/models/&lt;author&gt;/&lt;repo&gt; \\
  -H &quot;Authorization: Bearer \$HF_TOKEN&quot; \\
  -H &quot;Content-Type: application/json&quot; \\
  -d '{&quot;inputs&quot;:&quot;Hello&quot;}' \\
  --output result.ext</pre>

<hr />

<h2>Use Cases</h2>
<table>
<tr><th>Use Case</th><th>Description</th></tr>
<tr><td><strong>Use case 1</strong></td><td>Description</td></tr>
</table>

<hr />

<h2>Intended Use &amp; Limits</h2>
<ul>
<li><strong>&#x2705; Great for:</strong> Use cases</li>
<li><strong>&#x26A0;&#xFE0F; Limits:</strong> Known limitations</li>
<li><strong>&#x1F4BB; Hardware:</strong> N MB RAM, any CPU including ARM</li>
</ul>

<hr />

<h2>SakThai Family</h2>
<table>
<tr><th>Model</th><th>DL</th></tr>
<tr><td><a href="...">top-model</a></td><td>N &#x2B07;</td></tr>
<!-- all siblings with current download counts -->
</table>

<h3>&#x1F331; Low-Download Gems</h3>
<table>
<tr><th>Model</th><th>DL</th><th>Best for</th></tr>
<tr><td><a href="...">underdog-model</a></td><td>N</td><td>Why it matters</td></tr>
</table>

<h3>Datasets</h3>
<table>
<tr><th>Dataset</th><th>DL</th></tr>
<tr><td><a href="...">dataset-name</a></td><td>N &#x2B07;</td></tr>
</table>

<h3>Spaces</h3>
<table>
<tr><th>Space</th><th>Role</th></tr>
<tr><td><a href="...">space-name</a></td><td>Role description</td></tr>
</table>

<p><strong>N models &#xB7; M datasets &#xB7; K Spaces</strong> &mdash; <a href="...">full collection</a></p>

<hr />

<h2>Links</h2>
<p><a href="https://house-of-sak.vercel.app">House of Sak</a> &#xB7;
<a href="https://github.com/beer-sakthai/Sak-Family-Agent">GitHub</a> &#xB7;
<a href="https://huggingface.co/<author>">All models</a></p>

<hr />

<h2>License</h2>
<p>&lt;license&gt;</p>
<hr />
<p><em>Built from a shelter in Cork, Ireland.</em></p>
```

## When to Use Each Format

| Format | When |
|--------|------|
| **HTML tags** (`<h1>`, `<table>`, `<pre>`, `<blockquote>`) | Card needs visual polish — badges, alignment, clean tables |
| **Pure markdown** (`##`, `|table|`, `` `code` ``) | Quick card for a fresh repo — get info up fast, polish later |
| **Mixed** (HTML for layout + markdown for prose) | Preferred for well-maintained ecosystem cards |

## Generating HTML Entities

For emojis in HTML context (inside `<h1>`, `<p>`, `<td>`), use hex entities:
- 🚀 = `&#x1F680;`
- 🌱 = `&#x1F331;`
- 🎤 = `&#x1F3A4;`
- ⬇ = `&#x2B07;`
- ⬅ = `&#x2B1F;`
- ✅ = `&#x2705;`
- ⚠️ = `&#x26A0;&#xFE0F;`
- 💻 = `&#x1F4BB;`
- 📖 = `&#x1F4D6;`

For inline HTML in markdown, use `&mdash;` (—), `&middot;` (·), `&amp;` (&amp;), `&lt;` (&lt;).

## Badge URL Patterns

| Badge | URL |
|-------|-----|
| Downloads | `https://img.shields.io/endpoint?url=https://huggingface.co/api/models/<author>/<repo>&label=downloads&color=blue` |
| Base model | `https://img.shields.io/badge/base-<Name>%<Size>-blueviolet` |
| GGUF type | `https://img.shields.io/badge/GGUF-<Qtype>%<Size>MB-orange` |
| License | `https://img.shields.io/badge/License-<name>-green` |
| Collection | `https://img.shields.io/badge/%F0%9F%8F%A0-SakThai%20Family-6644cc` |
| Spaces demo | `https://img.shields.io/badge/%F0%9F%9A%80-Try%20on%20Spaces-47d147` |

## Write-Through via Git Clone

```bash
# Clone (token auth)
git clone https://<author>:$(cat ~/.cache/huggingface/token)@huggingface.co/<author>/<repo>

# Write README
python3 -c "
with open('/tmp/cloned-repo/README.md', 'w') as f:
    f.write(content)
"

# Commit + push
cd /tmp/cloned-repo
git add README.md
git commit -m "Comprehensive card: badges, Space link, full family table, datasets, low-download gems"
git push origin main
```

> **Token note:** The stored HF token works for git pushes and REST API writes despite `whoami` returning `"Invalid"`. This is a known quirk — the token has write scopes even if the identity endpoint rejects it.
