## 2026-06-18 - XSS Protection in Dashboard
**Vulnerability:** The Streamlit dashboard was using `unsafe_allow_html=True` in several `st.markdown` calls while interpolating user-controlled or external data (skill names, descriptions, tags, agent thought processes). This could lead to Cross-Site Scripting (XSS) if a malicious skill definition or memory entry was loaded.
**Learning:** Streamlit's `unsafe_allow_html` is often necessary for custom styling, but it shifts the responsibility of sanitization entirely to the developer. Even "metadata" like timestamps or source labels should be escaped if they originate from external sources.
**Prevention:** Always wrap variables in `html.escape()` when using `unsafe_allow_html=True`. Added this to the project's security patterns.
