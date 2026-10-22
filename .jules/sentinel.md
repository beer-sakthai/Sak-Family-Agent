## 2024-10-22 - Replace xml.etree.ElementTree with defusedxml to prevent XML attacks
**Vulnerability:** The standard library `xml.etree.ElementTree` is vulnerable to XML attacks such as Billion Laughs and XXE (flagged by Bandit B405/B314).
**Learning:** `xml.etree.ElementTree` was used extensively in skills for parsing arXiv results and modifying Office Open XML documents (PowerPoint redlines).
**Prevention:** Always use `defusedxml.ElementTree` (or `defusedxml.minidom`) when parsing untrusted XML, as it is a drop-in replacement that safely defuses malicious entities. Ensure updates are applied symmetrically across duplicated persona skill files.
