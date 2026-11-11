## 2024-10-22 - Replace xml.etree.ElementTree with defusedxml to prevent XML attacks
**Vulnerability:** The standard library `xml.etree.ElementTree` is vulnerable to XML attacks such as Billion Laughs and XXE (flagged by Bandit B405/B314).
**Learning:** `xml.etree.ElementTree` was used extensively in skills for parsing arXiv results and modifying Office Open XML documents (PowerPoint redlines).
**Prevention:** Always use `defusedxml.ElementTree` (or `defusedxml.minidom`) when parsing untrusted XML, as it is a drop-in replacement that safely defuses malicious entities. Ensure updates are applied symmetrically across duplicated persona skill files.

## 2024-10-23 - Replace eval with simpleeval.simple_eval
**Vulnerability:** Use of `eval()` in Python examples without restrictions can lead to arbitrary code execution, command injection, and sandbox escapes if executed directly.
**Learning:** We identified an instance of `eval()` in `personas/sakking/skills/SakKing-smolagents/SKILL.md` parsing arbitrary mathematical expressions. Restricting `__builtins__` in `eval()` is a known anti-pattern and does NOT prevent sandbox escapes; safe alternatives like `simpleeval` or `ast.literal_eval` must be used for arbitrary string evaluation.
**Prevention:** Always use safe string evaluation alternatives like `simpleeval.simple_eval()` instead of `eval()` when evaluating dynamically provided code strings or inputs.
## 2024-10-23 - Avoid restricted eval anti-pattern
**Vulnerability:** Command Injection via `eval()`. Attempting to secure `eval()` by restricting globals/locals (e.g., `eval(expr, {"__builtins__": {}})`) is an anti-pattern and does NOT prevent sandbox escapes.
**Learning:** Python's object introspection allows traversing `().__class__.__bases__[0].__subclasses__()` to bypass the restricted dictionary and execute arbitrary commands.
**Prevention:** Never use `eval()` on user input. Use secure evaluators like `ast.literal_eval` for literals, or dedicated safe-parsing libraries like `simpleeval` for mathematical expressions.
