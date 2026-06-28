# Gradio 6 Migration — condensed reference

Source: https://gradio.app/main/guides/gradio-6-migration-guide (retrieved 2026-06-21)

## Breaking changes (Gradio 5 → 6)

### App-level
- `theme`, `css`, `css_paths`, `js`, `head`, `head_paths` moved from `gr.Blocks()` constructor to `demo.launch()`.
- `show_api` in `launch()` replaced by `footer_links` (list of: `"api"`, `"gradio"`, `"settings"`).

### Events / API visibility
- Event listener `show_api` removed.
- `api_name=False` no longer valid.
- Use `api_visibility` instead: `"public"`, `"undocumented"`, `"private"`.

### Chat format
- Tuple format `[[user, bot], ...]` removed. Use `[{"role": "user", "content": [...]}, ...]`.
- Content is always a list of content blocks: `{"type": "text", "text": "..."}` (OpenAI-style).
- `like_user_message` moved from `.like()` event to `gr.Chatbot(like_user_message=True)`.

### Interface / ChatInterface API names
- Default API names now derive from the passed function name (e.g. `generate_text` → `/generate_text`).
- Previously: `/predict` and `/chat`.

### Video subtitles
- Returning `(video_path, subtitle_path)` tuple removed.
- Return `gr.Video(value=..., subtitles=...)` instead.

### Dataframe counts
- `row_count=(5, "fixed")` and `col_count=(3, "dynamic")` tuple format removed.
- Use `row_count=5, row_limits=(5,5)` and `column_count=3, column_limits=(3,3)`.
- Dynamic: pass `row_limits=None`.

### Other defaults changed
- `gr.HTML(padding=...)` default is now `False` (was `True`).
- `allow_tags=True` is now default for `gr.Chatbot` (was `False`).
- `cache_examples` no longer accepts `"lazy"`; use `cache_examples=True` + `cache_mode="lazy"`.

## Compatibility helper
```bash
pip install --upgrade gradio==5.50
```
Emits deprecation warnings for all Gradio 6 breaking changes before you actually upgrade.
