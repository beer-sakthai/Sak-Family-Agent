#!/usr/bin/env python3
"""Generate HTML and PDF from CV markdown files.
Usage: uv run python generate-cv-pdf.py

Requires: weasyprint, markdown (installed via uv)
"""

import markdown
from weasyprint import HTML
import os
import sys

HOME = os.path.expanduser("~/home/house-of-sak")

def make_html(header_name, header_title, contact_lines, body_md, closing="Built from a shelter in Cork. Still here. Still building."):
    body = markdown.markdown(body_md, extensions=["tables", "fenced_code"])
    contact_html = ""
    if contact_lines:
        parts = []
        for label, url in contact_lines:
            if url:
                parts.append(f'<a href="{url}">{label}</a>')
            else:
                parts.append(label)
        contact_html = '<div class="contact">' + ' <span class="sep">|</span> '.join(parts) + "</div>"

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><style>
@page {{
    size: A4;
    margin: 1.8cm 1.5cm 1.5cm 1.5cm;
    @bottom-center {{
        content: "{closing}";
        font-size: 7pt;
        color: #999;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }}
}}
body {{ font-family: 'Helvetica Neue', Arial, Helvetica, sans-serif; font-size: 9.5pt; line-height: 1.45; color: #222; max-width: 100%; }}
h2 {{ font-size: 12pt; color: #1a73e8; border-bottom: 1px solid #ddd; padding-bottom: 2px; margin: 16px 0 8px 0; page-break-after: avoid; }}
h3 {{ font-size: 10.5pt; color: #333; margin: 10px 0 4px 0; page-break-after: avoid; }}
table {{ width: 100%; border-collapse: collapse; font-size: 9pt; margin: 5px 0; }}
table th {{ background: #f0f4fa; color: #333; font-weight: 600; text-align: left; padding: 4px 8px; border: 1px solid #d0d7de; }}
table td {{ padding: 4px 8px; border: 1px solid #d0d7de; vertical-align: top; }}
table tr:nth-child(even) td {{ background: #f8f9fa; }}
ul {{ margin: 3px 0; padding-left: 18px; }}
li {{ margin-bottom: 1px; }}
a {{ color: #1a73e8; text-decoration: none; }}
hr {{ border: none; border-top: 1px solid #e0e0e0; margin: 6px 0; }}
.header {{ text-align: center; margin-bottom: 0.6cm; padding-bottom: 0.4cm; border-bottom: 2.5px solid #1a73e8; }}
.header h1 {{ font-size: 20pt; margin: 0 0 2px 0; color: #1a1a1a; letter-spacing: 0.5px; }}
.subtitle {{ font-size: 11pt; color: #1a73e8; font-weight: 600; margin: 0 0 4px 0; }}
.contact {{ font-size: 8.5pt; color: #555; margin-top: 4px; }}
.contact a {{ color: #1a73e8; }}
.sep {{ color: #bbb; margin: 0 4px; }}
</style></head>
<body>
<div class="header">
    <h1>{header_name}</h1>
    <div class="subtitle">{header_title}</div>
    {contact_html}
</div>
{body}
</body>
</html>"""


def parse_md(filepath):
    with open(filepath) as f:
        content = f.read()
    lines = content.strip().split("\n")
    header_name = lines[0].replace("# ", "").strip()
    header_title = lines[1].replace("**", "").strip()
    contact_lines = []
    for item in lines[3].split("|"):
        item = item.strip()
        if "[" in item and "](" in item:
            label = item[item.index("[") + 1 : item.index("]")]
            url = item[item.index("(") + 1 : item.index(")")]
            contact_lines.append((label, url))
        elif item:
            contact_lines.append((item, None))
    sep_idx = next((i for i, l in enumerate(lines) if l.strip() == "---"), None)
    body_md = "\n".join(lines[sep_idx + 1 :]) if sep_idx else "\n".join(lines[4:])
    return header_name, header_title, contact_lines, body_md


def main():
    variants = [
        ("cv-ai-skills-2026.md", "cv-ai-skills-2026.html", "cv-ai-skills-2026.pdf",
         "Built from a shelter in Cork. Still here. Still building."),
        ("cv-business-2026.md", "cv-business-2026.html", "cv-business-2026.pdf",
         "Available for operations, management, and business development roles in Cork."),
    ]

    for src_md, out_html, out_pdf, closing in variants:
        src_path = os.path.join(HOME, src_md)
        if not os.path.exists(src_path):
            print(f"⚠ Skipping {src_md}: not found")
            continue

        name, title, contacts, body = parse_md(src_path)
        html_content = make_html(name, title, contacts, body, closing)

        html_path = os.path.join(HOME, out_html)
        with open(html_path, "w") as f:
            f.write(html_content)

        pdf_path = os.path.join(HOME, out_pdf)
        HTML(string=html_content).write_pdf(pdf_path)

        print(f"✅ {out_html} ({len(html_content)} chars) + {out_pdf} ({os.path.getsize(pdf_path)} bytes)")


if __name__ == "__main__":
    main()
