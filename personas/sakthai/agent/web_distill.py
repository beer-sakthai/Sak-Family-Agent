"""Zero-cost HTML distillation and prompt-injection boundary sanitization.

Provides lightweight HTML-to-Markdown distillation stripping scripts, styles,
and navigation boilerplates, and wraps external untrusted web content in
impermeable boundary tags (`<untrusted_web_content source="...">`).
"""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser


class _HTMLToMarkdownParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.result: list[str] = []
        self._tag_stack: list[str] = []
        self._current_href: str | None = None
        self._link_text: list[str] = []
        self._ignore_stack: list[str] = []

    _IGNORE_TAGS = {"script", "style", "noscript", "svg", "header", "footer", "nav"}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in self._IGNORE_TAGS:
            self._ignore_stack.append(tag_lower)
            return

        if self._ignore_stack:
            return

        self._tag_stack.append(tag_lower)

        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag_lower[1])
            self.result.append("\n\n" + "#" * level + " ")
        elif tag_lower in ("p", "div", "article", "section"):
            self.result.append("\n\n")
        elif tag_lower == "li":
            self.result.append("\n- ")
        elif tag_lower == "a":
            href_dict = dict(attrs)
            self._current_href = href_dict.get("href")
            self._link_text = []
        elif tag_lower == "br":
            self.result.append("\n")
        elif tag_lower == "code":
            self.result.append("`")
        elif tag_lower == "pre":
            self.result.append("\n```\n")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if self._ignore_stack:
            if tag_lower == self._ignore_stack[-1]:
                self._ignore_stack.pop()
            return

        if self._tag_stack and self._tag_stack[-1] == tag_lower:
            self._tag_stack.pop()

        if tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6", "p", "div", "article", "section"):
            self.result.append("\n\n")
        elif tag_lower == "a":
            link_content = "".join(self._link_text).strip()
            if self._current_href and link_content:
                self.result.append(f"[{link_content}]({self._current_href})")
            elif link_content:
                self.result.append(link_content)
            self._current_href = None
            self._link_text = []
        elif tag_lower == "code":
            self.result.append("`")
        elif tag_lower == "pre":
            self.result.append("\n```\n")

    def handle_data(self, data: str) -> None:
        if self._ignore_stack:
            return

        clean_text = unescape(data)
        if self._current_href is not None:
            self._link_text.append(clean_text)
        else:
            self.result.append(clean_text)


def distill_html_to_markdown(html_content: str, source_url: str | None = None) -> str:
    """Distill raw HTML to semantic Markdown, stripping boilerplate and scripts."""
    if not html_content or not html_content.strip():
        return ""

    parser = _HTMLToMarkdownParser()
    try:
        parser.feed(html_content)
        parser.close()
        raw_markdown = "".join(parser.result)
    except Exception:
        # Graceful fallback: regex-based strip
        no_scripts = re.sub(
            r"<(script|style|svg|noscript)[^>]*>.*?</\1>",
            "",
            html_content,
            flags=re.DOTALL | re.IGNORECASE,
        )
        raw_markdown = re.sub(r"<[^>]+>", " ", no_scripts)

    # Clean whitespace while preserving markdown headers and linebreaks
    lines = [line.strip() for line in raw_markdown.splitlines()]
    compact_lines: list[str] = []
    blank = False
    for line in lines:
        if line:
            compact_lines.append(line)
            blank = False
        elif not blank:
            compact_lines.append("")
            blank = True

    return "\n".join(compact_lines).strip()


def wrap_untrusted_web_content(content: str, source_url: str) -> str:
    """Wrap scraped or extracted external text in protective untrusted boundary tags."""
    # Sanitize closing tags to prevent prompt injection boundary escapes
    sanitized = content.replace("</untrusted_web_content>", "&lt;/untrusted_web_content&gt;")
    clean_url = (source_url or "unknown").strip().replace('"', "%22").replace(">", "%3E")
    return f'<untrusted_web_content source="{clean_url}">\n{sanitized}\n</untrusted_web_content>'


def sanitize_and_distill_web_response(raw_html: str, source_url: str) -> str:
    """Combine zero-cost HTML distillation with untrusted boundary protection."""
    distilled = distill_html_to_markdown(raw_html, source_url=source_url)
    return wrap_untrusted_web_content(distilled, source_url=source_url)
